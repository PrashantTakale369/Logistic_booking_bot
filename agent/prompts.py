"""System prompts for the booking agent."""

SYSTEM_PROMPT = """You are a friendly logistics booking assistant. Help users book parcel shipments by collecting information step by step.

RULES:
1. Ask for ONE section at a time. Do not dump all questions at once.
2. When user provides a phone number, ALWAYS call validate_phone tool before accepting it.
3. When user provides an email, ALWAYS call validate_email tool before accepting it.
4. When user provides an address, ALWAYS call validate_address tool before accepting it.
5. When shipment and service details are collected, call calculate_shipping_rate to show the cost.
6. Before that, you may call check_service_availability to show available options.
7. Be conversational and helpful. If a validation fails, politely ask the user to correct it.
8. When all sections are done, call format_summary and ask user to confirm.
9. On confirmation, call save_booking with all collected data.
10. If user wants to look up a booking, call lookup_booking.
11. If user wants to cancel, call cancel_booking.

AVAILABLE TOOLS: validate_phone, validate_email, validate_address, calculate_shipping_rate, check_service_availability, save_booking, lookup_booking, cancel_booking, get_current_datetime, format_summary"""


def build_dynamic_prompt(current_section: str, booking_data: dict, validation_errors: list) -> str:
    """Build the dynamic state context to inject into the system prompt."""

    section_fields = {
        "shipper": {
            "required": ["shipper_name", "shipper_contact", "shipper_phone", "shipper_email", "pickup_address", "pickup_date"],
            "optional": ["pickup_time"],
            "ask": "Ask for the shipper (sender) details: name, contact person, phone, email, pickup address, and preferred pickup date/time.",
        },
        "consignee": {
            "required": ["consignee_name", "consignee_contact", "consignee_phone", "consignee_email", "delivery_address"],
            "optional": ["preferred_delivery_date"],
            "ask": "Ask for the consignee (receiver) details: name, contact person, phone, email, delivery address, and preferred delivery date.",
        },
        "shipment": {
            "required": ["goods_type", "num_packages", "total_weight_kg", "dimensions", "declared_value"],
            "optional": ["total_volume_cbm", "is_fragile", "is_perishable", "special_handling"],
            "ask": "Ask for shipment details: type of goods, number of packages, weight, dimensions (L×W×H), declared value, and whether fragile/perishable.",
        },
        "service": {
            "required": ["service_type", "transport_mode"],
            "optional": [],
            "ask": "Ask which service type (standard/express/same-day/overnight) and transport mode (road/air/rail/sea) they prefer. Call check_service_availability first to show options.",
        },
        "documentation": {
            "required": [],
            "optional": ["invoice_number", "packing_list", "eway_bill"],
            "ask": "Ask about documentation: invoice number, packing list, and e-way bill (if applicable). These are optional.",
        },
        "payment": {
            "required": ["payment_mode"],
            "optional": ["insurance_opted", "insured_value"],
            "ask": "Ask for payment mode (prepaid/COD/credit) and whether they want insurance.",
        },
        "additional": {
            "required": [],
            "optional": ["delivery_confirmation", "return_option", "remarks"],
            "ask": "Ask about additional preferences: delivery confirmation, return option if undelivered, and any remarks. These are optional.",
        },
        "summary": {
            "required": [],
            "optional": [],
            "ask": "Call format_summary with the booking_data and present it. Ask user to confirm with 'yes' or request corrections.",
        },
    }

    if current_section == "greeting":
        return f"\n\nCURRENT STATE:\n- Section: greeting\n- Greet the user and ask if they want to book a new parcel or look up an existing booking."

    if current_section == "confirmed":
        return f"\n\nCURRENT STATE:\n- Section: confirmed\n- Booking is complete. Thank the user and provide the booking reference."

    info = section_fields.get(current_section, {})
    collected_keys = list(booking_data.keys())
    required = info.get("required", [])
    missing = [f for f in required if f not in booking_data or not booking_data[f]]

    errors_str = ""
    if validation_errors:
        errors_str = f"\n- Errors to communicate: {'; '.join(validation_errors)}"

    return f"""

CURRENT STATE:
- Section: {current_section}
- Collected so far: {collected_keys}
- Missing required fields: {missing}
- Instruction: {info.get('ask', '')}
{errors_str}

Ask for the missing fields naturally. Validate each value using appropriate tools."""
