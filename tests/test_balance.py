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
