from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ProductsQuoteRequest(BaseModel):
    sat_description: str = Field(default="", description="Description Sat Code")
    sat_code: str = Field(default="", description="Sat Code")
    weight: int = Field(default=1, gt=0, description="Weight in kg")
    width: float = Field(default=10.0, gt=0, description="Width in cm")
    height: float = Field(default=10.0, gt=0, description="Height in cm")
    length: float = Field(default=10.0, gt=0, description="Length in cm")
    price: float = Field(default=0, description="Product Price")


class QuoteRequest(BaseModel):
    origin_postal_code: str
    destination_postal_code: str
    weight: int = Field(default=1, gt=0, description="Weight in kg")
    width: float = Field(default=10.0, gt=0, description="Width in cm")
    height: float = Field(default=10.0, gt=0, description="Height in cm")
    length: float = Field(default=10.0, gt=0, description="Length in cm")
    package_value: float = Field(default=0.0, ge=0)
    shipping_days: int = Field(default=3, ge=0, description="Days until shipment")
    packages: int = Field(default=1, ge=1, description="Number of packages")
    insurance: bool = Field(default=False, description="Add insurance to the quote")
    package_type: int = Field(default=1, description="Package type: 1 for Sobre, 2 for Paquete")
    products: Optional[ProductsQuoteRequest] = Field(
        default=None,
        description="Products list with sat_description, sat_code, weight, length, width, height, price.",
    )


class Rate(BaseModel):
    rate_id: str
    carrier: str
    service: str
    price: float
    currency: str = "MXN"
    estimated_days: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class QuoteResponse(BaseModel):
    success: bool
    message: str | None = None
    detail: List[Any] | None = None
