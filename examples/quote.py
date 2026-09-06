"""Example: quoting a shipment step by step.

Usage:
  # Option 1: Using an active session saved with 't1 auth login'
  uv run python examples/quote.py

  # Option 2: Passing credentials explicitly
  uv run python examples/quote.py --client-id <ID> --client-secret <SECRET> \\
      --username <USER> --password <PASS>
"""

import argparse
import sys

from t1shipments.core.client import T1Client
from t1shipments.core.exceptions import ConfigError, SessionExpiredError
from t1shipments.core.models.quote import QuoteRequest


def run_quote(
    client_id: str | None = None,
    client_secret: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> None:
    try:
        # Pass client_id and client_secret as parameters, or load from stored session
        client = T1Client.from_settings(
            client_id=client_id,
            client_secret=client_secret,
        )
    except ConfigError as e:
        print(f"Error de configuración: {e}", file=sys.stderr)
        print(
            "Tip: Pasa --client-id y --client-secret, o ejecuta 't1 auth login' primero.",
            file=sys.stderr,
        )
        sys.exit(1)

    with client:
        # If user/pass provided, log in explicitly
        if username and password:
            client.login(username=username, password=password)

        try:
            # List available carriers
            carriers = client.list_carriers()
            print("Paqueterías disponibles:")
            for c in carriers:
                print(f"  {c.name} ({c.carrier_id}) — {'activo' if c.active else 'inactivo'}")

            # Build a quote request
            # Billable weight is the maximum of physical weight and volumetric weight:
            # volumetric = ceil(width * height * length / 5000)
            req = QuoteRequest(
                origin_postal_code="06600",
                destination_postal_code="44100",
                weight=2,  # billable kg
                width=20.0,
                height=15.0,
                length=10.0,
                shipping_days=3,
                insurance=False,
                package_value=500.0,
                package_type=2,  # 1: Sobre, 2: Paquete
                packages=1,
            )

            # Fetch rates
            quote = client.quote(req)
            if not quote.success:
                print(f"Error al cotizar: {quote.message}")
                sys.exit(1)

            print(f"\nCotización #{len(quote.detail or [])} tarifas:")
            hdr = (
                f"{'#':<3} {'Paquetería':<12} {'Servicio':<30} "
                f"{'Tipo':<25} {'Costo':<10} {'Entrega':<10}"
            )
            print(hdr)
            print("-" * 90)
            for i, rate in enumerate(quote.detail or [], start=1):
                cost = rate.get("total_cost", 0)
                days = rate.get("delivery_days") or "-"
                recommended = " ★" if rate.get("recommended") else ""
                print(
                    f"{i:<3} {rate.get('carrier', ''):<12}"
                    f"{rate.get('service_name', ''):<30}"
                    f"{rate.get('service_type', ''):<25}"
                    f"${cost:<8,.2f}"
                    f"{days!s:<10}{recommended}"
                )
        except SessionExpiredError:
            print(
                "Sesión no válida o expirada. Proporciona --username y --password "
                "o inicia sesión con 't1 auth login'.",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="T1Shipments quote example")
    parser.add_argument("--client-id", help="Client ID for Keycloak auth")
    parser.add_argument("--client-secret", help="Client Secret for Keycloak auth")
    parser.add_argument("--username", help="Username / email for login")
    parser.add_argument("--password", help="Password for login")
    args = parser.parse_args()

    run_quote(
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password,
    )


if __name__ == "__main__":
    main()
