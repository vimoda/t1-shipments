from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta

import mcp.types as types
from mcp.server import Server

_PROMPTS: list[types.Prompt] = [
    types.Prompt(
        name="quick_quote",
        description="Quick quote: origin ZIP, destination ZIP, dimensions, weight, and insurance (yes/no). No guide generation.",
        arguments=[
            types.PromptArgument(name="origin_zip", description="Origin ZIP code", required=True),
            types.PromptArgument(
                name="dest_zip", description="Destination ZIP code", required=True
            ),
            types.PromptArgument(name="weight_kg", description="Weight in kg", required=True),
            types.PromptArgument(
                name="width_cm", description="Width in cm (default 30)", required=False
            ),
            types.PromptArgument(
                name="height_cm", description="Height in cm (default 20)", required=False
            ),
            types.PromptArgument(
                name="length_cm", description="Length in cm (default 15)", required=False
            ),
            types.PromptArgument(
                name="insurance", description="With insurance? true/false", required=True
            ),
            types.PromptArgument(
                name="package_value",
                description="Declared value in MXN (only if insurance=true, skip otherwise)",
                required=False,
            ),
        ],
    ),
    types.Prompt(
        name="create_shipment_with_stored_address",
        description="Create a shipment using a quote_token and previously stored addresses.",
        arguments=[
            types.PromptArgument(
                name="quote_token", description="Selected rate token", required=True
            ),
            types.PromptArgument(
                name="content", description="Package contents (max 25 chars)", required=False
            ),
            types.PromptArgument(
                name="package_type",
                description="Package type: 1=Envelope/Sobre, 2=Parcel/Paquete (default 2)",
                required=False,
            ),
            types.PromptArgument(
                name="use_stored_origin",
                description="Use stored origin address? true/false",
                required=False,
            ),
            types.PromptArgument(
                name="use_stored_destination",
                description="Use stored destination address? true/false",
                required=False,
            ),
        ],
    ),
    types.Prompt(
        name="quote",
        description="Full quote to create a shipment/guide: ZIPs, weight, dimensions, insurance, package type.",
        arguments=[
            types.PromptArgument(name="origin_zip", description="Origin ZIP code", required=True),
            types.PromptArgument(
                name="dest_zip", description="Destination ZIP code", required=True
            ),
            types.PromptArgument(name="weight_kg", description="Weight in kg", required=True),
            types.PromptArgument(name="width_cm", description="Width in cm", required=False),
            types.PromptArgument(name="height_cm", description="Height in cm", required=False),
            types.PromptArgument(name="length_cm", description="Length in cm", required=False),
            types.PromptArgument(
                name="insurance", description="With insurance? true/false", required=True
            ),
            types.PromptArgument(
                name="package_value",
                description="Declared value in MXN (only if insurance=true, skip otherwise)",
                required=False,
            ),
            types.PromptArgument(
                name="packages", description="Number of packages (default 1)", required=False
            ),
            types.PromptArgument(
                name="package_type",
                description="Package type: 1=Envelope/Sobre, 2=Parcel/Paquete (default 2)",
                required=False,
            ),
            types.PromptArgument(
                name="shipping_days", description="Days until shipment", required=False
            ),
        ],
    ),
    types.Prompt(
        name="ship",
        description="Create a shipment from a quote_token.",
        arguments=[
            types.PromptArgument(
                name="quote_token", description="Rate token (from /quote)", required=True
            ),
            types.PromptArgument(
                name="content", description="Package contents, max 25 chars", required=False
            ),
            types.PromptArgument(
                name="package_type",
                description="Package type: 1=Envelope/Sobre, 2=Parcel/Paquete (default 2)",
                required=False,
            ),
        ],
    ),
    types.Prompt(
        name="track_status",
        description="Track a guide with full history.",
        arguments=[
            types.PromptArgument(name="guide", description="Guide number", required=True),
        ],
    ),
    types.Prompt(
        name="schedule_pickup_tomorrow",
        description="Schedule a pickup for tomorrow with predefined times.",
        arguments=[
            types.PromptArgument(
                name="carrier", description="Carrier: DHL, FEDEX, UPS", required=True
            ),
            types.PromptArgument(name="weight_kg", description="Total weight in kg", required=True),
        ],
    ),
    types.Prompt(
        name="choose_quote_flow",
        description="Ask the user if they want a quick quote or the full shipment flow.",
        arguments=[],
    ),
]


