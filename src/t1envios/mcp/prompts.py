from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import mcp.types as types
from mcp.server import Server

_PROMPTS: list[types.Prompt] = [
    types.Prompt(
        name="quick_quote",
        description="Cotización rápida: CP origen, CP destino, peso, dimensiones y seguro opcional.",
        arguments=[
            types.PromptArgument(name="origin_zip", description="Código postal origen", required=True),
            types.PromptArgument(name="dest_zip", description="Código postal destino", required=True),
            types.PromptArgument(name="weight_kg", description="Peso en kg", required=True),
            types.PromptArgument(name="width_cm", description="Ancho en cm (default 30)", required=False),
            types.PromptArgument(name="height_cm", description="Alto en cm (default 20)", required=False),
            types.PromptArgument(name="length_cm", description="Largo en cm (default 15)", required=False),
            types.PromptArgument(name="insurance", description="Con seguro? true/false", required=False),
            types.PromptArgument(name="package_value", description="Valor del paquete en MXN (requerido solo si con seguro)", required=False),
        ],
    ),
    types.Prompt(
        name="create_shipment_with_stored_address",
        description="Crear envío usando quote_token y direcciones previamente almacenadas.",
        arguments=[
            types.PromptArgument(name="quote_token", description="Token de la tarifa elegida", required=True),
            types.PromptArgument(name="content", description="Contenido del paquete (máx 25 chars)", required=False),
            types.PromptArgument(name="use_stored_origin", description="Usar dirección de origen almacenada? true/false", required=False),
            types.PromptArgument(name="use_stored_destination", description="Usar dirección de destino almacenada? true/false", required=False),
        ],
    ),
    types.Prompt(
        name="quote",
        description="Cotiza envío completo entre dos códigos postales.",
        arguments=[
            types.PromptArgument(name="origin_zip", description="Código postal origen", required=True),
            types.PromptArgument(name="dest_zip", description="Código postal destino", required=True),
            types.PromptArgument(name="weight_kg", description="Peso en kg", required=True),
            types.PromptArgument(name="width_cm", description="Ancho en cm", required=False),
            types.PromptArgument(name="height_cm", description="Alto en cm", required=False),
            types.PromptArgument(name="length_cm", description="Largo en cm", required=False),
            types.PromptArgument(name="insurance", description="Con seguro? true/false", required=False),
            types.PromptArgument(name="package_value", description="Valor del paquete en MXN (requerido solo si con seguro)", required=False),
        ],
    ),
    types.Prompt(
        name="ship",
        description="Crear envío desde un quote_token.",
        arguments=[
            types.PromptArgument(name="quote_token", description="Token de la tarifa elegida (de /quote)", required=True),
            types.PromptArgument(name="content", description="Contenido del paquete, máx 25 chars", required=False),
        ],
    ),
    types.Prompt(
        name="track_status",
        description="Rastrear guía con historial completo.",
        arguments=[
            types.PromptArgument(name="guide", description="Número de guía", required=True),
        ],
    ),
    types.Prompt(
        name="schedule_pickup_tomorrow",
        description="Programar recolección para mañana con horarios predefinidos.",
        arguments=[
            types.PromptArgument(name="carrier", description="Paquetería: DHL, FEDEX, UPS", required=True),
            types.PromptArgument(name="weight_kg", description="Peso total en kg", required=True),
        ],
    ),
    types.Prompt(
        name="choose_quote_flow",
        description="Preguntar al usuario si quiere cotización rápida o flujo completo de envío.",
        arguments=[],
    ),
]


