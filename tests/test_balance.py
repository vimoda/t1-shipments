from __future__ import annotations

import pytest
from conftest import InMemoryStorage, load_fixture
from t1shipments.core.client import T1Client
from t1shipments.core.config import Endpoints


def test_balance_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json=load_fixture("wallet_balance"),
    )
    bal = client.balance()
    assert bal.amount == 1585.86
    assert bal.currency == "MXN"
    assert bal.can_ship is True  # amount > 0


def test_balance_seller_id_normalized_to_str(httpx_mock, client):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json={
            "success": True,
            "message": "Consulta exitosa",
            "seller_id": 204577,
            "current_balance": 938.06,
            "timestamp": "2026-09-21T05:28:54.842329",
            "overweight": False,
            "overweight_pending": False,
        },
    )
    bal = client.balance()
    assert bal.seller_id == "204577"


def test_balance_failure_raises_with_message(httpx_mock, client):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json={"success": False, "message": "Seller not found"},
    )
    with pytest.raises(ValueError, match="Seller not found"):
        client.balance()


def test_balance_cannot_ship(httpx_mock, client):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json={
            "success": True,
            "message": "Consulta exitosa",
            "seller_id": 9365,
            "current_balance": 0,
            "timestamp": "2026-09-21T05:28:54.842329",
        },
    )
    bal = client.balance()
    assert bal.can_ship is False


def test_balance_overweight_flags_propagate(httpx_mock, client):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json={
            "success": True,
            "message": "Consulta exitosa",
            "seller_id": 9365,
            "current_balance": 100.0,
            "timestamp": "2026-09-21T05:28:54.842329",
            "overweight": True,
            "overweight_pending": True,
        },
    )
    bal = client.balance()
    assert bal.overweight is True
    assert bal.overweight_pending is True


def test_balance_can_ship_in_model_dump(httpx_mock, client):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json=load_fixture("wallet_balance"),
    )
    bal = client.balance()
    dumped = bal.model_dump()
    assert "can_ship" in dumped
    assert dumped["can_ship"] is True


def test_balance_sends_seller_id_header(httpx_mock, endpoints: Endpoints, valid_token):
    httpx_mock.add_response(
        url="https://wallet.example.com/wallet/movements",
        json=load_fixture("wallet_balance"),
    )
    storage = InMemoryStorage(token=valid_token)
    client = T1Client(
        client_id="test-id",
        client_secret="test-secret",
        endpoints=endpoints,
        token_storage=storage,
        commerce_id="204577",
    )
    client.balance()
    request = httpx_mock.get_requests()[0]
    assert request.headers["seller_id"] == "204577"
