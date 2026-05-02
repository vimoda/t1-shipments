from __future__ import annotations

import json
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from t1envios.core.auth.storage import FileStorage, HybridStorage
from t1envios.core.auth.token import Token


@pytest.fixture
def tmp_credentials(tmp_path) -> Path:
    return tmp_path / "credentials.json"


@pytest.fixture
def sample_token() -> Token:
    return Token(
        access_token="abc",
        refresh_token="xyz",
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
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
    from t1envios.core.auth.storage import FileStorage
    storage = FileStorage(path=creds)
    storage.save(sample_token)
    loaded = storage.load()
    assert loaded is not None
    assert loaded.access_token == "abc"
