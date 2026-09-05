from __future__ import annotations

from conftest import load_fixture


def test_balance_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/balance/consult",
        json=load_fixture("balance"),
    )
    bal = client.balance()
    assert bal.amount == 1250.50
    assert bal.currency == "MXN"
    assert bal.credit is False
    assert bal.can_ship is True  # amount > 0


def test_balance_can_ship_via_credit(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/balance/consult",
        json={
            "success": False,
            "message": "Insufficient Balance",
            "detail": {
                "monto_actual": 0,
                "comercio_id": "9365",
                "comercio_id_t1paginas": None,
                "credito": True,
            },
        },
    )
    bal = client.balance()
    assert bal.amount == 0
    assert bal.credit is True
    assert bal.can_ship is True  # credit covers it


def test_balance_cannot_ship(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/balance/consult",
        json={
            "success": False,
            "message": "Insufficient Balance",
            "detail": {
                "monto_actual": 0,
                "comercio_id": "9365",
                "comercio_id_t1paginas": None,
                "credito": False,
            },
        },
    )
    bal = client.balance()
    assert bal.can_ship is False


def test_balance_can_ship_in_model_dump(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/balance/consult",
        json=load_fixture("balance"),
    )
    bal = client.balance()
    dumped = bal.model_dump()
    assert "can_ship" in dumped
    assert dumped["can_ship"] is True
