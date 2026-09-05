"""Example: tracking shipments with state and detail.

Expects T1_CLIENT_ID, T1_CLIENT_SECRET, T1_USERNAME, T1_PASSWORD
in the environment or .env file.
"""

import os

from t1shipments.core.client import T1Client

client = T1Client.from_settings()

with client:
    client.login(
        username=os.getenv("T1_USERNAME", "YOUR_USERNAME"),
        password=os.getenv("T1_PASSWORD", "YOUR_PASSWORD"),
    )

    # --- Quick status (track_state) ---
    state = client.track_state("4399894590")
    print(f"Guía: {state.guide}")
    print(f"Estado: {state.current_status}")
    print(f"Entrega estimada: {state.estimated_delivery_date or '—'}")

    # --- Full detail (track_detail) ---
    detail = client.track_detail("4399894590")
    print(f"\nDetalle ({len(detail.detail)} eventos):")
    for ev in detail.detail:
        print(f"  {ev.date} {ev.time} — {ev.carrier_name}: {ev.description}")
