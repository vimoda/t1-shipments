"""Example: using t1shipments as an importable SDK."""

from t1shipments.core.client import T1Client
from t1shipments.core.config import Endpoints
from t1shipments.core.models.quote import QuoteRequest

# Direct credentials + custom base URL
client = T1Client(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    # Defaults to dev env; override with Endpoints(base_url=..., auth_base_url=...)
    endpoints=Endpoints(),
)

with client:
    # Login before making API calls
    client.login(username="YOUR_USERNAME", password="YOUR_PASSWORD")

    # List carriers
    carriers = client.list_carriers()
    print("Paqueterías:", [c.name for c in carriers])

    # Quote — weight=2 is the billable weight (max of physical and volumetric).
    # The model will raise if volumetric > physical weight; set weight to the
    # volumetric value to confirm.
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
        print(f"  {rate.get('token')} {rate.get('service_id')}: ${cost:,.2f} MXN ({days} días)")