def _get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
    args = arguments or {}

    if name == "choose_quote_flow":
        text = (
            "Antes de responder, revisá tu memoria por direcciones guardadas. "
            "- Si existen ORIGEN y DESTINO: preguntá '¿Querés usar [origen] → [destino], "
            "cambiar solo el origen, cambiar solo el destino, o dar ambos nuevos?' "
            "- Si solo existe ORIGEN: 'Tengo guardado [origen]. ¿Lo usamos o ponemos otro? Y decime el destino.' "
            "- Si solo existe DESTINO: 'Tengo guardado [destino]. ¿Lo usamos o ponemos otro? Y decime el origen.' "
            "- Si no hay nada: seguí normal. "
            "Luego preguntá: ¿Querés una cotización rápida (datos mínimos) o iniciar el flujo completo de envío "
            "(se pedirán todos los datos de dirección)? "
            "Respondé con 'rápida' o 'envío'. "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Elegir flujo de cotización",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "quick_quote":
        origin = args.get("origin_zip", "?")
        dest = args.get("dest_zip", "?")
        weight = args.get("weight_kg", "?")
        width = args.get("width_cm", "?")
        height = args.get("height_cm", "?")
        length = args.get("length_cm", "?")
        insurance = args.get("insurance", "false")
        text = (
            f"Cotiza un envío rápido desde el CP {origin} al CP {dest}, "
            f"peso={weight} kg, "
            f"dimensiones: ancho={width}cm, alto={height}cm, largo={length}cm, "
            f"{'con' if str(insurance).lower() == 'true' else 'sin'} seguro. "
            "Si no se proporcionaron dimensiones, usá los valores por defecto: ancho=30cm, alto=20cm, largo=15cm. "
            "Calculá el peso volumétrico = ceil(ancho × alto × largo / 5000). "
            "Todos los pesos se redondean HACIA ARRIBA al entero más cercano. "
            "Usá el MAYOR entre el peso físico y el peso volumétrico como peso cotizado. "
            "Si se solicita seguro, también incluí el valor del paquete (package_value en MXN). "
            "Llamá a quote_shipment y mostrá las tarifas en una tabla numerada. "
            "Columnas: #, Paquetería, Servicio, Tipo, Costo guía, Costo seguro, Total, Moneda, "
            "Días, Entrega estimada, Peso (kg), Peso volumétrico (kg), Dimensiones (cm), Quote token. "
            "Cuando insurance=true y insurance_applied=true: Costo guía = base_cost, Costo seguro = insurance_cost, Total = total_cost. "
            "Cuando insurance=false o insurance_applied=false: Costo guía = total_cost, Costo seguro = '—', Total = total_cost. "
            "En tu respuesta, aclará claramente qué peso se usó para cotizar — "
            "ej. 'Cotizando con peso volumétrico de X kg (redondeado, peso físico de Y kg).' "
            "Si ambos son iguales, decí: 'Cotizando con peso físico de X kg.' "
            "Luego revisá tu memoria para ver si esas direcciones ya están guardadas. "
            "Si no están, preguntale al usuario: '¿Querés guardarlas?' "
            "Terminá con: '¿Con qué servicio deseas proceder?' "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Cotización rápida",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "quote":
        origin = args.get("origin_zip", "?")
        dest = args.get("dest_zip", "?")
        weight = args.get("weight_kg", "?")
        width = args.get("width_cm", "?")
        height = args.get("height_cm", "?")
        length = args.get("length_cm", "?")
        insurance = args.get("insurance", "false")
        text = (
            f"Cotiza un envío desde el código postal {origin} al {dest}, "
            f"peso={weight} kg, "
            f"dimensiones: ancho={width}cm, alto={height}cm, largo={length}cm, "
            f"{'con' if str(insurance).lower() == 'true' else 'sin'} seguro. "
            "Si no se proporcionaron dimensiones, usá los valores por defecto: ancho=30cm, alto=20cm, largo=15cm. "
            "Calculá el peso volumétrico = ceil(ancho × alto × largo / 5000). "
            "Todos los pesos se redondean HACIA ARRIBA al entero más cercano. "
            "Usá el MAYOR entre el peso físico y el peso volumétrico como peso cotizado. "
            "Si se solicita seguro, también incluí el valor del paquete (package_value en MXN). "
            "Llamá a quote_shipment y preséntame los resultados como una tabla numerada con columnas: "
            "#, Paquetería, Servicio, Tipo, Costo guía, Costo seguro, Total, Moneda, "
            "Días, Entrega estimada, Peso (kg), Peso volumétrico (kg), Dimensiones (cm), Quote token. "
            "Marca con ★ las tarifas con recommended=true. "
            "Cuando insurance=true y insurance_applied=true: Costo guía = base_cost, Costo seguro = insurance_cost, Total = total_cost. "
            "Cuando insurance=false o insurance_applied=false: Costo guía = total_cost, Costo seguro = '—', Total = total_cost. "
            "Si pedí seguro y alguna tarifa no lo aplica, indícalo claramente en su fila (insurance_note). "
            "En tu respuesta, aclará claramente qué peso se usó para cotizar — "
            "ej. 'Cotizando con peso volumétrico de X kg (redondeado, peso físico de Y kg).' "
            "Si ambos son iguales, decí: 'Cotizando con peso físico de X kg.' "
            "Luego revisá tu memoria para ver si esas direcciones ya están guardadas. "
            "Si no están, preguntale al usuario: '¿Querés guardarlas?' "
            "Termina preguntando: '¿Con qué servicio deseas proceder?' "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Cotización de envío",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "create_shipment_with_stored_address":
        token = args.get("quote_token", "?")
        content = args.get("content", "Producto")
        use_origin = str(args.get("use_stored_origin", "false")).lower() == "true"
        use_dest = str(args.get("use_stored_destination", "false")).lower() == "true"
        text = (
            f"Crea un envío usando el token de cotización: {token}. "
            f"Contenido del paquete: {content}. "
            "Si use_stored_origin es true, usá la dirección de origen ya almacenada. "
            "Si es false, revisá tu memoria primero (sesiones anteriores). "
            "Si hay direcciones guardadas, ofrecéselas al usuario. Si no, pedí los datos UNO POR UNO: "
            "nombre, esperá respuesta, luego apellido, email, teléfono, calle, número, colonia, "
            "municipio, estado, CP y referencias. "
            "⚠️ references = opcional (ej. 'junto al OXXO'). Mandá '' si el usuario no las da. "
            "⚠️ También preguntale al usuario qué contiene el paquete (content, máx 25 chars). "
            "⚠️ guide_origin no se incluye (usa el default). "
            "De igual forma para el destinatario: si use_stored_destination es true, usá la almacenada; "
             "si es false, revisá memoria y ofrecé las guardadas, o pedí datos uno por uno. "
            "⚠️ AVISO: esta operación tiene costo monetario. Confirmá con el usuario antes de continuar. "
            "DESPUÉS de la guía: revisá si esas direcciones ya están en tu memoria. "
            "Si ya existen: decí 'Las direcciones ya las tengo guardadas.' "
            "Si no: preguntale '¿Querés guardarlas?' "
            "Al éxito, respondé: número de guía, paquetería, fecha estimada de entrega y link de etiqueta. "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Crear envío con direcciones almacenadas",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "ship":
        token = args.get("quote_token", "?")
        content = args.get("content", "Producto")
        text = (
            f"Crea un envío usando el token de cotización: {token}. "
            f"Contenido del paquete: {content}. "
            "ANTES de pedir datos, revisá tu memoria (sesiones anteriores). "
            "Si el usuario tiene direcciones guardadas, mostráselas y preguntá si quiere reusarlas o dar datos nuevos. "
            "Si no hay guardadas o prefiere datos nuevos, pedí cada campo UNO POR UNO: "
            "primero nombre del remitente, esperá respuesta, "
            "luego apellido, email, teléfono, calle, número, colonia, municipio, estado, CP y referencias. "
            "Luego lo mismo con el destinatario. "
            "⚠️ references = opcional (ej. 'junto al OXXO'). Mandá '' si el usuario no las da. "
            "⚠️ También preguntale al usuario qué contiene el paquete (content, máx 25 chars). "
            "⚠️ guide_origin no se incluye (usa el default). "
            "⚠️ AVISO: esta operación tiene costo monetario. Confirmá con el usuario antes de continuar.\n"
            "DESPUÉS de la guía: revisá si esas direcciones ya están en tu memoria. "
            "Si ya existen: decí 'Las direcciones ya las tengo guardadas.' "
            "Si no: preguntale '¿Querés guardarlas?' "
            "Al éxito, respondé: número de guía, paquetería, fecha estimada de entrega y link de etiqueta. "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Creación de envío",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "track_status":
        guide = args.get("guide", "?")
        text = (
            f"Rastrea la guía {guide}. "
            "Primero llamá a track_guide para obtener el estado actual y última actualización. "
            "Si el paquete parece retrasado (fecha estimada vencida o estado estancado), "
            "llamá también a track_detail para obtener el historial completo y resumí qué ocurrió. "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Estado de rastreo",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "schedule_pickup_tomorrow":
        carrier = args.get("carrier", "?")
        weight = args.get("weight_kg", "?")
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        text = (
            f"Programá una recolección con {carrier} para mañana ({tomorrow}), {weight} kg en total. "
            "Usá open_time=09:00 y close_time=18:00. "
            "Pedí los datos UNO POR UNO: primero el nombre de contacto, esperá la respuesta, "
            "luego apellido, teléfono, email, calle, número, colonia, municipio, estado, CP, "
            "referencias, piezas y dimensiones. No preguntes varios campos en un mismo mensaje. "
            "y luego llamá a schedule_pickup. Avísale que esta operación tiene costo monetario. "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Recolección mañana",
            messages=[types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))],
        )

    if name == "check_balance_before_ship":
        text = (
            "Revisá mi saldo de T1Envios con get_balance. "
            "Si el saldo es menor a 200 MXN, avisame que podría no tener fondos suficientes para crear un envío y sugerí recargar. "
            "De lo contrario, confirmá el saldo disponible e indicame que puedo continuar. "
            "Respondé en el mismo idioma que el usuario está usando."
        )
        return types.GetPromptResult(
            description="Verificar saldo",
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
