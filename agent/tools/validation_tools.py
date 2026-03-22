"""Validation tools for phone, email, and address."""

import re
import phonenumbers
from email_validator import validate_email as _validate_email, EmailNotValidError
from langchain_core.tools import tool


@tool
def validate_phone(phone: str, country_code: str = "IN") -> dict:
    """Validate a phone number and return formatted version.
    Args:
        phone: The phone number string to validate.
        country_code: ISO country code, defaults to IN (India).
    """
    try:
        parsed = phonenumbers.parse(phone, country_code)
        if phonenumbers.is_valid_number(parsed):
            formatted = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
            return {"valid": True, "formatted": formatted, "error": ""}
        return {"valid": False, "formatted": "", "error": "Invalid phone number."}
    except phonenumbers.NumberParseException as e:
        return {"valid": False, "formatted": "", "error": str(e)}


@tool
def validate_email(email: str) -> dict:
    """Validate an email address.
    Args:
        email: The email address to validate.
    """
    try:
        result = _validate_email(email, check_deliverability=False)
        return {"valid": True, "normalized": result.normalized, "error": ""}
    except EmailNotValidError as e:
        return {"valid": False, "normalized": "", "error": str(e)}


@tool
def validate_address(address: str) -> dict:
    """Validate a shipping address (basic heuristic check).
    Args:
        address: The full address string to validate.
    """
    if len(address.strip()) < 10:
        return {"valid": False, "suggestion": "Address seems too short. Please include street, city, state, and PIN code."}

    # Check for PIN code pattern (Indian 6-digit)
    has_pin = bool(re.search(r'\b\d{6}\b', address))

    if not has_pin:
        return {
            "valid": False,
            "suggestion": "Address is missing a PIN code. Please include the 6-digit PIN code.",
        }

    return {"valid": True, "suggestion": ""}
