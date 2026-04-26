from __future__ import annotations

from conftest import load_fixture


def test_create_shipment_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/shipments",
        json=load_fixture("shipment"),
    )
    shipment = client.create_shipment(quote_id="q-123", rate_id="r-001")
    assert shipment.shipment_id == "shp-001"
    assert shipment.guide_number == "1Z999AA10123456784"
    assert shipment.carrier == "FedEx"
    assert shipment.label_url is not None
