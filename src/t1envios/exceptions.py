from __future__ import annotations

from typing import Any


class T1Error(Exception):
    """Base exception for all T1Envios errors."""


class AuthError(T1Error):
    """Authentication or token refresh failed."""


class RateLimitError(T1Error):
    """HTTP 429 received."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ApiError(T1Error):
    """Non-2xx HTTP response from the API."""

    def __init__(
        self,
        status: int,
        message: str,
        code: str | None = None,
        payload: Any = None,
    ) -> None:
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.code = code
        self.payload = payload


class ConfigError(T1Error):
    """Missing or invalid configuration."""
