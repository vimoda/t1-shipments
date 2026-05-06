# t1envios

> **Disclaimer:** This is an unofficial, community-built SDK. It is not affiliated with or endorsed by T1Envios.

Python SDK, CLI, and MCP Server for the [T1Envios](https://t1envios.com) API. Quote shipments, generate guides, schedule pickups, and track packages.

## Installation

### Using pip

```bash
# SDK only (httpx, pydantic, pydantic-settings)
pip install t1envios

# With CLI (adds typer, rich, keyring)
pip install "t1envios[cli]"

# With MCP server (adds mcp)
pip install "t1envios[mcp]"

# Everything
pip install "t1envios[cli,mcp]"

# Development (cli + mcp + pytest, ruff, mypy)
pip install "t1envios[dev]"
```

### Using uv (recommended)

```bash
# SDK only
uv add t1envios

# With CLI
uv add "t1envios[cli]"

# With MCP server
uv add "t1envios[mcp]"

# Development dependencies
uv sync --extra dev
```

### Dependency breakdown

| Extra | Dependencies |
|-------|-------------|
| _(none)_ | `httpx>=0.28.1`, `pydantic>=2.13.3`, `pydantic-settings>=2.14.0` |
| `cli` | _SDK_ + `typer[all]>=0.24.2`, `rich>=15.0.0`, `keyring>=25.7.0` |
| `mcp` | _SDK_ + `mcp>=1.27.0` |
| `dev` | _cli_ + _mcp_ + `pytest>=8`, `pytest-httpx>=0.30`, `pytest-cov`, `ruff`, `mypy` |

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
| `T1_TIMEOUT` | No | HTTP timeout in seconds (default: `30.0`) |

## Quick Start

### SDK
```python
from t1envios import T1Client

with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")
    balance = client.balance()
    print(f"Balance: {balance.amount} {balance.currency}")
```

### CLI
```bash
t1 auth login          # Prompt for credentials
t1 quote --from-zip 02719 --to-zip 40900 --weight 1
t1 balance
```

### MCP
```bash
t1 mcp run
```

---

## SDK Usage

All public types are importable from the top-level package:

```python
from t1envios import (
    T1Client,
    QuoteRequest,
    ShipmentRequest,
    Balance,
    Carrier,
    TrackingResponse,
    TrackingState,
    SessionExpiredError,
    ApiError,
)
```

### Authentication

```python
from t1envios import T1Client

# Login with username and password (required for all operations)
client = T1Client(client_id="...", client_secret="...")
client.login("username", "password")

# Or use context manager
with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")
    # ... use client
```

### Quote and Create Shipment

```python
from t1envios import T1Client, QuoteRequest, ShipmentRequest

with T1Client(client_id="...", client_secret="...", shop_id="...") as client:
    client.login("username", "password")

    # 1. Get shipping quote
    response = client.quote(QuoteRequest(
        origin_postal_code="02719",
        destination_postal_code="40900",
        weight=1,
        width=10, height=10, length=10,
        package_value=500,
        packages=1,
        shipping_days=2,
        insurance=False,
        package_type=2,  # 1=Sobre, 2=Paquete
    ))

    # Pick a rate by token
    quote_token = response.detail[0]["token"]

    # 2. Create shipment
    shipment = client.create_shipment(ShipmentRequest(
        quote_token=quote_token,
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

    print(f"Tracking number: {shipment.tracking_number}")

    # 3. Download label PDF
    pdf = client.download_label(shipment.label_url)
    with open("label.pdf", "wb") as f:
        f.write(pdf)
```

### Tracking

```python
from t1envios import T1Client

with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")

    # Current status + history
    state = client.track_state("1373188795")
    print(state.current_status)
    for event in state.history:
        print(event.date, event.description)

    # Full carrier detail
    detail = client.track_detail("1373188795")
    print(detail.detail)
```

### Balance and Carriers

```python
from t1envios import T1Client

with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")

    balance = client.balance()
    print(f"Balance: {balance.amount} {balance.currency}")

    carriers = client.list_carriers()
    for c in carriers:
        print(c.name, c.services)
```

### Schedule Pickup

> The origin address must be registered in T1Envios before scheduling a pickup.

```python
from t1envios import T1Client, PickupRequest

with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")

    pickup = client.schedule_pickup(PickupRequest(
        carrier="DHL",
        contact_name="Juan",
        contact_last_name="Pérez",
        email="juan@example.com",
        phone="5512345678",
        street="Av. Azcapotzalco",
        number="45",
        neighborhood="Bondojito",
        state="Ciudad de Mexico",
        municipality="Gustavo A. Madero",
        zip_code="02719",
        references="Frente a la papelería",
        pieces=1,
        weight=2,
        length=30,
        width=20,
        height=15,
        date="2026-04-28",
        open_time="09:00",
        close_time="18:00",
    ))
    print(f"Pickup scheduled: {pickup}")
```

### Token Storage

By default `T1Client` uses in-memory storage (token is lost when the process exits). For persistent sessions use `HybridStorage`, which tries `keyring` first and falls back to `~/.t1envios/credentials.json`:

```python
from t1envios import T1Client
from t1envios.core.auth.storage import HybridStorage, InMemoryStorage

# Persistent (default for CLI)
client = T1Client(..., token_storage=HybridStorage())

# In-memory — useful for scripts, serverless, or tests
client = T1Client(..., token_storage=InMemoryStorage())
```

### Load Config from Environment

```python
from t1envios import T1Client

# Reads T1_CLIENT_ID, T1_CLIENT_SECRET, T1_SHOP_ID, etc. from env / .env
with T1Client.from_settings() as client:
    client.login("username", "password")
    print(client.balance())
```

### Exception Handling

```python
from t1envios import T1Client, SessionExpiredError, ApiError, InsufficientBalanceError

with T1Client(client_id="...", client_secret="...") as client:
    try:
        client.login("username", "password")
        balance = client.balance()
    except SessionExpiredError:
        # Token expired and refresh failed — re-login required
        client.login("username", "password")
    except InsufficientBalanceError:
        print("Not enough balance to create shipment")
    except ApiError as e:
        print(f"API error {e.status}: {e}")
```

Exception hierarchy:

```
T1Error
├── AuthError
│   ├── SessionExpiredError   # no valid session / refresh failed
│   └── RefreshExpiredError   # refresh token itself expired
├── ApiError                  # non-2xx HTTP response
├── RateLimitError            # HTTP 429
├── StorageError              # token storage backend unavailable
├── ConfigError               # missing or invalid configuration
├── QuotaExceededError        # account quota exceeded
├── InvalidAddressError       # address validation failed
├── CarrierUnavailableError   # carrier or service not available
└── InsufficientBalanceError  # account balance too low
```

---

## CLI Usage

The CLI is available after installing with `pip install "t1envios[cli]"` or `uv sync --extra cli`.

### Authentication

```bash
t1 auth login      # Prompt for username and password
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

### Create Shipment

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

### Download Label

```bash
t1 label --guide-link "https://..." --output label.pdf
```

### Track Shipment

```bash
t1 trackstate  --guide 1373188795   # Current status + history
t1 trackdetail --guide 1373188795   # Full carrier detail
```

### Schedule Pickup

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

### Other Commands

```bash
t1 balance       # Account balance
t1 carriers      # List available carriers
t1 mcp run       # Start MCP server
```

---

## MCP Server

t1envios ships an [MCP](https://modelcontextprotocol.io) server compatible with any MCP client (Claude Desktop, opencode, Cursor, IDE plugins, custom stdio clients, etc.).

### Installation

The MCP extra is required:

```bash
pip install "t1envios[mcp]"
# or
uv add "t1envios[mcp]"
```

### Configuration

The server reads credentials from environment variables (or a `.env` file in the working directory):

| Variable | Required | Description |
|----------|----------|-------------|
| `T1_CLIENT_ID` | Yes | OAuth client ID |
| `T1_CLIENT_SECRET` | Yes | OAuth client secret |
| `T1_USERNAME` | Yes* | T1Envios account email |
| `T1_PASSWORD` | Yes* | T1Envios account password |
| `T1_ENV` | No | `dev` (default) or `prod` |

`T1_USERNAME`/`T1_PASSWORD` enable automatic bearer-token login on first use. If omitted, the server falls back to a token previously stored by `t1 auth login`.

### Auth & Token Lifecycle

The server keeps a **single `T1Client` instance** alive for the entire MCP session. Before every tool call it calls `ensure_valid()`:

1. Token valid → proceeds immediately.
2. Token expires within 60 s → **refresh** using `refresh_token` (no re-login needed).
3. No session / refresh expired → **re-login** with `T1_USERNAME`/`T1_PASSWORD`.

No manual intervention is required at any point.

### Testing with MCP Inspector

```bash
# requires mcp[cli] — already included in the mcp extra
uv run mcp dev src/t1envios/mcp/server.py
```

Opens a local web inspector where you can invoke tools interactively. Make sure the `.env` file (or env vars) is present before running.

### Starting the Server (production)

```bash
t1 mcp run
# or
python -m t1envios.mcp.server
```

### Client Configuration

Example config for any stdio-based MCP client (`mcp.json`, `claude_desktop_config.json`, etc.):

```json
{
  "mcpServers": {
    "t1envios": {
      "command": "python",
      "args": ["-m", "t1envios.mcp.server"],
      "env": {
        "T1_CLIENT_ID": "t1envios",
        "T1_CLIENT_SECRET": "<your-secret>",
        "T1_USERNAME": "<your-email>",
        "T1_PASSWORD": "<your-password>",
        "T1_ENV": "prod"
      }
    }
  }
}
```

If using `uv` in an isolated environment:

```json
{
  "mcpServers": {
    "t1envios": {
      "command": "uv",
      "args": ["run", "python", "-m", "t1envios.mcp.server"],
      "env": {
        "T1_CLIENT_ID": "t1envios",
        "T1_CLIENT_SECRET": "<your-secret>",
        "T1_USERNAME": "<your-email>",
        "T1_PASSWORD": "<your-password>",
        "T1_ENV": "prod"
      }
    }
  }
}
```

### Available Tools

| Tool | Description |
|------|-------------|
| `quote_shipment` | Get available shipping rates for a package. Returns a list of carrier options with prices. Always call this BEFORE `create_shipment`. |
| `create_shipment` | Create a shipment using a quote token from `quote_shipment`. |
| `track_guide` | Track a shipment by guide number. Returns current status, estimated delivery date, and history. |
| `get_balance` | Get the current account balance in MXN. |
| `list_carriers` | List all shipping carriers and services available in your T1Envios account. |
| `schedule_pickup` | Schedule a pickup for an existing shipment. |

### MCP Tool Input Schemas

**quote_shipment:**
```json
{
  "origin_postal_code": "02719",
  "destination_postal_code": "40900",
  "weight": 1.0,
  "width": 10.0,
  "height": 10.0,
  "length": 10.0,
  "package_value": 500,
  "packages": 1
}
```

**create_shipment:**
```json
{
  "quote_token": "...",
  "content": "Ropa",
  "origin_first_name": "Juan",
  "origin_last_name": "Pérez",
  "origin_email": "juan@example.com",
  "origin_phone": "5512345678",
  "origin_street": "Av. Azcapotzalco",
  "origin_number": "45",
  "origin_neighborhood": "Bondojito",
  "origin_state": "Ciudad de Mexico",
  "origin_municipality": "Gustavo A. Madero",
  "origin_postal_code": "02719",
  "destination_first_name": "Ana",
  "destination_last_name": "García",
  "destination_email": "ana@example.com",
  "destination_phone": "7471234567",
  "destination_street": "Av. Insurgentes",
  "destination_number": "200",
  "destination_neighborhood": "Centro",
  "destination_state": "Guerrero",
  "destination_municipality": "Chilpancingo de los Bravo",
  "destination_postal_code": "40900",
  "packages": 1
}
```

---

## Development

```bash
uv sync --extra dev
uv run pytest tests/ -v
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

## License

MIT
