from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from t1envios.auth.token import Token
from t1envios.cli.main import app
from t1envios.models.quote import QuoteResponse, Rate
from t1envios.models.tracking import Balance, Carrier, TrackingResponse

runner = CliRunner()


def _valid_token() -> Token:
    return Token(
        access_token="tok",
        refresh_token=None,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
    )


@patch("t1envios.cli.carriers_cmd.T1Client")
def test_carriers_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.list_carriers.return_value = [
        Carrier(carrier_id="fedex", name="FedEx", services=["Express"]),
    ]
    result = runner.invoke(app, ["carriers"])
    assert result.exit_code == 0
    assert "FedEx" in result.output


@patch("t1envios.cli.balance_cmd.T1Client")
def test_balance_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.balance.return_value = Balance(amount=500.0, currency="MXN")
    result = runner.invoke(app, ["balance"])
    assert result.exit_code == 0
    assert "500" in result.output


@patch("t1envios.cli.track_cmd.T1Client")
def test_track_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.track_detail.return_value = TrackingResponse(
        guide_number="GUIDE123",
        carrier="FedEx",
        current_status="En tránsito",
        events=[],
    )
    result = runner.invoke(app, ["trackdetail", "GUIDE123"])
    assert result.exit_code == 0
    assert "GUIDE123" in result.output


@patch("t1envios.cli.quote_cmd.T1Client")
def test_quote_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.quote.return_value = QuoteResponse(
        quote_id="q-001",
        rates=[Rate(rate_id="r-1", carrier="FedEx", service="Express", price=120.0)],
    )
    result = runner.invoke(app, ["quote", "--from-zip", "06600", "--to-zip", "44100", "--weight", "1.5"])
    assert result.exit_code == 0
    assert "q-001" in result.output
    assert "FedEx" in result.output


@patch("t1envios.cli.auth_cmd.T1Client")
def test_auth_login(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value = mock_client
    result = runner.invoke(app, ["auth", "login"])
    assert result.exit_code == 0
    mock_client.login.assert_called_once()


@patch("t1envios.cli.auth_cmd.HybridStorage")
def test_auth_status_not_authenticated(mock_storage_cls):
    mock_storage_cls.return_value.load.return_value = None
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 1
    assert "Not authenticated" in result.output


@patch("t1envios.cli.auth_cmd.HybridStorage")
def test_auth_status_valid(mock_storage_cls):
    mock_storage_cls.return_value.load.return_value = _valid_token()
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "Authenticated" in result.output
