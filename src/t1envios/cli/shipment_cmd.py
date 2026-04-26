from __future__ import annotations

from typing import Optional

import typer
from rich import print as rprint

from ..client import T1Client
from ..exceptions import T1Error
from ..models.shipment import ShipmentRequest


def run(
    quote_token: str = typer.Option(..., "--quote-id", help="Quote token from `t1 quote`"),
    content: str = typer.Option(..., "--content", help="Brief description of package contents (max 25 chars)."),

    origin_first_name: str = typer.Option(..., "--origin-name", help="Sender's first name."),
    origin_last_name: str = typer.Option(..., "--origin-last-name", help="Sender's last name(s)."),
    origin_email: str = typer.Option(..., "--origin-email", help="Sender's email address."),
    origin_street: str = typer.Option(..., "--origin-street", help="Sender's street name."),
    origin_number: str = typer.Option(..., "--origin-number", help="Sender's exterior/interior number."),
    origin_neighborhood: str = typer.Option(..., "--origin-neighborhood", help="Sender's neighborhood (colonia)."),
    origin_phone: str = typer.Option(..., "--origin-phone", help="Sender's phone number (8-10 digits)."),
    origin_state: str = typer.Option(..., "--origin-state", help="Sender's state."),
    origin_municipality: str = typer.Option(..., "--origin-municipality", help="Sender's municipality."),
    origin_references: str = typer.Option(..., "--origin-references", help="Sender's address references."),
    origin_zip_code: str = typer.Option(..., "--origin-zip-code", help="5-digit origin ZIP code."),
    origin_commerce_name: Optional[str] = typer.Option("", "--origin-commerce", help="Sender's commerce name."),

    destination_first_name: str = typer.Option(..., "--destination-name", help="Recipient's first name."),
    destination_last_name: str = typer.Option(..., "--destination-last-name", help="Recipient's last name(s)."),
    destination_email: str = typer.Option(..., "--destination-email", help="Recipient's email address."),
    destination_street: str = typer.Option(..., "--destination-street", help="Recipient's street name."),
    destination_number: str = typer.Option(..., "--destination-number", help="Recipient's exterior/interior number."),
    destination_neighborhood: str = typer.Option(..., "--destination-neighborhood", help="Recipient's neighborhood (colonia)."),
    destination_phone: str = typer.Option(..., "--destination-phone", help="Recipient's phone number (8-10 digits)."),
    destination_state: str = typer.Option(..., "--destination-state", help="Recipient's state."),
    destination_municipality: str = typer.Option(..., "--destination-municipality", help="Recipient's municipality."),
    destination_references: str = typer.Option(..., "--destination-references", help="Recipient's address references."),
    destination_zip_code: str = typer.Option(..., "--destination-zip-code", help="5-digit destination ZIP code."),
    destination_commerce_name: Optional[str] = typer.Option("", "--destination-commerce", help="Recipient's commerce name."),

    packages: int = typer.Option(1, "--packages", help="Number of packages."),
    generate_pickup: bool = typer.Option(False, "--generate-pickup", help="Generate pickup when creating shipment."),
    has_notification: bool = typer.Option(False, "--has-notification", help="Send notifications for this shipment."),
    guide_origin: str = typer.Option("t1envios", "--guide-origin", help='Guide origin. Allowed: "t1envios".'),
) -> None:
    """Create a shipment from a quote."""

    req = ShipmentRequest(
        quote_token=quote_token,
        content=content,
        origin_first_name=origin_first_name,
        origin_last_name=origin_last_name,
        origin_email=origin_email,
        origin_street=origin_street,
        origin_number=origin_number,
        origin_neighborhood=origin_neighborhood,
        origin_phone=origin_phone,
        origin_state=origin_state,
        origin_municipality=origin_municipality,
        origin_references=origin_references,
        origin_postal_code=origin_zip_code,
        origin_commerce_name=origin_commerce_name,
        destination_first_name=destination_first_name,
        destination_last_name=destination_last_name,
        destination_email=destination_email,
        destination_street=destination_street,
        destination_number=destination_number,
        destination_neighborhood=destination_neighborhood,
        destination_phone=destination_phone,
        destination_state=destination_state,
        destination_municipality=destination_municipality,
        destination_references=destination_references,
        destination_postal_code=destination_zip_code,
        destination_commerce_name=destination_commerce_name,
        packages=packages,
        generate_pickup=generate_pickup,
        has_notification=has_notification,
        guide_origin=guide_origin
    )

    try:
        with T1Client.from_settings() as client:
            shipment = client.create_shipment(req)
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    rprint("[green]Guía creada.[/green]")
    rprint(f"[bold]Orden:[/bold] {shipment.order_number}")
    rprint(f"[bold]Guía:[/bold] {shipment.tracking_number}")
    rprint(f"[bold]Paquetería:[/bold] {shipment.carrier}")
    rprint(f"[bold]Costo:[/bold] {shipment.cost}")
    rprint(f"[bold]Destino:[/bold] {shipment.destination}")
    if shipment.guide_link:
        rprint(f"[bold]Etiqueta:[/bold] {shipment.guide_link}")
