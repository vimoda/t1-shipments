# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install deps (including dev)
uv sync --extra dev

# Run all tests
uv run pytest tests/ -v

# Run single test file
uv run pytest tests/test_auth.py -v

# Run single test
uv run pytest tests/test_auth.py::test_login_success -v

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy src/

# CLI (after install)
uv run t1 --help
uv run t1 auth login
uv run t1 balance
uv run t1 quote --from-zip 02719 --to-zip 40900 --weight 1 --width 10 --height 10 --length 10 --package-value 500  --packages 1

uv run t1 create-shipment \
  --quote-id <TOKEN_FROM_QUOTE> \
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

uv run t1 trackdetail --guide "1373188795"
uv run t1 trackstate --guide "1373188795"

# Para que el pickup sea aceptado debe de estar registrada la dirección en T1, como dirección de Origen.
uv run t1 pickup \
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
```

## Architecture

### Dual-use design
The library works both as an importable SDK and as a CLI. `T1Client` is the single entry point for programmatic use; `cli/` wraps it with Typer commands for terminal use.

### URL routing — two base URLs
`Endpoints` (in `config.py`) holds **two** base URLs:
- `base_url` → all shipment/business endpoints (`url()` method)
- `auth_base_url` → Keycloak authentication server (`auth_url()` method)

`Authenticator` calls `endpoints.auth_url(...)` for login/refresh; all resource classes call `endpoints.url(...)` for business calls. When overriding URLs as SDK user, set both fields on `Endpoints`.

### Auth flow
`Authenticator` (`auth/authenticator.py`) manages the full lifecycle:
1. `login()` — POST client_id + client_secret + optional user/pass to `auth_base_url`
2. `ensure_valid()` — called by `BaseResource.request()` before every HTTP call; refreshes if token expires within 60s
3. `refresh()` — uses refresh_token; falls back to `login()` on failure
4. On HTTP 401 — `BaseResource` retries once after refresh before raising `AuthError`

### Token persistence
`HybridStorage` tries `keyring` first; falls back to `~/.t1envios/credentials.json` (chmod 0600 on POSIX). Both implement the `TokenStorage` protocol. Pass a custom `token_storage=` to `T1Client` to override (e.g., `InMemoryStorage` in tests).

### Config
- **CLI** reads `Settings` via `pydantic-settings` from env vars prefixed `T1_` or `.env` file. `T1Client.from_settings()` builds the client from it.
- **SDK** — pass params directly to `T1Client(...)`. `Endpoints` fields can be set individually via `set_*` methods or constructor kwargs.

### Adding a new endpoint
1. Add path field to `Endpoints` in `config.py`
2. Create `src/t1envios/api/<resource>.py` extending `BaseResource`
3. Add method to `T1Client`
4. Add model to `models/` if needed
5. Add CLI command in `cli/<cmd>.py` (top-level imports required — lazy imports break `@patch` in tests)
6. Register command in `cli/main.py`

### Testing pattern
Tests use `pytest-httpx` (`httpx_mock` fixture) to intercept HTTP calls. The `conftest.py` `client` fixture pre-loads a valid token via `InMemoryStorage` so tests skip the login flow. JSON fixtures live in `tests/fixtures/responses/`.

CLI tests use `typer.testing.CliRunner` with `unittest.mock.patch` — patch the **module-level** name (e.g., `t1envios.cli.balance_cmd.T1Client`), not the source module.
