from __future__ import annotations

import httpx
from pydantic import ValidationError

import mcp.types as types

from ...core.exceptions import ApiError
from ...core.models.quote import QuoteRequest, QuoteResponse
from ...core.models.shipment import ShipmentRequest
from ...core.models.tracking import PickupRequest

TOOL_GET_BALANCE = types.Tool(
    name="get_balance",
    description=(
        "Get the current account balance in MXN. "
        "Call before creating shipments to verify sufficient funds. "
        "Respond with the balance amount and a warning if insufficient. "
        "Always respond in the user's language."
    ),
    inputSchema={"type": "object", "properties": {}},
)

TOOL_TRACK_GUIDE = types.Tool(
    name="track_guide",
    description=(
        "Track a shipment by guide number. "
        "Returns current status, estimated delivery date, and event history. "
        "Respond with: status, estimated delivery date, and last event. "
        "One short paragraph max. If delayed, say so explicitly. "
        "Always respond in the user's language."
    ),
    inputSchema={
        "type": "object",
        "properties": {"guide": {"type": "string", "description": "Guide/tracking number"}},
        "required": ["guide"],
    },
)

TOOL_TRACK_DETAIL = types.Tool(
    name="track_detail",
    description=(
        "Get full tracking detail for a shipment. "
        "Returns all tracking events with timestamps, locations, and carrier info. "
        "Use when track_guide shows a delayed or stuck status. "
        "Respond with a bullet list of events (date, location, status). Most recent first. No extra commentary. "
        "Always respond in the user's language."
    ),
    inputSchema={
        "type": "object",
        "properties": {"guide": {"type": "string", "description": "Guide/tracking number"}},
        "required": ["guide"],
    },
)

TOOL_QUOTE = types.Tool(
    name="quote_shipment",
    description=(
        "This tool ONLY returns shipping rates/prices. It does NOT create a shipment. "
        "There are two flows:\n"
        "1) QUICK QUOTE — user just wants to know prices. Required: origin ZIP, destination ZIP, weight, "
        "dimensions (or defaults), insurance (true/false). package_value only if insurance=true. "
        "package_type and packages are NOT needed (defaults: 1 package, parcel). "
        "Show rates WITHOUT the quote_token column and STOP — do not proceed to create_shipment.\n"
        "2) FULL QUOTE — user wants to create a shipment/generate a guide. Requires all quick quote fields "
        "PLUS package_type and packages. Show rates WITH the quote_token column so the user can "
        "select a rate to proceed with create_shipment.\n"
        "Before quoting, check your memory for saved addresses. "
        "If there are saved addresses, list each showing its name, email, and phone so the user can identify it. "
        "Then ask: 'What email or phone is the address saved under?' to find the right one. "
        "- If ORIGIN and DESTINATION are found: ask 'Do you want to use [origin] → [destination], "
        "change only the origin, change only the destination, or provide both new ones?' "
        "- If only ORIGIN is found: 'I have [origin]. Use it or a different one? And tell me the destination.' "
        "- If only DESTINATION is found: 'I have [destination]. Use it or a different one? And tell me the origin.' "
        "- If none saved: proceed normally asking for ZIP codes. "
        "Get available shipping rates. "
        "Requires weight, dimensions (width/height/length), and origin/destination ZIP codes. "
        "Calculate the volumetric weight = ceil(width × height × length / 5000). "
        "All weights are rounded UP to the nearest integer. "
        "Use the LARGER of the physical weight and the volumetric weight as the weight parameter. "
        "Returns a list sorted cheapest-first; rows with recommended=true appear first. "
        "Each rate exposes: quote_token, carrier, service, service_type, base_cost, total_cost, "
        "currency, estimated_days, delivery_date, weight_kg, volumetric_weight_kg, "
        "dimensions_cm {length,width,height}, package_value, packages, insurance_applied, recommended. "
        "The response also includes insurance_requested at the root level. "
        "When insurance=true: if insurance_applied=true and base_cost differs from total_cost, "
        "the rate also includes insurance_cost (= total_cost - base_cost). "
        "If insurance_applied=false, the rate includes insurance_note explaining insurance was not applied. "
        "package_value is only needed when insurance=true — otherwise omit it. "
        "Dimension defaults if omitted: width=30cm, height=20cm, length=15cm, "
        "package_value=500 MXN, packages=1, package_type=2 (parcel). "
        "QUICK QUOTE: show a numbered table with columns: #, Carrier, Service, Type, Guide cost, Insurance cost, Total, Currency, "
        "Days, Estimated delivery, Weight (kg), Volumetric weight (kg), Dimensions (cm). "
        "Do NOT show the quote_token column for quick quotes. "
        "FULL QUOTE: show the same table WITH the Quote token column. "
        "Highlight rows with recommended=true with ★. "
        "When insurance=true and insurance_applied=true: Guide cost = base_cost, Insurance cost = insurance_cost, Total = total_cost. "
        "When insurance=false or insurance_applied=false: Guide cost = total_cost, Insurance cost = '—', Total = total_cost. "
        "Also show insurance_note clearly when insurance_applied=false. "
        "In your response, clarify which weight was used (physical vs volumetric) and its rounded integer value. "
        "When the user asks for a simple quote (quick quote): show the table and STOP. "
        "When the user wants to create a shipment: show the table and end by asking "
        "which service to proceed with, in the user's language. "
        "The response includes a 'recommendations' field with 'cheapest', 'fastest', and 'best_value' "
        "(best cost-to-delivery-time ratio). Use this data to suggest the best option to the user "
        "based on their priorities. For example: 'La opción más barata es [carrier] [service] "
        "con $[total_cost] y [estimated_days] días hábiles.' Always highlight the recommendation "
        "that best matches the user's stated or implied needs. "
        "Always respond in the user's language."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "origin_postal_code": {
                "type": "string",
                "description": "5-digit Mexican origin ZIP code",
            },
            "destination_postal_code": {
                "type": "string",
                "description": "5-digit Mexican destination ZIP code",
            },
            "weight": {
                "type": "number",
                "description": "Weight in kg. Use the LARGER of physical weight and volumetric weight (ceil(W×H×L/5000)), rounded UP to integer.",
            },
            "width": {"type": "number", "description": "Width in cm (default 30)"},
            "height": {"type": "number", "description": "Height in cm (default 20)"},
            "length": {"type": "number", "description": "Length in cm (default 15)"},
            "shipping_days": {"type": "integer", "description": "Days until shipment"},
            "package_value": {
                "type": "number",
                "description": "Declared value in MXN (only required when insurance=true)",
            },
            "insurance": {"type": "boolean", "description": "Include insurance"},
            "packages": {"type": "integer", "description": "Number of packages (default 1)"},
            "package_type": {"type": "integer", "description": "1=Envelope, 2=Parcel (default 2)"},
        },
        "required": [
            "origin_postal_code",
            "destination_postal_code",
            "weight",
            "insurance",
        ],
    },
)

