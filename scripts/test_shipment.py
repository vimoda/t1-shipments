"""Smoke test: quote → create shipment using the SDK."""
from __future__ import annotations

from http.cookies import _quote
import json
import sys

from t1envios.core.client import T1Client
from t1envios.core.exceptions import ApiError
from t1envios.core.models.quote import QuoteRequest
from t1envios.core.models.shipment import ShipmentRequest
from t1envios.core.utils.logging import configure_logging

configure_logging("DEBUG")


def fail(msg: str, exc: Exception | None = None) -> None:
    print(f"\n✘ {msg}", file=sys.stderr)
    if isinstance(exc, ApiError) and exc.payload:
        try:
            print(json.dumps(json.loads(exc.payload), indent=2, ensure_ascii=False), file=sys.stderr)
        except Exception:
            print(exc.payload, file=sys.stderr)
    elif exc:
        print(exc, file=sys.stderr)
    sys.exit(1)


client = T1Client.from_settings()
quote = None
# 1. Cotizar
print("── Cotizando ──")
try:
    quote = client.quote(QuoteRequest(
        origin_postal_code="02719",
        destination_postal_code="40900",
        weight=1,
        width=10,
        height=10,
        length=10,
        package_value=500,
        insurance=False,
        packages=1,
        package_type=1,
    ))
except Exception as e:
    fail("Error al cotizar", e)

if quote:

    rates = quote.detail or []
    for r in rates:
        print(f"  {r.get('carrier')} | {r.get('service_name')} | ${r.get('total_cost')} | token: {r.get('token')}")

    if not rates:
        fail("Sin tarifas disponibles")

    token = rates[0].get("token")
    print(f"\nUsando token: {token}")

    # 2. Crear guía
    print("\n── Creando guía ──")

    _req = ShipmentRequest(
        quote_token=token,
        content="Ropa",
        origin_first_name="Juan",
        origin_last_name="Pérez",
        origin_email="juan@example.com",
        origin_phone="5512345678",
        origin_street="Av. Azcapotzalco",
        origin_number="45",
        origin_neighborhood="Bondojito",
        origin_state="Ciudad de Mexico",
        origin_municipality="Gustavo A. Madero",
        origin_references="Frente a la papelería",
        origin_postal_code="02719",
        destination_first_name="Ana",
        destination_last_name="García",
        destination_email="ana@example.com",
        destination_phone="7471234567",
        destination_street="Av. Insurgentes",
        destination_number="200",
        destination_neighborhood="Centro",
        destination_state="Guerrero",
        destination_municipality="Chilpancingo de los Bravo",
        destination_references="Edificio blanco esquina",
        destination_postal_code="40900",
        packages=1,
        generate_pickup=False,
        has_notification=False,
        guide_origin="",
    )
    shipment = None
    try:
        shipment = client.create_shipment(_req)
    except Exception as e:
        fail("Error al crear guía", e)

    if shipment:

        print(f"  Guía:      {shipment.tracking_number}")
        print(f"  Orden:     {shipment.order_number}")
        print(f"  Carrier:   {shipment.carrier}")
        print(f"  Costo:     {shipment.cost}")
        if shipment.guide_link:
            print(f"  Etiqueta:  {shipment.guide_link}")
