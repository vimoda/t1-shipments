from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import mcp.types as types
from mcp.server import Server

_PROMPTS: list[types.Prompt] = [
    types.Prompt(
        name="quote",
        description="Cotiza envío / Quote shipment between two ZIP codes with sensible defaults",
        arguments=[
            types.PromptArgument(name="origin_zip", description="Código postal origen / Origin ZIP", required=True),
            types.PromptArgument(name="dest_zip", description="Código postal destino / Destination ZIP", required=True),
            types.PromptArgument(name="weight_kg", description="Peso en kg / Weight in kg", required=True),
            types.PromptArgument(name="insurance", description="¿Con seguro? true/false / Include insurance? true/false", required=False),
            types.PromptArgument(name="lang", description="Response language: es (default) or en", required=False),
        ],
    ),
    types.Prompt(
        name="ship",
        description="Crear envío con tarifa elegida / Create shipment from a selected quote_token",
        arguments=[
            types.PromptArgument(name="quote_token", description="Token de la tarifa elegida (de /quote) / Selected rate token from quote", required=True),
            types.PromptArgument(name="content", description="Contenido del paquete, máx 25 chars / Package contents, max 25 chars", required=False),
            types.PromptArgument(name="lang", description="Response language: es (default) or en", required=False),
        ],
    ),
    types.Prompt(
        name="track_status",
        description="Rastrear guía con historial / Track shipment guide with full history",
        arguments=[
            types.PromptArgument(name="guide", description="Número de guía / Guide/tracking number", required=True),
            types.PromptArgument(name="lang", description="Response language: es (default) or en", required=False),
        ],
    ),
    types.Prompt(
        name="schedule_pickup_tomorrow",
        description="Programar recolección para mañana / Schedule pickup for tomorrow with preset hours",
        arguments=[
            types.PromptArgument(name="carrier", description="Paquetería: DHL, FEDEX, UPS / Carrier name", required=True),
            types.PromptArgument(name="weight_kg", description="Peso total en kg / Total weight in kg", required=True),
            types.PromptArgument(name="lang", description="Response language: es (default) or en", required=False),
        ],
    ),
    types.Prompt(
        name="check_balance_before_ship",
        description="Verificar saldo antes de crear envío / Check balance before creating a shipment",
        arguments=[
            types.PromptArgument(name="lang", description="Response language: es (default) or en", required=False),
        ],
    ),
]


def _lang(args: dict | None) -> str:
    return (args or {}).get("lang", "es")


