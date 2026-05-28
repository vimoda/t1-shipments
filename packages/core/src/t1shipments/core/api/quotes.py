from __future__ import annotations

from .base import BaseResource
from ..models.quote import QuoteRequest, QuoteResponse


class QuotesResource(BaseResource):
    def quote(self, req: QuoteRequest) -> QuoteResponse:
        url = self._endpoints.url(self._endpoints.quote)
        data = self.request("POST", url, json=req.model_dump())

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict response, got {type(data)}")
        if data.get("success") is False:
            raise ValueError(f"API error: {data.get('message', 'Unknown error')}")

        return QuoteResponse.model_validate(data)
