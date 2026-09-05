from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ShipmentRequest(BaseModel):
    quote_token: str = Field(..., description="Quote token from the quote request.")
    content: str = Field(..., description="Brief description of the package contents.", max_length=25)

    origin_first_name: str = Field(..., description="Sender's first name.", min_length=1, max_length=25)
    origin_last_name: str = Field(..., description="Sender's last name(s).", min_length=1, max_length=25)
    origin_email: str = Field(..., description="Sender's email address.", min_length=3, max_length=35)
    origin_street: str = Field(..., description="Sender's street name.", min_length=3, max_length=35)
    origin_number: str = Field(..., description="Sender's exterior/interior number.", min_length=1, max_length=15)
    origin_neighborhood: str = Field(..., description="Sender's neighborhood (colonia).", min_length=3, max_length=35)
    origin_phone: str = Field(..., description="Sender's phone number.", min_length=8, max_length=10)
    origin_state: str = Field(..., description="Sender's state.", min_length=3, max_length=35)
    origin_municipality: str = Field(..., description="Sender's municipality.", min_length=3, max_length=35)
    origin_references: str = Field(default="", description="Sender's address references.", max_length=35)
    origin_postal_code: str = Field(..., min_length=5, max_length=5, description="5-digit origin postal code (Mexico).")
    origin_commerce_name: Optional[str] = Field(default="", description="Sender's commerce name.", max_length=60)

    destination_first_name: str = Field(..., description="Recipient's first name.", min_length=3, max_length=25)
    destination_last_name: str = Field(..., description="Recipient's last name(s).", min_length=3, max_length=25)
    destination_email: str = Field(..., description="Recipient's email address.", min_length=3, max_length=35)
    destination_street: str = Field(..., description="Recipient's street name.", min_length=3, max_length=35)
    destination_number: str = Field(..., description="Recipient's exterior/interior number.", min_length=1, max_length=15)
    destination_neighborhood: str = Field(..., description="Recipient's neighborhood (colonia).", min_length=3, max_length=35)
    destination_phone: str = Field(..., description="Recipient's phone number.", min_length=8, max_length=10)
    destination_state: str = Field(..., description="Recipient's state.", min_length=3, max_length=35)
    destination_municipality: str = Field(..., description="Recipient's municipality.", min_length=3, max_length=35)
    destination_references: str = Field(default="", description="Recipient's address references.", max_length=35)
    destination_postal_code: str = Field(..., min_length=5, max_length=5, description="5-digit destination postal code.")
    destination_commerce_name: Optional[str] = Field(default="", description="Recipient's commerce name.", max_length=60)

    packages: int = Field(..., gt=0, description="Number of packages.")
    generate_pickup: bool = Field(False, description="Generate a pickup request when creating the shipment.")
    has_notification: bool = Field(False, description="Send notifications for this shipment.")
    guide_origin: str = Field("t1envios", description='Source of the guide. Allowed: "t1envios".')

    @model_validator(mode="after")
    def validate_guide_origin(self) -> "ShipmentRequest":
        allowed = {"t1envios"}
        if self.guide_origin not in allowed:
            raise ValueError(f"guide_origin must be one of {allowed}, got '{self.guide_origin}'")
        return self


class Address(BaseModel):
    name: str
    company: str | None = None
    street: str
    street2: str | None = None
    city: str
    state: str
    zip_code: str
    country: str = "MX"
    phone: str | None = None
    email: str | None = None


class Parcel(BaseModel):
    weight: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    length: float = Field(gt=0)
    description: str | None = None
    package_value: float = 0.0


class Shipment(BaseModel):
    order_number: int
    carrier: str
    creation_date: str
    cost: str
    destination: str
    current_balance: str
    tracking_number: str
    extended_zone: bool
    packages: int
    guide_link: str | None = None
    file: str | None = None
