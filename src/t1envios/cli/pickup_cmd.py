from __future__ import annotations

import typer
from rich import print as rprint

from ..client import T1Client
from ..exceptions import T1Error
from ..models.tracking import PickupRequest


def run(
    carrier: str = typer.Option(..., "--carrier", help="Carrier name: DHL, FEDEX, UPS"),
    contact_first_name: str = typer.Option(..., "--contact-name", help="Contact first name."),
    contact_last_name: str = typer.Option(..., "--contact-last-name", help="Contact last name(s)."),
    email: str = typer.Option(..., "--email", help="Contact email."),
    street: str = typer.Option(..., "--street", help="Pickup street."),
    number: str = typer.Option(..., "--number", help="Pickup exterior/interior number."),
    neighborhood: str = typer.Option(..., "--neighborhood", help="Pickup neighborhood (colonia)."),
    phone: str = typer.Option(..., "--phone", help="Contact phone number."),
    state: str = typer.Option(..., "--state", help="Pickup state."),
    municipality: str = typer.Option(..., "--municipality", help="Pickup municipality."),
    postal_code: str = typer.Option(..., "--zip-code", help="5-digit pickup ZIP code."),
    references: str = typer.Option(..., "--references", help="Address references."),
    pieces: int = typer.Option(..., "--pieces", help="Number of pieces to pick up."),
    weight: int = typer.Option(..., "--weight", help="Total weight in kg."),
    length: int = typer.Option(..., "--length", help="Package length in cm."),
    width: int = typer.Option(..., "--width", help="Package width in cm."),
    height: int = typer.Option(..., "--height", help="Package height in cm."),
    date: str = typer.Option(..., "--date", help="Pickup date (YYYY-MM-DD)."),
    open_time: str = typer.Option(..., "--open-time", help="Commerce open time (HH:MM)."),
    close_time: str = typer.Option(..., "--close-time", help="Commerce close time (HH:MM)."),
) -> None:
    """Schedule a package pickup."""

    req = PickupRequest(
        carrier=carrier,
        contact_first_name=contact_first_name,
        contact_last_name=contact_last_name,
        email=email,
        street=street,
        number=number,
        neighborhood=neighborhood,
        phone=phone,
        state=state,
        municipality=municipality,
        postal_code=postal_code,
        references=references,
        pieces=pieces,
        weight=weight,
        length=length,
        width=width,
        height=height,
        date=date,
        open_time=open_time,
        close_time=close_time,
    )

    try:
        with T1Client.from_settings() as client:
            pickup = client.schedule_pickup(req)
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    rprint("[green]Recolección programada.[/green]")
    rprint(f"[bold]ID:[/bold] {pickup.pickup_id}")
    rprint(f"[bold]Status:[/bold] {pickup.status}")
    rprint(f"[bold]Mensaje:[/bold] {pickup.message}")
    rprint(f"[bold]Localización:[/bold] {pickup.localization}")
