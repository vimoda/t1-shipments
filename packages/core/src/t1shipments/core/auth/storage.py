from __future__ import annotations

import json
import logging
import os
import stat
from pathlib import Path
from typing import Protocol

from ..exceptions import StorageError
from .token import Token

log = logging.getLogger("t1shipments.auth")

_SERVICE_NAME = "t1shipments"
_ACCOUNT_NAME = "default"


class TokenStorage(Protocol):
    def save(self, token: Token) -> None: ...
    def load(self) -> Token | None: ...
    def clear(self) -> None: ...


class InMemoryStorage:
    """Non-persistent storage — token lives only for the lifetime of the object."""

    def __init__(self, token: Token | None = None) -> None:
        self._token = token

    def save(self, token: Token) -> None:
        self._token = token

    def load(self) -> Token | None:
        return self._token

    def clear(self) -> None:
        self._token = None


class KeyringStorage:
    def save(self, token: Token) -> None:
        import keyring
        keyring.set_password(_SERVICE_NAME, _ACCOUNT_NAME, json.dumps(token.to_dict()))

    def load(self) -> Token | None:
        import keyring
        raw = keyring.get_password(_SERVICE_NAME, _ACCOUNT_NAME)
        if raw is None:
            return None
        return Token.from_dict(json.loads(raw))

    def clear(self) -> None:
        import keyring
        try:
            keyring.delete_password(_SERVICE_NAME, _ACCOUNT_NAME)
        except Exception:
            pass


class FileStorage:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (Path.home() / ".t1shipments" / "credentials.json")

    def save(self, token: Token) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(token.to_dict(), indent=2))
        if os.name != "nt":
            self._path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    def load(self) -> Token | None:
        if not self._path.exists():
            return None
        try:
            return Token.from_dict(json.loads(self._path.read_text()))
        except Exception:
            return None

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()


class HybridStorage:
    """Uses keyring when available; falls back to file-based storage.

    Set allow_file_fallback=False to raise StorageError if keyring is unavailable
    instead of silently falling back.
    """

    def __init__(self, allow_file_fallback: bool = True) -> None:
        self._allow_file_fallback = allow_file_fallback
        self._backend: TokenStorage
        try:
            import keyring
            kr = keyring.get_keyring()
            if type(kr).__name__ == "fail.Keyring" or "null" in type(kr).__name__.lower():
                raise RuntimeError("no suitable keyring backend")
            self._backend = KeyringStorage()
        except Exception:
            if not allow_file_fallback:
                raise StorageError(
                    "Keyring is unavailable and allow_file_fallback=False. "
                    "Install a keyring backend or use FileStorage directly."
                )
            self._backend = FileStorage()

    def _demote_to_file(self, exc: Exception) -> None:
        """Called when the keyring backend fails at runtime (not just at init) —
        e.g. a denied/locked macOS Keychain. Falls back to file storage for the
        rest of this process, matching the class's documented behavior."""
        if not self._allow_file_fallback:
            raise StorageError(
                f"Keyring backend failed and allow_file_fallback=False: {exc}"
            ) from exc
        log.warning("Keyring backend failed (%s); falling back to file storage.", exc)
        self._backend = FileStorage()

    def save(self, token: Token) -> None:
        try:
            self._backend.save(token)
        except Exception as exc:
            if not isinstance(self._backend, KeyringStorage):
                raise
            self._demote_to_file(exc)
            self._backend.save(token)

    def load(self) -> Token | None:
        try:
            token = self._backend.load()
        except Exception as exc:
            if not isinstance(self._backend, KeyringStorage):
                raise
            self._demote_to_file(exc)
            return self._backend.load()

        # A keyring read can succeed (no exception) yet return a stale entry
        # left over from before client_id/client_secret were persisted, or
        # from a login that itself silently failed to overwrite it. Such a
        # token is unusable for from_settings() re-auth, so don't let it
        # shadow a usable, fully-populated token saved to file storage.
        if isinstance(self._backend, KeyringStorage) and not self._has_client_credentials(token):
            file_token = FileStorage().load()
            if self._has_client_credentials(file_token):
                log.warning(
                    "Keyring token is missing client credentials (stale entry?); "
                    "using file storage token instead."
                )
                self._backend = FileStorage()
                return file_token

        return token

    @staticmethod
    def _has_client_credentials(token: Token | None) -> bool:
        return bool(token and token.client_id and token.client_secret)

    def clear(self) -> None:
        self._backend.clear()
        if isinstance(self._backend, KeyringStorage):
            # Best-effort: also clear the file fallback so a stale keyring
            # entry can't resurrect credentials logout was meant to remove.
            try:
                FileStorage().clear()
            except Exception:
                pass
