from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Pagination(BaseModel):
    page: int = 1
    per_page: int = 20
    total: int | None = None


class ErrorDetail(BaseModel):
    code: str | None = None
    message: str
    payload: Any = None
