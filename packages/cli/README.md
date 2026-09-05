# t1-shipments-cli

> **Disclaimer:** This is an unofficial, community-built CLI. Not affiliated with or endorsed by T1Envios.

Command-line interface for the [T1Envios](https://t1envios.com) shipping API. Built with [Typer](https://typer.tiangolo.com/).

[Leer en español](README.es.md)

---

## Installation

```bash
pip install "t1-shipments-cli @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/cli"
```

## Usage

All commands are under the `t1` executable:

```bash
t1 --help
```

### Authentication

```bash
# Provide client-id and client-secret as arguments (or enter interactively when prompted)
t1 auth login --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET --username user@example.com
t1 auth status
t1 auth refresh
t1 auth logout
```

### Core operations

| Command | Description | Example |
|---|---|---|
| `t1 quote` | Get shipping rates | `t1 quote --from-zip 02719 --to-zip 40900 --weight 1` |
| `t1 create-shipment` | Create a shipping guide | `t1 create-shipment --quote-id TOKEN --content "Ropa" --origin-name Juan ...` |
| `t1 trackdetail` | Full tracking info | `t1 trackdetail --guide ABC123` |
| `t1 trackstate` | Status + history | `t1 trackstate --guide ABC123` |
| `t1 balance` | Account balance | `t1 balance` |
| `t1 carriers` | List carriers | `t1 carriers` |
| `t1 pickup` | Schedule pickup | `t1 pickup --carrier REDPACK --contact-name Juan ...` |
| `t1 label` | Download label PDF | `t1 label --guide-link LINK -o label.pdf` |
| `t1 mcp install` | Install MCP in Claude Desktop | `t1 mcp install --client-id YOUR_ID --client-secret YOUR_SECRET` |
| `t1 mcp run` | Start MCP stdio server | `t1 mcp run --client-id YOUR_ID --client-secret YOUR_SECRET` |

### Environment

Optional: Set `T1_USERNAME`, `T1_PASSWORD`, `T1_SHOP_ID`, `T1_ENV` (`dev`/`prod`), etc.
Credentials (`client-id` and `client-secret`) are passed as CLI parameters to `t1 auth login` and persisted securely in system keyring/file storage.

### Output

All commands use `rich` for formatted terminal output. Table layouts for lists; colored status for tracking.

## Development

```bash
uv sync --extra dev
uv run pytest tests/
```

## License

MIT
