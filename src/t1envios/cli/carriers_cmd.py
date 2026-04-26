from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from ..client import T1Client
from ..exceptions import T1Error


def run() -> None:
    """List supported carriers."""

    try:
        with T1Client.from_settings() as client:
            carriers = client.list_carriers()
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    table = Table(title="Paqueterías disponibles")
    table.add_column("ID")
    table.add_column("Nombre")
    table.add_column("Servicios")
    table.add_column("Activo")

    for c in carriers:
        table.add_row(
            c.carrier_id,
            c.name,
            ", ".join(c.services) or "-",
            "[green]Sí[/green]" if c.active else "[red]No[/red]",
        )

    rprint(table)
