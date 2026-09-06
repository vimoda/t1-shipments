# Ejemplos de T1Shipments

Esta carpeta contiene scripts de ejemplo para interactuar con la plataforma T1Shipments mediante el SDK en Python.

## Requisitos previos

Instalar dependencias del proyecto:

```bash
uv sync --extra dev
```

## Modos de autenticación

1. **Sesión persistente (Recomendado):**
   Iniciá sesión una sola vez con la CLI:
   ```bash
   t1 auth login --client-id "TU_CLIENT_ID" --client-secret "TU_CLIENT_SECRET"
   ```
   Luego podés ejecutar cualquier ejemplo directamente sin pasar credenciales repetidamente:
   ```bash
   uv run python examples/quote.py
   ```

2. **Parámetros explícitos por CLI:**
   Podés pasar las credenciales en la llamada:
   ```bash
   uv run python examples/quote.py --client-id "TU_CLIENT_ID" --client-secret "TU_CLIENT_SECRET" --username "usuario@correo.com" --password "tu-password"
   ```

---

## Archivos de ejemplo

### 1. `quote.py` — Cotización paso a paso
Muestra cómo configurar una solicitud de cotización (`QuoteRequest`), listar las paqueterías disponibles y desplegar una tabla formateada con los servicios, costos y tiempos estimados de entrega.

```bash
# Con sesión activa de t1 auth login
uv run python examples/quote.py

# Con credenciales directas
uv run python examples/quote.py --client-id "ID" --client-secret "SECRET" --username "USER" --password "PASS"
```

### 2. `tracking.py` — Rastreo de envíos
Muestra cómo consultar el estado general de una guía (`track_state`) y el historial detallado de eventos de paquetería (`track_detail`).

```bash
# Con sesión activa
uv run python examples/tracking.py --guide 4399894590

# Con credenciales directas
uv run python examples/tracking.py --guide 4399894590 --client-id "ID" --client-secret "SECRET" --username "USER" --password "PASS"
```

### 3. `as_library.py` — Uso como librería SDK
Demuestra cómo inicializar `T1Client` directamente en tu propia aplicación o script pasando `client_id` y `client_secret` al constructor.

```bash
uv run python examples/as_library.py --client-id "ID" --client-secret "SECRET" --username "USER" --password "PASS"
```
