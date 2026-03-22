from agent.tools.validation_tools import validate_phone, validate_email, validate_address
from agent.tools.rate_tools import calculate_shipping_rate, check_service_availability
from agent.tools.booking_tools import save_booking, lookup_booking, cancel_booking
from agent.tools.utility_tools import get_current_datetime, format_summary

ALL_TOOLS = [
    validate_phone,
    validate_email,
    validate_address,
    calculate_shipping_rate,
    check_service_availability,
    save_booking,
    lookup_booking,
    cancel_booking,
    get_current_datetime,
    format_summary,
]
