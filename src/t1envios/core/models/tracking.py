from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class TrackingEvent(BaseModel):
    timestamp: datetime
    status: str
    description: str
    location: str | None = None


class TrackingDetail(BaseModel):
    id: str
    code: str
    description: str
    internal_family: str
    generic_family: str
    tracking_number: str
    estimated_date: str
    date: str
    time: str
    carrier_id: int
    carrier_name: str
    tracking_link: str
    timezone: str


class TrackingResponse(BaseModel):
    detail: List[TrackingDetail]


class TrackingHistoryEvent(BaseModel):
    date: str
    location: str
    status: str
    description: str


class TrackingState(BaseModel):
    guide: str
    current_status: str
    estimated_delivery_date: str
    history: List[TrackingHistoryEvent]


class Balance(BaseModel):
    amount: float
    currency: str = "MXN"
    commerce_id: str | None = None
    commerce_id_t1_pages: str | None = None
    credit: bool = False

    @computed_field  # type: ignore[misc]
    @property
    def can_ship(self) -> bool:
        return self.amount > 0 or self.credit


class Carrier(BaseModel):
    carrier_id: str
    name: str
    services: list[str] = []
    active: bool = True


class PickupRequest(BaseModel):
    carrier: str
    contact_first_name: str
    contact_last_name: str
    email: str
    street: str
    number: str
    neighborhood: str
    phone: str
    state: str
    municipality: str
    postal_code: str
    references: str
    pieces: int
    weight: int
    length: int
    width: int
    height: int
    date: str
    open_time: str
    close_time: str


class Pickup(BaseModel):
    pickup_id: str
    location: str
    localization: str
    status: str
    message: str
