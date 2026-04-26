# t1envios

Python SDK and CLI for the [T1Envios](https://t1envios.com) API. Quote shipments, generate guides, schedule pickups, and track packages — from code or the terminal.

## Installation

```bash
pip install t1envios
# or with uv
uv add t1envios
```

## Configuration

Set environment variables (or use a `.env` file):

```env
T1_CLIENT_ID=your_client_id
T1_CLIENT_SECRET=your_client_secret
T1_BASE_URL=https://api.t1envios.com
T1_SHOP_ID=your_shop_id
```

| Variable | Required | Description |
|---|---|---|
| `T1_CLIENT_ID` | Yes | Keycloak client ID |
| `T1_CLIENT_SECRET` | Yes | Keycloak client secret |
| `T1_BASE_URL` | No | API base URL (default: `https://api.t1envios.com`) |
| `T1_SHOP_ID` | No | Commerce ID — sent as `comercio_id` on every request |
| `T1_USERNAME` | No | Optional username for user-level auth |
| `T1_PASSWORD` | No | Optional password for user-level auth |
| `T1_TIMEOUT` | No | HTTP timeout in seconds (default: `30.0`) |

---

## CLI

### Auth

```bash
t1 auth login      # Authenticate and store token
t1 auth logout     # Clear stored token
t1 auth status     # Show current token status
```

### Quote

```bash
t1 quote \
  --from-zip 02719 --to-zip 40900 \
  --weight 1 --width 10 --height 10 --length 10 \
  --package-value 500 --packages 1
```

### Create shipment

```bash
t1 create-shipment \
  --quote-id <TOKEN_FROM_QUOTE> \
  --content "Ropa" \
  --origin-name "Juan" --origin-last-name "Pérez" \
  --origin-email "juan@example.com" \
  --origin-phone "5512345678" \
  --origin-street "Av. Azcapotzalco" --origin-number "45" \
  --origin-neighborhood "Bondojito" \
  --origin-state "Ciudad de Mexico" --origin-municipality "Gustavo A. Madero" \
  --origin-references "Frente a la papelería" \
  --origin-zip-code 02719 \
  --destination-name "Ana" --destination-last-name "García" \
  --destination-email "ana@example.com" \
  --destination-phone "7471234567" \
  --destination-street "Av. Insurgentes" --destination-number "200" \
  --destination-neighborhood "Centro" \
  --destination-state "Guerrero" --destination-municipality "Chilpancingo de los Bravo" \
  --destination-references "Edificio blanco esquina" \
  --destination-zip-code 40900
```

### Track shipment

```bash
t1 trackstate  --guide 1373188795   # Current status + history
t1 trackdetail --guide 1373188795   # Full carrier detail
```

### Schedule pickup

> The origin address must be registered in T1Envios before scheduling a pickup.

```bash
t1 pickup \
  --carrier DHL \
  --contact-name "Juan" --contact-last-name "Pérez" \
  --email "juan@example.com" \
  --phone "5512345678" \
  --street "Av. Azcapotzalco" --number "45" \
  --neighborhood "Bondojito" \
  --state "Ciudad de Mexico" --municipality "Gustavo A. Madero" \
  --zip-code 02719 \
  --references "Frente a la papelería" \
  --pieces 1 --weight 2 \
  --length 30 --width 20 --height 15 \
  --date 2026-04-28 \
  --open-time "09:00" --close-time "18:00"
```

### Other

```bash
t1 balance       # Account balance
t1 carriers      # List available carriers
t1 mcp start     # Start MCP server
```

---

## SDK

```python
from t1envios import T1Client
from t1envios.models.quote import QuoteRequest
from t1envios.models.shipment import ShipmentRequest

with T1Client(
    client_id="...",
    client_secret="...",
    shop_id="...",
) as client:

    # Quote
    rates = client.quote(QuoteRequest(
        origin_postal_code="02719",
        destination_postal_code="40900",
        weight=1,
        width=10, height=10, length=10,
        package_value=500,
        packages=1,
        shipping_days=2,
        insurance=False,
        package_type=2,
    ))

    # Create shipment
    shipment = client.create_shipment(ShipmentRequest(
        quote_token=rates.quote_token,
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
    ))
    print(shipment.tracking_number)

    # Track
    state = client.track_state("1373188795")
    print(state.current_status, state.estimated_delivery_date)

    # Balance
    balance = client.balance()
    print(balance.amount)
```

### Custom storage

Token storage defaults to `keyring`, falling back to `~/.t1envios/credentials.json`. Override with any `TokenStorage` implementation:

```python
from t1envios.auth.storage import InMemoryStorage

client = T1Client(..., token_storage=InMemoryStorage())
```

---

## MCP Server

t1envios ships an [MCP](https://modelcontextprotocol.io) server for use with Claude and other AI assistants.

```bash
t1 mcp start
```

Tools exposed: `quote_shipment`, `create_shipment`, `track_guide`, `get_balance`, `list_carriers`, `schedule_pickup`.

---

## Development

```bash
uv sync --extra dev
uv run pytest tests/ -v
uv run ruff check src/ tests/
uv run mypy src/
```

## License

MIT
