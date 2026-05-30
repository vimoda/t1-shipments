# t1-shipments-mcp

> **Disclaimer:** This is an unofficial, community-built MCP server. Not affiliated with or endorsed by T1Envios.

[MCP](https://modelcontextprotocol.io) (Model Context Protocol) server for the [T1Envios](https://t1envios.com) shipping API. Enables AI assistants (Claude Desktop, Cursor, etc.) to quote, create shipments, track packages, and manage carriers.

[Leer en español](README.es.md)

---

## Installation

```bash
pip install "t1-shipments-mcp @ git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp"
```

## Quick Start

```bash
# Set credentials
export T1_CLIENT_ID="your-client-id"
export T1_CLIENT_SECRET="your-client-secret"
export T1_USERNAME="user@example.com"   # optional auto-login
export T1_PASSWORD="your-password"      # optional auto-login

# Run the server
t1shipments-mcp
```

## Configuration for AI Assistants

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/t1-shipments", "t1shipments-mcp"],
      "env": {
        "T1_CLIENT_ID": "your-client-id",
        "T1_CLIENT_SECRET": "your-client-secret",
        "T1_USERNAME": "user@example.com",
        "T1_PASSWORD": "your-password",
        "T1_SHOP_ID": "optional-commerce-id"
      }
    }
  }
}
```

Or install via CLI:

```bash
t1 mcp install
```

### Cursor / opencode

```json
{
  "mcpServers": {
    "t1shipments": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/t1-shipments", "t1shipments-mcp"],
      "env": { "T1_CLIENT_ID": "...", "T1_CLIENT_SECRET": "..." }
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `quote` | Get shipping rates |
| `create_shipment` | Create a shipping guide |
| `track_state` | Current status + history |
| `track_detail` | Full carrier tracking detail |
| `balance` | Account balance in MXN |
| `list_carriers` | List enabled carriers |
| `schedule_pickup` | Schedule a pickup |
| `download_label` | Download label PDF |
| `auth_login` | Authenticate user |
| `auth_status` | Show token status |

## Resources

| URI | Description |
|---|---|
| `t1://carriers` | List of enabled carriers + services |
| `t1://carriers/{carrier_id}` | Carrier details and available services |

## Prompts

| Prompt | Description |
|---|---|
| `quote` | Guide the user through getting a shipping quote |
| `create_shipment` | Guide the user through creating a shipment |
| `track` | Guide the user through tracking a package |
| `pickup` | Guide the user through scheduling a pickup |

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `T1_CLIENT_ID` | API client ID | — |
| `T1_CLIENT_SECRET` | API client secret | — |
| `T1_USERNAME` | Auto-login user | — |
| `T1_PASSWORD` | Auto-login password | — |
| `T1_SHOP_ID` | Commerce ID | — |
| `T1_BASE_URL` | API base URL | preset `"dev"` |
| `T1_TIMEOUT` | Request timeout (seconds) | `30` |

## License

MIT
