from __future__ import annotations

from conftest import load_fixture
from t1shipments.core.models.tracking import PickupRequest


def _req() -> PickupRequest:
    return PickupRequest(
        carrier="DHL",
        contact_first_name="Juan",
        contact_last_name="Pérez",
        email="juan@example.com",
        street="Av. Insurgentes",
        number="100",
        neighborhood="Centro",
        phone="5512345678",
        state="Ciudad de Mexico",
        municipality="Cuauhtémoc",
        postal_code="06600",
        references="Frente al banco",
        pieces=1,
        weight=2,
        length=30,
        width=20,
        height=15,
        date="2024-01-20",
        open_time="09:00",
        close_time="18:00",
    )


def test_schedule_pickup_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/pickup/create",
        json=load_fixture("pickup"),
    )
    pickup = client.schedule_pickup(_req())
    assert pickup.pickup_id == "pck-001"
    assert pickup.status == "scheduled"
    assert pickup.message == "Recolección programada exitosamente"
