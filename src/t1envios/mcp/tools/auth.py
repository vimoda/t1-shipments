from __future__ import annotations

"""Placeholder for future auth-related MCP tools (token introspection, session status, etc.)."""

ALL_TOOLS: list = []


def handle(name: str, arguments: dict, client) -> dict:
    raise ValueError(f"Unknown auth tool: {name}")
