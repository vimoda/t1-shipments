#!/usr/bin/env bash
set -euo pipefail

REPO="vimoda/t1-shipments"
BRANCH="main"
GITHUB="https://github.com/$REPO"

# ── helpers ──────────────────────────────────────────────────────────────
info()  { printf "\033[1;34m➜\033[0m %s\n" "$*"; }
ok()    { printf "\033[1;32m✓\033[0m %s\n" "$*"; }
err()   { printf "\033[1;31m✗\033[0m %s\n" "$*" >&2; }
die()   { err "$*"; exit 1; }

# ── detect / install uv ──────────────────────────────────────────────────
ensure_uv() {
    if command -v uv &>/dev/null; then
        ok "uv ya está instalado ($(uv --version))"
    else
        info "Instalando uv…"
        curl -fsSL https://astral.sh/uv/install.sh | bash
        export PATH="$HOME/.local/bin:$PATH"
        command -v uv &>/dev/null || die "No se pudo instalar uv"
        ok "uv instalado"
    fi
}

# ── MCP server config JSON ───────────────────────────────────────────────
mcp_json() {
    cat <<'EOF'
{
  "mcpServers": {
    "t1shipments": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/vimoda/t1-shipments#subdirectory=packages/mcp",
        "t1shipments-mcp",
        "--client-id",
        "<tu_client_id>",
        "--client-secret",
        "<tu_client_secret>"
      ],
      "env": {
        "T1_BASE_URL":      "https://api.t1envios.com",
        "T1_SHOP_ID":       "<tu_shop_id>"
      }
    }
  }
}
EOF
}

cli_json() {
    cat <<'EOF'
{
  "CLI instalado correctamente",
  "Uso: t1 --help"
}
EOF
}

# ── install ───────────────────────────────────────────────────────────────
install_mcp() {
    ensure_uv
    info "Instalando t1-shipments-mcp desde GitHub…"
    uv tool install --from "git+$GITHUB#subdirectory=packages/mcp" t1-shipments-mcp
    ok "t1-shipments-mcp instalado"
    echo ""
    echo "──────────────────────────────────────────────────────"
    echo "  Agrega este bloque a tu config de MCP cliente:"
    echo "──────────────────────────────────────────────────────"
    mcp_json
}

install_core() {
    ensure_uv
    info "Instalando t1-shipments-core desde GitHub…"
    uv tool install --from "git+$GITHUB#subdirectory=packages/core" t1-shipments-core
    ok "t1-shipments-core instalado"
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo "  Uso: from t1shipments.core.client import T1Client"
    echo "───────────────────────────────────────────────────────────"
}

install_cli() {
    ensure_uv
    info "Instalando t1-shipments-cli desde GitHub…"
    uv tool install --from "git+$GITHUB#subdirectory=packages/cli" t1-shipments-cli
    ok "t1-shipments-cli instalado"
    echo ""
    echo "──────────────────────────────────────────────────────"
    echo "  Ejecuta:  t1 --help"
    echo "──────────────────────────────────────────────────────"
}

install_all() {
    install_core
    echo ""
    install_cli
    echo ""
    install_mcp
}

# ── menu interactivo ────────────────────────────────────────────────────
menu() {
    echo "¿Qué paquete deseas instalar?"
    echo "  1) t1-shipments-core  — SDK programático"
    echo "  2) t1-shipments-cli   — CLI de terminal"
    echo "  3) t1-shipments-mcp   — Servidor MCP para agentes de IA"
    echo "  4) Todos"
    echo ""
    read -rp "Opción [1-4]: " choice </dev/tty
    case "$choice" in
        1) install_core ;;
        2) install_cli ;;
        3) install_mcp ;;
        4) install_all ;;
        *) die "Opción inválida: $choice" ;;
    esac
}

# ── main ─────────────────────────────────────────────────────────────────
case "${1:-}" in
    core) install_core ;;
    cli) install_cli ;;
    mcp) install_mcp ;;
    all) install_all ;;
    "")  menu ;;
    *)   die "Uso: $0 {core|cli|mcp|all}" ;;
esac