TOOL_CREATE_SHIPMENT = types.Tool(
    name="create_shipment",
    description=(
        "⚠️ This operation has a monetary cost. "
        "Create a shipment and generate a shipping guide. "
        "Requires a quote_token from quote_shipment. "
        "Flow: quote_shipment → select rate → create_shipment. "
        "Before calling this tool, check your memory for saved addresses. "
        "If there are saved addresses, list each showing its name, email, and phone so the user can identify it. "
        "Then ask: 'What email or phone is the address saved under?' to find the right one. "
        "- If ORIGIN and DESTINATION are found: ask 'Do you want to use [origin] → [destination], "
        "change only the origin, change only the destination, or provide both new ones?' "
        "- If only ORIGIN is found: 'I have [origin]. Use it or a different one? And tell me the destination.' "
        "- If only DESTINATION is found: 'I have [destination]. Use it or a different one? And tell me the origin.' "
        "- If none saved: proceed normally asking for details. "
        "AFTER creating the guide successfully, check your memory to see if those addresses are already saved. "
        "- If they exist: say 'The addresses are already saved.' "
        "- If they don't exist: ask the user 'Would you like to save the addresses for later use?' "
        "If the origin ZIP has multiple neighborhoods, ask the user which one applies before calling. "
        "On success respond with: guide number, carrier, estimated delivery date, and label download link. "
        "One sentence each. No JSON, no raw data. "
        "Always respond in the user's language."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "quote_token": {"type": "string", "description": "Rate token from quote_shipment"},
            "content": {"type": "string", "description": "Package contents (max 25 chars)"},
            "origin_first_name": {"type": "string", "description": "Sender first name"},
            "origin_last_name": {"type": "string", "description": "Sender last name"},
            "origin_email": {"type": "string", "description": "Sender email"},
            "origin_street": {"type": "string", "description": "Sender street"},
            "origin_number": {"type": "string", "description": "Sender exterior number"},
            "origin_neighborhood": {
                "type": "string",
                "description": "Sender neighborhood/colonia. If ZIP has multiple colonias, confirm with user first",
            },
            "origin_phone": {"type": "string", "description": "Sender phone"},
            "origin_state": {"type": "string", "description": "Sender state"},
            "origin_municipality": {"type": "string", "description": "Sender municipality"},
            "origin_references": {
                "type": "string",
                "description": "Address references — include interior/apartment/tower details first, then general references. Max 35 chars.",
            },
            "origin_postal_code": {"type": "string", "description": "Sender 5-digit ZIP"},
            "destination_first_name": {"type": "string", "description": "Recipient first name"},
            "destination_last_name": {"type": "string", "description": "Recipient last name"},
            "destination_email": {"type": "string", "description": "Recipient email"},
            "destination_street": {"type": "string", "description": "Recipient street"},
            "destination_number": {"type": "string", "description": "Recipient exterior number"},
            "destination_neighborhood": {
                "type": "string",
                "description": "Recipient neighborhood/colonia",
            },
            "destination_phone": {"type": "string", "description": "Recipient phone"},
            "destination_state": {"type": "string", "description": "Recipient state"},
            "destination_municipality": {"type": "string", "description": "Recipient municipality"},
            "destination_references": {
                "type": "string",
                "description": "Address references — include interior/apartment/tower details first, then general references. Max 35 chars.",
            },
            "destination_postal_code": {"type": "string", "description": "Recipient 5-digit ZIP"},
            "packages": {"type": "integer", "description": "Number of packages"},
        },
        "required": [
            "quote_token",
            "content",
            "origin_first_name",
            "origin_last_name",
            "origin_email",
            "origin_street",
            "origin_number",
            "origin_neighborhood",
            "origin_phone",
            "origin_state",
            "origin_municipality",
            "origin_postal_code",
            "destination_first_name",
            "destination_last_name",
            "destination_email",
            "destination_street",
            "destination_number",
            "destination_neighborhood",
            "destination_phone",
            "destination_state",
            "destination_municipality",
            "destination_postal_code",
            "packages",
        ],
    },
)

