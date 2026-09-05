# t1-shipments-cli

> **Aviso:** Esta es una CLI no oficial, creada por la comunidad. No está afiliada ni respaldada por T1Envios.

Interfaz de línea de comandos para la API de envíos de [T1Envios](https://t1envios.com). Construida con [Typer](https://typer.tiangolo.com/).

[Read in English](README.md)

---

## Instalación

```bash
pip install "t1-shipments-cli @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/cli"
```

## Uso

Todos los comandos están bajo el ejecutable `t1`:

```bash
t1 --help
```

### Autenticación

```bash
# Pasa client-id y client-secret como argumentos (o ingrésalos interactivamente cuando se te soliciten)
t1 auth login --client-id TU_CLIENT_ID --client-secret TU_CLIENT_SECRET --username usuario@example.com
t1 auth status
t1 auth refresh
t1 auth logout
```

### Operaciones principales

| Comando | Descripción | Ejemplo |
|---|---|---|
| `t1 quote` | Cotizar tarifas de envío | `t1 quote --from-zip 02719 --to-zip 40900 --weight 1` |
| `t1 create-shipment` | Crear guía de envío | `t1 create-shipment --quote-id TOKEN --content "Ropa" --origin-name Juan ...` |
| `t1 trackdetail` | Rastreo detallado | `t1 trackdetail --guide ABC123` |
| `t1 trackstate` | Estado + historial | `t1 trackstate --guide ABC123` |
| `t1 balance` | Saldo disponible | `t1 balance` |
| `t1 carriers` | Listar transportistas | `t1 carriers` |
| `t1 pickup` | Agendar recolección | `t1 pickup --carrier REDPACK --contact-name Juan ...` |
| `t1 label` | Descargar etiqueta PDF | `t1 label --guide-link LINK -o label.pdf` |
| `t1 mcp install` | Instalar MCP en Claude Desktop | `t1 mcp install --client-id TU_ID --client-secret TU_SECRET` |
| `t1 mcp run` | Iniciar servidor MCP stdio | `t1 mcp run --client-id TU_ID --client-secret TU_SECRET` |

### Entorno

Opcional: Define `T1_USERNAME`, `T1_PASSWORD`, `T1_SHOP_ID`, `T1_ENV` (`dev`/`prod`), etc.
Las credenciales (`client-id` y `client-secret`) se pasan como parámetros a `t1 auth login` y se almacenan de forma segura en el llavero/archivo local.

### Salida

Todos los comandos usan `rich` para salida formateada. Tablas para listados, colores para rastreo.

## Desarrollo

```bash
uv sync --extra dev
uv run pytest tests/
```

## Licencia

MIT
