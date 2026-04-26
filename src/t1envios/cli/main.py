from __future__ import annotations

import typer

from . import auth_cmd, mcp_cmd, track_detail_cmd, track_state_cmd
from . import balance_cmd, carriers_cmd, pickup_cmd, quote_cmd, shipment_cmd

app = typer.Typer(
    name="t1",
    help="T1Envios SDK — cotiza, rastrea y crea guías desde la terminal.",
    no_args_is_help=True,
)

app.add_typer(auth_cmd.app, name="auth")
app.add_typer(mcp_cmd.app, name="mcp")
app.command("quote")(quote_cmd.run)
app.command("trackdetail")(track_detail_cmd.run)
app.command("trackstate")(track_state_cmd.run)
app.command("balance")(balance_cmd.run)
app.command("pickup")(pickup_cmd.run)
app.command("carriers")(carriers_cmd.run)
app.command("create-shipment")(shipment_cmd.run)


if __name__ == "__main__":
    app()
