from __future__ import annotations

from t1envios.models.tracking import PickupRequest

from conftest import load_fixture


def test_schedule_pickup_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/shipments/pickup",
        json=load_fixture("pickup"),
    )
    req = PickupRequest(pickup_date="2024-01-20", packages=2)
    pickup = client.schedule_pickup(req)
    assert pickup.pickup_id == "pck-001"
    assert pickup.status == "scheduled"
    assert pickup.confirmation == "CONF-ABC123"
