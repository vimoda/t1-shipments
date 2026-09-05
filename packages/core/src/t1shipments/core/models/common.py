from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    code: str | None = None


class Pagination(BaseModel):
    page: int = 1
    per_page: int = 20
    total: int = 0
    extra: dict[str, Any] = {}
