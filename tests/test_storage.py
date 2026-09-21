from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from t1shipments.core.auth.storage import FileStorage
from t1shipments.core.auth.token import Token


@pytest.fixture
def tmp_credentials(tmp_path) -> Path:
    return tmp_path / "credentials.json"


@pytest.fixture
def sample_token() -> Token:
    return Token(
        access_token="abc",
        refresh_token="xyz",
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
    )


def test_file_storage_save_and_load(tmp_credentials, sample_token):
    storage = FileStorage(path=tmp_credentials)
    storage.save(sample_token)
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "abc"
    assert loaded.refresh_token == "xyz"


def test_file_storage_permissions(tmp_credentials, sample_token):
    import os
    storage = FileStorage(path=tmp_credentials)
    storage.save(sample_token)
    if os.name != "nt":
        mode = oct(tmp_credentials.stat().st_mode)[-3:]
        assert mode == "600"


def test_file_storage_clear(tmp_credentials, sample_token):
    storage = FileStorage(path=tmp_credentials)
    storage.save(sample_token)
    storage.clear()
    assert not tmp_credentials.exists()


def test_file_storage_load_missing(tmp_credentials):
    storage = FileStorage(path=tmp_credentials)
    assert storage.load() is None


def test_file_storage_load_corrupt(tmp_credentials):
    tmp_credentials.parent.mkdir(parents=True, exist_ok=True)
    tmp_credentials.write_text("NOT JSON")
    storage = FileStorage(path=tmp_credentials)
    assert storage.load() is None


def test_hybrid_falls_back_to_file(monkeypatch, tmp_path, sample_token):
    def bad_import(name, *args, **kwargs):
        if name == "keyring":
            raise ImportError("no keyring")
        return original_import(name, *args, **kwargs)

    import builtins
    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", bad_import)

    creds = tmp_path / "credentials.json"
    from t1shipments.core.auth.storage import FileStorage
    storage = FileStorage(path=creds)
    storage.save(sample_token)
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "abc"


def test_hybrid_demotes_to_file_when_keyring_save_fails(monkeypatch, tmp_path, sample_token):
    """Keyring backend exists (passes init probing) but errors at runtime — e.g. a
    denied/locked macOS Keychain. HybridStorage must fall back to file storage
    instead of propagating the keyring error."""
    from t1shipments.core.auth.storage import FileStorage, HybridStorage, KeyringStorage

    storage = HybridStorage.__new__(HybridStorage)
    storage._allow_file_fallback = True
    storage._backend = KeyringStorage()

    def bad_save(self, token):
        raise RuntimeError("keychain denied")

    monkeypatch.setattr(KeyringStorage, "save", bad_save)
    monkeypatch.setattr(FileStorage, "save", lambda self, token: None)
    monkeypatch.setattr(FileStorage, "load", lambda self: sample_token)

    storage.save(sample_token)
    assert isinstance(storage._backend, FileStorage)
    assert storage.load() is sample_token


def test_hybrid_raises_when_keyring_fails_and_fallback_disabled(monkeypatch, sample_token):
    from t1shipments.core.auth.storage import HybridStorage, KeyringStorage
    from t1shipments.core.exceptions import StorageError

    storage = HybridStorage.__new__(HybridStorage)
    storage._allow_file_fallback = False
    storage._backend = KeyringStorage()

    def bad_save(self, token):
        raise RuntimeError("keychain denied")

    monkeypatch.setattr(KeyringStorage, "save", bad_save)

    with pytest.raises(StorageError):
        storage.save(sample_token)


def test_hybrid_load_prefers_file_when_keyring_token_lacks_client_credentials(
    monkeypatch, sample_token
):
    """A keyring read can succeed but return a stale entry saved before
    client_id/client_secret existed. That unusable token must not shadow a
    usable, fully-populated token sitting in file storage."""
    from t1shipments.core.auth.storage import FileStorage, HybridStorage, KeyringStorage

    stale_keyring_token = Token(access_token="stale", refresh_token="stale-r")
    full_file_token = Token(
        access_token="fresh", refresh_token="fresh-r", client_id="cid", client_secret="csec"
    )

    storage = HybridStorage.__new__(HybridStorage)
    storage._allow_file_fallback = True
    storage._backend = KeyringStorage()

    monkeypatch.setattr(KeyringStorage, "load", lambda self: stale_keyring_token)
    monkeypatch.setattr(FileStorage, "load", lambda self: full_file_token)

    loaded = storage.load()
    assert loaded is full_file_token
    assert isinstance(storage._backend, FileStorage)


def test_hybrid_load_keeps_keyring_token_when_it_has_client_credentials(monkeypatch, sample_token):
    from t1shipments.core.auth.storage import HybridStorage, KeyringStorage

    complete_token = Token(
        access_token="tok", refresh_token="ref", client_id="cid", client_secret="csec"
    )

    storage = HybridStorage.__new__(HybridStorage)
    storage._allow_file_fallback = True
    storage._backend = KeyringStorage()

    monkeypatch.setattr(KeyringStorage, "load", lambda self: complete_token)

    loaded = storage.load()
    assert loaded is complete_token
    assert isinstance(storage._backend, KeyringStorage)


def test_hybrid_clear_also_clears_file_fallback(monkeypatch):
    from t1shipments.core.auth.storage import FileStorage, HybridStorage, KeyringStorage

    storage = HybridStorage.__new__(HybridStorage)
    storage._allow_file_fallback = True
    storage._backend = KeyringStorage()

    monkeypatch.setattr(KeyringStorage, "clear", lambda self: None)
    file_cleared = []
    monkeypatch.setattr(FileStorage, "clear", lambda self: file_cleared.append(True))

    storage.clear()
    assert file_cleared == [True]


def test_token_serialization_with_client_credentials():
    token = Token(
        access_token="tok",
        refresh_token="ref",
        client_id="my-client-id",
        client_secret="my-client-secret",
    )
    d = token.to_dict()
    assert d["client_id"] == "my-client-id"
    assert d["client_secret"] == "my-client-secret"

    restored = Token.from_dict(d)
    assert restored.client_id == "my-client-id"
    assert restored.client_secret == "my-client-secret"


def test_file_storage_saves_and_loads_client_credentials(tmp_credentials):
    token = Token(
        access_token="tok",
        refresh_token="ref",
        client_id="cid-123",
        client_secret="csec-456",
    )
    storage = FileStorage(path=tmp_credentials)
    storage.save(token)
    loaded = storage.load()
    assert loaded is not None
    assert loaded.client_id == "cid-123"
    assert loaded.client_secret == "csec-456"
