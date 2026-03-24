import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:4b")

# Database
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "db" / "logistics.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Booking reference prefix
BOOKING_REF_PREFIX = "LB"

# Questionnaire sections in order
SECTIONS = [
    "greeting",
    "shipper",
    "consignee",
    "shipment",
    "service",
    "documentation",
    "payment",
    "additional",
    "summary",
    "confirmed",
]

# Required fields per section
SECTION_FIELDS = {
    "shipper": [
        "shipper_name", "shipper_contact", "shipper_phone",
        "shipper_email", "pickup_address", "pickup_date",
    ],
    "consignee": [
        "consignee_name", "consignee_contact", "consignee_phone",
        "consignee_email", "delivery_address",
    ],
    "shipment": [
        "goods_type", "num_packages", "total_weight_kg",
        "dimensions", "declared_value",
    ],
    "service": ["service_type", "transport_mode"],
    "documentation": [],  # all optional
    "payment": ["payment_mode"],
    "additional": [],  # all optional
}
