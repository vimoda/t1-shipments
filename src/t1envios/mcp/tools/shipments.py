from __future__ import annotations

import mcp.types as types

from ...core.models.quote import QuoteRequest, QuoteResponse
from ...core.models.shipment import ShipmentRequest
from ...core.models.tracking import PickupRequest

TOOL_GET_BALANCE = types.Tool(
    name="get_balance",
    description=(
        "Get the current account balance in MXN / Obtiene el saldo actual en MXN. "
        "Call before creating shipments to verify sufficient funds. "
        "Respond with exactly: 'Tu saldo disponible es $X,XXX.XX MXN.' "
        "If balance < 200 MXN add: 'Es posible que no tengas fondos suficientes para crear un envío.'"
    ),
    inputSchema={"type": "object", "properties": {}},
)

TOOL_TRACK_GUIDE = types.Tool(
    name="track_guide",
    description=(
        "Track a shipment by guide number / Rastrea un envío por número de guía. "
        "Returns current status, estimated delivery date, and event history. "
        "Respond with: status, estimated delivery date, and last event. "
        "One short paragraph max. If delayed, say so explicitly."
    ),
    inputSchema={
        "type": "object",
        "properties": {"guide": {"type": "string", "description": "Guide/tracking number / Número de guía"}},
        "required": ["guide"],
    },
)

TOOL_TRACK_DETAIL = types.Tool(
    name="track_detail",
    description=(
        "Get full tracking detail for a shipment / Obtiene el detalle completo de rastreo. "
        "Returns all tracking events with timestamps, locations, and carrier info. "
        "Use when track_guide shows a delayed or stuck status. "
        "Respond with a bullet list of events (date, location, status). Most recent first. No extra commentary."
    ),
    inputSchema={
        "type": "object",
        "properties": {"guide": {"type": "string", "description": "Guide/tracking number / Número de guía"}},
        "required": ["guide"],
    },
)

TOOL_QUOTE = types.Tool(
    name="quote_shipment",
    description=(
        "Get available shipping rates / Cotiza tarifas de envío. "
        "Returns a list sorted cheapest-first; rows with recommended=true appear first. "
        "Each rate exposes: quote_token, carrier, service, service_type, base_cost, total_cost, "
        "currency, estimated_days, delivery_date, weight_kg, volumetric_weight_kg, "
        "dimensions_cm {length,width,height}, package_value, packages, insurance_applied, recommended. "
        "When insurance_requested=true: if insurance_applied=true and base_cost differs from total_cost, "
        "the rate also includes insurance_cost (= total_cost - base_cost). "
        "If insurance_applied=false, the rate includes insurance_note explaining insurance was not applied. "
        "Always call this BEFORE create_shipment — quote_token is required to ship. "
        "Dimension defaults if omitted: width=30cm, height=20cm, length=15cm, "
        "package_value=500 MXN, packages=1, package_type=2 (parcel). "
        "Respond with a numbered table. Columns: #, Carrier, Service, Type, Total cost, Currency, "
        "Days, Estimated delivery, Weight (kg), Volumetric weight (kg), Dimensions (cm), Quote token. "
        "Highlight rows with recommended=true with ★. "
        "If insurance was requested, append '+ insurance_cost = total' per row where insurance_applied=true; "
        "mark insurance_note rows clearly. "
        "End with: '¿Con qué servicio deseas proceder?'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "origin_postal_code": {"type": "string", "description": "5-digit Mexican origin ZIP code / CP origen (5 dígitos)"},
            "destination_postal_code": {"type": "string", "description": "5-digit Mexican destination ZIP code / CP destino (5 dígitos)"},
            "weight": {"type": "number", "description": "Weight in kg / Peso en kg"},
            "width": {"type": "number", "description": "Width in cm (default 30) / Ancho en cm (default 30)"},
            "height": {"type": "number", "description": "Height in cm (default 20) / Alto en cm (default 20)"},
            "length": {"type": "number", "description": "Length in cm (default 15) / Largo en cm (default 15)"},
            "shipping_days": {"type": "integer", "description": "Days until shipment / Días hasta envío"},
            "package_value": {"type": "number", "description": "Declared value in MXN (default 500) / Valor declarado en MXN (default 500)"},
            "insurance": {"type": "boolean", "description": "Include insurance / Incluir seguro"},
            "packages": {"type": "integer", "description": "Number of packages (default 1) / Número de paquetes (default 1)"},
            "package_type": {"type": "integer", "description": "1=Envelope/Sobre, 2=Parcel/Paquete (default 2)"},
        },
        "required": [
            "origin_postal_code", "destination_postal_code", "weight", "insurance"
        ],
    },
)

