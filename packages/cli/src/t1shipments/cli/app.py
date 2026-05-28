from __future__ import annotations

try:
    import typer
except ImportError as exc:
    raise ImportError(
        "CLI extras not installed. Run: pip install t1-shipments-cli"
    ) from exc

from . import auth, mcp_cmd
from .carriers import run as carriers_run
from .shipments import (
    run_balance,
    run_create_shipment,
    run_label,
    run_pickup,
    run_quote,
    run_track_detail,
    run_track_state,
)

app = typer.Typer(
    name="t1",
    help="T1Envios SDK — cotiza, rastrea y crea guías desde la terminal.",
    no_args_is_help=True,
)

app.add_typer(auth.app, name="auth")
app.add_typer(mcp_cmd.app, name="mcp")
app.command("quote")(run_quote)
app.command("trackdetail")(run_track_detail)
app.command("trackstate")(run_track_state)
app.command("balance")(run_balance)
app.command("pickup")(run_pickup)
app.command("carriers")(carriers_run)
app.command("create-shipment")(run_create_shipment)
app.command("label")(run_label)


if __name__ == "__main__":
    app()
