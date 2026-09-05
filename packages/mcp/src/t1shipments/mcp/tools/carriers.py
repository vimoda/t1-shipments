from __future__ import annotations

import mcp.types as types

_SCHEMA: dict = {"type": "object", "properties": {}}

TOOL_DEF = types.Tool(
    name="list_carriers",
    description=(
        "List all shipping carriers and services available in your T1Envios account. "
        "Call this to discover which carriers (DHL, FedEx, etc.) are enabled before quoting or scheduling pickups. "
        "Respond with a simple list: carrier name and available services. No extra explanation."
    ),
    inputSchema=_SCHEMA,
)


def handle(arguments: dict, client) -> dict:
    carriers = client.list_carriers()
    return {"carriers": [c.model_dump() for c in carriers]}
