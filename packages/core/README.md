# t1-shipments-core

> **Disclaimer:** This is an unofficial, community-built SDK. Not affiliated with or endorsed by T1Envios.

Python SDK for the [T1Envios](https://t1envios.com) shipping API. Provides `T1Client` with auth, quote, shipment creation, tracking, balance, carriers, and pickup scheduling.

[Leer en español](README.es.md)

---

## Installation

```bash
pip install "t1-shipments-core @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/core"
# or from source
uv sync
```

## Quick Start

```python
from t1shipments.core.client import T1Client
from t1shipments.core.models.quote import QuoteRequest
from t1shipments.core.models.shipment import ShipmentRequest

with T1Client.from_settings() as client:
    client.login("user@example.com", "password")

    # Quote (free)
    quote = client.quote(QuoteRequest(
        origin_postal_code="02719",
        destination_postal_code="40900",
        weight=1, width=30, height=20, length=15,
        insurance=False,
    ))
    token = quote.detail[0]["token"]

    # Create shipment (cost)
    shipment = client.create_shipment(ShipmentRequest(
        quote_token=token,
        content="Ropa",
        origin_first_name="Juan", origin_last_name="Pérez",
        origin_email="juan@example.com", origin_phone="5512345678",
        origin_street="Av. Azcapotzalco", origin_number="45",
        origin_neighborhood="Bondojito", origin_state="CDMX",
        origin_municipality="Gustavo A. Madero", origin_postal_code="02719",
        destination_first_name="Ana", destination_last_name="García",
        destination_email="ana@example.com", destination_phone="7471234567",
        destination_street="Av. Insurgentes", destination_number="200",
        destination_neighborhood="Centro", destination_state="Guerrero",
        destination_municipality="Chilpancingo", destination_postal_code="40900",
        packages=1,
    ))
```

## Public API

### `T1Client`

| Method | Description | Cost |
|---|---|---|
| `login(username, password, store_id?)` | Authenticate via Keycloak | No |
| `quote(req: QuoteRequest)` | Get shipping rates | No |
| `create_shipment(req: ShipmentRequest)` | Generate a shipping guide | Yes |
| `track_state(guide)` | Current status + history | No |
| `track_detail(guide)` | Full carrier tracking detail | No |
| `balance()` | Account balance in MXN | No |
| `list_carriers()` | List enabled carriers/services | No |
| `schedule_pickup(req: PickupRequest)` | Schedule a pickup | Yes |
| `download_label(guide_link)` | Download label PDF | No |
| `inject_token(access, refresh?, expires?)` | Load externally managed token | No |

### Configuration and initialization

Pass `client_id` and `client_secret` directly as input parameters, or load from stored session:

```python
# Direct parameters (recommended for scripts & integrations):
client = T1Client(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)

# Or via from_settings (loads from arguments or stored session):
client = T1Client.from_settings(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)
```

### Token storage

| Storage | Behavior |
|---|---|
| `InMemoryStorage` | Default — lost on process exit |
| `HybridStorage()` | Tries `keyring` → falls back to `~/.t1shipments/credentials.json` |
| `FileStorage(path?)` | JSON file only |

### Exceptions

```
T1Error
├── AuthError
│   ├── SessionExpiredError
│   └── RefreshExpiredError
├── ApiError
├── RateLimitError
├── StorageError
├── ConfigError
├── QuotaExceededError
├── InvalidAddressError
├── CarrierUnavailableError
└── InsufficientBalanceError
```

## Models

All request/response models are Pydantic v2 `BaseModel` instances. Import from `t1shipments.core.models`:

- `QuoteRequest`, `QuoteResponse`, `Rate`
- `ShipmentRequest`, `Shipment`
- `TrackingResponse`, `TrackingState`
- `PickupRequest`, `Pickup`
- `Balance`, `Carrier`

## Auth flow

1. `login()` → `POST {auth_url}/protocol/openid-connect/token` with `application/x-www-form-urlencoded` payload.
2. Token auto-refreshes when expiring within 60 s (`auto_refresh=True` by default).
3. On 401, SDK refreshes once and retries.

## Development

```bash
uv sync
uv run pytest tests/
uv run ruff check src/
uv run mypy src/
```

## License

MIT
