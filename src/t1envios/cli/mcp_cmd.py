from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import typer
from rich import print as rprint

app = typer.Typer(help="MCP server management")


def _claude_config_path() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


@app.command("install")
def install() -> None:
    """Register the T1Envios MCP server in Claude Desktop."""
    config_path = _claude_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config: dict = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            config = {}

    config.setdefault("mcpServers", {})
    config["mcpServers"]["t1envios"] = {
        "command": sys.executable,
        "args": ["-m", "t1envios.mcp_server.server"],
        "env": {
            "T1_CLIENT_ID": "${T1_CLIENT_ID}",
            "T1_CLIENT_SECRET": "${T1_CLIENT_SECRET}",
        },
    }

    config_path.write_text(json.dumps(config, indent=2))
    rprint(f"[green]MCP server registered.[/green]")
    rprint(f"Config: {config_path}")
    rprint("Restart Claude Desktop to apply changes.")


@app.command("run")
def run_server() -> None:
    """Start the MCP server (stdio mode)."""
    from ..mcp_server.server import main
    main()
