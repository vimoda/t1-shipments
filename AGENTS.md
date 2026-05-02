# AGENTS.md

## Commands

```bash
uv sync --extra dev          # install deps (including dev)
uv run pytest tests/ -v      # run all tests (coverage enabled by default)
uv run pytest tests/test_auth.py::test_login_success -v  # single test
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

## Architecture

- **Dual-use**: SDK (`T1Client`) and CLI (`typer` app at `t1envios.cli.app:app`)
- **Two base URLs** in `Endpoints` (`config.py`): `base_url` for business endpoints, `auth_base_url` for Keycloak auth. Override both together.
- **ENV_PRESETS** in `core/config.py`: `"dev"` and `"prod"` sets. Default is `dev`.
- **Auth flow**: `Authenticator` auto-refreshes tokens expiring within 60s. On 401, `BaseResource` retries once.
- **Token storage**: `HybridStorage` tries `keyring` first, falls back to `~/.t1envios/credentials.json` (chmod 0600).
- **Retries**: `BaseResource` retries on 5xx and network errors with exponential backoff (default 3 retries).

## Testing

- Uses `pytest-httpx` (`httpx_mock` fixture) to mock HTTP calls
- `conftest.py` `client` fixture pre-loads a valid token via `InMemoryStorage` to skip login flow
- JSON fixtures in `tests/fixtures/responses/`
- **CLI tests**: patch **module-level** names (e.g., `t1envios.cli.balance_cmd.T1Client`), not source module
- **CLI modules require top-level imports** — lazy imports break `@patch` in tests
- `pythonpath` includes `"tests"` (see `pyproject.toml`)

## Adding endpoints

1. Add path to `Endpoints` in `core/config.py`
2. Create `core/api/<resource>.py` extending `BaseResource`
3. Add method to `T1Client` in `core/client.py`
4. Add model to `core/models/` if needed
5. Add CLI command in `cli/<cmd>.py` (top-level imports required)
6. Register command in `cli/app.py`

## Config

- `pyproject.toml`: ruff (line-length 100, select E/F/I/UP/B), mypy (strict, py311), pytest (`--cov=t1envios` by default)
- `pydantic-settings` with `T1_` prefix or `.env` file
- `T1Client.from_settings()` builds client from env
