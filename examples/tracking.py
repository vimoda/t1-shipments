"""Example: tracking shipments with state and detail.

Usage:
  # Option 1: Using an active session saved with 't1 auth login'
  uv run python examples/tracking.py --guide 4399894590

  # Option 2: Passing credentials explicitly
  uv run python examples/tracking.py --guide 4399894590 --client-id <ID> --client-secret <SECRET> \\
      --username <USER> --password <PASS>
"""

import argparse
import sys

from t1shipments.core.client import T1Client
from t1shipments.core.exceptions import ConfigError, SessionExpiredError


def run_tracking(
    guide: str,
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
            # --- Quick status (track_state) ---
            state = client.track_state(guide)
            print(f"Guía: {state.guide}")
            print(f"Estado: {state.current_status}")
            print(f"Entrega estimada: {state.estimated_delivery_date or '—'}")

            # --- Full detail (track_detail) ---
            detail = client.track_detail(guide)
            print(f"\nDetalle ({len(detail.detail)} eventos):")
            for ev in detail.detail:
                print(f"  {ev.date} {ev.time} — {ev.carrier_name}: {ev.description}")
        except SessionExpiredError:
            print(
                "Sesión no válida o expirada. Proporciona --username y --password "
                "o inicia sesión con 't1 auth login'.",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="T1Shipments tracking example")
    parser.add_argument(
        "--guide",
        default="4399894590",
        help="Tracking guide number (default: 4399894590)",
    )
    parser.add_argument("--client-id", help="Client ID for Keycloak auth")
    parser.add_argument("--client-secret", help="Client Secret for Keycloak auth")
    parser.add_argument("--username", help="Username / email for login")
    parser.add_argument("--password", help="Password for login")
    args = parser.parse_args()

    run_tracking(
        guide=args.guide,
        client_id=args.client_id,
        client_secret=args.client_secret,
        username=args.username,
        password=args.password,
    )


if __name__ == "__main__":
    main()
