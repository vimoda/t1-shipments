from __future__ import annotations

import logging

from ..exceptions import ApiError
from ..models.shipment import Shipment, ShipmentRequest, ShipmentSummary
from .base import BaseResource

log = logging.getLogger("t1shipments.api")


class ShipmentsResource(BaseResource):
    def create_shipment(self, req: ShipmentRequest) -> Shipment:
        url = self._endpoints.url(self._endpoints.create_shipment)
        payload = req.model_dump()
        if payload.get("commercial_order") is None:
            payload.pop("commercial_order", None)
        if self._shop_id:
            payload["comercio_id"] = self._shop_id
        log.debug("create_shipment payload: %s", payload)
        # POST is not idempotent and T1 has no idempotency keys: a retry after a
        # 5xx/timeout can double-create (and double-charge) the guide.
        data = self.request("POST", url, json=payload, retries=1)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')} | raw: {data}")
        return Shipment.model_validate(data["detail"])

    def list_shipments(self, items: int = 10, page: int = 1, **filters: str) -> list[ShipmentSummary]:
        """List created guides (GET /adminseller/status-shipment). Filters are the API's
        query params, e.g. start_date, end_date, guide, destination_email."""
        url = self._endpoints.url(self._endpoints.list_shipments, items=items, page=page)
        data = self.request("GET", url, params=filters or None)
        detail = data.get("detail") if isinstance(data, dict) else None
        return [ShipmentSummary.model_validate(item) for item in detail or []]

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
