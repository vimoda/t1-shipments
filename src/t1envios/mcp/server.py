from __future__ import annotations

import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ..core.client import T1Client
from ..core.exceptions import SessionExpiredError
from . import prompts as prompts_module
from . import resources as resources_module
from .tools import carriers as carriers_tools
from .tools import shipments as shipment_tools

server = Server("t1envios")

# Singleton — shared across all tool calls to reuse httpx.Client and in-memory token.
_CLIENT: T1Client | None = None

# Register prompts and resources (decorators bind to server at import time)
prompts_module.register(server, lambda: _get_client())
resources_module.register(server, lambda: _get_client())


def _get_client() -> T1Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = T1Client.from_settings()

    # ensure_valid() refreshes transparently if token expires within 60s.
    try:
        _CLIENT._auth.ensure_valid()
    except SessionExpiredError:
        from ..core.config import Settings

        s = Settings()  # type: ignore[call-arg]
        if s.username and s.password:
            _CLIENT.login(s.username, s.password.get_secret_value())
        else:
            raise SessionExpiredError(
                "No active session. Set T1_USERNAME and T1_PASSWORD env vars or run: t1 auth login"
            )

    return _CLIENT


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [carriers_tools.TOOL_DEF] + shipment_tools.ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _get_client()
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
