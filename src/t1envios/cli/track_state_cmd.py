from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from ..client import T1Client
from ..exceptions import T1Error


def run(
        guide: str = typer.Option(..., "--guide", help="Guide number to track")
    ) -> None:
    """Track a shipment by guide number."""

    try:
        with T1Client.from_settings() as client:
            result = client.track_state(guide)
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    

    rprint(f"[bold]Guía:[/bold] {result.guide}")
    rprint(f"[bold]Estatus:[/bold] {result.current_status}")
    rprint(f"[bold]Entrega estimada:[/bold] {result.estimated_delivery_date}")

    if result.history:
        table = Table(title="Historial")
        table.add_column("Fecha")
        table.add_column("Estatus")
        table.add_column("Descripción")
        table.add_column("Ubicación")
        for ev in result.history:
            table.add_row(ev.date, ev.status, ev.description, ev.location)
        rprint(table)
