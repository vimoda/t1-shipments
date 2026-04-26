from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from ..client import T1Client
from ..exceptions import T1Error


def run(
    guide_link: str = typer.Option(..., "--guide-link", help="Label URL from shipment response."),
    output: Path = typer.Option(Path("label.pdf"), "--output", "-o", help="Output file path."),
) -> None:
    """Download a shipment label to a local file."""

    try:
        with T1Client.from_settings() as client:
            data = client.download_label(guide_link)
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    output.write_bytes(data)
    rprint(f"[green]Label saved:[/green] {output.resolve()}")
