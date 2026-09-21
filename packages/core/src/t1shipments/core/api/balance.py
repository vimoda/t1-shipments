from __future__ import annotations

from ..models.tracking import Balance
from .base import BaseResource


class BalanceResource(BaseResource):
    def balance(self) -> Balance:
        url = self._endpoints.wallet_url(self._endpoints.wallet_movements)
        headers = {"seller_id": self._commerce_id} if self._commerce_id else {}
        data = self.request("GET", url, headers=headers)

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")

        if not data.get("success", False):
            raise ValueError(data.get("message") or "Wallet balance request failed")

        # T1 returns seller_id as a number — normalize to str so the field
        # always validates and consumers get a stable type.
        seller_id = data.get("seller_id")

        return Balance.model_validate(
            {
                "amount": data.get("current_balance", 0.0),
                "seller_id": str(seller_id) if seller_id is not None else None,
                "updated_at": data.get("timestamp"),
                "overweight": data.get("overweight", False),
                "overweight_pending": data.get("overweight_pending", False),
            }
        )
