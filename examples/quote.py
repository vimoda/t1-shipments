"""Example: quoting a shipment step by step."""

from t1shipments.core.client import T1Client
from t1shipments.core.models.quote import QuoteRequest

# Uses env vars T1_CLIENT_ID, T1_CLIENT_SECRET, and optionally
# T1_ENV=dev|prod, T1_SHOP_ID, T1_COMMERCE_ID, T1_BASE_URL, T1_AUTH_URL.
client = T1Client.from_settings()

with client:
    # Login with your credentials
    client.login(username="YOUR_USERNAME", password="YOUR_PASSWORD")

    # List available carriers
    carriers = client.list_carriers()
    print("Paqueterías disponibles:")
    for c in carriers:
        print(f"  {c.name} ({c.carrier_id}) — {'activo' if c.active else 'inactivo'}")

    # Build a quote request
    # The model automatically resolves the billable weight:
    #   - If you give dimensions only, volumetric weight = ceil(W×H×L÷5000)
    #   - If you give both physical weight and dimensions, it compares them
    #     and raises if volumetric > physical, so you can confirm by resubmitting
    #     with weight set to the volumetric value.
    req = QuoteRequest(
        origin_postal_code="06600",
        destination_postal_code="44100",
        weight=2,  # billable kg (physical = 2, volumetric = ceil(20×15×10÷5000) = 1)
        width=20.0,
        height=15.0,
        length=10.0,
        shipping_days=3,
        insurance=False,
        package_value=500.0,  # declared value (required only when insurance=True)
        package_type=2,  # 1: Sobre, 2: Paquete
        packages=1,
    )

    # Fetch rates
    quote = client.quote(req)
    if not quote.success:
        print(f"Error: {quote.message}")
        exit(1)

    print(f"\nCotización #{len(quote.detail)} tarifas:")
    hdr = f"{'#':<3} {'Paquetería':<12} {'Servicio':<30} {'Tipo':<25} {'Costo':<10} {'Entrega':<10}"
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

    # To create a shipment, pass the selected rate's token:
    #
    #   token = quote.detail[0]["token"]
    #   shipment = client.create_shipment(ShipmentRequest(
    #       quote_token=token,
    #       content="Documentos",
    #       origin_first_name="...", ...
    #       destination_first_name="...", ...
    #       packages=1,
    #   ))
    #   print(f"Guía: {shipment.tracking_number} — {shipment.guide_link}")
