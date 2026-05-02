from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest

from t1envios.core.auth.storage import TokenStorage
from t1envios.core.auth.token import Token
from t1envios.core.client import T1Client
from t1envios.core.config import Endpoints

FIXTURES = Path(__file__).parent / "fixtures" / "responses"


def load_fixture(name: str) -> dict | list:
    return json.loads((FIXTURES / f"{name}.json").read_text())


class InMemoryStorage:
    def __init__(self, token: Token | None = None) -> None:
        self._token = token

    def save(self, token: Token) -> None:
        self._token = token

    def load(self) -> Token | None:
        return self._token

    def clear(self) -> None:
        self._token = None


@pytest.fixture
def valid_token() -> Token:
    return Token(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
    )


@pytest.fixture
def expired_token() -> Token:
    return Token(
        access_token="expired-access-token",
        refresh_token="test-refresh-token",
        expires_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )


@pytest.fixture
def storage(valid_token: Token) -> InMemoryStorage:
    return InMemoryStorage(token=valid_token)


@pytest.fixture
def endpoints() -> Endpoints:
    return Endpoints(base_url="https://api.example.com", auth_base_url="https://api.example.com")


@pytest.fixture
def client(httpx_mock, valid_token: Token, endpoints: Endpoints) -> T1Client:
    storage = InMemoryStorage(token=valid_token)
    http = httpx.Client()
    c = T1Client(
        client_id="test-id",
        client_secret="test-secret",
        endpoints=endpoints,
        token_storage=storage,
        http_client=http,
    )
    return c
