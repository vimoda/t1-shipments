from __future__ import annotations

import pytest

from t1envios.exceptions import ApiError

from conftest import load_fixture


def test_track_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/shipments/track/GUIDE123",
        json=load_fixture("tracking"),
    )
    result = client.track("GUIDE123")
    assert result.guide_number == "GUIDE123"
    assert result.carrier == "FedEx"
    assert len(result.events) == 2
    assert result.events[0].status == "Recolectado"


def test_track_not_found(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/shipments/track/NOPE",
        status_code=404,
        json={"message": "Guide not found"},
    )
    with pytest.raises(ApiError) as exc_info:
        client.track("NOPE")
    assert exc_info.value.status == 404
