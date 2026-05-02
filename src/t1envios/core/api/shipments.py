from __future__ import annotations

import logging

from ..exceptions import ApiError
from ..models.shipment import Shipment, ShipmentRequest
from .base import BaseResource

log = logging.getLogger("t1envios.api")


class ShipmentsResource(BaseResource):
    def create_shipment(self, req: ShipmentRequest) -> Shipment:
        url = self._endpoints.url(self._endpoints.create_shipment)
        payload = req.model_dump()
        if self._shop_id:
            payload["comercio_id"] = self._shop_id
        data = self.request("POST", url, json=payload)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')}")
        return Shipment.model_validate(data["detail"])

    def download_label(self, guide_link: str) -> bytes:
        log.debug("Downloading label from %s", guide_link)
        resp = self._http.get(guide_link)
        if resp.status_code != 200:
            raise ApiError(
                status=resp.status_code,
                message="Failed to download label",
                code=None,
                payload=resp.text,
            )
        return resp.content
