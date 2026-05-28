from __future__ import annotations

import pytest
from conftest import load_fixture
from t1shipments.core.exceptions import ApiError


def test_track_state_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/rastreo/estado-guia/GUIDE123",
        json=load_fixture("tracking"),
    )
    result = client.track_state("GUIDE123")
    assert result.guide == "GUIDE123"
    assert result.current_status == "En tránsito"
    assert result.estimated_delivery_date == "2024-01-20"
    assert len(result.history) == 2
    assert result.history[0].status == "Recolectado"


def test_track_state_not_found(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/rastreo/estado-guia/NOPE",
        status_code=404,
        json={"message": "Guide not found"},
    )
    with pytest.raises(ApiError) as exc_info:
        client.track_state("NOPE")
    assert exc_info.value.status == 404


def test_track_detail_success(httpx_mock, client):
    httpx_mock.add_response(
        url="https://api.example.com/rastreo/detail-guia/GUIDE123",
        json=load_fixture("tracking_detail"),
    )
    result = client.track_detail("GUIDE123")
    assert len(result.detail) == 1
    assert result.detail[0].code == "CR"
    assert result.detail[0].tracking_number == "GUIDE123"
