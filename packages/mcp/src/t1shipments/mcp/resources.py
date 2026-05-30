from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import mcp.types as types
from mcp.server import Server

_DEVELOPER_INSTRUCTIONS_MD = """# T1Envios / T1Shippings — Developer Guide

T1Envios is a Mexican shipping integration platform. This SDK and MCP server
let you quote shipping rates, create shipments (guides), track packages, check
balance, list carriers, and schedule pickups.

---

## 1. Python SDK (`t1-shipments-core`)

### Entry point

```python
from t1shipments.core.client import T1Client
```

### Configuration

Set these environment variables (prefix `T1_`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `T1_CLIENT_ID` | Yes | — | API client ID |
| `T1_CLIENT_SECRET` | Yes | — | API client secret |
| `T1_USERNAME` | No | — | Auto-login username |
| `T1_PASSWORD` | No | — | Auto-login password |
| `T1_ENV` | No | `dev` | Preset: `dev` or `prod` |
| `T1_BASE_URL` | No | preset | Override API base URL |
| `T1_AUTH_URL` | No | preset | Override auth base URL |
| `T1_SHOP_ID` | No | — | Shop/commerce ID |
| `T1_COMMERCE_ID` | No | — | Commerce/store ID (alias) |
| `T1_TIMEOUT` | No | `30.0` | HTTP timeout in seconds |
| `T1_RETRIES` | No | `3` | Max retries on 5xx / network errors |
| `T1_LOG_LEVEL` | No | — | Python log level |

### Quick start

```python
from t1shipments.core.client import T1Client
from t1shipments.core.models.quote import QuoteRequest
from t1shipments.core.models.shipment import ShipmentRequest

# Build client from env vars (recommended)
with T1Client.from_settings() as client:
    client.login("user@example.com", "password")

    # 1. Quote (no cost)
    req = QuoteRequest(
        origin_postal_code="02719",
        destination_postal_code="40900",
        weight=1,
        width=30,
        height=20,
        length=15,
        insurance=False,
    )
    quote_resp = client.quote(req)

    # 2. Create shipment (monetary cost)
    ship_req = ShipmentRequest(
        quote_token=quote_resp.detail[0]["token"],
        content="Ropa",
        origin_first_name="Juan",
        origin_last_name="Pérez",
        origin_email="juan@example.com",
        origin_street="Av. Reforma",
        origin_number="123",
        origin_neighborhood="Juárez",
        origin_phone="5512345678",
        origin_state="CDMX",
        origin_municipality="Cuauhtémoc",
        origin_postal_code="02719",
        destination_first_name="María",
        destination_last_name="García",
        destination_email="maria@example.com",
        destination_street="Hidalgo",
        destination_number="456",
        destination_neighborhood="Centro",
        destination_phone="5598765432",
        destination_state="Guerrero",
        destination_municipality="Tecoanapa",
        destination_postal_code="40900",
        packages=1,
    )
    shipment = client.create_shipment(ship_req)
    print(shipment.tracking_number, shipment.guide_link)
```

### Available client methods

| Method | Description | Cost |
|---|---|---|
| `login(username, password, store_id?)` | Authenticate | No |
| `quote(req: QuoteRequest)` | Get shipping rates | No |
| `create_shipment(req: ShipmentRequest)` | Generate a shipping guide | **Yes** |
| `track_state(guide)` | Get current status | No |
| `track_detail(guide)` | Get full tracking history | No |
| `balance()` | Check account balance | No |
| `list_carriers()` | List enabled carriers | No |
| `schedule_pickup(req: PickupRequest)` | Schedule a pickup | **Yes** |
| `download_label(guide_link)` | Download label PDF | No |

### Token management

- `T1Client.from_settings()` uses `HybridStorage` (keyring → file fallback).
- For headless/CLI, use `InMemoryStorage` or inject tokens via `inject_token()`.
- The SDK auto-refreshes tokens expiring within 60 seconds when `auto_refresh=True`.
- On a 401 response, the SDK refreshes once and retries the request.

---

## 2. Direct API Usage (without the SDK)

### Base URLs

| Environment | API | Auth (Keycloak) |
|---|---|---|
| Dev | `https://apiv2.dev.t1envios.com` | `https://keycloak.dev.plataformat1.com` |
| Prod | `https://apiv2.t1envios.com` | `https://keycloak.plataformat1.com` |

### Authentication (Keycloak OIDC)

```
POST {auth_base_url}/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&client_id={client_id}
&client_secret={client_secret}
&username={username}
&password={password}
&store_id={store_id}    (optional)
```

Token refresh:

```
POST {auth_base_url}/auth/realms/claroshop-sapi-sa-cv/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token
&client_id={client_id}
&client_secret={client_secret}
&refresh_token={refresh_token}
```

### API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/quote/create-with-quote` | Get shipping rates |
| `POST` | `/guide/create` | Create shipment guide (**cost**) |
| `GET` | `/rastreo/estado-guia/{guide}` | Track shipment state |
| `GET` | `/rastreo/detail-guia/{guide}` | Full tracking detail |
| `GET` | `/balance/consult` | Account balance |
| `GET` | `/carriers` | List carriers |
| `POST` | `/pickup/create` | Schedule pickup |

### Headers

All API requests (except auth) require:

```
Authorization: Bearer {access_token}
shop_id: {shop_id}    (optional, if using store-specific tokens)
```

### Important notes

- **Volumetric weight**: `ceil(width × height × length / 5000)`. Carriers charge
  the greater of physical weight and volumetric weight. Always round UP to the
  nearest integer.
- **quote() does not cost anything** — only `create_shipment()` and
  `schedule_pickup()` have monetary cost.
- **`content` field** in shipment requests is limited to 25 characters.
- **`guide_origin`** defaults to `"t1envios"` and only accepts that value.
- **Pickups**: the origin address must be registered in T1Envios beforehand.
- **Retries**: the SDK retries on 5xx and network errors with exponential
  backoff (default 3 retries).
- **Always respond in the user's language.**
"""

