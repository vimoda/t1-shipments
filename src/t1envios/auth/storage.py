from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Protocol

from .token import Token

_SERVICE_NAME = "t1envios"
_ACCOUNT_NAME = "default"


class TokenStorage(Protocol):
    def save(self, token: Token) -> None: ...
    def load(self) -> Token | None: ...
    def clear(self) -> None: ...


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
        self._path = path or (Path.home() / ".t1envios" / "credentials.json")

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
    """Uses keyring when available, falls back to file-based storage."""

    def __init__(self) -> None:
        self._backend: TokenStorage
        try:
            import keyring
            kr = keyring.get_keyring()
            # fail-fast if only dummy keyring available
            if type(kr).__name__ == "fail.Keyring" or "null" in type(kr).__name__.lower():
                raise RuntimeError("no suitable keyring backend")
            self._backend = KeyringStorage()
        except Exception:
            self._backend = FileStorage()

    def save(self, token: Token) -> None:
        self._backend.save(token)

    def load(self) -> Token | None:
        return self._backend.load()

    def clear(self) -> None:
        self._backend.clear()