def _get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
    args = arguments or {}

    if name == "choose_quote_flow":
        text = (
            "Before responding, check your memory for saved addresses. "
            "List each saved address showing its name, email, and phone so the user can identify it. "
            "Then ask: 'What email or phone is the address saved under?' to find the right one. "
            "- If both ORIGIN and DESTINATION are found: ask 'Want to use [origin] → [destination], "
            "change only the origin, change only the destination, or provide both new?' "
            "- If only ORIGIN is found: 'I have [origin]. Use it or a different one? And tell me the destination.' "
            "- If only DESTINATION is found: 'I have [destination]. Use it or a different one? And tell me the origin.' "
            "- If nothing is saved: proceed normally. "
            "Then ask: Do you want a quick quote (minimal data) or start the full shipment flow "
            "(all address details will be requested)? "
            "Reply with 'quick' or 'shipment'. "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Choose quote flow",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
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
            f"Quick-quote a shipment from ZIP {origin} to ZIP {dest}, "
            f"weight={weight} kg, "
            f"dimensions: width={width}cm, height={height}cm, length={length}cm, "
            f"{'with' if str(insurance).lower() == 'true' else 'without'} insurance. "
            "⚠️ This is a QUICK QUOTE only — do NOT proceed to create a shipment or generate a guide. "
            "Do NOT ask for package type or packages — those are only needed when creating a guide. "
            "If the user wants to create a shipment, tell them to use the full quote flow instead. "
            "If dimensions were not provided, use defaults: width=30cm, height=20cm, length=15cm. "
            "Calculate volumetric weight = ceil(width × height × length / 5000). "
            "All weights are rounded UP to the nearest integer. "
            "Use the LARGER of physical weight and volumetric weight as the quoted weight. "
            "If insurance is requested, also include the package value (package_value in MXN). "
            "Call quote_shipment and display rates in a numbered table. "
            "Columns: #, Carrier, Service, Type, Guide cost, Insurance cost, Total, Currency, "
            "Days, Estimated delivery, Weight (kg), Volumetric weight (kg), Dimensions (cm). "
            "⚠️ Do NOT display the quote token in the table — this is a quick quote only, not for guide generation. "
            "When insurance=true and insurance_applied=true: Guide cost = base_cost, Insurance cost = insurance_cost, Total = total_cost. "
            "When insurance=false or insurance_applied=false: Guide cost = total_cost, Insurance cost = '—', Total = total_cost. "
            "In your response, clarify which weight was used — "
            "e.g. 'Quoting with volumetric weight of X kg (rounded up, physical weight Y kg).' "
            "If both are equal, say: 'Quoting with physical weight of X kg.' "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Quick quote",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    if name == "quote":
        origin = args.get("origin_zip", "?")
        dest = args.get("dest_zip", "?")
        weight = args.get("weight_kg", "?")
        width = args.get("width_cm", "?")
        height = args.get("height_cm", "?")
        length = args.get("length_cm", "?")
        insurance = args.get("insurance", "false")
        pkgs = args.get("packages", "1")
        pkg_type = args.get("package_type", "2")
        shipping_days = args.get("shipping_days", "?")
        text = (
            f"Quote a shipment from ZIP code {origin} to {dest}, "
            f"weight={weight} kg, "
            f"dimensions: width={width}cm, height={height}cm, length={length}cm, "
            f"{'with' if str(insurance).lower() == 'true' else 'without'} insurance, "
            f"packages={pkgs}, package_type={pkg_type} ({'Envelope/Sobre' if pkg_type == '1' else 'Parcel/Paquete'}), "
            f"shipping_days={shipping_days}. "
            "⚠️ This is the FULL QUOTE flow — use it when the user wants to create a shipment/generate a guide. "
            "BEFORE calling quote_shipment, request any missing data from the user ONE BY ONE. "
            "This flow requires ALL data: quick quote fields (ZIPs, weight, dimensions, insurance) "
            "PLUS package_type and packages (needed for guide generation). "
            "Suggest examples for each: "
            "- weight: 'e.g. 1.5 kg', "
            "- dimensions: 'e.g. width=30cm, height=20cm, length=15cm' (defaults if not provided), "
            "- insurance: 'Do you want insurance? (yes/no)', "
            "- package_value: 'Declared value in MXN (only if insurance=true, skip otherwise)', "
            "- packages: 'How many packages? (default 1)', "
            "- package_type: 'Package type: 1 = Envelope/Sobre, 2 = Parcel/Paquete (default 2)', "
            "- shipping_days: 'How many days until you ship? (e.g. 0=today, 1=tomorrow, etc.)'. "
            "If dimensions were not provided, use defaults: width=30cm, height=20cm, length=15cm. "
            "Calculate volumetric weight = ceil(width × height × length / 5000). "
            "All weights are rounded UP to the nearest integer. "
            "Use the LARGER of physical weight and volumetric weight as the quoted weight. "
            "package_value is ONLY asked and sent when insurance=true — otherwise omit it. "
            "Call quote_shipment and present results in a numbered table with columns: "
            "#, Carrier, Service, Type, Guide cost, Insurance cost, Total, Currency, "
            "Days, Estimated delivery, Weight (kg), Volumetric weight (kg), Dimensions (cm), Quote token. "
            "Mark rates with recommended=true with ★. "
            "When insurance=true and insurance_applied=true: Guide cost = base_cost, Insurance cost = insurance_cost, Total = total_cost. "
            "When insurance=false or insurance_applied=false: Guide cost = total_cost, Insurance cost = '—', Total = total_cost. "
            "If insurance was requested and a rate did not apply it, clearly note it in that row (insurance_note). "
            "In your response, clarify which weight was used — "
            "e.g. 'Quoting with volumetric weight of X kg (rounded up, physical weight Y kg).' "
            "If both are equal, say: 'Quoting with physical weight of X kg.' "
            "After showing the table, end by asking: 'Which service would you like to proceed with to create the guide?' "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Shipment quote",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    if name == "create_shipment_with_stored_address":
        token = args.get("quote_token", "?")
        content = args.get("content", "Producto")
        pkg_type = args.get("package_type", "2")
        text = (
            f"Create a shipment using the quote token: {token}. "
            f"Package contents: {content}. "
            f"Package type: {pkg_type} ({'Envelope/Sobre' if pkg_type == '1' else 'Parcel/Paquete'}). "
            "If use_stored_origin is true, use the already stored origin address. "
            "If false, check your memory first (previous sessions). "
            "If there are saved addresses, list each showing name, email, and phone. "
            "Then ask: 'What email or phone is the address saved under?' to find the right one. "
            "If no saved addresses match or the user prefers new data, request fields ONE BY ONE: "
            "first name, wait for response, then last name, email, phone, street, exterior number, neighborhood, "
            "municipality, and state. "
            "⚠️ DO NOT ask for the ZIP code — you already know it from the previous quote, use that same one. If you don't have it then ask for it again. "
            "⚠️ references (max 35 chars) has two parts combined: "
            "first ask for interior details (interior, apartment, tower, etc. e.g. 'Int 3B', 'Apt 501', 'Tower A Apt 12'), "
            "then ask for general references (e.g. 'next to the OXXO'). "
            "If the user provides both, combine them in references separated by ' — ' "
            "(e.g. 'Apt 501 — next to the OXXO'). If it doesn't all fit, prioritize the interior detail. "
            "If neither is given, send ''. "
            "⚠️ Also ask the user what the package contains (content, max 25 chars). Suggest examples: 'Ropa', 'Electrónicos', 'Documentos', 'Accesorios', etc. "
            "⚠️ Ask for the package type. Accepted values: 1 = Envelope/Sobre, 2 = Parcel/Paquete (default). Suggest these options to the user. "
            "⚠️ guide_origin is not included (uses default). "
            "Same for the recipient: if use_stored_destination is true, use the stored one; "
            "if false, check memory and list saved ones (name, email, phone), "
            "ask 'What email or phone is the address saved under?' to identify, "
            "or request data one by one. "
            "⚠️ WARNING: this operation has a monetary cost. Confirm with the user before proceeding. "
            "AFTER the guide: check if those addresses are already in your memory. "
            "If they already exist: say 'I already have those addresses saved.' "
            "If not: ask 'Would you like to save them?' "
            "On success, respond with: guide number, carrier, estimated delivery date, and label link. "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Create shipment with stored addresses",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    if name == "ship":
        token = args.get("quote_token", "?")
        content = args.get("content", "Producto")
        pkg_type = args.get("package_type", "2")
        text = (
            f"Create a shipment using the quote token: {token}. "
            f"Package contents: {content}. "
            f"Package type: {pkg_type} ({'Envelope/Sobre' if pkg_type == '1' else 'Parcel/Paquete'}). "
            "BEFORE requesting data, check your memory (previous sessions). "
            "If the user has saved addresses, list each showing name, email, and phone. "
            "Then ask: 'What email or phone is the address saved under?' to find the right one. "
            "If no saved addresses match or the user prefers new data, request each field ONE BY ONE: "
            "first the sender's first name, wait for response, "
            "then last name, email, phone, street, exterior number, neighborhood, municipality, and state. "
            "⚠️ DO NOT ask for the ZIP code — you already know it from the previous quote, use that same one. If you don't have it then ask for it again. "
            "⚠️ references (max 35 chars) has two parts combined: "
            "first ask for interior details (interior, apartment, tower, etc. e.g. 'Int 3B', 'Apt 501', 'Tower A Apt 12'), "
            "then ask for general references (e.g. 'next to the OXXO'). "
            "If the user provides both, combine them in references separated by ' — ' "
            "(e.g. 'Apt 501 — next to the OXXO'). If it doesn't all fit, prioritize the interior detail. "
            "If neither is given, send ''. "
            "Then do the same for the recipient. "
            "⚠️ Also ask the user what the package contains (content, max 25 chars). Suggest examples: 'Ropa', 'Electrónicos', 'Documentos', 'Accesorios', etc. "
            "⚠️ Ask for the package type. Accepted values: 1 = Envelope/Sobre, 2 = Parcel/Paquete (default). Suggest these options to the user. "
            "⚠️ guide_origin is not included (uses default). "
            "⚠️ WARNING: this operation has a monetary cost. Confirm with the user before proceeding.\n"
            "AFTER the guide: check if those addresses are already in your memory. "
            "If they already exist: say 'I already have those addresses saved.' "
            "If not: ask 'Would you like to save them?' "
            "On success, respond with: guide number, carrier, estimated delivery date, and label link. "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Create shipment",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    if name == "track_status":
        guide = args.get("guide", "?")
        text = (
            f"Track guide {guide}. "
            "First call track_guide to get the current status and last update. "
            "If the package appears delayed (estimated date expired or stuck status), "
            "also call track_detail to get the full history and summarize what happened. "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Tracking status",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    if name == "schedule_pickup_tomorrow":
        carrier = args.get("carrier", "?")
        weight = args.get("weight_kg", "?")
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        text = (
            f"Schedule a pickup with {carrier} for tomorrow ({tomorrow}), {weight} kg total. "
            "Use open_time=09:00 and close_time=18:00. "
            "The origin address must be registered in T1Envios beforehand. "
            "If the address is not registered, tell the user it needs to be set up first. "
            "Request data ONE BY ONE: first the contact name, wait for the response, "
            "then last name, phone, email, street, number, neighborhood, municipality, state, ZIP, "
            "references, pieces, and dimensions. Do not ask multiple fields in the same message. "
            "Then call schedule_pickup. Warn the user that this operation has a monetary cost. "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Schedule pickup tomorrow",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    if name == "check_balance_before_ship":
        text = (
            "Check my T1Envios balance with get_balance. "
            "If the balance is less than 200 MXN, let me know I might not have sufficient funds to create a shipment and suggest topping up. "
            "Otherwise, confirm the available balance and let me know I can proceed. "
            "Always respond in the user's language."
        )
        return types.GetPromptResult(
            description="Check balance",
            messages=[
                types.PromptMessage(role="user", content=types.TextContent(type="text", text=text))
            ],
        )

    raise ValueError(f"Unknown prompt: {name}")


def register(server: Server, get_client: Callable) -> None:  # noqa: ARG001
    @server.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return _PROMPTS

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
        return _get_prompt(name, arguments)