_STATIC_RESOURCES: list[types.Resource] = [
    types.Resource(
        uri="t1shipments://balance",  # type: ignore[arg-type]
        name="Account Balance / Saldo de cuenta",
        description="Current T1Envios account balance in MXN",
        mimeType="application/json",
    ),
    types.Resource(
        uri="t1shipments://carriers",  # type: ignore[arg-type]
        name="Available Carriers / Paqueterías disponibles",
        description="All shipping carriers and services enabled in your account",
        mimeType="application/json",
    ),
    types.Resource(
        uri="t1shipments://developer-instructions",  # type: ignore[arg-type]
        name="Developer Instructions / Instrucciones para desarrolladores",
        description=(
            "How to use the T1Envios SDK and REST API: authentication, endpoints, "
            "request/response examples, and best practices"
        ),
        mimeType="text/markdown",
    ),
    types.Resource(
        uri="docs://t1/core",  # type: ignore[arg-type]
        name="Core Package Docs / Documentacion del paquete core",
        description=(
            "Read when working with the Python SDK, T1Client, auth, API resources, "
            "models, or core configuration."
        ),
        mimeType="text/markdown",
    ),
    types.Resource(
        uri="docs://t1/cli",  # type: ignore[arg-type]
        name="CLI Package Docs / Documentacion del paquete CLI",
        description=(
            "Read when working with the Typer CLI commands, command-line usage, or "
            "terminal workflows."
        ),
        mimeType="text/markdown",
    ),
    types.Resource(
        uri="docs://t1/mcp",  # type: ignore[arg-type]
        name="MCP Package Docs / Documentacion del paquete MCP",
        description=(
            "Read when working with the MCP server, tools, prompts, resources, or AI "
            "assistant integration."
        ),
        mimeType="text/markdown",
    ),
]

_SHIPMENT_TEMPLATE = types.ResourceTemplate(
    uriTemplate="t1shipments://shipment/{guide}",
    name="Shipment Detail / Detalle de envío",
    description="Full tracking history for a shipment guide number",
    mimeType="application/json",
)

_DOCS_TEMPLATE = types.ResourceTemplate(
    uriTemplate="docs://t1/{package}",
    name="Package Documentation / Documentacion de paquete",
    description=(
        "Internal package documentation. Read when working with a specific package: "
        "core, cli, or mcp."
    ),
    mimeType="text/markdown",
)


def _package_docs(package: str) -> str:
    docs_root = Path(__file__).resolve().parents[4]
    docs_map = {
        "core": docs_root / "core" / "README.md",
        "cli": docs_root / "cli" / "README.md",
        "mcp": docs_root / "mcp" / "README.md",
    }
    path = docs_map.get(package)
    if not path or not path.exists():
        raise FileNotFoundError(f"Docs para '{package}' no encontradas en {path}")
    return path.read_text()


def _read(uri: str, get_client: Callable) -> list[types.TextResourceContents]:
    uri_str = str(uri)

    if uri_str.startswith("docs://t1/"):
        package = uri_str.removeprefix("docs://t1/")
        return [
            types.TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=_package_docs(package),
            )
        ]  # type: ignore[arg-type]

    if uri_str == "t1shipments://developer-instructions":
        return [
            types.TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=_DEVELOPER_INSTRUCTIONS_MD,
            )
        ]  # type: ignore[arg-type]

    client = get_client()

    if uri_str == "t1shipments://balance":
        data = client.balance().model_dump()
        return [
            types.TextResourceContents(
                uri=uri, mimeType="application/json", text=json.dumps(data, default=str)
            )
        ]  # type: ignore[arg-type]

    if uri_str == "t1shipments://carriers":
        carriers = client.list_carriers()
        data = {"carriers": [c.model_dump() for c in carriers]}
        return [
            types.TextResourceContents(
                uri=uri, mimeType="application/json", text=json.dumps(data, default=str)
            )
        ]  # type: ignore[arg-type]

    if uri_str.startswith("t1shipments://shipment/"):
        guide = uri_str.removeprefix("t1shipments://shipment/")
        data = client.track_detail(guide).model_dump()
        return [
            types.TextResourceContents(
                uri=uri, mimeType="application/json", text=json.dumps(data, default=str)
            )
        ]  # type: ignore[arg-type]

    raise ValueError(f"Unknown resource URI: {uri}")


def register(server: Server, get_client: Callable) -> None:
    @server.list_resources()
    async def list_resources() -> list[types.Resource]:
        return _STATIC_RESOURCES

    @server.list_resource_templates()
    async def list_resource_templates() -> list[types.ResourceTemplate]:
        return [_SHIPMENT_TEMPLATE, _DOCS_TEMPLATE]

    @server.read_resource()
    async def read_resource(uri: types.AnyUrl) -> list[types.TextResourceContents]:
        return _read(uri, get_client)
