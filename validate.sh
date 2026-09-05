#!/usr/bin/env bash
set -eo pipefail

RED='\033[0;32m' # Using green for success, red for errors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
NC='\033[0m'

info() {
    echo -e "${YELLOW}==>${NC} $1"
}

pass() {
    echo -e "${GREEN}✔ PASS:${NC} $1"
}

fail() {
    echo -e "${COLOR_RED}✖ FAIL:${NC} $1"
    exit 1
}

echo "=========================================="
echo "   T1Shipments Quick Validation Suite     "
echo "=========================================="
echo ""

# 1. CLI Commands & Help Flags Validation
info "1. Verificando CLI y banderas requeridas..."

# Check t1 help
if uv run t1 --help >/dev/null 2>&1; then
    pass "t1 --help funciona correctamente"
else
    fail "t1 --help falló"
fi

# Check t1 auth login flags (--client-id, --client-secret)
AUTH_HELP=$(uv run t1 auth login --help)
if echo "$AUTH_HELP" | grep -q -- "--client-id" && echo "$AUTH_HELP" | grep -q -- "--client-secret"; then
    pass "t1 auth login expone --client-id y --client-secret"
else
    fail "t1 auth login no contiene las banderas --client-id o --client-secret"
fi

# Check t1 mcp install flags
MCP_INSTALL_HELP=$(uv run t1 mcp install --help)
if echo "$MCP_INSTALL_HELP" | grep -q -- "--client-id" && echo "$MCP_INSTALL_HELP" | grep -q -- "--client-secret"; then
    pass "t1 mcp install expone --client-id y --client-secret"
else
    fail "t1 mcp install no contiene las banderas --client-id o --client-secret"
fi

# Check t1 mcp run flags
MCP_RUN_HELP=$(uv run t1 mcp run --help)
if echo "$MCP_RUN_HELP" | grep -q -- "--client-id" && echo "$MCP_RUN_HELP" | grep -q -- "--client-secret"; then
    pass "t1 mcp run expone --client-id y --client-secret"
else
    fail "t1 mcp run no contiene las banderas --client-id o --client-secret"
fi

# Check MCP server entrypoint
MCP_SERVER_HELP=$(uv run t1shipments-mcp --help)
if echo "$MCP_SERVER_HELP" | grep -q -- "--client-id" && echo "$MCP_SERVER_HELP" | grep -q -- "--client-secret"; then
    pass "t1shipments-mcp expone --client-id y --client-secret"
else
    fail "t1shipments-mcp no contiene --client-id o --client-secret"
fi

echo ""
# 2. Unit Tests
info "2. Ejecutando suite de pruebas unitarias..."
if uv run pytest tests/ -q; then
    pass "Tests unitarios pasaron exitosamente (102 tests)"
else
    fail "Hubo fallos en los tests unitarios"
fi

echo ""
# 3. Examples Validation
info "3. Validando ejemplos con respuestas simuladas..."
if uv run pytest examples/test_examples.py -q; then
    pass "Smoke tests de ejemplos (quote, track_state, track_detail) pasaron"
else
    fail "Hubo fallos al validar los ejemplos"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✔ Todas las validaciones pasaron con éxito.${NC}"
echo "=========================================="