TOOL_CREATE_SHIPMENT = types.Tool(
    name="create_shipment",
    description=(
        "⚠️ This operation has a monetary cost / Esta operación tiene costo monetario. "
        "Create a shipment and generate a shipping guide / Crea un envío y genera la guía. "
        "Requires a quote_token from quote_shipment. "
        "Flow: quote_shipment → select rate → create_shipment. "
        "If the origin ZIP has multiple neighborhoods, ask the user which one applies before calling. "
        "On success respond with: guide number, carrier, estimated delivery date, and label download link. "
        "One sentence each. No JSON, no raw data."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "quote_token": {"type": "string", "description": "Rate token from quote_shipment / Token de tarifa"},
            "content": {"type": "string", "description": "Package contents (max 25 chars) / Contenido del paquete (máx 25 chars)"},
            "origin_first_name": {"type": "string", "description": "Sender first name / Nombre del remitente"},
            "origin_last_name": {"type": "string", "description": "Sender last name / Apellido del remitente"},
            "origin_email": {"type": "string", "description": "Sender email / Correo del remitente"},
            "origin_street": {"type": "string", "description": "Sender street / Calle del remitente"},
            "origin_number": {"type": "string", "description": "Sender exterior number / Número exterior"},
            "origin_neighborhood": {"type": "string", "description": "Sender neighborhood/colonia. If ZIP has multiple colonias, confirm with user first"},
            "origin_phone": {"type": "string", "description": "Sender phone / Teléfono del remitente"},
            "origin_state": {"type": "string", "description": "Sender state / Estado del remitente"},
            "origin_municipality": {"type": "string", "description": "Sender municipality / Municipio del remitente"},
            "origin_references": {"type": "string", "description": "Address references / Referencias de la dirección"},
            "origin_postal_code": {"type": "string", "description": "Sender 5-digit ZIP / CP del remitente"},
            "origin_commerce_name": {"type": "string", "description": "Sender business name (optional) / Nombre comercial (opcional)"},
            "destination_first_name": {"type": "string", "description": "Recipient first name / Nombre del destinatario"},
            "destination_last_name": {"type": "string", "description": "Recipient last name / Apellido del destinatario"},
            "destination_email": {"type": "string", "description": "Recipient email / Correo del destinatario"},
            "destination_street": {"type": "string", "description": "Recipient street / Calle del destinatario"},
            "destination_number": {"type": "string", "description": "Recipient exterior number / Número exterior"},
            "destination_neighborhood": {"type": "string", "description": "Recipient neighborhood/colonia"},
            "destination_phone": {"type": "string", "description": "Recipient phone / Teléfono del destinatario"},
            "destination_state": {"type": "string", "description": "Recipient state / Estado del destinatario"},
            "destination_municipality": {"type": "string", "description": "Recipient municipality / Municipio del destinatario"},
            "destination_references": {"type": "string", "description": "Address references / Referencias"},
            "destination_postal_code": {"type": "string", "description": "Recipient 5-digit ZIP / CP del destinatario"},
            "destination_commerce_name": {"type": "string", "description": "Recipient business name (optional) / Nombre comercial (opcional)"},
            "packages": {"type": "integer", "description": "Number of packages / Número de paquetes"},
            "generate_pickup": {"type": "boolean", "description": "Auto-schedule pickup / Programar recolección automática"},
            "has_notification": {"type": "boolean", "description": "Send tracking notification / Enviar notificación de rastreo"},
            "guide_origin": {"type": "string", "description": "Guide origin label / Etiqueta de origen de guía"},
        },
        "required": [
            "quote_token", "content",
            "origin_first_name", "origin_last_name", "origin_email",
            "origin_street", "origin_number", "origin_neighborhood",
            "origin_phone", "origin_state", "origin_municipality",
            "origin_references", "origin_postal_code",
            "destination_first_name", "destination_last_name", "destination_email",
            "destination_street", "destination_number", "destination_neighborhood",
            "destination_phone", "destination_state", "destination_municipality",
            "destination_references", "destination_postal_code",
            "packages",
        ],
    },
)

TOOL_DOWNLOAD_LABEL = types.Tool(
    name="download_label",
    description=(
        "Download the shipping label PDF for a guide / Descarga la etiqueta PDF de una guía. "
        "Use the guide_link returned by create_shipment. Returns base64-encoded PDF content. "
        "Respond with: 'Etiqueta lista. Puedes descargarla aquí: [link]' Do not show the base64 data."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "guide_link": {"type": "string", "description": "Label URL from create_shipment response / URL de etiqueta del envío creado"},
        },
        "required": ["guide_link"],
    },
)

