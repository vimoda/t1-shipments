from __future__ import annotations

import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ..core.client import T1Client
from .tools import carriers as carriers_tools
from .tools import shipments as shipment_tools

server = Server("t1envios")


def _client() -> T1Client:
    return T1Client.from_settings()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [carriers_tools.TOOL_DEF] + shipment_tools.ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    with _client() as client:
        if name == carriers_tools.TOOL_DEF.name:
            result = carriers_tools.handle(arguments, client)
        else:
            result = shipment_tools.handle(name, arguments, client)

    return [types.TextContent(type="text", text=json.dumps(result, default=str))]


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
