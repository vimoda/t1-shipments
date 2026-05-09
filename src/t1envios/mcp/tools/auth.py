from __future__ import annotations

from datetime import datetime, timezone

import mcp.types as types

TOOL_AUTH_LOGIN = types.Tool(
    name="auth_login",
    description=(
        "Log in to T1Envios and get an access + refresh token. "
        "Store both tokens on the client side and call auth_set_session before using other tools. "
        "Iniciar sesión en T1Envios y obtener access + refresh token. "
        "After success respond only: 'Sesión iniciada correctamente.' Do not show tokens to the user."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "username": {"type": "string", "description": "T1Envios username / Usuario"},
            "password": {"type": "string", "description": "T1Envios password / Contraseña"},
        },
        "required": ["username", "password"],
    },
)

TOOL_AUTH_REFRESH = types.Tool(
    name="auth_refresh",
    description=(
        "Exchange a refresh token for a new access + refresh token pair. "
        "Call when the access token has expired. Store the new tokens and call auth_set_session. "
        "Renovar tokens cuando el access token expira. "
        "After success continue silently with the original user request. Do not mention token renewal to the user."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "refresh_token": {
                "type": "string",
                "description": "Refresh token from auth_login or previous auth_refresh",
            },
        },
        "required": ["refresh_token"],
    },
)

TOOL_AUTH_SET_SESSION = types.Tool(
    name="auth_set_session",
    description=(
        "Inject previously obtained tokens into the server session. "
        "Call at the start of each conversation with stored tokens before using other tools. "
        "If refresh_token is provided, the server will auto-refresh on 401. "
        "Inyectar tokens almacenados antes de usar otras herramientas. "
        "This is an internal operation — do not mention it to the user. Proceed silently."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "access_token": {"type": "string", "description": "Bearer access token"},
            "refresh_token": {
                "type": "string",
                "description": "Refresh token (optional — enables auto-refresh on 401)",
            },
            "expires_at": {
                "type": "string",
                "description": "ISO 8601 expiry datetime e.g. 2026-05-08T15:00:00Z (optional)",
            },
        },
        "required": ["access_token"],
    },
)

ALL_TOOLS = [TOOL_AUTH_LOGIN, TOOL_AUTH_REFRESH, TOOL_AUTH_SET_SESSION]


def handle(name: str, arguments: dict, client) -> dict:
    if name == "auth_login":
        token = client.login(arguments["username"], arguments["password"])
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at.isoformat(),
        }

    if name == "auth_refresh":
        from ...core.auth.token import Token

        # Temporarily load the refresh_token so authenticator.refresh() can use it
        client._auth._token = Token(
            access_token="",
            refresh_token=arguments["refresh_token"],
            expires_at=datetime.fromtimestamp(0, tz=timezone.utc),
        )
        token = client._auth.refresh()
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at.isoformat(),
        }

    if name == "auth_set_session":
        expires_at = None
        if raw := arguments.get("expires_at"):
            dt = datetime.fromisoformat(raw)
            expires_at = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

        client.inject_token(
            access_token=arguments["access_token"],
            refresh_token=arguments.get("refresh_token"),
            expires_at=expires_at,
        )
        return {"ok": True, "auto_refresh": client._auth.auto_refresh}

    raise ValueError(f"Unknown auth tool: {name}")
