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
def install(
    client_id: str | None = typer.Option(None, "--client-id", help="T1 API Client ID"),
    client_secret: str | None = typer.Option(None, "--client-secret", help="T1 API Client Secret"),
) -> None:
    """Register the T1Envios MCP server in Claude Desktop."""
    config_path = _claude_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    from ..core.auth.storage import HybridStorage

    stored = HybridStorage().load()
    cid = client_id or (stored.client_id if stored and stored.client_id else "YOUR_CLIENT_ID")
    csec = client_secret or (
        stored.client_secret if stored and stored.client_secret else "YOUR_CLIENT_SECRET"
    )

    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            config = {}

    config.setdefault("mcpServers", {})
    config["mcpServers"]["t1shipments"] = {
        "command": sys.executable,
        "args": [
            "-m",
            "t1shipments.mcp.server",
            "--client-id",
            cid,
            "--client-secret",
            csec,
        ],
    }

    config_path.write_text(json.dumps(config, indent=2))
    rprint("[green]MCP server registered.[/green]")
    rprint(f"Config: {config_path}")
    rprint("Restart Claude Desktop to apply changes.")


@app.command("run")
def run_server(
    client_id: str | None = typer.Option(None, "--client-id", help="T1 API Client ID"),
    client_secret: str | None = typer.Option(None, "--client-secret", help="T1 API Client Secret"),
) -> None:
    """Start the MCP server (stdio mode)."""
    try:
        from ..mcp.server import main
    except ImportError:
        rprint("[red]Error:[/red] MCP extra not installed. Run: pip install t1-shipments-mcp")
        raise typer.Exit(1)

    from ..core.auth.storage import HybridStorage

    stored = HybridStorage().load()
    cid = client_id or (stored.client_id if stored and stored.client_id else None)
    csec = client_secret or (stored.client_secret if stored and stored.client_secret else None)

    argv: list[str] = []
    if cid:
        argv.extend(["--client-id", cid])
    if csec:
        argv.extend(["--client-secret", csec])

    main(argv=argv if argv else None)
