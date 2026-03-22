"""Tests for agent tools."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.tools.validation_tools import validate_phone, validate_email, validate_address


def test_validate_phone_valid():
    result = validate_phone.invoke({"phone": "+919876543210"})
    assert result["valid"] is True
    assert result["formatted"] != ""


def test_validate_phone_invalid():
    result = validate_phone.invoke({"phone": "abc"})
    assert result["valid"] is False


def test_validate_phone_short():
    result = validate_phone.invoke({"phone": "123"})
    assert result["valid"] is False


def test_validate_email_valid():
    result = validate_email.invoke({"email": "user@example.com"})
    assert result["valid"] is True
    assert result["normalized"] != ""


def test_validate_email_invalid():
    result = validate_email.invoke({"email": "not-an-email"})
    assert result["valid"] is False


def test_validate_address_valid():
    result = validate_address.invoke({"address": "123 MG Road, Mumbai, Maharashtra 400001"})
    assert result["valid"] is True


def test_validate_address_too_short():
    result = validate_address.invoke({"address": "abc"})
    assert result["valid"] is False


def test_validate_address_no_pin():
    result = validate_address.invoke({"address": "123 MG Road, Mumbai, Maharashtra"})
    assert result["valid"] is False
