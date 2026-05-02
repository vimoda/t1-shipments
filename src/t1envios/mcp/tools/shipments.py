from __future__ import annotations

import mcp.types as types

from ...core.models.quote import QuoteRequest
from ...core.models.shipment import ShipmentRequest
from ...core.models.tracking import PickupRequest

TOOL_GET_BALANCE = types.Tool(
    name="get_balance",
    description="Get the current account balance in MXN. Use before creating shipments to verify sufficient funds.",
    inputSchema={"type": "object", "properties": {}},
)

TOOL_TRACK_GUIDE = types.Tool(
    name="track_guide",
    description="Track a shipment by guide number. Returns current status, estimated delivery date, and history.",
    inputSchema={
        "type": "object",
        "properties": {"guide": {"type": "string", "description": "Guide/tracking number"}},
        "required": ["guide"],
    },
)

TOOL_QUOTE = types.Tool(
    name="quote_shipment",
    description=(
        "Get available shipping rates for a package. Returns a list of carrier options with prices. "
        "Always call this BEFORE create_shipment — the quote_token from the selected rate is required to create the shipment."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "origin_postal_code": {"type": "string", "description": "5-digit Mexican origin ZIP code"},
            "destination_postal_code": {"type": "string", "description": "5-digit Mexican destination ZIP code"},
            "weight": {"type": "number", "description": "Weight in kg"},
            "width": {"type": "number", "description": "Width in cm"},
            "height": {"type": "number", "description": "Height in cm"},
            "length": {"type": "number", "description": "Length in cm"},
            "shipping_days": {"type": "integer", "description": "Estimated days until shipment"},
            "package_value": {"type": "number", "description": "Declared value in MXN"},
            "insurance": {"type": "boolean", "description": "Include insurance"},
            "packages": {"type": "integer", "description": "Number of packages"},
            "package_type": {"type": "integer", "description": "1=Sobre, 2=Paquete"},
        },
        "required": [
            "origin_postal_code", "destination_postal_code", "weight",
            "shipping_days", "package_value", "insurance", "packages", "package_type",
        ],
    },
)

TOOL_CREATE_SHIPMENT = types.Tool(
    name="create_shipment",
    description=(
        "⚠️ Esta operación tiene costo monetario. "
        "Create a shipment and generate a shipping guide. "
        "Requires a quote_token obtained from quote_shipment. "
        "Recommended flow: quote_shipment → select rate → create_shipment."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "quote_token": {"type": "string", "description": "Rate token from quote_shipment"},
            "content": {"type": "string", "description": "Package contents description (max 25 chars)"},
            "origin_first_name": {"type": "string"},
            "origin_last_name": {"type": "string"},
            "origin_email": {"type": "string"},
            "origin_street": {"type": "string"},
            "origin_number": {"type": "string"},
            "origin_neighborhood": {"type": "string"},
            "origin_phone": {"type": "string"},
            "origin_state": {"type": "string"},
            "origin_municipality": {"type": "string"},
            "origin_references": {"type": "string"},
            "origin_postal_code": {"type": "string"},
            "origin_commerce_name": {"type": "string"},
            "destination_first_name": {"type": "string"},
            "destination_last_name": {"type": "string"},
            "destination_email": {"type": "string"},
            "destination_street": {"type": "string"},
            "destination_number": {"type": "string"},
            "destination_neighborhood": {"type": "string"},
            "destination_phone": {"type": "string"},
            "destination_state": {"type": "string"},
            "destination_municipality": {"type": "string"},
            "destination_references": {"type": "string"},
            "destination_postal_code": {"type": "string"},
            "destination_commerce_name": {"type": "string"},
            "packages": {"type": "integer"},
            "generate_pickup": {"type": "boolean"},
            "has_notification": {"type": "boolean"},
            "guide_origin": {"type": "string"},
        },
        "required": [
            "quote_token", "content",
            "origin_first_name", "origin_last_name", "origin_email",
            "origin_street", "origin_number", "origin_neighborhood",
            "origin_phone", "origin_state", "origin_municipality",
            "origin_references", "origin_postal_code",
            "destination_first_name", "destination_last_name", "destination_email",
            "destination_street", "destination_number", "destination_neighborhood",
            "destination_phone", "destination_state", "destination_municipality",
            "destination_references", "destination_postal_code",
            "packages",
        ],
    },
)

TOOL_SCHEDULE_PICKUP = types.Tool(
    name="schedule_pickup",
    description=(
        "⚠️ Esta operación tiene costo monetario. "
        "Schedule a package pickup at the origin address. "
        "The origin address must be registered in T1Envios beforehand."
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
            "carrier", "contact_first_name", "contact_last_name", "email",
            "street", "number", "neighborhood", "phone", "state", "municipality",
            "postal_code", "references", "pieces", "weight", "length", "width",
            "height", "date", "open_time", "close_time",
        ],
    },
)

ALL_TOOLS = [TOOL_GET_BALANCE, TOOL_TRACK_GUIDE, TOOL_QUOTE, TOOL_CREATE_SHIPMENT, TOOL_SCHEDULE_PICKUP]


def handle(name: str, arguments: dict, client) -> dict:
    if name == "get_balance":
        return client.balance().model_dump()
    if name == "track_guide":
        return client.track_state(arguments["guide"]).model_dump()
    if name == "quote_shipment":
        req = QuoteRequest(**arguments)
        return client.quote(req).model_dump()
    if name == "create_shipment":
        req = ShipmentRequest(**arguments)
        return client.create_shipment(req).model_dump()
    if name == "schedule_pickup":
        req = PickupRequest(**arguments)
        return client.schedule_pickup(req).model_dump()
    raise ValueError(f"Unknown tool: {name}")
