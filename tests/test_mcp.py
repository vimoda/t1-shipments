from __future__ import annotations

import pytest

from t1envios.mcp import prompts as prompts_module
from t1envios.mcp import resources as resources_module
from t1envios.mcp.tools import auth as auth_tools_module

from conftest import load_fixture


# ---------------------------------------------------------------------------
# Prompt tests — pure unit, no HTTP needed
# ---------------------------------------------------------------------------

class TestPrompts:
    def test_list_prompts_count(self):
        assert len(prompts_module._PROMPTS) == 5

    def test_list_prompts_names(self):
        names = {p.name for p in prompts_module._PROMPTS}
        assert names == {
            "quote_simple",
            "quote_and_ship",
            "track_status",
            "schedule_pickup_tomorrow",
            "check_balance_before_ship",
        }

    def test_quote_simple_es(self):
        result = prompts_module._get_prompt(
            "quote_simple",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "1", "insurance": "false"},
        )
        assert result.messages
        text = result.messages[0].content.text
        assert "02719" in text
        assert "40900" in text
        assert "sin seguro" in text

    def test_quote_simple_en(self):
        result = prompts_module._get_prompt(
            "quote_simple",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "1", "insurance": "false", "lang": "en"},
        )
        text = result.messages[0].content.text
        assert "insurance=no" in text
        assert "quote_shipment" in text

    def test_quote_simple_with_insurance(self):
        result = prompts_module._get_prompt(
            "quote_simple",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "2", "insurance": "true"},
        )
        text = result.messages[0].content.text
        assert "con seguro" in text

    def test_quote_and_ship_es(self):
        result = prompts_module._get_prompt(
            "quote_and_ship",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "1"},
        )
        text = result.messages[0].content.text
        assert "create_shipment" in text
        assert "costo monetario" in text

    def test_quote_and_ship_en(self):
        result = prompts_module._get_prompt(
            "quote_and_ship",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "1", "lang": "en"},
        )
        text = result.messages[0].content.text
        assert "monetary cost" in text

    def test_track_status_es(self):
        result = prompts_module._get_prompt("track_status", {"guide": "1373188795"})
        text = result.messages[0].content.text
        assert "1373188795" in text
        assert "track_guide" in text
        assert "track_detail" in text

    def test_track_status_en(self):
        result = prompts_module._get_prompt("track_status", {"guide": "1373188795", "lang": "en"})
        text = result.messages[0].content.text
        assert "delayed" in text

    def test_schedule_pickup_tomorrow_fills_date(self):
        result = prompts_module._get_prompt(
            "schedule_pickup_tomorrow",
            {"carrier": "DHL", "weight_kg": "2"},
        )
        text = result.messages[0].content.text
        assert "DHL" in text
        assert "09:00" in text
        assert "18:00" in text
        # date is tomorrow, not hardcoded — just check format
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", text)

    def test_check_balance_es(self):
        result = prompts_module._get_prompt("check_balance_before_ship", {})
        text = result.messages[0].content.text
        assert "200 MXN" in text
        assert "get_balance" in text

    def test_check_balance_en(self):
        result = prompts_module._get_prompt("check_balance_before_ship", {"lang": "en"})
        text = result.messages[0].content.text
        assert "200 MXN" in text
        assert "get_balance" in text

    def test_unknown_prompt_raises(self):
        with pytest.raises(ValueError, match="Unknown prompt"):
            prompts_module._get_prompt("nonexistent", {})


# ---------------------------------------------------------------------------
# Resource tests — needs HTTP mock via client fixture
# ---------------------------------------------------------------------------

class TestResources:
    def test_static_resources_listed(self):
        uris = {str(r.uri) for r in resources_module._STATIC_RESOURCES}
        assert "t1envios://balance" in uris
        assert "t1envios://carriers" in uris

    def test_shipment_template_uri(self):
        assert "{guide}" in resources_module._SHIPMENT_TEMPLATE.uriTemplate

    def test_read_balance(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/balance/consult",
            json=load_fixture("balance"),
        )
        contents = resources_module._read("t1envios://balance", lambda: client)
        assert len(contents) == 1
        import json
        data = json.loads(contents[0].text)
        assert data["amount"] == 1250.50

    def test_read_carriers(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/carriers",
            json=load_fixture("carriers"),
        )
        contents = resources_module._read("t1envios://carriers", lambda: client)
        import json
        data = json.loads(contents[0].text)
        assert len(data["carriers"]) == 3

    def test_read_shipment_resource(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/rastreo/detail-guia/GUIDE123",
            json=load_fixture("tracking_detail"),
        )
        contents = resources_module._read("t1envios://shipment/GUIDE123", lambda: client)
        import json
        data = json.loads(contents[0].text)
        assert len(data["detail"]) == 1

    def test_unknown_resource_raises(self, client):
        with pytest.raises(ValueError, match="Unknown resource URI"):
            resources_module._read("t1envios://unknown", lambda: client)