TOOL_SCHEDULE_PICKUP = types.Tool(
    name="schedule_pickup",
    description=(
        "⚠️ This operation has a monetary cost / Esta operación tiene costo monetario. "
        "Schedule a package pickup at the origin address / Programa recolección en la dirección de origen. "
        "The origin address must be registered in T1Envios beforehand. "
        "On success respond with: 'Recolección programada para [fecha] entre [open_time] y [close_time] con [carrier].' One line only."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "carrier": {"type": "string", "description": "Carrier name: DHL, FEDEX, UPS"},
            "contact_first_name": {"type": "string"},
            "contact_last_name": {"type": "string"},
            "email": {"type": "string"},
            "street": {"type": "string"},
            "number": {"type": "string"},
            "neighborhood": {"type": "string"},
            "phone": {"type": "string"},
            "state": {"type": "string"},
            "municipality": {"type": "string"},
            "postal_code": {"type": "string"},
            "references": {"type": "string"},
            "pieces": {"type": "integer"},
            "weight": {"type": "integer", "description": "Total weight in kg"},
            "length": {"type": "integer", "description": "Length in cm"},
            "width": {"type": "integer", "description": "Width in cm"},
            "height": {"type": "integer", "description": "Height in cm"},
            "date": {"type": "string", "description": "Pickup date YYYY-MM-DD"},
            "open_time": {"type": "string", "description": "Open time HH:MM"},
            "close_time": {"type": "string", "description": "Close time HH:MM"},
        },
        "required": [
            "carrier", "contact_first_name", "contact_last_name", "email",
            "street", "number", "neighborhood", "phone", "state", "municipality",
            "postal_code", "references", "pieces", "weight", "length", "width",
            "height", "date", "open_time", "close_time",
        ],
    },
)

ALL_TOOLS = [
    TOOL_GET_BALANCE,
    TOOL_TRACK_GUIDE,
    TOOL_TRACK_DETAIL,
    TOOL_QUOTE,
    TOOL_CREATE_SHIPMENT,
    TOOL_DOWNLOAD_LABEL,
    TOOL_SCHEDULE_PICKUP,
]


def handle(name: str, arguments: dict, client) -> dict:
    if name == "get_balance":
        return client.balance().model_dump()
    if name == "track_guide":
        return client.track_state(arguments["guide"]).model_dump()
    if name == "track_detail":
        return client.track_detail(arguments["guide"]).model_dump()
    if name == "quote_shipment":
        req = QuoteRequest(**arguments)
        resp = client.quote(req)
        return _normalize_quote(resp, insurance_requested=arguments.get("insurance", False))
    if name == "create_shipment":
        req = ShipmentRequest(**arguments)
        return client.create_shipment(req).model_dump()
    if name == "download_label":
        pdf_bytes = client.download_label(arguments["guide_link"])
        import base64
        return {"content_type": "application/pdf", "data_base64": base64.b64encode(pdf_bytes).decode()}
    if name == "schedule_pickup":
        req = PickupRequest(**arguments)
        return client.schedule_pickup(req).model_dump()
    raise ValueError(f"Unknown tool: {name}")


def _normalize_quote(resp: QuoteResponse, *, insurance_requested: bool) -> dict:
    rates = []
    for raw in (resp.detail or []):
        if not isinstance(raw, dict):
            rates.append(raw)
            continue

        base_cost = raw.get("cost")
        total_cost = raw.get("total_cost") or 0.0
        insurance_applied = bool(raw.get("insurance", False))

        rate: dict = {
            "quote_token": raw.get("token"),
            "carrier": raw.get("carrier") or raw.get("service_id") or "",
            "service": raw.get("service_name") or raw.get("service") or "",
            "service_type": raw.get("service_type"),
            "base_cost": base_cost,
            "total_cost": total_cost,
            "currency": raw.get("currency", "MXN"),
            "estimated_days": raw.get("delivery_days"),
            "delivery_date": raw.get("delivery_date_carrier") or raw.get("delivery_date_claro"),
            "weight_kg": raw.get("weight"),
            "volumetric_weight_kg": raw.get("volumetric_weight"),
            "dimensions_cm": {
                "length": raw.get("length"),
                "width": raw.get("width"),
                "height": raw.get("height"),
            },
            "package_value": raw.get("package_value"),
            "packages": raw.get("total_packages", 1),
            "insurance_applied": insurance_applied,
            "recommended": bool(raw.get("recommended", False)),
        }

        if insurance_requested:
            if insurance_applied and base_cost is not None and base_cost != total_cost:
                rate["insurance_cost"] = round(total_cost - base_cost, 2)
            elif not insurance_applied:
                rate["insurance_note"] = "Insurance was requested but this rate did not apply it."

        rates.append(rate)

    # recommended rows first, then ascending total_cost
    rates.sort(key=lambda r: (not r.get("recommended", False), r.get("total_cost") or 0.0))

    return {
        "success": resp.success,
        "insurance_requested": insurance_requested,
        "rate_count": len(rates),
        "rates": rates,
    }
