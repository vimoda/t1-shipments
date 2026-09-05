"""Example: tracking shipments with state and detail.
"""

import os

from t1shipments.core.client import T1Client

client = T1Client.from_settings(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)

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
