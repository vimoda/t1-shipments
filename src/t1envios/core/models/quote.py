from __future__ import annotations

import math
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator

# Standard volumetric divisor used by most carriers in Mexico (cm³/kg).
_VOLUMETRIC_DIVISOR = 5000


class ProductsQuoteRequest(BaseModel):
    sat_description: str = Field(default="", description="Description Sat Code")
    sat_code: str = Field(default="", description="Sat Code")
    weight: float = Field(default=1.0, gt=0, description="Weight in kg")
    width: float = Field(default=10.0, gt=0, description="Width in cm")
    height: float = Field(default=10.0, gt=0, description="Height in cm")
    length: float = Field(default=10.0, gt=0, description="Length in cm")
    price: float = Field(default=0, description="Product Price")


class QuoteRequest(BaseModel):
    origin_postal_code: str
    destination_postal_code: str
    weight: int = Field(default=0, ge=0, description="Actual weight in kg (integer). If omitted, calculated from dimensions and rounded up.")
    width: float = Field(default=0.0, ge=0, description="Width in cm. Required when weight is omitted.")
    height: float = Field(default=0.0, ge=0, description="Height in cm. Required when weight is omitted.")
    length: float = Field(default=0.0, ge=0, description="Length in cm. Required when weight is omitted.")
    package_value: float = Field(default=0.0, ge=0)
    shipping_days: int = Field(default=3, ge=0, description="Days until shipment")
    packages: int = Field(default=1, ge=1, description="Number of packages")
    insurance: bool = Field(default=False, description="Add insurance to the quote")
    package_type: int = Field(default=1, description="Package type: 1 for Sobre, 2 for Paquete")
    products: Optional[ProductsQuoteRequest] = Field(
        default=None,
        description="Products list with sat_description, sat_code, weight, length, width, height, price.",
    )

    @model_validator(mode="after")
    def resolve_billable_weight(self) -> "QuoteRequest":
        provided = self.model_fields_set
        has_weight = "weight" in provided and self.weight > 0
        has_dims = (
            all(f in provided for f in ("width", "height", "length"))
            and self.width > 0 and self.height > 0 and self.length > 0
        )

        if not has_weight and not has_dims:
            raise ValueError("Provide weight, dimensions (width/height/length), or both.")

        if has_dims:
            vol_kg = math.ceil((self.width * self.height * self.length) / _VOLUMETRIC_DIVISOR)
            vol_kg = max(vol_kg, 1)
            if has_weight and vol_kg > self.weight:
                raise ValueError(
                    f"Volumetric weight ({vol_kg} kg) exceeds actual weight ({self.weight} kg). "
                    f"Carriers will charge {vol_kg} kg. "
                    f"Resubmit with weight={vol_kg} to confirm, or review your dimensions."
                )
            if not has_weight:
                self.weight = vol_kg

        if self.weight == 0:
            self.weight = 1

        # Fill missing dimensions with defaults so the API payload is complete
        if not has_dims:
            if self.width == 0:
                self.width = 10.0
            if self.height == 0:
                self.height = 10.0
            if self.length == 0:
                self.length = 10.0

        return self


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