TOOL_DOWNLOAD_LABEL = types.Tool(
    name="download_label",
    description=(
        "Download the shipping label PDF for a guide. "
        "Use the guide_link returned by create_shipment. Returns base64-encoded PDF content. "
        "Respond with a message saying the label is ready with the download link. Do not show the base64 data. "
        "Always respond in the user's language."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "guide_link": {
                "type": "string",
                "description": "Label URL from create_shipment response",
            },
        },
        "required": ["guide_link"],
    },
)

TOOL_SCHEDULE_PICKUP = types.Tool(
    name="schedule_pickup",
    description=(
        "⚠️ This operation has a monetary cost. "
        "Schedule a package pickup at the origin address. "
        "The origin address must be registered in T1Envios beforehand. "
        "On success respond with a message confirming the pickup date, time window, and carrier. One line only. "
        "Always respond in the user's language."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "carrier": {"type": "string", "description": "Carrier name: DHL, FEDEX, UPS"},
            "contact_first_name": {"type": "string"},
            "contact_last_name": {"type": "string"},
            "email": {"type": "string"},
            "street": {"type": "string"},
            "number": {"type": "string"},
            "neighborhood": {"type": "string"},
            "phone": {"type": "string"},
            "state": {"type": "string"},
            "municipality": {"type": "string"},
            "postal_code": {"type": "string"},
            "references": {"type": "string"},
            "pieces": {"type": "integer"},
            "weight": {"type": "integer", "description": "Total weight in kg"},
            "length": {"type": "integer", "description": "Length in cm"},
            "width": {"type": "integer", "description": "Width in cm"},
            "height": {"type": "integer", "description": "Height in cm"},
            "date": {"type": "string", "description": "Pickup date YYYY-MM-DD"},
            "open_time": {"type": "string", "description": "Open time HH:MM"},
            "close_time": {"type": "string", "description": "Close time HH:MM"},
        },
        "required": [
            "carrier",
            "contact_first_name",
            "contact_last_name",
            "email",
            "street",
            "number",
            "neighborhood",
            "phone",
            "state",
            "municipality",
            "postal_code",
            "references",
            "pieces",
            "weight",
            "length",
            "width",
            "height",
            "date",
            "open_time",
            "close_time",
        ],
    },
)

ALL_TOOLS = [
    TOOL_GET_BALANCE,
    TOOL_TRACK_GUIDE,
    TOOL_TRACK_DETAIL,
    TOOL_QUOTE,
    TOOL_CREATE_SHIPMENT,
    TOOL_DOWNLOAD_LABEL,
    TOOL_SCHEDULE_PICKUP,
]


