# t1-shipments-core

> **Aviso:** Este es un SDK no oficial, creado por la comunidad. No está afiliado ni respaldado por T1Envios.

SDK en Python para la API de envíos de [T1Envios](https://t1envios.com). Proporciona `T1Client` con autenticación, cotización, creación de guías, rastreo, saldo, transportistas y agendado de recolecciones.

[Read in English](README.md)

---

## Instalación

```bash
pip install "t1-shipments-core @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/core"
# o desde el código fuente
uv sync
```

## Inicio rápido

```python
from t1shipments.core.client import T1Client
from t1shipments.core.models.quote import QuoteRequest
from t1shipments.core.models.shipment import ShipmentRequest

with T1Client.from_settings() as client:
    client.login("usuario@example.com", "password")

    # Cotizar (gratuito)
    cotizacion = client.quote(QuoteRequest(
        origin_postal_code="02719",
        destination_postal_code="40900",
        weight=1, width=30, height=20, length=15,
        insurance=False,
    ))
    token = cotizacion.detail[0]["token"]

    # Crear guía (con costo)
    guia = client.create_shipment(ShipmentRequest(
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

## API pública

### `T1Client`

| Método | Descripción | Costo |
|---|---|---|
| `login(username, password, store_id?)` | Autenticación vía Keycloak | No |
| `quote(req: QuoteRequest)` | Cotizar tarifas de envío | No |
| `create_shipment(req: ShipmentRequest)` | Generar guía de envío | Sí |
| `track_state(guide)` | Estado actual + historial | No |
| `track_detail(guide)` | Detalle completo de rastreo | No |
| `balance()` | Saldo disponible en MXN | No |
| `list_carriers()` | Listar transportistas/servicios | No |
| `schedule_pickup(req: PickupRequest)` | Agendar recolección | Sí |
| `download_label(guide_link)` | Descargar PDF de etiqueta | No |
| `inject_token(access, refresh?, expires?)` | Cargar token administrado externamente | No |

### Configuración e inicialización

Pasa `client_id` y `client_secret` directamente como parámetros de entrada, o cárgalos desde una sesión almacenada:

```python
# Parámetros directos (recomendado para scripts e integraciones):
client = T1Client(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)

# O mediante from_settings (recibe argumentos o los toma de la sesión almacenada):
client = T1Client.from_settings(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)
```

### Almacenamiento de tokens

| Almacenamiento | Comportamiento |
|---|---|
| `InMemoryStorage` | Default — se pierde al salir del proceso |
| `HybridStorage()` | Intenta `keyring` → fallback a `~/.t1shipments/credentials.json` |
| `FileStorage(path?)` | Solo archivo JSON |

### Excepciones

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

## Modelos

Todos los modelos son `BaseModel` de Pydantic v2. Se importan desde `t1shipments.core.models`:

- `QuoteRequest`, `QuoteResponse`, `Rate`
- `ShipmentRequest`, `Shipment`
- `TrackingResponse`, `TrackingState`
- `PickupRequest`, `Pickup`
- `Balance`, `Carrier`

## Flujo de autenticación

1. `login()` → `POST {auth_url}/protocol/openid-connect/token` con payload `application/x-www-form-urlencoded`.
2. El token se refresca automáticamente cuando expira en menos de 60 s (`auto_refresh=True` por defecto).
3. En caso de 401, el SDK refresca una vez y reintenta.

## Desarrollo

```bash
uv sync
uv run pytest tests/
uv run ruff check src/
uv run mypy src/
```

## Licencia

MIT
