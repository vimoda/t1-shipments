from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PRESETS: dict[str, dict[str, str]] = {
    "dev": {
        "base_url": "https://apiv2.dev.t1envios.com",
        "auth_base_url": "https://keycloak.dev.plataformat1.com",
    },
    "prod": {
        "base_url": "https://apiv2.t1envios.com",
        "auth_base_url": "https://keycloak.plataformat1.com",
    },
}


class Endpoints(BaseModel):
    """API endpoint paths. Override per-path or change base_url entirely."""

    base_url: str = ENV_PRESETS["dev"]["base_url"]
    auth_base_url: str = ENV_PRESETS["dev"]["auth_base_url"]
    auth: str = "/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token"
    refresh: str = "/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token"
    quote: str = "/quote/create-with-quote"
    track_state: str = "/rastreo/estado-guia/{guide}"
    track_detail: str = "/rastreo/detail-guia/{guide}"
    balance: str = "/balance/consult"
    pickup: str = "/pickup/create"
    carriers: str = "/carriers"
    create_shipment: str = "/guide/create"

    def auth_url(self, path: str, **kwargs: str) -> str:
        return self.auth_base_url.rstrip("/") + path.format(**kwargs)

    def url(self, path: str, **kwargs: str) -> str:
        return self.base_url.rstrip("/") + path.format(**kwargs)

    def set_auth_url(self, url: str) -> None:
        self.auth_base_url = url

    def set_base_url(self, url: str) -> None:
        self.base_url = url

    def set_auth_path(self, path: str) -> None:
        self.auth = path

    def set_refresh_path(self, path: str) -> None:
        self.refresh = path

    def set_quote_path(self, path: str) -> None:
        self.quote = path

    def set_track_state_path(self, path: str) -> None:
        self.track_state = path

    def set_track_detail_path(self, path: str) -> None:
        self.track_detail = path

    def set_balance_path(self, path: str) -> None:
        self.balance = path

    def set_pickup_path(self, path: str) -> None:
        self.pickup = path

    def set_carriers_path(self, path: str) -> None:
        self.carriers = path

    def set_create_shipment_path(self, path: str) -> None:
        self.create_shipment = path


class Settings(BaseSettings):
    """CLI configuration — reads from env vars prefixed T1_ or .env file."""

    model_config = SettingsConfigDict(env_prefix="T1_", env_file=".env", extra="ignore")

    client_id: str
    client_secret: SecretStr
    username: str | None = None
    password: SecretStr | None = None
    env: Literal["dev", "prod"] = "dev"
    base_url: str | None = None
    auth_url: str | None = None
    shop_id: str | None = None
    commerce_id: str | None = None
    timeout: float = 30.0
    retries: int = 3
    log_level: str | None = None

    def endpoints(self) -> "Endpoints":
        preset = ENV_PRESETS[self.env]
        return Endpoints(
            base_url=self.base_url or preset["base_url"],
            auth_base_url=self.auth_url or preset["auth_base_url"],
        )
