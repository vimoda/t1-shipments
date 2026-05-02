from __future__ import annotations

import typer
from rich import print as rprint
from rich.panel import Panel

from ..core.auth.storage import HybridStorage
from ..core.client import T1Client
from ..core.exceptions import AuthError, ConfigError, SessionExpiredError, T1Error

app = typer.Typer(help="Authentication commands")


@app.command("login")
def login() -> None:
    """Authenticate and persist tokens."""
    try:
        client = T1Client.from_settings()
        username = typer.prompt("Username")
        password = typer.prompt("Password", hide_input=True)
        client.login(username, password)
        rprint(Panel("[green]Login successful.[/green] Tokens stored.", title="t1 auth"))
    except (AuthError, ConfigError, T1Error) as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)


@app.command("logout")
def logout() -> None:
    """Clear stored tokens."""
    HybridStorage().clear()
    rprint("[yellow]Logged out.[/yellow] Tokens removed.")


@app.command("status")
def status() -> None:
    """Show current token status."""
    token = HybridStorage().load()
    if token is None:
        rprint("[yellow]Not authenticated.[/yellow] Run [bold]t1 auth login[/bold].")
        raise typer.Exit(1)
    if token.is_expired():
        rprint(f"[yellow]Token expired[/yellow] at {token.expires_at.isoformat()}")
    else:
        rprint(f"[green]Authenticated.[/green] Token valid until {token.expires_at.isoformat()}")
