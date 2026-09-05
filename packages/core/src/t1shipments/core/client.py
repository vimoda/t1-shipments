from __future__ import annotations

from datetime import datetime, timezone
from types import TracebackType
from typing import Any

import httpx

from .api.balance import BalanceResource
from .api.carriers import CarriersResource
from .api.pickups import PickupsResource
from .api.quotes import QuotesResource
from .api.shipments import ShipmentsResource
from .api.tracking import TrackingResource
from .auth.authenticator import Authenticator
from .auth.storage import InMemoryStorage, TokenStorage
from .auth.token import Token
from .config import Endpoints
from .models.quote import QuoteRequest, QuoteResponse
from .models.shipment import Shipment, ShipmentRequest
from .models.tracking import Balance, Carrier, Pickup, PickupRequest, TrackingResponse, TrackingState
from .utils.logging import configure_logging


class T1Client:
    """High-level T1Envios client. Use as context manager or call close() when done."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        endpoints: Endpoints | None = None,
        timeout: float = 30.0,
        token_storage: TokenStorage | None = None,
        http_client: httpx.Client | None = None,
        shop_id: str | None = None,
        commerce_id: str | None = None,
        log_level: str | None = None,
        retries: int = 3,
        auto_refresh: bool = True,
    ) -> None:
        if log_level is not None:
            configure_logging(log_level)
        self._endpoints = endpoints or Endpoints()
        self._http = http_client or httpx.Client(timeout=timeout)
        _storage = token_storage if token_storage is not None else InMemoryStorage()
        self._auth = Authenticator(
            client_id=client_id,
            client_secret=client_secret,
            endpoints=self._endpoints,
            http=self._http,
            storage=_storage,
            auto_refresh=auto_refresh,
        )
        self._quotes = QuotesResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id, retries=retries)
        self._tracking = TrackingResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id, retries=retries)
        self._balance = BalanceResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id, retries=retries)
        self._pickups = PickupsResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id, retries=retries)
        self._carriers = CarriersResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id, retries=retries)
        self._shipments = ShipmentsResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id, retries=retries)

    def login(self, username: str, password: str, store_id: str | None = None) -> Token:
        return self._auth.login(username, password, store_id=store_id)

    def logout(self) -> None:
        self._auth.logout()

    def quote(self, req: QuoteRequest) -> QuoteResponse:
        return self._quotes.quote(req)

    def track_detail(self, guide: str) -> TrackingResponse:
        return self._tracking.track_detail(guide)

    def track_state(self, guide: str) -> TrackingState:
        return self._tracking.track_state(guide)

    def balance(self) -> Balance:
        return self._balance.balance()

    def schedule_pickup(self, req: PickupRequest) -> Pickup:
        return self._pickups.schedule_pickup(req)

    def list_carriers(self) -> list[Carrier]:
        return self._carriers.list_carriers()

    def create_shipment(self, req: ShipmentRequest) -> Shipment:
        return self._shipments.create_shipment(req)

    def download_label(self, guide_link: str) -> bytes:
        return self._shipments.download_label(guide_link)

    def inject_token(
        self,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> None:
        """Load an externally managed token (e.g. from MCP client).

        Sets auto_refresh=True if refresh_token provided, False otherwise.
        """
        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at or datetime(9999, 1, 1, tzinfo=timezone.utc),
        )
        self._auth._token = token
        self._auth._storage.save(token)
        self._auth.auto_refresh = refresh_token is not None

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "T1Client":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    @classmethod
    def from_settings(
        cls,
        client_id: str | None = None,
        client_secret: str | None = None,
        **kwargs: Any,
    ) -> "T1Client":
        from .auth.storage import HybridStorage
        from .config import Settings
        from .exceptions import ConfigError

        s = Settings()
        storage = kwargs.get("token_storage")
        if storage is None:
            storage = HybridStorage()
            kwargs["token_storage"] = storage

        resolved_client_id = client_id
        resolved_client_secret = client_secret

        if not resolved_client_id or not resolved_client_secret:
            stored = storage.load()
            if stored:
                resolved_client_id = resolved_client_id or stored.client_id
                resolved_client_secret = resolved_client_secret or stored.client_secret

        if not resolved_client_id or not resolved_client_secret:
            raise ConfigError(
                "client_id and client_secret are required. Provide them as arguments "
                "or authenticate first via 't1 auth login'."
            )

        return cls(
            client_id=resolved_client_id,
            client_secret=resolved_client_secret,
            endpoints=s.endpoints(),
            timeout=s.timeout,
            shop_id=s.shop_id,
            commerce_id=s.commerce_id,
            retries=s.retries,
            log_level=s.log_level,
            **kwargs,
        )
