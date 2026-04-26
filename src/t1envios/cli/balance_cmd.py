from __future__ import annotations

import typer
from rich import print as rprint

from ..client import T1Client
from ..exceptions import T1Error


def run() -> None:
    """Show account balance."""

    try:
        with T1Client.from_settings() as client:
            bal = client.balance()
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    rprint(f"[bold]Saldo:[/bold] {bal.amount:,.2f} {bal.currency}")
