from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from t1shipments.cli.app import app
from t1shipments.core.auth.token import Token
from t1shipments.core.models.quote import QuoteResponse
from t1shipments.core.models.tracking import Balance, Carrier, TrackingResponse
from typer.testing import CliRunner

runner = CliRunner()


def _valid_token() -> Token:
    return Token(
        access_token="tok",
        refresh_token=None,
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
    )


@patch("t1shipments.cli.carriers.T1Client")
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


@patch("t1shipments.cli.shipments.T1Client")
def test_balance_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.balance.return_value = Balance(amount=500.0, currency="MXN")
    result = runner.invoke(app, ["balance"])
    assert result.exit_code == 0
    assert "500" in result.output


@patch("t1shipments.cli.shipments.T1Client")
def test_track_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.track_detail.return_value = TrackingResponse(detail=[])
    result = runner.invoke(app, ["trackdetail", "--guide", "GUIDE123"])
    assert result.exit_code == 0


@patch("t1shipments.cli.shipments.T1Client")
def test_quote_cmd(mock_cls):
    mock_client = MagicMock()
    mock_cls.from_settings.return_value.__enter__ = lambda s: mock_client
    mock_cls.from_settings.return_value.__exit__ = MagicMock(return_value=False)
    mock_client.quote.return_value = QuoteResponse(
        success=True,
        detail=[{"token": "q-001", "service_id": "FedEx", "service_name": "Express",
                 "service_type": "express", "total_cost": 120.0, "currency": "MXN",
                 "delivery_days": 2}],
    )
    result = runner.invoke(app, ["quote", "--from-zip", "06600", "--to-zip", "44100", "--weight", "1"])
    assert result.exit_code == 0
    assert "FedEx" in result.output


@patch("t1shipments.cli.auth.T1Client")
@patch("t1shipments.cli.auth.Settings")
def test_auth_login(mock_settings_cls, mock_cls):
    mock_settings_cls.return_value.username = None
    mock_settings_cls.return_value.password = None
    mock_settings_cls.return_value.commerce_id = None
    mock_settings_cls.return_value.shop_id = None
    mock_client = MagicMock()
    mock_cls.from_settings.return_value = mock_client
    mock_client.login.return_value.refresh_token = "ref"
    mock_client.login.return_value.expires_at = datetime.now(tz=UTC) + timedelta(hours=1)
    result = runner.invoke(
        app,
        ["auth", "login"],
        input="my-client-id\nmy-client-secret\nuser@example.com\nsecret123\n",
    )
    assert result.exit_code == 0
    mock_cls.from_settings.assert_called_once_with(
        client_id="my-client-id", client_secret="my-client-secret"
    )
    mock_client.login.assert_called_once_with("user@example.com", "secret123", store_id=None)


@patch("t1shipments.cli.auth.T1Client")
@patch("t1shipments.cli.auth.Settings")
def test_auth_login_with_flags(mock_settings_cls, mock_cls):
    mock_settings_cls.return_value.username = None
    mock_settings_cls.return_value.password = None
    mock_settings_cls.return_value.commerce_id = None
    mock_settings_cls.return_value.shop_id = None
    mock_client = MagicMock()
    mock_cls.from_settings.return_value = mock_client
    mock_client.login.return_value.refresh_token = "ref"
    mock_client.login.return_value.expires_at = datetime.now(tz=UTC) + timedelta(hours=1)
    result = runner.invoke(
        app,
        [
            "auth",
            "login",
            "--client-id",
            "flag-id",
            "--client-secret",
            "flag-secret",
            "-u",
            "user@example.com",
            "-p",
            "secret123",
        ],
    )
    assert result.exit_code == 0
    mock_cls.from_settings.assert_called_once_with(
        client_id="flag-id", client_secret="flag-secret"
    )
    mock_client.login.assert_called_once_with("user@example.com", "secret123", store_id=None)


@patch("t1shipments.cli.auth.HybridStorage")
def test_auth_status_not_authenticated(mock_storage_cls):
    mock_storage_cls.return_value.load.return_value = None
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 1
    assert "Not authenticated" in result.output


@patch("t1shipments.cli.auth.HybridStorage")
def test_auth_status_valid(mock_storage_cls):
    mock_storage_cls.return_value.load.return_value = _valid_token()
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "Válido" in result.output
    assert "Refresh token" in result.output


@patch("t1shipments.cli.auth.HybridStorage")
def test_auth_refresh_no_session(mock_storage_cls):
    mock_storage_cls.return_value.load.return_value = None
    result = runner.invoke(app, ["auth", "refresh"])
    assert result.exit_code == 1
    assert "No session found" in result.output


@patch("t1shipments.cli.auth.HybridStorage")
def test_auth_refresh_no_refresh_token(mock_storage_cls):
    mock_storage_cls.return_value.load.return_value = _valid_token()
    result = runner.invoke(app, ["auth", "refresh"])
    assert result.exit_code == 1
    assert "No refresh token stored" in result.output


@patch("t1shipments.cli.auth.T1Client")
@patch("t1shipments.cli.auth.HybridStorage")
def test_auth_refresh_success(mock_storage_cls, mock_client_cls):
    token = Token(
        access_token="old-token",
        refresh_token="my-refresh-token",
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=5),
        client_id="cid",
        client_secret="csecret",
    )
    mock_storage_cls.return_value.load.return_value = token
    new_token = Token(
        access_token="new-token",
        refresh_token="new-refresh",
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        client_id="cid",
        client_secret="csecret",
    )
    mock_client = MagicMock()
    mock_client.refresh.return_value = new_token
    mock_client_cls.from_settings.return_value = mock_client

    result = runner.invoke(app, ["auth", "refresh"])
    assert result.exit_code == 0
    assert "Token renovado" in result.output
    mock_client.refresh.assert_called_once()