def _get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
    args = arguments or {}
    lang = _lang(args)

    if name == "quote":
        origin = args.get("origin_zip", "?")
        dest = args.get("dest_zip", "?")
        weight = args.get("weight_kg", "?")
        insurance = args.get("insurance", "false")
        if lang == "en":
            text = (
                f"Quote a shipment from ZIP {origin} to ZIP {dest}, {weight} kg, "
                f"insurance={'yes' if str(insurance).lower() == 'true' else 'no'}. "
                "Use these defaults if not specified: width=30cm, height=20cm, length=15cm, "
                "package_value=500 MXN, packages=1, package_type=2 (parcel). "
                "Call quote_shipment with those values and present the results as a numbered table. "
                "Columns: #, Carrier, Service, Type, Total cost, Currency, Days, Estimated delivery, "
                "Weight (kg), Volumetric weight (kg), Dimensions (cm), Quote token. "
                "Mark rows with recommended=true with ★. "
                "If insurance was requested and a rate did not apply it, show the insurance_note clearly. "
                "End with: 'Which service would you like to proceed with?'"
            )
        else:
            text = (
                f"Cotiza un envío desde el código postal {origin} al {dest}, {weight} kg, "
                f"{'con' if str(insurance).lower() == 'true' else 'sin'} seguro. "
                "Usa estos valores por defecto si no se especifican: ancho=30cm, alto=20cm, largo=15cm, "
                "valor_paquete=500 MXN, paquetes=1, tipo_paquete=2 (paquete). "
                "Llama a quote_shipment y preséntame los resultados como una tabla numerada con columnas: "
                "#, Paquetería, Servicio, Tipo, Costo total, Moneda, Días, Entrega estimada, "
                "Peso (kg), Peso volumétrico (kg), Dimensiones (cm), Quote token. "
                "Marca con ★ las tarifas con recommended=true. "
                "Si pedí seguro y alguna tarifa no lo aplica, indícalo claramente en su fila (insurance_note). "
                "Termina preguntando: '¿Con qué servicio deseas proceder?'"
            )
        return types.GetPromptResult(
            description="Cotización de envío / Shipment quote",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "ship":
        token = args.get("quote_token", "?")
        content = args.get("content", "Producto")
        if lang == "en":
            text = (
                f"Create a shipment using quote token: {token}. "
                f"Package contents: {content}. "
                "If you don't have the following information in context, ask the user for it before calling create_shipment:\n"
                "Sender: first name, last name, email, phone, street, number, neighborhood (colonia), municipality, state, ZIP code, address references.\n"
                "Recipient: same fields.\n"
                "⚠️ WARNING: this operation has a monetary cost. Confirm with the user before proceeding.\n"
                "On success, respond with: guide number, carrier, estimated delivery date, and label download link."
            )
        else:
            text = (
                f"Crea un envío usando el token de cotización: {token}. "
                f"Contenido del paquete: {content}. "
                "Si no tienes la siguiente información en el contexto, pídela al usuario antes de llamar a create_shipment:\n"
                "Remitente: nombre, apellido, email, teléfono, calle, número, colonia, municipio, estado, código postal, referencias.\n"
                "Destinatario: los mismos campos.\n"
                "⚠️ AVISO: esta operación tiene costo monetario. Confirma con el usuario antes de continuar.\n"
                "Al éxito, responde con: número de guía, paquetería, fecha estimada de entrega y link de etiqueta."
            )
        return types.GetPromptResult(
            description="Creación de envío / Create shipment",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "track_status":
        guide = args.get("guide", "?")
        if lang == "en":
            text = (
                f"Track shipment guide {guide}. "
                "First call track_guide to get the current status and last update. "
                "If the package appears delayed (estimated delivery passed or status is stuck), "
                "also call track_detail to get the full event history and summarize what happened."
            )
        else:
            text = (
                f"Rastrea la guía {guide}. "
                "Primero llama a track_guide para obtener el estado actual y última actualización. "
                "Si el paquete parece retrasado (fecha estimada vencida o estado estancado), "
                "llama también a track_detail para obtener el historial completo y resumir qué ocurrió."
            )
        return types.GetPromptResult(
            description="Estado de rastreo / Tracking status",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "schedule_pickup_tomorrow":
        carrier = args.get("carrier", "?")
        weight = args.get("weight_kg", "?")
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        if lang == "en":
            text = (
                f"Schedule a pickup with {carrier} for tomorrow ({tomorrow}), {weight} kg total. "
                "Use open_time=09:00 and close_time=18:00. "
                "Ask me for the address details (street, number, neighborhood, municipality, state, ZIP, references, contact name, phone, email, pieces, dimensions) "
                "then call schedule_pickup. Warn me this has a monetary cost."
            )
        else:
            text = (
                f"Programa una recolección con {carrier} para mañana ({tomorrow}), {weight} kg en total. "
                "Usa open_time=09:00 y close_time=18:00. "
                "Pídeme los datos de la dirección (calle, número, colonia, municipio, estado, CP, referencias, nombre contacto, teléfono, email, piezas, dimensiones) "
                "y luego llama a schedule_pickup. Avísame que esta operación tiene costo monetario."
            )
        return types.GetPromptResult(
            description="Recolección mañana / Tomorrow pickup",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "check_balance_before_ship":
        if lang == "en":
            text = (
                "Check my T1Envios balance with get_balance. "
                "If the balance is below 200 MXN, warn me that I may not have enough funds to create a shipment and suggest recharging. "
                "Otherwise, confirm the available balance and that I can proceed."
            )
        else:
            text = (
                "Revisa mi saldo de T1Envios con get_balance. "
                "Si el saldo es menor a 200 MXN, avísame que podría no tener fondos suficientes para crear un envío y sugiere recargar. "
                "De lo contrario, confirma el saldo disponible e indícame que puedo continuar."
            )
        return types.GetPromptResult(
            description="Verificar saldo / Check balance",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    raise ValueError(f"Unknown prompt: {name}")


def register(server: Server, get_client: Callable) -> None:  # noqa: ARG001
    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return _PROMPTS

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
        return _get_prompt(name, arguments)
