from __future__ import annotations

import pytest

from t1envios.mcp import prompts as prompts_module
from t1envios.mcp import resources as resources_module

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

    def test_all_tools_list_length(self):
        from t1envios.mcp.tools import shipments as st
        names = {t.name for t in st.ALL_TOOLS}
        assert "track_detail" in names
        assert "download_label" in names
        assert len(st.ALL_TOOLS) == 7
