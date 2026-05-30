from __future__ import annotations

from datetime import UTC

import pytest
from conftest import load_fixture
from t1shipments.mcp import prompts as prompts_module
from t1shipments.mcp import resources as resources_module
from t1shipments.mcp.tools import auth as auth_tools_module

# ---------------------------------------------------------------------------
# Prompt tests — pure unit, no HTTP needed
# ---------------------------------------------------------------------------


class TestPrompts:
    def test_list_prompts_count(self):
        assert len(prompts_module._PROMPTS) == 8

    def test_list_prompts_names(self):
        names = {p.name for p in prompts_module._PROMPTS}
        assert names == {
            "quick_quote",
            "create_shipment_with_stored_address",
            "quote",
            "ship",
            "track_status",
            "schedule_pickup_tomorrow",
            "choose_quote_flow",
            "developer_instructions",
        }

    def test_quick_quote_no_quote_token(self):
        result = prompts_module._get_prompt(
            "quick_quote",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "1", "insurance": "false"},
        )
        assert result.messages
        text = result.messages[0].content.text
        assert "02719" in text
        assert "40900" in text
        assert "without insurance" in text or "sin seguro" in text
        assert "QUICK QUOTE only" in text
        assert "Quote token" not in text

    def test_quick_quote_with_insurance_value(self):
        result = prompts_module._get_prompt(
            "quick_quote",
            {
                "origin_zip": "02719",
                "dest_zip": "40900",
                "weight_kg": "1",
                "insurance": "true",
                "package_value": "500",
            },
        )
        text = result.messages[0].content.text
        assert "with insurance" in text or "con seguro" in text

    def test_quote_es(self):
        result = prompts_module._get_prompt(
            "quote",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "1", "insurance": "false"},
        )
        assert result.messages
        text = result.messages[0].content.text
        assert "02719" in text
        assert "40900" in text
        assert "without insurance" in text or "sin seguro" in text
        assert "Volumetric weight" in text or "Peso volumétrico" in text
        assert "Quote token" in text
        assert "Dimensions" in text or "Dimensiones" in text
        assert "FULL QUOTE" in text or "full quote" in text.lower()

    def test_quote_en(self):
        result = prompts_module._get_prompt(
            "quote",
            {
                "origin_zip": "02719",
                "dest_zip": "40900",
                "weight_kg": "1",
                "insurance": "false",
                "lang": "en",
            },
        )
        text = result.messages[0].content.text
        assert "quote_shipment" in text
        assert "Volumetric weight" in text
        assert "Quote token" in text
        assert "Dimensions" in text

    def test_quote_with_insurance(self):
        result = prompts_module._get_prompt(
            "quote",
            {"origin_zip": "02719", "dest_zip": "40900", "weight_kg": "2", "insurance": "true"},
        )
        text = result.messages[0].content.text
        assert "with" in text or "con seguro" in text

    def test_ship_es(self):
        result = prompts_module._get_prompt("ship", {"quote_token": "tok-abc"})
        text = result.messages[0].content.text
        assert "tok-abc" in text
        assert "monetary cost" in text
        assert "sender" in text.lower() or "remitente" in text.lower()
        assert "recipient" in text.lower() or "destinatario" in text.lower()

    def test_ship_en(self):
        result = prompts_module._get_prompt("ship", {"quote_token": "tok-abc", "lang": "en"})
        text = result.messages[0].content.text
        assert "tok-abc" in text
        assert "monetary cost" in text
        assert "sender" in text.lower() or "remitente" in text.lower()
        assert "recipient" in text.lower() or "destinatario" in text.lower()

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

    def test_developer_instructions_full(self):
        result = prompts_module._get_prompt("developer_instructions", {})
        text = result.messages[0].content.text
        assert "t1shipments://developer-instructions" in text
        assert "Python SDK" in text or "SDK" in text
        assert "REST API" in text
        assert "user's language" in text

    def test_developer_instructions_sdk_topic(self):
        result = prompts_module._get_prompt("developer_instructions", {"topic": "sdk"})
        text = result.messages[0].content.text
        assert "T1Client" in text
        assert "T1_CLIENT_ID" in text
        assert "user's language" in text

    def test_developer_instructions_api_topic(self):
        result = prompts_module._get_prompt("developer_instructions", {"topic": "api"})
        text = result.messages[0].content.text
        assert "Keycloak" in text or "OIDC" in text
        assert "Authorization" in text
        assert "user's language" in text

    def test_developer_instructions_auth_topic(self):
        result = prompts_module._get_prompt("developer_instructions", {"topic": "auth"})
        text = result.messages[0].content.text
        assert "auto-refresh" in text
        assert "401" in text
        assert "user's language" in text

    def test_developer_instructions_models_topic(self):
        result = prompts_module._get_prompt("developer_instructions", {"topic": "models"})
        text = result.messages[0].content.text
        assert "QuoteRequest" in text
        assert "ShipmentRequest" in text
        assert "user's language" in text

    def test_unknown_prompt_raises(self):
        with pytest.raises(ValueError, match="Unknown prompt"):
            prompts_module._get_prompt("nonexistent", {})


