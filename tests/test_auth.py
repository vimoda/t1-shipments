from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from t1envios.core.auth.authenticator import Authenticator
from t1envios.core.auth.token import Token
from t1envios.core.config import Endpoints
from t1envios.core.exceptions import AuthError, SessionExpiredError

from conftest import InMemoryStorage, load_fixture

AUTH_URL = "https://api.example.com/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token"
BALANCE_URL = "https://api.example.com/balance/consult"


@pytest.fixture
def endpoints() -> Endpoints:
    return Endpoints(base_url="https://api.example.com", auth_base_url="https://api.example.com")


def _auth(endpoints, storage=None, username=None, password=None) -> Authenticator:
    return Authenticator(
        client_id="id",
        client_secret="secret",
        endpoints=endpoints,
        http=httpx.Client(),
        username=username,
        password=password,
        storage=storage or InMemoryStorage(),
    )


def test_login_success(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, json=load_fixture("login"))
    storage = InMemoryStorage()
    auth = _auth(endpoints, storage=storage)
    token = auth.login()
    assert token.access_token == "test-access-token"
    assert token.refresh_token == "test-refresh-token"
    assert not token.is_expired()
    assert storage.load() == token


def test_login_client_credentials_grant(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, json=load_fixture("login"))
    auth = _auth(endpoints)
    auth.login()
    request = httpx_mock.get_requests()[0]
    body = request.content.decode()
    assert "grant_type=client_credentials" in body
    assert "username" not in body


def test_login_password_grant(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, json=load_fixture("login"))
    auth = _auth(endpoints, username="user@example.com", password="secret123")
    auth.login()
    request = httpx_mock.get_requests()[0]
    body = request.content.decode()
    assert "grant_type=password" in body
    assert "username=user%40example.com" in body


def test_login_failure(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, status_code=401)
    with pytest.raises(AuthError):
        _auth(endpoints).login()


def test_refresh_token(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, json=load_fixture("login"))
    expired = Token(
        access_token="old",
        refresh_token="old-refresh",
        expires_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    storage = InMemoryStorage(token=expired)
    auth = _auth(endpoints, storage=storage)
    auth._token = expired
    token = auth.refresh()
    assert token.access_token == "test-access-token"
    request = httpx_mock.get_requests()[0]
    body = request.content.decode()
    assert "grant_type=refresh_token" in body
    assert "refresh_token=old-refresh" in body


def test_refresh_raises_session_expired_on_failure(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, status_code=401)
    expired = Token(
        access_token="old",
        refresh_token="old-refresh",
        expires_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
    )
    auth = _auth(endpoints, storage=InMemoryStorage(token=expired))
    auth._token = expired
    with pytest.raises(SessionExpiredError):
        auth.refresh()


def test_ensure_valid_uses_stored_token(endpoints):
    valid = Token(
        access_token="stored",
        refresh_token=None,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=2),
    )
    auth = _auth(endpoints, storage=InMemoryStorage(token=valid))
    assert auth.ensure_valid().access_token == "stored"


def test_401_triggers_refresh_then_retry(httpx_mock, endpoints):
    httpx_mock.add_response(url=AUTH_URL, json=load_fixture("login"))
    httpx_mock.add_response(url=BALANCE_URL, status_code=401)
    httpx_mock.add_response(
        url=BALANCE_URL,
        json={"success": True, "detail": {"monto_actual": 100.0, "currency": "MXN", "credito": False}},
    )

    from t1envios.core.api.balance import BalanceResource

    valid = Token(
        access_token="old-valid",
        refresh_token="refresh-token",
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
    )
    storage = InMemoryStorage(token=valid)
    http = httpx.Client()
    auth = Authenticator("id", "secret", endpoints, http, storage=storage)
    auth._token = valid
    balance = BalanceResource(http, auth, endpoints).balance()
    assert balance.amount == 100.0
