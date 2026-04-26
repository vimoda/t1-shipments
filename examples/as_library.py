"""Example: using t1envios as an importable SDK."""

from t1envios import T1Client, Endpoints, QuoteRequest, PickupRequest

# Direct credentials + custom base URL
client = T1Client(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    endpoints=Endpoints(base_url="https://api.t1envios.com", auth_base_url="https://keycloak.dev.plataformat1.com"),
)

with client:
    # List carriers
    carriers = client.list_carriers()
    print("Paqueterías:", [c.name for c in carriers])

    # Quote
    req = QuoteRequest(
        origin_postal_code="06600",
        destination_postal_code="44100",
        weight=2,
        width=20,
        height=15,
        length=10,
        shipping_days=2,
        insurance=False, # False | True
        package_value=500.0,
        package_type=1, # 1: Sobre, 2: Paquete
        packages=1
    )
    quote = client.quote(req)
    print(f"\nQuote ID: {quote}")
    for rate in quote.detail or []:
        print(f"  {rate.get("token")} {rate.get("service_id")}: ${rate.get('total_cost'):,.2f} MXN ({str(rate.get('delivery_days')) if rate.get('delivery_days') else "-"} días)")
