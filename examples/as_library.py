"""Example: using t1shipments as an importable SDK.

Demonstrates initializing T1Client directly with explicit client_id and client_secret
parameters, or reusing stored session credentials from 't1 auth login'.

Usage:
  # Option 1: Passing credentials explicitly
  uv run python examples/as_library.py --client-id <ID> --client-secret <SECRET> \\
      --username <USER> --password <PASS>

  # Option 2: Using an active session saved with 't1 auth login'
  uv run python examples/as_library.py
"""

import argparse
import sys

from t1shipments.core.client import T1Client
from t1shipments.core.config import Endpoints
from t1shipments.core.exceptions import ConfigError, SessionExpiredError
from t1shipments.core.models.quote import QuoteRequest


def run_sdk_example(
    client_id: str | None = None,
    client_secret: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> None:
    # Direct initialization passing credentials as parameters
    if client_id and client_secret:
        client = T1Client(
            client_id=client_id,
            client_secret=client_secret,
            # Defaults to dev env; override with Endpoints(base_url=..., auth_base_url=...)
            endpoints=Endpoints(),
        )
    else:
        # Fallback to credentials stored via 't1 auth login'
        try:
            client = T1Client.from_settings()
        except ConfigError as e:
            print(f"Error de configuración: {e}", file=sys.stderr)
            print(
                "Tip: Pasa --client-id y --client-secret, o ejecuta 't1 auth login' primero.",
                file=sys.stderr,
            )
            sys.exit(1)

    with client:
        # Login if user and password are provided
        if username and password:
            client.login(username=username, password=password)

        try:
            # List carriers
            carriers = client.list_carriers()
            print("Paqueterías:", [c.name for c in carriers])

            # Quote — weight=2 is the billable weight (max of physical and volumetric).
            req = QuoteRequest(
                origin_postal_code="06600",
                destination_postal_code="44100",
                weight=2,
                width=20,
                height=15,
                length=10,
                shipping_days=2,
                insurance=False,
                package_type=1,  # 1: Sobre, 2: Paquete
                packages=1,
            )
            quote = client.quote(req)
            print(f"Cotización exitosa: {quote.message or ''}")
            for rate in quote.detail or []:
                cost = rate.get("total_cost", 0)
                days = rate.get("delivery_days") or "-"
                token = rate.get("token")
                svc = rate.get("service_id")
                print(f"  {token} {svc}: ${cost:,.2f} MXN ({days} días)")
        except SessionExpiredError:
            print(
                "Sesión no válida o expirada. Proporciona --username y --password "
                "o inicia sesión con 't1 auth login'.",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="T1Shipments SDK library example")
    parser.add_argument("--client-id", help="Client ID for Keycloak auth")
    parser.add_argument("--client-secret", help="Client Secret for Keycloak auth")
    parser.add_argument("--username", help="Username / email for login")
    parser.add_argument("--password", help="Password for login")
    args = parser.parse_args()

    run_sdk_example(
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password,
    )


if __name__ == "__main__":
    main()
