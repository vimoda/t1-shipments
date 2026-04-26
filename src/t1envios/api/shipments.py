from __future__ import annotations

from .base import BaseResource
from ..models.shipment import ShipmentRequest, Shipment


class ShipmentsResource(BaseResource):
    def create_shipment(self, req: ShipmentRequest) -> Shipment:
        url = self._endpoints.url(self._endpoints.create_shipment)
        payload = req.model_dump()
        if self._shop_id:
            payload["comercio_id"] = self._shop_id
        data = self.request("POST", url, json=payload)
        
        print("Raw response data:", data)  # Debugging line
        print("Type of response data:", type(data))  # Debugging line

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
        return Shipment.model_validate(data["detail"])
