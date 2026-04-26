from __future__ import annotations

import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ..client import T1Client
from ..models.quote import QuoteRequest
from ..models.shipment import ShipmentRequest
from ..models.tracking import PickupRequest

server = Server("t1envios")


def _client() -> T1Client:
    return T1Client.from_settings()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_carriers",
            description="List all supported carriers and their services.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_balance",
            description="Get the current account balance.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="track_guide",
            description="Track a shipment by guide number.",
            inputSchema={
                "type": "object",
                "properties": {"guide": {"type": "string", "description": "Guide number"}},
                "required": ["guide"],
            },
        ),
        types.Tool(
            name="quote_shipment",
            description="Get shipping rates for a package.",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin_postal_code": {"type": "string"},
                    "destination_postal_code": {"type": "string"},
                    "weight": {"type": "number"},
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "length": {"type": "number"},
                    "shipping_days": {"type": "integer"},
                    "package_value": {"type": "number"},
                    "insurance": {"type": "boolean"},
                    "packages": {"type": "integer"},
                    "package_type": {"type": "integer", "description": "1 for Sobre, 2 for Paquete"},
                },
                "required": [
                    "origin_postal_code",
                    "destination_postal_code",
                    "weight",
                    "shipping_days",
                    "package_value",
                    "insurance",
                    "packages",
                    "package_type"
                ],
            },
        ),
        types.Tool(
            name="create_shipment",
            description="Create a shipment from a quote token.",
            inputSchema={
                "type": "object",
                "properties": {
                    "quote_token": {"type": "string"},
                    "content": {"type": "string"},
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
        ),
        types.Tool(
            name="schedule_pickup",
            description="Schedule a package pickup.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pickup_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "address_id": {"type": "string"},
                    "packages": {"type": "integer"},
                    "notes": {"type": "string"},
                },
                "required": ["pickup_date"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    with _client() as client:
        if name == "list_carriers":
            result = [c.model_dump() for c in client.list_carriers()]
        elif name == "get_balance":
            result = client.balance().model_dump()
        elif name == "track_guide":
            result = client.track_state(arguments["guide"]).model_dump()
        elif name == "quote_shipment":
            req = QuoteRequest(**arguments)
            result = client.quote(req).model_dump()
        elif name == "create_shipment":
            req = ShipmentRequest(**arguments)
            result = client.create_shipment(req).model_dump()
        elif name == "schedule_pickup":
            req = PickupRequest(**arguments)
            result = client.schedule_pickup(req).model_dump()
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    return [types.TextContent(type="text", text=json.dumps(result, default=str, indent=2))]


def main() -> None:
    import asyncio

    async def _run() -> None:
        async with mcp.server.stdio.stdio_server() as (read, write):
            await server.run(
                read,
                write,
                InitializationOptions(
                    server_name="t1envios",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    asyncio.run(_run())


if __name__ == "__main__":
    main()