# ---------------------------------------------------------------------------
# New shipment tools — handler unit tests
# ---------------------------------------------------------------------------

class TestNewShipmentTools:
    def test_track_detail_tool(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/rastreo/detail-guia/GUIDE123",
            json=load_fixture("tracking_detail"),
        )
        from t1envios.mcp.tools import shipments as st
        result = st.handle("track_detail", {"guide": "GUIDE123"}, client)
        assert "detail" in result
        assert result["detail"][0]["code"] == "CR"

    def test_download_label_tool(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/label/GUIDE123",
            content=b"%PDF-1.4 fake",
        )
        from t1envios.mcp.tools import shipments as st
        result = st.handle("download_label", {"guide_link": "https://api.example.com/label/GUIDE123"}, client)
        assert result["content_type"] == "application/pdf"
        import base64
        assert base64.b64decode(result["data_base64"]) == b"%PDF-1.4 fake"

    def test_unknown_tool_raises(self, client):
        from t1envios.mcp.tools import shipments as st
        with pytest.raises(ValueError, match="Unknown tool"):
            st.handle("nonexistent", {}, client)


# ---------------------------------------------------------------------------
# Quote normalization tests
# ---------------------------------------------------------------------------

class TestQuoteNormalization:
    def _make_resp(self, detail):
        from t1envios.core.models.quote import QuoteResponse
        return QuoteResponse(success=True, detail=detail)

    def test_no_insurance_basic_fields(self):
        from t1envios.mcp.tools.shipments import _normalize_quote
        resp = self._make_resp([{
            "token": "qt-001", "service_id": "DHL", "service_name": "DHL Express",
            "total_cost": 120.0, "currency": "MXN", "delivery_days": 3,
        }])
        result = _normalize_quote(resp, insurance_requested=False)
        assert result["insurance_requested"] is False
        rate = result["rates"][0]
        assert rate["quote_token"] == "qt-001"
        assert rate["carrier"] == "DHL"
        assert rate["total_cost"] == 120.0
        assert "insurance_cost" not in rate
        assert "insurance_requested" not in rate

    def test_insurance_separated_when_field_present(self):
        from t1envios.mcp.tools.shipments import _normalize_quote
        resp = self._make_resp([{
            "token": "qt-001", "service_id": "DHL", "service_name": "DHL Express",
            "total_cost": 135.0, "insurance_cost": 15.0, "currency": "MXN", "delivery_days": 3,
        }])
        result = _normalize_quote(resp, insurance_requested=True)
        rate = result["rates"][0]
        assert rate["insurance_requested"] is True
        assert rate["insurance_cost"] == 15.0
        assert rate["base_cost"] == 120.0
        assert rate["total_cost"] == 135.0

    def test_insurance_bundled_adds_note(self):
        from t1envios.mcp.tools.shipments import _normalize_quote
        resp = self._make_resp([{
            "token": "qt-001", "service_id": "FedEx", "total_cost": 150.0, "currency": "MXN",
        }])
        result = _normalize_quote(resp, insurance_requested=True)
        rate = result["rates"][0]
        assert "insurance_note" in rate
        assert "insurance_cost" not in rate

    def test_base_cost_inferred_from_total_minus_insurance(self):
        from t1envios.mcp.tools.shipments import _normalize_quote
        resp = self._make_resp([{
            "token": "qt-1", "service_id": "UPS", "total_cost": 200.0,
            "costo_seguro": 20.0, "currency": "MXN",
        }])
        result = _normalize_quote(resp, insurance_requested=True)
        rate = result["rates"][0]
        assert rate["insurance_cost"] == 20.0
        assert rate["base_cost"] == 180.0

    def test_rate_count_and_structure(self):
        from t1envios.mcp.tools.shipments import _normalize_quote
        resp = self._make_resp([
            {"token": "a", "service_id": "DHL", "total_cost": 100.0, "currency": "MXN"},
            {"token": "b", "service_id": "FedEx", "total_cost": 120.0, "currency": "MXN"},
        ])
        result = _normalize_quote(resp, insurance_requested=False)
        assert result["rate_count"] == 2
        assert len(result["rates"]) == 2

    def test_all_tools_list_length(self):
        from t1envios.mcp.tools import shipments as st
        names = {t.name for t in st.ALL_TOOLS}
        assert "track_detail" in names
        assert "download_label" in names
        assert len(st.ALL_TOOLS) == 7


