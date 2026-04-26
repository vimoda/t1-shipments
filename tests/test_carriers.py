from __future__ import annotations

from conftest import load_fixture


def test_list_carriers_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/carriers",
        json=load_fixture("carriers"),
    )
    carriers = client.list_carriers()
    assert len(carriers) == 3
    assert carriers[0].carrier_id == "fedex"
    assert "Express" in carriers[0].services


def test_list_carriers_wrapped(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/carriers",
        json={"carriers": load_fixture("carriers")},
    )
    carriers = client.list_carriers()
    assert len(carriers) == 3
