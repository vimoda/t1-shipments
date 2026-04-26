from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Token:
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime = field(default_factory=lambda: datetime.fromtimestamp(0, tz=timezone.utc))

    def is_expired(self, buffer_seconds: int = 60) -> bool:
        now = datetime.now(tz=timezone.utc)
        return (self.expires_at - now).total_seconds() < buffer_seconds

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Token":
        expires_raw = data.get("expires_at")
        if expires_raw:
            expires_at = datetime.fromisoformat(expires_raw)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = datetime.fromtimestamp(0, tz=timezone.utc)
        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
        )
