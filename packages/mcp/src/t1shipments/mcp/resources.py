from __future__ import annotations

import json
from collections.abc import Callable

import mcp.types as types
from mcp.server import Server

_STATIC_RESOURCES: list[types.Resource] = [
    types.Resource(
        uri="t1shipments://balance",  # type: ignore[arg-type]
        name="Account Balance / Saldo de cuenta",
        description="Current T1Envios account balance in MXN",
        mimeType="application/json",
    ),
    types.Resource(
        uri="t1shipments://carriers",  # type: ignore[arg-type]
        name="Available Carriers / Paqueterías disponibles",
        description="All shipping carriers and services enabled in your account",
        mimeType="application/json",
    ),
]

_SHIPMENT_TEMPLATE = types.ResourceTemplate(
    uriTemplate="t1shipments://shipment/{guide}",
    name="Shipment Detail / Detalle de envío",
    description="Full tracking history for a shipment guide number",
    mimeType="application/json",
)


def _read(uri: str, get_client: Callable) -> list[types.TextResourceContents]:
    client = get_client()
    uri_str = str(uri)

    if uri_str == "t1shipments://balance":
        data = client.balance().model_dump()
        return [types.TextResourceContents(uri=uri, mimeType="application/json", text=json.dumps(data, default=str))]  # type: ignore[arg-type]

    if uri_str == "t1shipments://carriers":
        carriers = client.list_carriers()
        data = {"carriers": [c.model_dump() for c in carriers]}
        return [types.TextResourceContents(uri=uri, mimeType="application/json", text=json.dumps(data, default=str))]  # type: ignore[arg-type]

    if uri_str.startswith("t1shipments://shipment/"):
        guide = uri_str.removeprefix("t1shipments://shipment/")
        data = client.track_detail(guide).model_dump()
        return [types.TextResourceContents(uri=uri, mimeType="application/json", text=json.dumps(data, default=str))]  # type: ignore[arg-type]

    raise ValueError(f"Unknown resource URI: {uri}")


def register(server: Server, get_client: Callable) -> None:
    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return _STATIC_RESOURCES

    @server.list_resource_templates()
    async def list_resource_templates() -> list[types.ResourceTemplate]:
        return [_SHIPMENT_TEMPLATE]

    @server.read_resource()
    async def read_resource(uri: types.AnyUrl) -> list[types.TextResourceContents]:
        return _read(uri, get_client)
