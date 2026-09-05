from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from t1shipments.cli.app import app
from t1shipments.core.auth.storage import InMemoryStorage
from t1shipments.core.auth.token import Token
from t1shipments.core.client import T1Client
from t1shipments.core.config import Settings
from t1shipments.core.exceptions import ConfigError
from t1shipments.mcp import server as mcp_server
from typer.testing import CliRunner

runner = CliRunner()


def test_settings_does_not_require_client_credentials():
    s = Settings()
    assert not hasattr(s, "client_id")
    assert not hasattr(s, "client_secret")


def test_from_settings_explicit_credentials():
    client = T1Client.from_settings(
        client_id="explicit-id",
        client_secret="explicit-secret",
        token_storage=InMemoryStorage(),
    )
    assert client._auth._client_id == "explicit-id"
    assert client._auth._client_secret == "explicit-secret"


def test_from_settings_loaded_from_storage():
    stored_token = Token(
        access_token="tok",
        refresh_token="ref",
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        client_id="stored-id",
        client_secret="stored-secret",
    )
    storage = InMemoryStorage(token=stored_token)
    client = T1Client.from_settings(token_storage=storage)
    assert client._auth._client_id == "stored-id"
    assert client._auth._client_secret == "stored-secret"


def test_from_settings_missing_credentials_raises_config_error():
    storage = InMemoryStorage()
    with pytest.raises(ConfigError, match="client_id and client_secret are required"):
        T1Client.from_settings(token_storage=storage)


@patch("t1shipments.core.config.Settings")
def test_mcp_set_credentials_and_get_client(mock_settings_cls):
    mock_settings_cls.return_value.username = None
    mock_settings_cls.return_value.password = None
    mock_settings_cls.return_value.endpoints.return_value = None
    mock_settings_cls.return_value.timeout = 30.0
    mock_settings_cls.return_value.shop_id = None
    mock_settings_cls.return_value.commerce_id = None
    mock_settings_cls.return_value.retries = 3
    mock_settings_cls.return_value.log_level = None
    mcp_server._CLIENT = None
    mcp_server.set_credentials("mcp-id", "mcp-secret")
    client = mcp_server._get_client()
    assert client._auth._client_id == "mcp-id"
    assert client._auth._client_secret == "mcp-secret"
    mcp_server._CLIENT = None


def test_mcp_main_missing_args_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        mcp_server.main(argv=[])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Faltan argumentos requeridos" in captured.err


def test_cli_mcp_install_writes_args(tmp_path, monkeypatch):
    mock_config = tmp_path / "claude_config.json"
    monkeypatch.setattr("t1shipments.cli.mcp_cmd._claude_config_path", lambda: mock_config)

    result = runner.invoke(
        app,
        ["mcp", "install", "--client-id", "custom-id", "--client-secret", "custom-sec"],
    )
    assert result.exit_code == 0
    assert mock_config.exists()
    data = json.loads(mock_config.read_text())
    server_cfg = data["mcpServers"]["t1shipments"]
    assert "--client-id" in server_cfg["args"]
    assert "custom-id" in server_cfg["args"]
    assert "--client-secret" in server_cfg["args"]
    assert "custom-sec" in server_cfg["args"]
    assert "env" not in server_cfg
