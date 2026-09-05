from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import httpx

from ..exceptions import AuthError, SessionExpiredError
from .storage import InMemoryStorage, TokenStorage
from .token import Token

if TYPE_CHECKING:
    from ..config import Endpoints

log = logging.getLogger("t1shipments.auth")


class Authenticator:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        endpoints: "Endpoints",
        http: httpx.Client,
        storage: TokenStorage | None = None,
        auto_refresh: bool = True,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._endpoints = endpoints
        self._http = http
        self._storage: TokenStorage = storage if storage is not None else InMemoryStorage()
        self._token: Token | None = None
        self.auto_refresh = auto_refresh

    def login(self, username: str, password: str, store_id: str | None = None) -> Token:
        payload = {
            "grant_type": "password",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "username": username,
            "password": password,
        }
        if store_id:
            payload["store_id"] = store_id

        log.debug("Logging in (grant_type=%s)", payload.get("grant_type"))
        resp = self._http.post(
            self._endpoints.auth_url(self._endpoints.auth),
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise AuthError(f"Login failed [{resp.status_code}]: {resp.text}")

        data = resp.json()
        token = self._parse_token(data)
        token.client_id = self._client_id
        token.client_secret = self._client_secret
        self._token = token
        self._storage.save(token)
        log.debug("Login successful, token expires at %s", token.expires_at)
        return token

    def refresh(self) -> Token:
        if not self._token or not self._token.refresh_token:
            raise SessionExpiredError("No active session. Run: t1 auth login")

        log.debug("Refreshing token")
        resp = self._http.post(
            self._endpoints.auth_url(self._endpoints.auth),
            data={
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._token.refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise SessionExpiredError(
                f"Session expired (refresh failed [{resp.status_code}]). Run: t1 auth login"
            )

        data = resp.json()
        token = self._parse_token(data)
        token.client_id = self._client_id
        token.client_secret = self._client_secret
        self._token = token
        self._storage.save(token)
        return token

    def ensure_valid(self) -> Token:
        if self._token is None:
            stored = self._storage.load()
            if stored:
                self._token = stored
                if not self._client_id and stored.client_id:
                    self._client_id = stored.client_id
                if not self._client_secret and stored.client_secret:
                    self._client_secret = stored.client_secret

        if self._token is None:
            raise SessionExpiredError("No active session. Run: t1 auth login")

        # With auto_refresh: proactive 60s buffer + automatic refresh on expiry.
        # Without auto_refresh: only fail on actual expiry; caller manages refresh explicitly.
        buffer = 60 if self.auto_refresh else 0
        if self._token.is_expired(buffer_seconds=buffer):
            if self.auto_refresh and self._token.refresh_token:
                return self.refresh()
            raise SessionExpiredError(
                "Token expired. "
                + ("Run: t1 auth login" if self.auto_refresh else "Call auth_refresh to get new tokens.")
            )

        return self._token

    @property
    def token(self) -> Token | None:
        return self._token

    def logout(self) -> None:
        self._token = None
        self._storage.clear()

    @staticmethod
    def _parse_token(data: dict[str, Any]) -> Token:
        access = data.get("access_token") or data.get("token")
        if not access:
            raise AuthError(f"No access_token in response: {data}")

        expires_in = data.get("expires_in")
        if expires_in:
            expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=int(expires_in))
        else:
            expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)

        return Token(
            access_token=access,
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
        )