def handle(name: str, arguments: dict, client) -> dict:
    arguments = {k: v for k, v in arguments.items() if v is not None}
    try:
        if name == "get_balance":
            return client.balance().model_dump()
        if name == "track_guide":
            return client.track_state(arguments["guide"]).model_dump()
        if name == "track_detail":
            return client.track_detail(arguments["guide"]).model_dump()
        if name == "quote_shipment":
            req = QuoteRequest(**arguments)
            resp = client.quote(req)
            return _normalize_quote(resp, insurance_requested=arguments.get("insurance", False))
        if name == "create_shipment":
            req = ShipmentRequest(**arguments)
            return client.create_shipment(req).model_dump()
        if name == "download_label":
            pdf_bytes = client.download_label(arguments["guide_link"])
            import base64

            return {
                "content_type": "application/pdf",
                "data_base64": base64.b64encode(pdf_bytes).decode(),
            }
        if name == "schedule_pickup":
            req = PickupRequest(**arguments)
            return client.schedule_pickup(req).model_dump()
        raise ValueError(f"Unknown tool: {name}")
    except ValidationError as e:
        return {"success": False, "error": f"Validation error: {e.errors()}"}
    except ApiError as e:
        return {"success": False, "error": str(e)}
    except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.TimeoutException) as e:
        return {"success": False, "error": f"Connection error: {e}"}


def _normalize_quote(resp: QuoteResponse, *, insurance_requested: bool) -> dict:
    rates = []
    for raw in resp.detail or []:
        if not isinstance(raw, dict):
            rates.append(raw)
            continue

        base_cost = raw.get("cost")
        total_cost = raw.get("total_cost") or 0.0
        insurance_applied = bool(raw.get("insurance", False))

        rate: dict = {
            "quote_token": raw.get("token"),
            "carrier": raw.get("carrier") or raw.get("service_id") or "",
            "service": raw.get("service_name") or raw.get("service") or "",
            "service_type": raw.get("service_type"),
            "base_cost": base_cost,
            "total_cost": total_cost,
            "currency": raw.get("currency", "MXN"),
            "estimated_days": raw.get("delivery_days"),
            "delivery_date": raw.get("delivery_date_carrier") or raw.get("delivery_date_claro"),
            "weight_kg": raw.get("weight"),
            "volumetric_weight_kg": raw.get("volumetric_weight"),
            "dimensions_cm": {
                "length": raw.get("length"),
                "width": raw.get("width"),
                "height": raw.get("height"),
            },
            "package_value": raw.get("package_value"),
            "packages": raw.get("total_packages", 1),
            "insurance_applied": insurance_applied,
            "recommended": bool(raw.get("recommended", False)),
        }

        if insurance_requested:
            if insurance_applied and base_cost is not None and base_cost != total_cost:
                rate["insurance_cost"] = round(total_cost - base_cost, 2)
            elif not insurance_applied:
                rate["insurance_note"] = "Insurance was requested but this rate did not apply it."

        rates.append(rate)

    # recommended rows first, then ascending total_cost
    rates.sort(key=lambda r: (not r.get("recommended", False), r.get("total_cost") or 0.0))

    recommendations = {}
    if rates:
        _cheapest = min(rates, key=lambda r: r.get("total_cost") or float("inf"))
        recommendations["cheapest"] = {
            "quote_token": _cheapest.get("quote_token"),
            "carrier": _cheapest.get("carrier"),
            "service": _cheapest.get("service"),
            "total_cost": _cheapest.get("total_cost"),
            "estimated_days": _cheapest.get("estimated_days"),
        }

        rates_with_days = [r for r in rates if r.get("estimated_days") is not None]
        if rates_with_days:
            _fastest = min(rates_with_days, key=lambda r: r["estimated_days"])
            recommendations["fastest"] = {
                "quote_token": _fastest.get("quote_token"),
                "carrier": _fastest.get("carrier"),
                "service": _fastest.get("service"),
                "total_cost": _fastest.get("total_cost"),
                "estimated_days": _fastest.get("estimated_days"),
            }

            _best_value = min(
                rates_with_days,
                key=lambda r: (r.get("total_cost") or float("inf")) / r["estimated_days"],
            )
            recommendations["best_value"] = {
                "quote_token": _best_value.get("quote_token"),
                "carrier": _best_value.get("carrier"),
                "service": _best_value.get("service"),
                "total_cost": _best_value.get("total_cost"),
                "estimated_days": _best_value.get("estimated_days"),
            }

    return {
        "success": resp.success,
        "has_insurance": insurance_requested,
        "insurance_requested": insurance_requested,
        "rate_count": len(rates),
        "rates": rates,
        "recommendations": recommendations,
    }
