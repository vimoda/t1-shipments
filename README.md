# T1Shipments

> **Disclaimer:** This is an unofficial, community-built SDK. It is not affiliated with or endorsed by T1Envios.

Python SDK, CLI, and MCP Server for the [T1Envios](https://t1envios.com) API. Quote shipments, generate guides, schedule pickups, and track packages.

[Leer en español](README.es.md)

## Packages

| Tool | Package | Description | Docs |
|------|---------|-------------|------|
| SDK (`T1Client`) | `t1-shipments-core` | Programmatic Python SDK | [README](packages/core/README.md) |
| CLI (`t1`) | `t1-shipments-cli` | Terminal interface | [README](packages/cli/README.md) |
| MCP server | `t1-shipments-mcp` | MCP server for AI agents | [README](packages/mcp/README.md) |

---

## SDK (`t1-shipments-core`)

The SDK provides `T1Client` for programmatic access to the T1Envios API.

### Installation

```bash
# From GitHub (no clone needed)
pip install "t1-shipments-core @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/core"

# From PyPI (when published)
pip install t1-shipments-core
uv add t1-shipments-core

# From install.sh
curl -fsSL https://raw.githubusercontent.com/vimoda/t1-shipments/main/install.sh | bash -s core

# From source (clone)
git clone https://github.com/vimoda/t1-shipments
cd t1-shipments
uv sync
```

### Usage

```python
from t1shipments.core.client import T1Client
from t1shipments.core.models.quote import QuoteRequest
from t1shipments.core.models.shipment import ShipmentRequest
from t1shipments.core.models.balance import Balance
from t1shipments.core.models.carrier import Carrier
from t1shipments.core.models.tracking import TrackingResponse, TrackingState
from t1shipments.core.exceptions import SessionExpiredError, ApiError, InsufficientBalanceError
```

#### Authentication

```python
# Login with username and password (required for all operations)
client = T1Client(client_id="...", client_secret="...")
client.login("username", "password")

# Or use context manager
with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")
    # ... use client
```

#### Quote and Create Shipment

```python
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
        package_type=2,  # 1=Envelope, 2=Parcel
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
        origin_references="Depto 5 — Frente a la papelería",
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
        destination_references="Int 3B — Edificio blanco esquina",
        destination_postal_code="40900",
        packages=1,
    ))

    print(f"Tracking number: {shipment.tracking_number}")

    # 3. Download label PDF
    pdf = client.download_label(shipment.label_url)
    with open("label.pdf", "wb") as f:
        f.write(pdf)
```

#### Tracking

```python
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

#### Balance and Carriers

```python
with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")

    balance = client.balance()
    print(f"Balance: {balance.amount} {balance.currency}")

    carriers = client.list_carriers()
    for c in carriers:
        print(c.name, c.services)
```

#### Schedule Pickup

> The origin address must be registered in T1Envios before scheduling a pickup.

```python
from t1shipments.core.models.tracking import PickupRequest

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

#### Token Storage

By default `T1Client` uses in-memory storage (token is lost when the process exits). For persistent sessions use `HybridStorage`, which tries `keyring` first and falls back to `~/.t1shipments/credentials.json`:

```python
from t1shipments.core.auth.storage import HybridStorage, InMemoryStorage

# Persistent (default for CLI)
client = T1Client(..., token_storage=HybridStorage())

# In-memory — useful for scripts, serverless, or tests
client = T1Client(..., token_storage=InMemoryStorage())
```

#### Load Config from Environment / Storage

```python
# Pass credentials explicitly, or load from stored session (t1 auth login)
with T1Client.from_settings(client_id="YOUR_CLIENT_ID", client_secret="YOUR_CLIENT_SECRET") as client:
    client.login("username", "password")
    print(client.balance())
```

#### Exception Handling

```python
from t1shipments.core.exceptions import SessionExpiredError, ApiError, InsufficientBalanceError

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

## CLI (`t1-shipments-cli`)

The CLI provides `t1` commands for terminal-based interaction with T1Envios.

### Installation

```bash
# From GitHub (no clone needed)
pip install "t1-shipments-cli @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/cli"

# From PyPI (when published)
pip install t1-shipments-cli
uv tool install t1-shipments-cli

# Run without installing (via uvx)
uvx --from "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/cli" t1 --help

# From install.sh
curl -fsSL https://raw.githubusercontent.com/vimoda/t1-shipments/main/install.sh | bash -s cli

# From source (clone)
git clone https://github.com/vimoda/t1-shipments
cd t1-shipments
uv sync
uv run t1 --help
```

### Usage

```bash
# Authentication
t1 auth login      # Prompt for username and password
t1 auth logout     # Clear stored token
t1 auth status     # Show current token status

# Quote
t1 quote \
  --from-zip 02719 --to-zip 40900 \
  --weight 1 --width 10 --height 10 --length 10 \
  --package-value 500 --packages 1

# Create Shipment
t1 create-shipment \
  --quote-id <TOKEN_FROM_QUOTE> \
  --content "Ropa" \
  --origin-name "Juan" --origin-last-name "Pérez" \
  --origin-email "juan@example.com" \
  --origin-phone "5512345678" \
  --origin-street "Av. Azcapotzalco" --origin-number "45" \
  --origin-neighborhood "Bondojito" \
  --origin-state "Ciudad de Mexico" --origin-municipality "Gustavo A. Madero" \
  --origin-references "Depto 5 — Frente a la papelería" \
  --origin-zip-code 02719 \
  --destination-name "Ana" --destination-last-name "García" \
  --destination-email "ana@example.com" \
  --destination-phone "7471234567" \
  --destination-street "Av. Insurgentes" --destination-number "200" \
  --destination-neighborhood "Centro" \
  --destination-state "Guerrero" --destination-municipality "Chilpancingo de los Bravo" \
  --destination-references "Int 3B — Edificio blanco esquina" \
  --destination-zip-code 40900

# Download Label
t1 label --guide-link "https://..." --output label.pdf

# Track Shipment
t1 trackstate  --guide 1373188795   # Current status + history
t1 trackdetail --guide 1373188795   # Full carrier detail

# Schedule Pickup
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

# Other Commands
t1 balance       # Account balance
t1 carriers      # List available carriers
t1 mcp run       # Start MCP server
```

> The origin address must be registered in T1Envios before scheduling a pickup.

---

## MCP Server (`t1-shipments-mcp`)

The MCP server enables AI agents (Claude Desktop, opencode, Cursor, etc.) to interact with T1Envios through the [Model Context Protocol](https://modelcontextprotocol.io).

> **Quick start from a cloned repo:** `git clone`, `uv sync`, then add the JSON block from the [Via `uv` — from a cloned repository](#via-uv--from-a-cloned-repository) section below.

### Installation

```bash
# From GitHub (no clone needed)
pip install "t1-shipments-mcp @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp"

# From PyPI (when published)
pip install t1-shipments-mcp
uv tool install t1-shipments-mcp

# Run without installing (via uvx)
uvx --from "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp" t1shipments-mcp

# From install.sh
curl -fsSL https://raw.githubusercontent.com/vimoda/t1-shipments/main/install.sh | bash -s mcp

# From source (clone)
git clone https://github.com/vimoda/t1-shipments
cd t1-shipments
uv sync
uv run t1shipments-mcp
```

### MCP Client Configuration

Once `t1-shipments-mcp` is installed, configure your MCP client with the JSON block that matches your installation method.

> ⚠️ **Client credentials:** Your MCP client must pass `--client-id` and `--client-secret` as command line arguments in the `args` array.
> Replace placeholders with your actual credentials.

#### Via `uvx` (no installation — runs from GitHub on demand)

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp",
        "t1shipments-mcp",
        "--client-id",
        "${T1_CLIENT_ID}",
        "--client-secret",
        "${T1_CLIENT_SECRET}"
      ],
      "env": {
        "T1_USERNAME":      "${T1_USERNAME}",
        "T1_PASSWORD":      "${T1_PASSWORD}",
        "T1_ENV":           "dev",
        "T1_SHOP_ID":       "${T1_SHOP_ID}",
        "T1_COMERCE_ID":    "${T1_COMERCE_ID}",
        "T1_LOG_LEVEL":     "DEBUG"
      }
    }
  }
}
```

Point to a specific tag / commit / branch:

```json
"args": ["--from", "git+https://github.com/vimoda/t1-shipments@v0.1.0#subdirectory=packages/mcp", "t1shipments-mcp", "--client-id", "${T1_CLIENT_ID}", "--client-secret", "${T1_CLIENT_SECRET}"]
```

#### Via `uv` — from a cloned repository

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/t1-shipments",
        "t1shipments-mcp",
        "--client-id",
        "${T1_CLIENT_ID}",
        "--client-secret",
        "${T1_CLIENT_SECRET}"
      ],
      "env": {
        "T1_USERNAME":      "${T1_USERNAME}",
        "T1_PASSWORD":      "${T1_PASSWORD}",
        "T1_ENV":           "dev",
        "T1_SHOP_ID":       "${T1_SHOP_ID}",
        "T1_COMERCE_ID":    "${T1_COMERCE_ID}",
        "T1_LOG_LEVEL":     "DEBUG"
      }
    }
  }
}
```

#### Via installed binary (`pip install` / `uv tool install`)

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "t1shipments-mcp",
      "args": [
        "--client-id",
        "${T1_CLIENT_ID}",
        "--client-secret",
        "${T1_CLIENT_SECRET}"
      ],
      "env": {
        "T1_USERNAME":      "${T1_USERNAME}",
        "T1_PASSWORD":      "${T1_PASSWORD}",
        "T1_ENV":           "dev",
        "T1_SHOP_ID":       "${T1_SHOP_ID}",
        "T1_COMERCE_ID":    "${T1_COMERCE_ID}",
        "T1_LOG_LEVEL":     "DEBUG"
      }
    }
  }
}
```