# ---------------------------------------------------------------------------
# Resource tests — needs HTTP mock via client fixture
# ---------------------------------------------------------------------------


class TestResources:
    def test_static_resources_listed(self):
        uris = {str(r.uri) for r in resources_module._STATIC_RESOURCES}
        assert "t1shipments://balance" in uris
        assert "t1shipments://carriers" in uris
        assert "t1shipments://developer-instructions" in uris

    def test_shipment_template_uri(self):
        assert "{guide}" in resources_module._SHIPMENT_TEMPLATE.uriTemplate

    def test_read_balance(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/balance/consult",
            json=load_fixture("balance"),
        )
        contents = resources_module._read("t1shipments://balance", lambda: client)
        assert len(contents) == 1
        import json

        data = json.loads(contents[0].text)
        assert data["amount"] == 1250.50

    def test_read_carriers(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/carriers",
            json=load_fixture("carriers"),
        )
        contents = resources_module._read("t1shipments://carriers", lambda: client)
        import json

        data = json.loads(contents[0].text)
        assert len(data["carriers"]) == 3

    def test_read_shipment_resource(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/rastreo/detail-guia/GUIDE123",
            json=load_fixture("tracking_detail"),
        )
        contents = resources_module._read("t1shipments://shipment/GUIDE123", lambda: client)
        import json

        data = json.loads(contents[0].text)
        assert len(data["detail"]) == 1

    def test_read_developer_instructions(self, client):
        contents = resources_module._read(
            "t1shipments://developer-instructions", lambda: client
        )
        assert len(contents) == 1
        text = contents[0].text
        assert "T1Envios" in text
        assert "T1Client.from_settings" in text
        assert "T1_CLIENT_ID" in text
        assert "/quote/create-with-quote" in text
        assert "Authorization: Bearer" in text
        assert "QuoteRequest" in text
        assert "ShipmentRequest" in text
        assert "user's language" in text

    def test_unknown_resource_raises(self, client):
        with pytest.raises(ValueError, match="Unknown resource URI"):
            resources_module._read("t1shipments://unknown", lambda: client)


# ---------------------------------------------------------------------------
# New shipment tools — handler unit tests
# ---------------------------------------------------------------------------


class TestNewShipmentTools:
    def test_track_detail_tool(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/rastreo/detail-guia/GUIDE123",
            json=load_fixture("tracking_detail"),
        )
        from t1shipments.mcp.tools import shipments as st

        result = st.handle("track_detail", {"guide": "GUIDE123"}, client)
        assert "detail" in result
        assert result["detail"][0]["code"] == "CR"

    def test_download_label_tool(self, httpx_mock, client):
        httpx_mock.add_response(
            url="https://api.example.com/label/GUIDE123",
            content=b"%PDF-1.4 fake",
        )
        from t1shipments.mcp.tools import shipments as st

        result = st.handle(
            "download_label", {"guide_link": "https://api.example.com/label/GUIDE123"}, client
        )
        assert result["content_type"] == "application/pdf"
        import base64

        assert base64.b64decode(result["data_base64"]) == b"%PDF-1.4 fake"

    def test_unknown_tool_raises(self, client):
        from t1shipments.mcp.tools import shipments as st

        with pytest.raises(ValueError, match="Unknown tool"):
            st.handle("nonexistent", {}, client)


# ---------------------------------------------------------------------------
# Quote normalization tests
# ---------------------------------------------------------------------------


