from __future__ import annotations

from .base import BaseResource
from ..models.tracking import Carrier


class CarriersResource(BaseResource):
    def list_carriers(self) -> list[Carrier]:
        url = self._endpoints.url(self._endpoints.carriers)
        data = self.request("GET", url)
        items = data if isinstance(data, list) else data.get("carriers", data.get("data", []))
        return [Carrier.model_validate(item) for item in items]
