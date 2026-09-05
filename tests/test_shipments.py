from __future__ import annotations

from conftest import load_fixture
from t1shipments.core.models.shipment import ShipmentRequest


def _req() -> ShipmentRequest:
    return ShipmentRequest(
        quote_token="qt-001",
        content="Ropa",
        origin_first_name="Juan",
        origin_last_name="Pérez",
        origin_email="juan@example.com",
        origin_street="Av. Insurgentes",
        origin_number="100",
        origin_neighborhood="Centro",
        origin_phone="5512345678",
        origin_state="Ciudad de Mexico",
        origin_municipality="Cuauhtémoc",
        origin_references="Frente al banco",
        origin_postal_code="06600",
        destination_first_name="Ana",
        destination_last_name="García",
        destination_email="ana@example.com",
        destination_street="Av. Vallarta",
        destination_number="200",
        destination_neighborhood="Americana",
        destination_phone="3312345678",
        destination_state="Jalisco",
        destination_municipality="Guadalajara",
        destination_references="Edificio azul",
        destination_postal_code="44100",
        packages=1,
    )


def test_create_shipment_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/guide/create",
        json=load_fixture("shipment"),
    )
    shipment = client.create_shipment(_req())
    assert shipment.order_number == 12345
    assert shipment.tracking_number == "1Z999AA10123456784"
    assert shipment.carrier == "DHL"
    assert shipment.guide_link == "https://labels.t1envios.com/12345.pdf"