# ---------------------------------------------------------------------------
# Auth tools tests
# ---------------------------------------------------------------------------

class TestAuthTools:
    def test_auth_tools_listed(self):
        names = {t.name for t in auth_tools_module.ALL_TOOLS}
        assert names == {"auth_login", "auth_refresh", "auth_set_session"}

    def test_auth_login(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token",
            json=load_fixture("login"),
        )
        result = auth_tools_module.handle("auth_login", {"username": "u", "password": "p"}, client)
        assert result["access_token"] == "test-access-token"
        assert result["refresh_token"] == "test-refresh-token"
        assert "expires_at" in result

    def test_auth_set_session_with_refresh(self, client):
        result = auth_tools_module.handle(
            "auth_set_session",
            {"access_token": "tok-abc", "refresh_token": "ref-xyz"},
            client,
        )
        assert result["ok"] is True
        assert result["auto_refresh"] is True
        assert client._auth._token.access_token == "tok-abc"
        assert client._auth._token.refresh_token == "ref-xyz"
        assert client._auth.auto_refresh is True

    def test_auth_set_session_access_only(self, client):
        result = auth_tools_module.handle(
            "auth_set_session",
            {"access_token": "tok-abc"},
            client,
        )
        assert result["auto_refresh"] is False
        assert client._auth.auto_refresh is False

    def test_auth_set_session_with_expires_at(self, client):
        auth_tools_module.handle(
            "auth_set_session",
            {"access_token": "tok", "expires_at": "2030-01-01T00:00:00Z"},
            client,
        )
        assert client._auth._token.expires_at.year == 2030

    def test_auth_refresh(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token",
            json={"access_token": "new-token", "refresh_token": "new-refresh", "expires_in": 3600},
        )
        result = auth_tools_module.handle("auth_refresh", {"refresh_token": "old-refresh"}, client)
        assert result["access_token"] == "new-token"
        assert result["refresh_token"] == "new-refresh"

    def test_unknown_auth_tool_raises(self, client):
        with pytest.raises(ValueError, match="Unknown auth tool"):
            auth_tools_module.handle("nonexistent", {}, client)


# ---------------------------------------------------------------------------
# auto_refresh behavior tests
# ---------------------------------------------------------------------------

class TestAutoRefresh:
    def test_inject_token_with_refresh_enables_auto_refresh(self, client):
        client.inject_token("access", "refresh")
        assert client._auth.auto_refresh is True

    def test_inject_token_access_only_disables_auto_refresh(self, client):
        client.inject_token("access")
        assert client._auth.auto_refresh is False

    def test_ensure_valid_no_auto_refresh_raises_on_expired(self, client):
        from datetime import datetime, timezone
        from t1envios.core.auth.token import Token
        from t1envios.core.exceptions import SessionExpiredError

        client._auth.auto_refresh = False
        client._auth._token = Token(
            access_token="expired",
            refresh_token="has-refresh",  # has refresh but auto_refresh=False
            expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(SessionExpiredError):
            client._auth.ensure_valid()

    def test_ensure_valid_auto_refresh_true_refreshes(self, httpx_mock, client):
        from datetime import datetime, timezone
        from t1envios.core.auth.token import Token

        client._auth.auto_refresh = True
        client._auth._token = Token(
            access_token="expired",
            refresh_token="valid-refresh",
            expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
        )
        httpx_mock.add_response(
            url="https://api.example.com/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token",
            json={"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 3600},
        )
        token = client._auth.ensure_valid()
        assert token.access_token == "new-access"
