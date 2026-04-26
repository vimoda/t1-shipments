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
            result = client.track_detail(guide)
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    

    if result.detail:
        table = Table(title="Eventos")
        table.add_column("Fecha")
        table.add_column("Code")
        table.add_column("Descripción")
        table.add_column("Ubicación")
        for ev in result.detail:
            table.add_row(
                ev.date+" "+ev.time,
                ev.code,
                ev.description,
               "-",
            )
        rprint(table)
