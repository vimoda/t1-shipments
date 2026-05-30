# t1-shipments-mcp

> **Aviso:** Este es un servidor MCP no oficial, creado por la comunidad. No está afiliado ni respaldado por T1Envios.

Servidor [MCP](https://modelcontextprotocol.io) (Model Context Protocol) para la API de envíos de [T1Envios](https://t1envios.com). Permite a asistentes de IA (Claude Desktop, Cursor, etc.) cotizar, crear guías, rastrear paquetes y gestionar transportistas.

[Read in English](README.md)

---

## Instalación

```bash
pip install "t1-shipments-mcp @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp"
```

## Inicio rápido

```bash
# Configura credenciales
export T1_CLIENT_ID="tu-client-id"
export T1_CLIENT_SECRET="tu-client-secret"
export T1_USERNAME="usuario@example.com"   # auto-login opcional
export T1_PASSWORD="tu-password"            # auto-login opcional

# Inicia el servidor
t1shipments-mcp
```

## Configuración para Asistentes de IA

### Claude Desktop

Agrega a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/a/t1-shipments", "t1shipments-mcp"],
      "env": {
        "T1_CLIENT_ID": "tu-client-id",
        "T1_CLIENT_SECRET": "tu-client-secret",
        "T1_USERNAME": "usuario@example.com",
        "T1_PASSWORD": "tu-password",
        "T1_SHOP_ID": "commerce-id-opcional"
      }
    }
  }
}
```

O instala vía CLI:

```bash
t1 mcp install
```

### Cursor / opencode

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/a/t1-shipments", "t1shipments-mcp"],
      "env": { "T1_CLIENT_ID": "...", "T1_CLIENT_SECRET": "..." }
    }
  }
}
```

## Herramientas

| Herramienta | Descripción |
|---|---|
| `quote` | Cotizar tarifas de envío |
| `create_shipment` | Crear guía de envío |
| `track_state` | Estado actual + historial |
| `track_detail` | Rastreo detallado |
| `balance` | Saldo disponible en MXN |
| `list_carriers` | Listar transportistas activos |
| `schedule_pickup` | Agendar recolección |
| `download_label` | Descargar etiqueta PDF |
| `auth_login` | Autenticar usuario |
| `auth_status` | Mostrar estado del token |

## Recursos

| URI | Descripción |
|---|---|
| `t1://carriers` | Lista de transportistas + servicios |
| `t1://carriers/{carrier_id}` | Detalles y servicios disponibles |

## Prompts

| Prompt | Descripción |
|---|---|
| `quote` | Guía al usuario para obtener una cotización |
| `create_shipment` | Guía al usuario para crear un envío |
| `track` | Guía al usuario para rastrear un paquete |
| `pickup` | Guía al usuario para agendar una recolección |

## Variables de Entorno

| Variable | Descripción | Default |
|---|---|---|
| `T1_CLIENT_ID` | ID del cliente API | — |
| `T1_CLIENT_SECRET` | Secreto del cliente API | — |
| `T1_USERNAME` | Usuario para auto-login | — |
| `T1_PASSWORD` | Contraseña para auto-login | — |
| `T1_SHOP_ID` | ID de comercio | — |
| `T1_BASE_URL` | URL base de la API | preset `"dev"` |
| `T1_TIMEOUT` | Timeout de peticiones (segundos) | `30` |

## Licencia

MIT
