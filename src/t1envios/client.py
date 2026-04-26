from __future__ import annotations

from turtle import st
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
from .auth.storage import HybridStorage, TokenStorage
from .config import Endpoints
from .models.quote import QuoteRequest, QuoteResponse
from .models.shipment import Shipment, ShipmentRequest
from .models.tracking import Balance, Carrier, Pickup, PickupRequest, TrackingResponse, TrackingState


class T1Client:
    """High-level T1Envios client. Use as context manager or call close() when done."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str | None = None,
        password: str | None = None,
        endpoints: Endpoints | None = None,
        timeout: float = 30.0,
        token_storage: TokenStorage | None = None,
        http_client: httpx.Client | None = None,
        shop_id: str | None = None,
        commerce_id: str | None = None
    ) -> None:
        self._endpoints = endpoints or Endpoints()
        self._http = http_client or httpx.Client(timeout=timeout)
        _storage = token_storage if token_storage is not None else HybridStorage()
        self._auth = Authenticator(
            client_id=client_id,
            client_secret=client_secret,
            endpoints=self._endpoints,
            http=self._http,
            username=username,
            password=password,
            storage=_storage,
        )
        self._quotes = QuotesResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id)
        self._tracking = TrackingResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id)
        self._balance = BalanceResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id)
        self._pickups = PickupsResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id)
        self._carriers = CarriersResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id)
        self._shipments = ShipmentsResource(self._http, self._auth, self._endpoints, shop_id=shop_id, commerce_id=commerce_id)

    def login(self) -> None:
        self._auth.login()

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
    def from_settings(cls, **kwargs: Any) -> "T1Client":
        from .config import Settings
        s = Settings()  # type: ignore[call-arg]
        return cls(
            client_id=s.client_id,
            client_secret=s.client_secret,
            username=s.username,
            password=s.password.get_secret_value() if s.password else None,
            endpoints=Endpoints(base_url=s.base_url),
            timeout=s.timeout,
            shop_id=s.shop_id,
            commerce_id=s.commerce_id,
            **kwargs,
        )