#### Config file locations

| Client | Config file |
|--------|-------------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Code | `.claude/mcp_config.json` in your project |

#### opencode

Add to your `opencode.json` or `~/.config/opencode/opencode.json`:

**Via `uv` — from a cloned repository:**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "t1shipments": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--directory",
        "/path/to/t1-shipments",
        "t1shipments-mcp",
        "--client-id",
        "${T1_CLIENT_ID}",
        "--client-secret",
        "${T1_CLIENT_SECRET}"
      ],
      "env": {
        "T1_SHOP_ID":       "${T1_SHOP_ID}",
        "T1_USERNAME":      "${T1_USERNAME}",
        "T1_PASSWORD":      "${T1_PASSWORD}",
        "T1_ENV":           "${T1_ENV}",
        "T1_COMERCE_ID":    "${T1_COMERCE_ID}",
        "T1_LOG_LEVEL":     "${T1_LOG_LEVEL}"
      },
      "enabled": true
    }
  }
}
```

**Via `uvx` — without cloning the repo (runs from GitHub on demand):**

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "t1shipments": {
      "type": "local",
      "command": [
        "uvx",
        "--from",
        "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp",
        "t1shipments-mcp",
        "--client-id",
        "${T1_CLIENT_ID}",
        "--client-secret",
        "${T1_CLIENT_SECRET}"
      ],
      "env": {
        "T1_SHOP_ID":       "${T1_SHOP_ID}",
        "T1_USERNAME":      "${T1_USERNAME}",
        "T1_PASSWORD":      "${T1_PASSWORD}",
        "T1_ENV":           "${T1_ENV}",
        "T1_COMERCE_ID":    "${T1_COMERCE_ID}",
        "T1_LOG_LEVEL":     "${T1_LOG_LEVEL}"
      },
      "enabled": true
    }
  }
}
```

