from __future__ import annotations

from ..models.tracking import Balance
from .base import BaseResource


class BalanceResource(BaseResource):
    def balance(self) -> Balance:
        url = self._endpoints.url(self._endpoints.balance)
        data = self.request("GET", url)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")

        detail = data.get("detail")
        if not detail or not isinstance(detail, dict):
            raise ValueError(data.get("message") or "No 'detail' field in response")

        commerce_id = detail.get("comercio_id")
        commerce_id_t1_pages = detail.get("comercio_id_t1paginas")

        return Balance.model_validate(
            {
                "amount": detail.get("monto_actual", 0.0),
                "currency": detail.get("currency", "MXN") or "MXN",
                # T1 returns comercio_id as either a string or a number depending on
                # environment (prod sends int, dev sends str) — normalize to str so
                # the field always validates and consumers get a stable type.
                "commerce_id": str(commerce_id) if commerce_id is not None else None,
                "commerce_id_t1_pages": (
                    str(commerce_id_t1_pages) if commerce_id_t1_pages is not None else None
                ),
                "credit": detail.get("credito", False),
            }
        )
