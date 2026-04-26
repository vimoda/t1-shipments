from __future__ import annotations

import pytest

from t1envios.exceptions import ApiError
from t1envios.models.quote import QuoteRequest

from conftest import load_fixture


def test_quote_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/shipments/quote",
        json=load_fixture("quote"),
    )
    req = QuoteRequest(
        origin_postal_code="06600",
        destination_postal_code="44100",
        weight=1.5,
        width=20,
        height=15,
        length=10,
        shipping_days=2,
        package_value=500.0,
        insurance=False,
        packages=1,
        package_type=1,
    )
    response = client.quote(req)
    assert response.quote_id == "q-123"
    assert len(response.rates) == 2
    assert response.rates[0].carrier == "FedEx"
    assert response.rates[1].price == 80.0


def test_quote_api_error(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/shipments/quote",
        status_code=400,
        json={"message": "Invalid ZIP code", "code": "INVALID_ZIP"},
    )
    req = QuoteRequest(
        origin_postal_code="00000",
        destination_postal_code="99999",
        weight=1.0,
        width=10,
        height=10,
        length=10,
        shipping_days=2,
        package_value=100.0,
        insurance=False,
        packages=1,
        package_type=1,
    )
    with pytest.raises(ApiError) as exc_info:
        client.quote(req)
    assert exc_info.value.status == 400
    assert exc_info.value.code == "INVALID_ZIP"
