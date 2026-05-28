try:
    import typer  # noqa: F401
except ImportError:
    import sys

    print(
        "❌ El CLI requiere t1-shipments-cli.\n"
        "   Instala con: pip install t1-shipments-cli\n"
        "   O con uv:    uv add t1-shipments-cli",
        file=sys.stderr,
    )
    sys.exit(1)

from .app import app

__all__ = ["app"]
