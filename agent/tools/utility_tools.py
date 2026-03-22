"""Utility tools."""

from datetime import datetime, timezone, timedelta

from langchain_core.tools import tool


IST = timezone(timedelta(hours=5, minutes=30))


@tool
def get_current_datetime() -> str:
    """Get the current date and time in IST (Indian Standard Time)."""
    now = datetime.now(IST)
    return now.strftime("%A, %d %B %Y, %I:%M %p IST")


@tool
def format_summary(booking_data: dict) -> str:
    """Format collected booking data into a readable summary for user confirmation.
    Args:
        booking_data: Dictionary of all collected booking fields.
    """
    sections = {
        "Shipper Details": [
            ("Name", "shipper_name"),
            ("Contact", "shipper_contact"),
            ("Phone", "shipper_phone"),
            ("Email", "shipper_email"),
            ("Pickup Address", "pickup_address"),
            ("Pickup Date", "pickup_date"),
            ("Pickup Time", "pickup_time"),
        ],
        "Consignee Details": [
            ("Name", "consignee_name"),
            ("Contact", "consignee_contact"),
            ("Phone", "consignee_phone"),
            ("Email", "consignee_email"),
            ("Delivery Address", "delivery_address"),
            ("Preferred Delivery Date", "preferred_delivery_date"),
        ],
        "Shipment Details": [
            ("Type of Goods", "goods_type"),
            ("Number of Packages", "num_packages"),
            ("Total Weight (kg)", "total_weight_kg"),
            ("Dimensions", "dimensions"),
            ("Total Volume (CBM)", "total_volume_cbm"),
            ("Declared Value (INR)", "declared_value"),
            ("Fragile", "is_fragile"),
            ("Perishable", "is_perishable"),
            ("Special Handling", "special_handling"),
        ],
        "Service": [
            ("Service Type", "service_type"),
            ("Transport Mode", "transport_mode"),
        ],
        "Documentation": [
            ("Invoice Number", "invoice_number"),
            ("Packing List", "packing_list"),
            ("E-way Bill", "eway_bill"),
        ],
        "Payment": [
            ("Payment Mode", "payment_mode"),
            ("Insurance", "insurance_opted"),
            ("Insured Value", "insured_value"),
        ],
        "Additional": [
            ("Delivery Confirmation", "delivery_confirmation"),
            ("Return Option", "return_option"),
            ("Remarks", "remarks"),
        ],
    }

    lines = ["=" * 40, "BOOKING SUMMARY", "=" * 40]
    for section_name, fields in sections.items():
        lines.append(f"\n--- {section_name} ---")
        for label, key in fields:
            value = booking_data.get(key, "")
            if value not in (None, "", False):
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                lines.append(f"  {label}: {value}")

    cost = booking_data.get("estimated_cost")
    if cost:
        lines.append(f"\n--- Estimated Cost: ₹{cost} ---")

    lines.append("=" * 40)
    return "\n".join(lines)
