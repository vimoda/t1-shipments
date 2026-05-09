from __future__ import annotations

import pytest

from t1envios.core.exceptions import ApiError
from t1envios.core.models.quote import QuoteRequest

from conftest import load_fixture


def _req() -> QuoteRequest:
    return QuoteRequest(
        origin_postal_code="06600",
        destination_postal_code="44100",
        weight=1,
        width=20,
        height=15,
        length=10,
        shipping_days=2,
        package_value=500.0,
        insurance=False,
        packages=1,
        package_type=1,
    )


def test_quote_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/quote/create-with-quote",
        json=load_fixture("quote"),
    )
    response = client.quote(_req())
    assert response.success is True
    assert len(response.detail) == 2
    assert response.detail[0]["service_id"] == "FEDEX"
    assert response.detail[1]["total_cost"] == 120.0


def test_quote_only_weight():
    req = QuoteRequest(origin_postal_code="06600", destination_postal_code="44100", weight=3)
    assert req.weight == 3
    assert req.width == 10.0  # defaults filled


def test_quote_only_dims():
    # 40×30×20 cm → vol = 4.8 → ceil = 5 kg
    req = QuoteRequest(origin_postal_code="06600", destination_postal_code="44100", width=40, height=30, length=20)
    assert req.weight == 5


def test_quote_real_weight_wins():
    # vol = ceil(0.6) = 1 kg, real = 2 kg → use 2
    req = QuoteRequest(origin_postal_code="06600", destination_postal_code="44100", weight=2, width=20, height=15, length=10)
    assert req.weight == 2


def test_quote_volumetric_exceeds_raises():
    # vol = ceil(4.8) = 5 kg > real 1 kg → must raise with integer in message
    with pytest.raises(ValueError, match="Volumetric weight \\(5 kg\\)"):
        QuoteRequest(origin_postal_code="06600", destination_postal_code="44100", weight=1, width=40, height=30, length=20)


def test_quote_volumetric_confirmed():
    # user resubmits with weight = ceil(volumetric) → passes
    req = QuoteRequest(origin_postal_code="06600", destination_postal_code="44100", weight=5, width=40, height=30, length=20)
    assert req.weight == 5


def test_quote_no_weight_no_dims_raises():
    with pytest.raises(ValueError, match="Provide weight"):
        QuoteRequest(origin_postal_code="06600", destination_postal_code="44100")


def test_quote_api_error(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/quote/create-with-quote",
        status_code=400,
        json={"message": "Invalid ZIP code", "code": "INVALID_ZIP"},
    )
    with pytest.raises(ApiError) as exc_info:
        client.quote(_req())
    assert exc_info.value.status == 400
    assert exc_info.value.code == "INVALID_ZIP"
