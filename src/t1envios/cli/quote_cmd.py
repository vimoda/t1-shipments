from __future__ import annotations

from typing import Optional

import typer
from rich import print as rprint
from rich.table import Table

from ..client import T1Client
from ..exceptions import T1Error
from ..models.quote import QuoteRequest


def run(
    from_zip: str = typer.Option(..., "--from-zip", help="Origin ZIP code"),
    to_zip: str = typer.Option(..., "--to-zip", help="Destination ZIP code"),
    weight: int = typer.Option(..., "--weight", help="Weight in kg"),
    width: float = typer.Option(10.0, "--width", help="Width in cm"),
    height: float = typer.Option(10.0, "--height", help="Height in cm"),
    length: float = typer.Option(10.0, "--length", help="Length in cm"),
    package_value: float = typer.Option(0.0, "--value", help="Declared value MXN"),
    packages: int = typer.Option(1, "--qty", help="Number of packages"),
    insurance: Optional[bool] = typer.Option(None, "--insurance", help="Add insurance to the quote"),
    shipping_days: int = typer.Option(2, "--shipping-days", help="Estimated shipping days"),
    commerce_id: Optional[str] = typer.Option(None, "--commerce-id", help="Unique identifier for the store"),
    package_type: int = typer.Option(1, "--package-type", help="Package type: 1 for Sobre, 2 for Paquete"),
    # programar recolección? (generar_recoleccion=True)
    pickup: bool = typer.Option(False, "--pickup", help="Schedule pickup for the shipment")
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
    #table.add_column("Recomendado", justify="center")

    for rate in response.detail or []:
        print("Type", type(rate.get('total_cost')))
        table.add_row(
            rate.get("token"),
            rate.get("service_id"),
            rate.get("service_name"),
            rate.get("service_type"),
            f"{rate.get('total_cost'):,.2f} {rate.get('currency')}",
            str(rate.get('delivery_days')) if rate.get('delivery_days') else "-",
            # "✅" if rate.get("recommended") else "",
        )

    rprint(table)
