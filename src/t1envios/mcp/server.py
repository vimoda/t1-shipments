from __future__ import annotations

import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from ..core.auth.storage import InMemoryStorage
from ..core.client import T1Client
from . import prompts as prompts_module
from . import resources as resources_module
from .tools import auth as auth_tools
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
        from ..core.config import Settings

        s = Settings()  # type: ignore[call-arg]
        # MCP server is always headless — InMemoryStorage avoids keychain popups.
        _CLIENT = T1Client.from_settings(token_storage=InMemoryStorage(), auto_refresh=False)

        # Auto-login if credentials are present in env — no need to call auth_login tool.
        if s.username and s.password:
            _CLIENT.login(s.username, s.password.get_secret_value(), store_id=s.commerce_id)
            _CLIENT._auth.auto_refresh = True

    return _CLIENT


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return auth_tools.ALL_TOOLS + [carriers_tools.TOOL_DEF] + shipment_tools.ALL_TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    client = _get_client()
    if name in {t.name for t in auth_tools.ALL_TOOLS}:
        result = auth_tools.handle(name, arguments, client)
    elif name == carriers_tools.TOOL_DEF.name:
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
