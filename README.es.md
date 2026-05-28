# T1Shipments

> **Aviso:** Este es un SDK no oficial, construido por la comunidad. No está afiliado ni respaldado por T1Envios.

SDK de Python, CLI y Servidor MCP para la API de [T1Envios](https://t1envios.com). Cotiza envíos, genera guías, programa recolecciones y rastrea paquetes.

[Read in English](README.md)

| Herramienta | Paquete | Descripción |
|-------------|---------|-------------|
| SDK (`T1Client`) | `t1-shipments-core` | SDK programático de Python |
| CLI (`t1`) | `t1-shipments-cli` | Interfaz de terminal |
| Servidor MCP | `t1-shipments-mcp` | Servidor MCP para agentes de IA |

---

## SDK (`t1-shipments-core`)

El SDK provee `T1Client` para acceso programático a la API de T1Envios.

### Instalación

```bash
# Desde GitHub (sin clonar)
pip install "t1-shipments-core @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/core"

# Desde PyPI (cuando se publique)
pip install t1-shipments-core
uv add t1-shipments-core

# Desde el script automático
curl -fsSL https://raw.githubusercontent.com/vimoda/t1-shipments/main/install.sh | bash -s core

# Desde el código fuente (clonar)
git clone https://github.com/vimoda/t1-shipments
cd t1-shipments
uv sync
```

### Uso

```python
from t1shipments.core.client import T1Client
from t1shipments.core.models.quote import QuoteRequest
from t1shipments.core.models.shipment import ShipmentRequest
from t1shipments.core.models.balance import Balance
from t1shipments.core.models.carrier import Carrier
from t1shipments.core.models.tracking import TrackingResponse, TrackingState
from t1shipments.core.exceptions import SessionExpiredError, ApiError, InsufficientBalanceError
```

#### Autenticación

```python
# Inicia sesión con usuario y contraseña (requerido para todas las operaciones)
client = T1Client(client_id="...", client_secret="...")
client.login("username", "password")

# O usa el context manager
with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")
    # ... usa el cliente
```

#### Cotizar y Crear Guía

```python
with T1Client(client_id="...", client_secret="...", shop_id="...") as client:
    client.login("username", "password")

    # 1. Cotizar envío
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

    # Elige una tarifa por token
    quote_token = response.detail[0]["token"]

    # 2. Crear guía
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

    print(f"Número de guía: {shipment.tracking_number}")

    # 3. Descargar etiqueta PDF
    pdf = client.download_label(shipment.label_url)
    with open("etiqueta.pdf", "wb") as f:
        f.write(pdf)
```

#### Rastreo

```python
with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")

    # Estado actual + historial
    state = client.track_state("1373188795")
    print(state.current_status)
    for event in state.history:
        print(event.date, event.description)

    # Detalle completo de la paquetería
    detail = client.track_detail("1373188795")
    print(detail.detail)
```

#### Saldo y Paqueterías

```python
with T1Client(client_id="...", client_secret="...") as client:
    client.login("username", "password")

    balance = client.balance()
    print(f"Saldo: {balance.amount} {balance.currency}")

    carriers = client.list_carriers()
    for c in carriers:
        print(c.name, c.services)
```

#### Programar Recolección

> La dirección de origen debe estar registrada en T1Envios antes de programar una recolección.

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
    print(f"Recolección programada: {pickup}")
```

#### Almacenamiento de Token

Por defecto `T1Client` usa almacenamiento en memoria (el token se pierde al salir del proceso). Para sesiones persistentes usa `HybridStorage`, que intenta `keyring` primero y falla a `~/.t1shipments/credentials.json`:

```python
from t1shipments.core.auth.storage import HybridStorage, InMemoryStorage

# Persistente (por defecto en CLI)
client = T1Client(..., token_storage=HybridStorage())

# En memoria — útil para scripts, serverless o pruebas
client = T1Client(..., token_storage=InMemoryStorage())
```

#### Cargar Config desde el Entorno

```python
# Lee T1_CLIENT_ID, T1_CLIENT_SECRET, T1_SHOP_ID, etc. de env / .env
with T1Client.from_settings() as client:
    client.login("username", "password")
    print(client.balance())
```

#### Manejo de Excepciones

```python
from t1shipments.core.exceptions import SessionExpiredError, ApiError, InsufficientBalanceError

with T1Client(client_id="...", client_secret="...") as client:
    try:
        client.login("username", "password")
        balance = client.balance()
    except SessionExpiredError:
        # Token expiró y falló el refresh — re-login requerido
        client.login("username", "password")
    except InsufficientBalanceError:
        print("Saldo insuficiente para crear el envío")
    except ApiError as e:
        print(f"Error de API {e.status}: {e}")
```

Jerarquía de excepciones:

```
T1Error
├── AuthError
│   ├── SessionExpiredError   # sin sesión válida / refresh falló
│   └── RefreshExpiredError   # el refresh token mismo expiró
├── ApiError                  # respuesta HTTP no-2xx
├── RateLimitError            # HTTP 429
├── StorageError              # backend de almacenamiento no disponible
├── ConfigError               # configuración faltante o inválida
├── QuotaExceededError        # cuota de cuenta excedida
├── InvalidAddressError       # validación de dirección falló
├── CarrierUnavailableError   # paquetería o servicio no disponible
└── InsufficientBalanceError  # saldo de cuenta insuficiente
```

---

## CLI (`t1-shipments-cli`)

El CLI provee el comando `t1` para interactuar con T1Envios desde la terminal.

### Instalación

```bash
# Desde GitHub (sin clonar)
pip install "t1-shipments-cli @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/cli"

# Desde PyPI (cuando se publique)
pip install t1-shipments-cli
uv tool install t1-shipments-cli

# Ejecutar sin instalar (via uvx)
uvx --from "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/cli" t1 --help

# Desde el script automático
curl -fsSL https://raw.githubusercontent.com/vimoda/t1-shipments/main/install.sh | bash -s cli

# Desde el código fuente (clonar)
git clone https://github.com/vimoda/t1-shipments
cd t1-shipments
uv sync
uv run t1 --help
```

### Uso

```bash
# Autenticación
t1 auth login      # Pide usuario y contraseña
t1 auth logout     # Limpia el token almacenado
t1 auth status     # Muestra el estado del token

# Cotizar
t1 quote \
  --from-zip 02719 --to-zip 40900 \
  --weight 1 --width 10 --height 10 --length 10 \
  --package-value 500 --packages 1

# Crear Guía
t1 create-shipment \
  --quote-id <TOKEN_DE_COTIZACION> \
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

# Descargar Etiqueta
t1 label --guide-link "https://..." --output etiqueta.pdf

# Rastrear Guía
t1 trackstate  --guide 1373188795   # Estado actual + historial
t1 trackdetail --guide 1373188795   # Detalle completo de paquetería

# Programar Recolección
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

# Otros Comandos
t1 balance       # Saldo de cuenta
t1 carriers      # Lista paqueterías disponibles
t1 mcp run       # Inicia el servidor MCP
```

> La dirección de origen debe estar registrada en T1Envios antes de programar una recolección.

---

## Servidor MCP (`t1-shipments-mcp`)

El servidor MCP permite que agentes de IA (Claude Desktop, opencode, Cursor, etc.) interactúen con T1Envios a través del [Model Context Protocol](https://modelcontextprotocol.io).

### Instalación

```bash
# Desde GitHub (sin clonar)
pip install "t1-shipments-mcp @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp"

# Desde PyPI (cuando se publique)
pip install t1-shipments-mcp
uv tool install t1-shipments-mcp

# Ejecutar sin instalar (via uvx)
uvx --from "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp" t1shipments-mcp

# Desde el script automático
curl -fsSL https://raw.githubusercontent.com/vimoda/t1-shipments/main/install.sh | bash -s mcp

# Desde el código fuente (clonar)
git clone https://github.com/vimoda/t1-shipments
cd t1-shipments
uv sync
uv run t1shipments-mcp
```

### Configuración del cliente MCP

Una vez instalado `t1-shipments-mcp`, configura tu cliente MCP con el bloque JSON que corresponda a tu método de instalación.

#### Via `uvx` (sin instalación — ejecuta desde GitHub bajo demanda)

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp",
        "t1shipments-mcp"
      ],
      "env": {
        "T1_CLIENT_ID":     "${T1_CLIENT_ID}",
        "T1_CLIENT_SECRET": "${T1_CLIENT_SECRET}",
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

Apuntar a un tag / commit / rama específico:

```json
"args": ["--from", "git+https://github.com/vimoda/t1-shipments@v0.1.0#subdirectory=packages/mcp", "t1shipments-mcp"]
```

#### Via `uv` — desde un repositorio clonado

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uv",
      "args": [
        "--directory",
        "/ruta/a/t1-shipments",
        "run",
        "python",
        "-m",
        "t1shipments.mcp.server"
      ],
      "env": {
        "T1_CLIENT_ID":     "${T1_CLIENT_ID}",
        "T1_CLIENT_SECRET": "${T1_CLIENT_SECRET}",
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

#### Via binario instalado (`pip install` / `uv tool install`)

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "t1shipments-mcp",
      "env": {
        "T1_CLIENT_ID":     "${T1_CLIENT_ID}",
        "T1_CLIENT_SECRET": "${T1_CLIENT_SECRET}",
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

#### Ubicación de archivos de configuración

| Cliente | Archivo |
|---------|---------|
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Code | `.claude/mcp_config.json` en tu proyecto |

#### Probar la instalación

```bash
# Con MCP Inspector (UI interactiva)
npx @modelcontextprotocol/inspector uvx --from "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp" t1shipments-mcp

# O si instalaste localmente
npx @modelcontextprotocol/inspector t1shipments-mcp
```

### Auth y Ciclo de Vida del Token

El servidor mantiene una **única instancia de `T1Client`** durante toda la sesión MCP. Antes de cada llamada a herramienta ejecuta `ensure_valid()`:

1. Token válido → procede inmediatamente.
2. Token expira en menos de 60 s → **refresca** usando `refresh_token` (sin re-login).
3. Sin sesión / refresh expirado → **re-login** con `T1_USERNAME`/`T1_PASSWORD`.

No se requiere intervención manual en ningún momento.

### Pruebas con MCP Inspector

```bash
# requiere mcp[cli] — ya incluido en el extra mcp
uv run mcp dev src/t1shipments/mcp/server.py
```

Abre un inspector web local donde puedes invocar herramientas interactivamente.

### Iniciar el Servidor (producción)

```bash
t1 mcp run
# o
python -m t1shipments.mcp.server
```

### Herramientas Disponibles

| Herramienta | Descripción |
|-------------|-------------|
| `quote_shipment` | Obtén tarifas de envío disponibles para un paquete. Devuelve una lista de opciones de paquetería con precios. Llama esto SIEMPRE antes de `create_shipment`. |
| `create_shipment` | Crea un envío usando un token de cotización de `quote_shipment`. |
| `track_guide` | Rastrea un envío por número de guía. Devuelve estado actual, fecha estimada de entrega e historial. |
| `get_balance` | Obtén el saldo actual de la cuenta en MXN. |
| `list_carriers` | Lista todas las paqueterías y servicios disponibles en tu cuenta T1Envios. |
| `schedule_pickup` | Programa una recolección para un envío existente. |

### Esquemas de Entrada de Herramientas MCP

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

## Configuración

Establece las variables de entorno (o usa un archivo `.env`):

```env
T1_CLIENT_ID=tu_client_id
T1_CLIENT_SECRET=tu_client_secret
T1_BASE_URL=https://api.t1envios.com
T1_SHOP_ID=tu_tienda_id
```

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `T1_CLIENT_ID` | Sí | — | ID de cliente Keycloak |
| `T1_CLIENT_SECRET` | Sí | — | Secreto de cliente Keycloak |
| `T1_BASE_URL` | No | `https://api.t1envios.com` | URL base de la API |
| `T1_SHOP_ID` | No | — | ID de comercio — se envía como `comercio_id` |
| `T1_USERNAME` | No | — | Correo de cuenta T1Envios (auto-login en MCP) |
| `T1_PASSWORD` | No | — | Contraseña de cuenta T1Envios |
| `T1_ENV` | No | `dev` | `dev` o `prod` |
| `T1_COMERCE_ID` | No | — | Identificador interno de comercio |
| `T1_LOG_LEVEL` | No | — | Nivel de logging (ej: `DEBUG`) |
| `T1_TIMEOUT` | No | `30.0` | Timeout HTTP en segundos |

---

## Desarrollo

```bash
uv sync --extra dev
uv run pytest tests/ -v
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

## Licencia

MIT
