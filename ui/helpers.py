"""UI helper functions — template loading, data extraction, state management."""

import re
import base64
from pathlib import Path
from datetime import date, timedelta

UI_DIR = Path(__file__).parent
STATIC_DIR = UI_DIR / "static"
TEMPLATES_DIR = UI_DIR / "templates"
ASSETS_DIR = UI_DIR / "assets"


# ---- File loaders ----

def load_file(path: Path) -> str:
    """Read a file and return its contents as a string."""
    return path.read_text(encoding="utf-8")


def load_bg_image_base64() -> str:
    """Load background image as base64 string."""
    bg_path = ASSETS_DIR / "bg.png"
    if bg_path.exists():
        return base64.b64encode(bg_path.read_bytes()).decode()
    return ""


def load_css() -> str:
    return load_file(STATIC_DIR / "styles.css")


def load_js() -> str:
    return load_file(STATIC_DIR / "script.js")


# ---- Template rendering ----

def render_landing() -> str:
    """Build the full landing page HTML with CSS, JS, and assets injected."""
    template = load_file(TEMPLATES_DIR / "landing.html")
    css = load_css()
    js = load_js()
    bg = load_bg_image_base64()

    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    html = template.replace("{{CSS}}", css)
    html = html.replace("{{JS}}", js)
    html = html.replace("{{BG_IMAGE}}", bg)
    html = html.replace("{{TODAY}}", today)
    html = html.replace("{{TOMORROW}}", tomorrow)
    return html


def render_chat_header(booking_data: dict) -> str:
    """Build the chat header HTML with route info."""
    template = load_file(TEMPLATES_DIR / "chat_header.html")

    pickup = booking_data.get("pickup_address", "")
    delivery = booking_data.get("delivery_address", "")
    fc = extract_city(pickup)
    tc = extract_city(delivery)
    fp = extract_pincode(pickup)
    tp = extract_pincode(delivery)

    fp_html = f'<span class="pin-badge">{fp}</span>' if fp else ""
    tp_html = f'<span class="pin-badge">{tp}</span>' if tp else ""

    svc = (booking_data.get("service_type") or "—").replace("_", " ").title()
    mode = (booking_data.get("transport_mode") or "—").title()
    pkgs = booking_data.get("num_packages", "—")
    pdate = booking_data.get("pickup_date", "—")
    cost = booking_data.get("estimated_cost")
    cost_s = f"₹{cost}" if cost else "Pending"

    html = template.replace("{{FROM_CITY}}", fc)
    html = html.replace("{{TO_CITY}}", tc)
    html = html.replace("{{FROM_PIN}}", fp_html)
    html = html.replace("{{TO_PIN}}", tp_html)
    html = html.replace("{{DATE}}", str(pdate))
    html = html.replace("{{SERVICE}}", svc)
    html = html.replace("{{MODE}}", mode)
    html = html.replace("{{PACKAGES}}", str(pkgs))
    html = html.replace("{{COST}}", cost_s)
    return html


# ---- Data extraction ----

def extract_city(address: str) -> str:
    """Extract city name from a full address string."""
    if not address:
        return "—"
    parts = [p.strip() for p in address.replace("\n", ",").split(",")]
    if len(parts) >= 3:
        return parts[-2]
    if len(parts) >= 2:
        return parts[-1]
    return parts[0][:30]


def extract_pincode(address: str) -> str:
    """Extract 6-digit Indian PIN code from address."""
    m = re.search(r'\b(\d{6})\b', address or "")
    return m.group(1) if m else ""


# ---- Query params → booking data ----

def parse_query_params(qp: dict) -> dict:
    """Convert URL query params from the landing page form into booking_data dict."""
    prefill = {}

    from_parts = [qp.get("from_address", ""), qp.get("from_city", ""),]
    full_pickup = ", ".join([p for p in from_parts if p])
    if full_pickup:
        prefill["pickup_address"] = full_pickup

    to_parts = [qp.get("to_address", ""), qp.get("to_city", ""),]
    full_delivery = ", ".join([p for p in to_parts if p])
    if full_delivery:
        prefill["delivery_address"] = full_delivery

    if qp.get("pickup_date"):
        prefill["pickup_date"] = qp["pickup_date"]
    if qp.get("service_type"):
        prefill["service_type"] = qp["service_type"].lower().replace("-", "_").replace(" ", "_")
    if qp.get("transport_mode"):
        prefill["transport_mode"] = qp["transport_mode"].lower()

    pkgs = qp.get("num_packages", "")
    if pkgs.isdigit():
        prefill["num_packages"] = int(pkgs)

    wt = qp.get("weight", "")
    try:
        prefill["total_weight_kg"] = float(wt)
    except (ValueError, TypeError):
        pass

    return prefill


def build_greeting(qp: dict) -> tuple[str, str]:
    """Build the initial user message and bot greeting from query params."""
    fc = qp.get("from_city", "—")
    tc = qp.get("to_city", "—")
    svc = qp.get("service_type", "Standard")
    mode = qp.get("transport_mode", "Road")
    pd_ = qp.get("pickup_date", "—")
    pkgs = qp.get("num_packages", "1")
    wt = qp.get("weight", "1")

    user_msg = f"Book parcel {fc} → {tc}. Date: {pd_}, {svc} ({mode}), {pkgs} pkg, {wt}kg"

    bot_msg = (
        f"I've captured your shipment:\n\n"
        f"**{fc} → {tc}**\n\n"
        f"📅 **{pd_}** | 🚚 **{svc}** | 🛤️ **{mode}** | 📦 **{pkgs} pkg** | ⚖️ **{wt}kg**\n\n"
        f"---\n\nNow please share:\n1. **Shipper's name**\n2. **Phone number**\n3. **Email address**"
    )

    return user_msg, bot_msg