#### Test the installation

```bash
# With MCP Inspector (interactive UI)
npx @modelcontextprotocol/inspector uvx --from "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp" t1shipments-mcp

# Or if installed locally
npx @modelcontextprotocol/inspector t1shipments-mcp
```

### Auth & Token Lifecycle

The server keeps a **single `T1Client` instance** alive for the entire MCP session. Before every tool call it calls `ensure_valid()`:

1. Token valid → proceeds immediately.
2. Token expires within 60 s → **refresh** using `refresh_token` (no re-login needed).
3. No session / refresh expired → **re-login** with `T1_USERNAME`/`T1_PASSWORD`.

No manual intervention is required at any point.

### Testing with MCP Inspector

```bash
# requires mcp[cli] — already included in the mcp extra
uv run mcp dev src/t1shipments/mcp/server.py
```

Opens a local web inspector where you can invoke tools interactively.

### Starting the Server (production)

```bash
t1 mcp run
# or
python -m t1shipments.mcp.server
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

### Tool Input Schemas

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

## Configuration

API credentials (`client_id` and `client_secret`) are supplied directly as parameters:
- **SDK**: Passed to `T1Client(client_id=..., client_secret=...)` or `T1Client.from_settings(client_id=..., client_secret=...)`.
- **CLI**: Passed via `t1 auth login --client-id ... --client-secret ...` (and persisted in local keyring/file storage).
- **MCP**: Passed via `--client-id` and `--client-secret` arguments in MCP runner configuration.

Optional environment variables (or in a `.env` file):

```env
T1_BASE_URL=https://api.t1envios.com
T1_SHOP_ID=your_shop_id
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `T1_BASE_URL` | No | `https://api.t1envios.com` | API base URL |
| `T1_SHOP_ID` | No | — | Commerce ID — sent as `comercio_id` on every request |
| `T1_USERNAME` | No | — | T1Envios account email (auto-login in MCP) |
| `T1_PASSWORD` | No | — | T1Envios account password |
| `T1_ENV` | No | `dev` | `dev` or `prod` |
| `T1_COMERCE_ID` | No | — | Internal commerce identifier |
| `T1_LOG_LEVEL` | No | — | Logging level (e.g., `DEBUG`) |
| `T1_TIMEOUT` | No | `30.0` | HTTP timeout in seconds |

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
