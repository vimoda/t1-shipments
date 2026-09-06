"""Smoke-test the examples with mocked HTTP."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from t1shipments.core.auth.token import Token
from t1shipments.core.client import T1Client
from t1shipments.core.config import Endpoints
from t1shipments.core.models.quote import QuoteRequest

FIXTURES = Path(__file__).parent.parent / "tests" / "fixtures" / "responses"


def load_fixture(name: str) -> dict | list:
    return json.loads((FIXTURES / f"{name}.json").read_text())


@pytest.fixture
def client(httpx_mock) -> T1Client:
    token = Token(
        access_token="test-token",
        refresh_token="test-refresh",
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
    )
    c = T1Client(
        client_id="test-id",
        client_secret="test-secret",
        endpoints=Endpoints(
            base_url="https://api.example.com", auth_base_url="https://api.example.com"
        ),
    )
    c.inject_token(token.access_token, token.refresh_token, token.expires_at)
    return c


def test_quote_flow(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/carriers",
        json=load_fixture("carriers"),
    )
    httpx_mock.add_response(
        url="https://api.example.com/quote/create-with-quote",
        json=load_fixture("quote"),
    )

    carriers = client.list_carriers()
    assert len(carriers) > 0
    print("Paqueterías:", [c.name for c in carriers])

    req = QuoteRequest(
        origin_postal_code="06600",
        destination_postal_code="44100",
        weight=2,
        width=20,
        height=15,
        length=10,
        shipping_days=2,
        insurance=False,
        package_type=1,
        packages=1,
    )
    quote = client.quote(req)
    assert quote.success
    for rate in quote.detail or []:
        cost = rate.get("total_cost", 0)
        days = rate.get("delivery_days") or "-"
        print(f"  {rate['token']} {rate['service_id']}: ${cost:,.2f} MXN ({days} días)")


def test_track_state(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/rastreo/estado-guia/GUIDE123",
        json=load_fixture("tracking"),
    )
    state = client.track_state("GUIDE123")
    assert state.guide == "GUIDE123"
    print(f"Estado: {state.current_status}")
    for ev in state.history:
        print(f"  {ev.date} — {ev.location}: {ev.status}")


def test_track_detail(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/rastreo/detail-guia/GUIDE123",
        json=load_fixture("tracking_detail"),
    )
    detail = client.track_detail("GUIDE123")
    assert len(detail.detail) > 0
    for ev in detail.detail:
        print(f"  {ev.date} {ev.time} — {ev.carrier_name}: {ev.description}")


def test_as_library_flow(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/carriers",
        json=load_fixture("carriers"),
    )
    httpx_mock.add_response(
        url="https://api.example.com/quote/create-with-quote",
        json=load_fixture("quote"),
    )

    carriers = client.list_carriers()
    assert len(carriers) > 0

    req = QuoteRequest(
        origin_postal_code="06600",
        destination_postal_code="44100",
        weight=2,
        width=20,
        height=15,
        length=10,
        shipping_days=2,
        insurance=False,
        package_type=1,
        packages=1,
    )
    quote = client.quote(req)
    assert quote.success
    assert len(quote.detail or []) > 0