class TestQuoteNormalization:
    def _make_resp(self, detail):
        from t1shipments.core.models.quote import QuoteResponse

        return QuoteResponse(success=True, detail=detail)

    def _flat_rate(self, **kwargs):
        base = {
            "token": "qt-001",
            "carrier": "DHL",
            "service_name": "DHL Express",
            "service_type": "Economico",
            "cost": 100.0,
            "total_cost": 100.0,
            "currency": "MXN",
            "delivery_days": 3,
            "delivery_date_carrier": "2026-05-12",
            "weight": 1.0,
            "volumetric_weight": 0.2,
            "length": 10.0,
            "width": 10.0,
            "height": 10.0,
            "package_value": 500.0,
            "insurance": False,
            "recommended": False,
        }
        base.update(kwargs)
        return base

    def test_basic_fields_exposed(self):
        from t1shipments.mcp.tools.shipments import _normalize_quote

        resp = self._make_resp([self._flat_rate(token="tok-x", carrier="FEDEX")])
        result = _normalize_quote(resp, insurance_requested=False)
        assert result["has_insurance"] is False
        assert result["insurance_requested"] is False
        rate = result["rates"][0]
        assert rate["quote_token"] == "tok-x"
        assert rate["carrier"] == "FEDEX"
        assert rate["service"] == "DHL Express"
        assert rate["service_type"] == "Economico"
        assert rate["base_cost"] == 100.0
        assert rate["total_cost"] == 100.0
        assert rate["weight_kg"] == 1.0
        assert rate["volumetric_weight_kg"] == 0.2
        assert rate["dimensions_cm"] == {"length": 10.0, "width": 10.0, "height": 10.0}
        assert rate["delivery_date"] == "2026-05-12"
        assert rate["recommended"] is False
        assert "insurance_cost" not in rate
        assert "insurance_note" not in rate

    def test_insurance_applied_derives_insurance_cost(self):
        from t1shipments.mcp.tools.shipments import _normalize_quote

        resp = self._make_resp([self._flat_rate(insurance=True, cost=100.0, total_cost=120.0)])
        result = _normalize_quote(resp, insurance_requested=True)
        rate = result["rates"][0]
        assert rate["insurance_applied"] is True
        assert rate["insurance_cost"] == 20.0
        assert rate["base_cost"] == 100.0
        assert rate["total_cost"] == 120.0

    def test_insurance_requested_but_not_applied_adds_note(self):
        from t1shipments.mcp.tools.shipments import _normalize_quote

        resp = self._make_resp([self._flat_rate(insurance=False)])
        result = _normalize_quote(resp, insurance_requested=True)
        rate = result["rates"][0]
        assert "insurance_note" in rate
        assert "insurance_cost" not in rate

    def test_no_insurance_path_omits_insurance_fields(self):
        from t1shipments.mcp.tools.shipments import _normalize_quote

        resp = self._make_resp([self._flat_rate(insurance=True, cost=100.0, total_cost=120.0)])
        result = _normalize_quote(resp, insurance_requested=False)
        rate = result["rates"][0]
        assert "insurance_cost" not in rate
        assert "insurance_note" not in rate

    def test_rates_sorted_by_total_cost_with_recommended_first(self):
        from t1shipments.mcp.tools.shipments import _normalize_quote

        resp = self._make_resp(
            [
                self._flat_rate(token="cheap", total_cost=80.0, cost=80.0, recommended=False),
                self._flat_rate(token="medium", total_cost=100.0, cost=100.0, recommended=True),
                self._flat_rate(token="expensive", total_cost=150.0, cost=150.0, recommended=False),
            ]
        )
        result = _normalize_quote(resp, insurance_requested=False)
        tokens = [r["quote_token"] for r in result["rates"]]
        assert tokens == ["medium", "cheap", "expensive"]

    def test_rate_count_and_structure(self):
        from t1shipments.mcp.tools.shipments import _normalize_quote

        resp = self._make_resp(
            [
                self._flat_rate(token="a", total_cost=100.0),
                self._flat_rate(token="b", total_cost=120.0),
            ]
        )
        result = _normalize_quote(resp, insurance_requested=False)
        assert result["rate_count"] == 2
        assert len(result["rates"]) == 2

    def test_all_tools_list_length(self):
        from t1shipments.mcp.tools import shipments as st

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
        from datetime import datetime

        from t1shipments.core.auth.token import Token
        from t1shipments.core.exceptions import SessionExpiredError

        client._auth.auto_refresh = False
        client._auth._token = Token(
            access_token="expired",
            refresh_token="has-refresh",  # has refresh but auto_refresh=False
            expires_at=datetime(2000, 1, 1, tzinfo=UTC),
        )
        with pytest.raises(SessionExpiredError):
            client._auth.ensure_valid()

    def test_ensure_valid_auto_refresh_true_refreshes(self, httpx_mock, client):
        from datetime import datetime

        from t1shipments.core.auth.token import Token

        client._auth.auto_refresh = True
        client._auth._token = Token(
            access_token="expired",
            refresh_token="valid-refresh",
            expires_at=datetime(2000, 1, 1, tzinfo=UTC),
        )
        httpx_mock.add_response(
            url="https://api.example.com/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token",
            json={"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 3600},
        )
        token = client._auth.ensure_valid()
        assert token.access_token == "new-access"
