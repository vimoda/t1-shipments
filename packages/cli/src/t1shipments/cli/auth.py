from __future__ import annotations

from datetime import datetime, timezone

import typer
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table

from ..core.auth.storage import HybridStorage
from ..core.client import T1Client
from ..core.config import Settings
from ..core.exceptions import AuthError, ConfigError, SessionExpiredError, T1Error

app = typer.Typer(help="Authentication commands")


@app.command("login")
def login(
    client_id: str = typer.Option(None, "--client-id", help="T1 API Client ID"),
    client_secret: str = typer.Option(None, "--client-secret", hide_input=True, help="T1 API Client Secret"),
    username: str = typer.Option(None, "--username", "-u", help="T1Envios username (or set T1_USERNAME)"),
    password: str = typer.Option(None, "--password", "-p", hide_input=True, help="T1Envios password (or set T1_PASSWORD)"),
    store_id: str = typer.Option(None, "--store-id", help="Store ID to embed in token (or set T1_COMMERCE_ID)"),
) -> None:
    """Authenticate and persist credentials and tokens."""
    try:
        s = Settings()

        resolved_client_id = client_id
        resolved_client_secret = client_secret
        resolved_user = username or (s.username if s.username else None)
        resolved_pass = password or (s.password.get_secret_value() if s.password else None)
        resolved_store = store_id or s.commerce_id

        if not resolved_client_id:
            resolved_client_id = typer.prompt("Client ID")
        if not resolved_client_secret:
            resolved_client_secret = typer.prompt("Client Secret", hide_input=True)
        if not resolved_user:
            resolved_user = typer.prompt("Username")
        if not resolved_pass:
            resolved_pass = typer.prompt("Password", hide_input=True)

        client = T1Client.from_settings(client_id=resolved_client_id, client_secret=resolved_client_secret)
        token = client.login(resolved_user, resolved_pass, store_id=resolved_store)

        remaining = (token.expires_at - datetime.now(tz=timezone.utc)).total_seconds()
        has_refresh = "✓" if token.refresh_token else "✗"
        rprint(Panel(
            f"[green]Login successful.[/green]\n"
            f"Token válido por [bold]{int(remaining // 60)}m[/bold]. "
            f"Refresh token: {has_refresh}",
            title="t1 auth",
        ))
    except (AuthError, ConfigError, T1Error) as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)


@app.command("refresh")
def refresh() -> None:
    """Refresh the access token using the stored refresh token."""
    storage = HybridStorage()
    token = storage.load()
    if token is None:
        rprint("[yellow]No session found.[/yellow] Run [bold]t1 auth login[/bold].")
        raise typer.Exit(1)
    if not token.refresh_token:
        rprint("[red]No refresh token stored.[/red] Run [bold]t1 auth login[/bold].")
        raise typer.Exit(1)
    try:
        client = T1Client.from_settings()
        new_token = client._auth.refresh()
        remaining = (new_token.expires_at - datetime.now(tz=timezone.utc)).total_seconds()
        rprint(
            f"[green]Token renovado.[/green] "
            f"Válido por [bold]{int(remaining // 60)}m[/bold]."
        )
    except (SessionExpiredError, AuthError, T1Error) as exc:
        rprint(f"[red]Error al renovar:[/red] {exc}")
        rprint("Ejecuta [bold]t1 auth login[/bold] para iniciar sesión de nuevo.")
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

    now = datetime.now(tz=timezone.utc)
    remaining_secs = (token.expires_at - now).total_seconds()
    has_refresh = token.refresh_token is not None

    table = Table(title="Token status", show_header=False, box=None)
    table.add_column("key", style="bold")
    table.add_column("value")

    if token.is_expired():
        table.add_row("Estado", "[red]Expirado[/red]")
    elif remaining_secs < 300:
        table.add_row("Estado", f"[yellow]Expira en {int(remaining_secs)}s[/yellow]")
    else:
        table.add_row("Estado", f"[green]Válido[/green]")

    table.add_row("Expira", token.expires_at.strftime("%Y-%m-%d %H:%M:%S UTC"))
    if not token.is_expired():
        mins = int(remaining_secs // 60)
        secs = int(remaining_secs % 60)
        table.add_row("Tiempo restante", f"{mins}m {secs}s")
    table.add_row("Refresh token", "[green]disponible[/green]" if has_refresh else "[red]no disponible[/red]")
    table.add_row("Auto-refresh", "[green]sí[/green]" if has_refresh else "[yellow]no — re-login requerido al expirar[/yellow]")

    rprint(table)

    if token.is_expired() and has_refresh:
        rprint("\n[dim]Tip: ejecuta [bold]t1 auth refresh[/bold] para renovar sin volver a iniciar sesión.[/dim]")
