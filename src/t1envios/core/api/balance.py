from __future__ import annotations

from .base import BaseResource
from ..models.tracking import Balance


class BalanceResource(BaseResource):
    def balance(self) -> Balance:
        url = self._endpoints.url(self._endpoints.balance)
        data = self.request("GET", url)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")

        detail = data.get("detail")
        if not detail or not isinstance(detail, dict):
            raise ValueError(data.get("message") or "No 'detail' field in response")

        return Balance.model_validate({
            "amount": detail.get("monto_actual", 0.0),
            "currency": detail.get("currency", "MXN") or "MXN",
            "commerce_id": detail.get("comercio_id"),
            "commerce_id_t1_pages": detail.get("comercio_id_t1paginas"),
            "credit": detail.get("credito", False),
        })
