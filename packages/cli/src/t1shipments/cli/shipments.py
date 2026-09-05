from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from ..core.client import T1Client
from ..core.exceptions import T1Error
from ..core.models.quote import QuoteRequest
from ..core.models.shipment import ShipmentRequest
from ..core.models.tracking import PickupRequest


def run_balance() -> None:
    """Show account balance."""
    try:
        with T1Client.from_settings() as client:
            bal = client.balance()
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    rprint(f"[bold]Saldo:[/bold] {bal.amount:,.2f} {bal.currency}")


def run_quote(
    from_zip: str = typer.Option(..., "--from-zip", help="Origin ZIP code"),
    to_zip: str = typer.Option(..., "--to-zip", help="Destination ZIP code"),
    weight: int = typer.Option(..., "--weight", help="Weight in kg"),
    width: float = typer.Option(10.0, "--width", help="Width in cm"),
    height: float = typer.Option(10.0, "--height", help="Height in cm"),
    length: float = typer.Option(10.0, "--length", help="Length in cm"),
    package_value: float = typer.Option(0.0, "--package-value", "--value", help="Declared value MXN"),
    packages: int = typer.Option(1, "--packages", "--qty", help="Number of packages"),
    insurance: Optional[bool] = typer.Option(None, "--insurance", help="Add insurance to the quote"),
    shipping_days: int = typer.Option(2, "--shipping-days", help="Estimated shipping days"),
    commerce_id: Optional[str] = typer.Option(None, "--commerce-id", help="Unique identifier for the store"),
    package_type: int = typer.Option(1, "--package-type", help="Package type: 1 for Sobre, 2 for Paquete"),
    pickup: bool = typer.Option(False, "--pickup", help="Schedule pickup for the shipment"),
) -> None:
    """Get shipping rates for a package."""
    req = QuoteRequest(
        origin_postal_code=from_zip,
        destination_postal_code=to_zip,
        weight=weight,
        width=width,
        height=height,
        length=length,
        shipping_days=shipping_days,
        insurance=insurance if insurance is not None else False,
        package_value=package_value,
        packages=packages,
        package_type=package_type,
    )

    try:
        with T1Client.from_settings() as client:
            response = client.quote(req)
    except T1Error as exc:
        rprint(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    rprint(f"[bold]Quote ID:[/bold] {response}")
    table = Table(title="Tarifas disponibles")
    table.add_column("Rate ID")
    table.add_column("Paquetería")
    table.add_column("Servicio")
    table.add_column("Tipo servicio")
    table.add_column("Precio")
    table.add_column("Días")

    for rate in response.detail or []:
        table.add_row(
            rate.get("token"),
            rate.get("service_id"),
            rate.get("service_name"),
            rate.get("service_type"),
            f"{rate.get('total_cost'):,.2f} {rate.get('currency')}",
            str(rate.get("delivery_days")) if rate.get("delivery_days") else "-",
        )

    rprint(table)


def run_create_shipment(
    quote_token: str = typer.Option(..., "--quote-id", help="Quote token from `t1 quote`"),
    content: str = typer.Option(..., "--content", help="Brief description of package contents (max 25 chars)."),
    origin_first_name: str = typer.Option(..., "--origin-name", help="Sender's first name."),
    origin_last_name: str = typer.Option(..., "--origin-last-name", help="Sender's last name(s)."),
    origin_email: str = typer.Option(..., "--origin-email", help="Sender's email address."),
    origin_street: str = typer.Option(..., "--origin-street", help="Sender's street name."),
    origin_number: str = typer.Option(..., "--origin-number", help="Sender's exterior number."),
    origin_neighborhood: str = typer.Option(..., "--origin-neighborhood", help="Sender's neighborhood (colonia)."),
    origin_phone: str = typer.Option(..., "--origin-phone", help="Sender's phone number (8-10 digits)."),
    origin_state: str = typer.Option(..., "--origin-state", help="Sender's state."),
    origin_municipality: str = typer.Option(..., "--origin-municipality", help="Sender's municipality."),
    origin_references: str = typer.Option(..., "--origin-references", help="Sender's address references (interior, depto, torre, etc. Max 35 chars)."),
    origin_zip_code: str = typer.Option(..., "--origin-zip-code", help="5-digit origin ZIP code."),
    origin_commerce_name: Optional[str] = typer.Option("", "--origin-commerce", help="Sender's commerce name."),
    destination_first_name: str = typer.Option(..., "--destination-name", help="Recipient's first name."),
    destination_last_name: str = typer.Option(..., "--destination-last-name", help="Recipient's last name(s)."),
    destination_email: str = typer.Option(..., "--destination-email", help="Recipient's email address."),
    destination_street: str = typer.Option(..., "--destination-street", help="Recipient's street name."),
    destination_number: str = typer.Option(..., "--destination-number", help="Recipient's exterior number."),
    destination_neighborhood: str = typer.Option(..., "--destination-neighborhood", help="Recipient's neighborhood."),
    destination_phone: str = typer.Option(..., "--destination-phone", help="Recipient's phone number (8-10 digits)."),
    destination_state: str = typer.Option(..., "--destination-state", help="Recipient's state."),
    destination_municipality: str = typer.Option(..., "--destination-municipality", help="Recipient's municipality."),
    destination_references: str = typer.Option(..., "--destination-references", help="Recipient's address references (interior, depto, torre, etc. Max 35 chars)."),
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
        guide_origin=guide_origin,
    )

    try:
        with T1Client.from_settings() as client:
            shipment = client.create_shipment(req)
    except T1Error as exc:
        from ..core.exceptions import ApiError
        if isinstance(exc, ApiError) and exc.payload:
            rprint(f"[red]Error:[/red] {exc}\n[dim]Raw:[/dim] {exc.payload}")
        else:
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


def run_track_detail(
    guide: str = typer.Option(..., "--guide", help="Guide number to track"),
) -> None:
    """Track a shipment by guide number (full detail)."""
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
            table.add_row(ev.date + " " + ev.time, ev.code, ev.description, "-")
        rprint(table)


def run_track_state(
    guide: str = typer.Option(..., "--guide", help="Guide number to track"),
) -> None:
    """Track a shipment by guide number (state + history)."""
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


def run_pickup(
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


def run_label(
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
