from __future__ import annotations

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Endpoints(BaseModel):
    """API endpoint paths. Override per-path or change base_url entirely."""

    base_url: str = "https://apiv2.dev.t1envios.com"
    auth_base_url: str = "https://keycloak.dev.plataformat1.com"
    auth: str = "/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token"
    refresh: str = "/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token" # Sugerido por IA: /auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token
    quote: str = "/quote/create-with-quote" # Sugerido por IA: /shipments/quote
    track_state: str = "/rastreo/estado-guia/{guide}" # Sugerido por IA: /shipments/track/{guide}
    track_detail: str = "/rastreo/detail-guia/{guide}"
    balance: str = "/balance/consult" # Sugerido por IA: /account/balance
    pickup: str = "/pickup/create" # Sugerido por IA: /shipments/pickup
    carriers: str = "/carriers" # Sugerido por IA: /carriers
    create_shipment: str = "/guide/create" # Sugerido por IA: /shipments
    # # Saldos y movimientos:
    # transactions: str = "/account/transactions" # Sugerido por IA: /account/transactions



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
    client_secret: str
    username: str | None = None
    password: SecretStr | None = None
    base_url: str = "https://api.t1envios.com"
    auth_url: str = "https://keycloak.dev.plataformat1.com"
    shop_id: str | None = None
    commerce_id: str | None = None
    timeout: float = 30.0
