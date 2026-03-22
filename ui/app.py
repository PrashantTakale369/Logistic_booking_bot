"""LogiBot — Streamlit Application Entry Point."""

import sys
import uuid
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

from db.database import init_db
from agent.graph import compiled_graph
from ui.helpers import render_chat_header, load_bg_image_base64

st.set_page_config(
    page_title="LogiBot - Parcel Booking",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()


def get_thread_id():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    return st.session_state.thread_id


def reset_conversation():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.booking_data = {}
    st.session_state.current_section = "greeting"
    st.session_state.booking_ref = ""
    st.session_state.page = "landing"


if "page" not in st.session_state:
    reset_conversation()


# ==================================================
# PAGE: Landing
# ==================================================
if st.session_state.page == "landing":

    bg = load_bg_image_base64()

    # Background image as a fixed div
    st.markdown(
        f'<div style="position:fixed;top:0;left:0;width:100%;height:100%;'
        f'background:url(data:image/png;base64,{bg}) center/cover no-repeat;'
        f'z-index:0;"></div>',
        unsafe_allow_html=True,
    )

    # Global styles
    st.markdown("""<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: transparent !important; }
[data-testid="stAppViewContainer"] > div { position: relative; z-index: 1; }
.stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label {
    color: #555 !important; font-size: 11px !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: 0.5px !important;
}
.stTextInput > div > div > input {
    border: 2px solid #e0e4ea !important; border-radius: 8px !important;
    color: #1a1a2e !important; background: #fff !important; font-size: 16px !important;
}
.stTextInput > div > div > input:focus { border-color: #4a8df8 !important; }
.stTextInput > div > div > input::placeholder { color: #bbb !important; }
.stSelectbox > div > div { border-radius: 8px !important; }
.stDateInput > div > div > input { border-radius: 8px !important; color: #1a1a2e !important; }
.stNumberInput > div > div > input { border-radius: 8px !important; color: #1a1a2e !important; }
div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4a8df8, #667eea) !important;
    color: #fff !important; font-size: 18px !important; font-weight: 800 !important;
    letter-spacing: 3px !important; text-transform: uppercase !important;
    padding: 14px 48px !important; border-radius: 40px !important; border: none !important;
    box-shadow: 0 6px 25px rgba(74,141,248,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 10px 35px rgba(74,141,248,0.55) !important;
    transform: translateY(-2px) !important;
}
</style>""", unsafe_allow_html=True)

    # Logo
    st.markdown(
        '<div style="max-width:1100px;margin:0 auto;padding:16px 32px 8px 32px;">'
        '<span style="font-size:24px;font-weight:900;">'
        '📦 <span style="color:#fff;">Logi</span><span style="color:#4a8df8;">Bot</span>'
        '</span></div>',
        unsafe_allow_html=True,
    )

    # White card start
    st.markdown(
        '<div style="max-width:1100px;margin:10px auto;background:rgba(255,255,255,0.97);'
        'border-radius:14px;padding:24px 28px;box-shadow:0 8px 40px rgba(0,0,0,0.25);">',
        unsafe_allow_html=True,
    )

    # From / To
    col_f, col_s, col_t = st.columns([10, 1, 10])
    with col_f:
        st.markdown('<p style="font-size:12px;color:#888;font-weight:600;margin:0 0 4px 0;">From</p>', unsafe_allow_html=True)
        from_city = st.text_input("from_city", key="fc", placeholder="Mumbai", label_visibility="collapsed")
        from_addr = st.text_input("from_addr", key="fa", placeholder="Address, State, PIN Code", label_visibility="collapsed")
    with col_s:
        st.markdown('<p style="text-align:center;color:#4a8df8;font-size:22px;margin-top:32px;">⇄</p>', unsafe_allow_html=True)
    with col_t:
        st.markdown('<p style="font-size:12px;color:#888;font-weight:600;margin:0 0 4px 0;">To</p>', unsafe_allow_html=True)
        to_city = st.text_input("to_city", key="tc", placeholder="Bangalore", label_visibility="collapsed")
        to_addr = st.text_input("to_addr", key="ta", placeholder="Address, State, PIN Code", label_visibility="collapsed")

    st.markdown('<hr style="border:none;height:1px;background:#e0e4ea;margin:16px 0;">', unsafe_allow_html=True)

    # Details
    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        pickup_date = st.date_input("📅 Pickup Date", value=date.today() + timedelta(days=1), min_value=date.today())
    with d2:
        service = st.selectbox("🚚 Service", ["Standard", "Express", "Same-day", "Overnight"], index=1)
    with d3:
        transport = st.selectbox("🛤️ Transport", ["Road", "Air", "Rail", "Sea"], index=1)
    with d4:
        num_packages = st.number_input("📦 Packages", min_value=1, max_value=100, value=1)
    with d5:
        weight = st.number_input("⚖️ Weight (kg)", min_value=0.1, max_value=5000.0, value=5.0, step=0.5)

    # Chips
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin:14px 0 8px 0;">'
        '<span style="font-size:11px;font-weight:800;color:#1a1a2e;text-transform:uppercase;line-height:1.2;">Special<br>Rates</span>'
        '<span style="border:2px solid #4a8df8;border-radius:8px;padding:6px 14px;text-align:center;background:rgba(74,141,248,.05);">'
        '  <span style="font-size:12px;font-weight:700;color:#4a8df8;">Regular</span><br><span style="font-size:9px;color:#999;">Standard rates</span></span>'
        '<span style="border:2px solid #e0e4ea;border-radius:8px;padding:6px 14px;text-align:center;">'
        '  <span style="font-size:12px;font-weight:700;color:#1a1a2e;">Bulk</span><br><span style="font-size:9px;color:#999;">10+ parcels</span></span>'
        '<span style="border:2px solid #e0e4ea;border-radius:8px;padding:6px 14px;text-align:center;">'
        '  <span style="font-size:12px;font-weight:700;color:#1a1a2e;">Corporate</span><br><span style="font-size:9px;color:#999;">Business</span></span>'
        '<span style="border:2px solid #e0e4ea;border-radius:8px;padding:6px 14px;text-align:center;">'
        '  <span style="font-size:12px;font-weight:700;color:#1a1a2e;">Fragile</span><br><span style="font-size:9px;color:#999;">Special handling</span></span>'
        '<span style="border:2px solid #e0e4ea;border-radius:8px;padding:6px 14px;text-align:center;">'
        '  <span style="font-size:12px;font-weight:700;color:#1a1a2e;">Perishable</span><br><span style="font-size:9px;color:#999;">Cold chain</span></span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")

    # START NOW
    c1, c2, c3 = st.columns([2, 3, 2])
    with c2:
        if st.button("START NOW", use_container_width=True, type="primary"):
            full_pickup = ", ".join([p for p in [from_addr.strip(), from_city.strip()] if p])
            full_delivery = ", ".join([p for p in [to_addr.strip(), to_city.strip()] if p])

            prefill = {}
            if full_pickup:
                prefill["pickup_address"] = full_pickup
            if full_delivery:
                prefill["delivery_address"] = full_delivery
            prefill["pickup_date"] = str(pickup_date)
            prefill["service_type"] = service.lower().replace("-", "_").replace(" ", "_")
            prefill["transport_mode"] = transport.lower()
            prefill["num_packages"] = num_packages
            prefill["total_weight_kg"] = weight

            st.session_state.booking_data = prefill
            st.session_state.current_section = "shipper"

            fc = from_city or "Pickup"
            tc = to_city or "Delivery"
            user_msg = f"Book parcel {fc} → {tc}. Date: {pickup_date}, {service} ({transport}), {num_packages} pkg, {weight}kg"
            bot_msg = (
                f"I've captured your shipment:\n\n"
                f"**{fc} → {tc}**\n\n"
                f"📅 **{pickup_date}** | 🚚 **{service}** | 🛤️ **{transport}** | 📦 **{num_packages} pkg** | ⚖️ **{weight}kg**\n\n"
                f"---\n\nNow please share:\n1. **Shipper's name**\n2. **Phone number**\n3. **Email address**"
            )
            st.session_state.messages = [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": bot_msg},
            ]
            st.session_state.page = "chat"
            st.rerun()

    # White card end
    st.markdown('</div>', unsafe_allow_html=True)


# ==================================================
# PAGE: Chat
# ==================================================
elif st.session_state.page == "chat":
    st.markdown("""<style>
#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 900px !important; margin: 0 auto !important; padding: 20px !important; }
.stChatMessage { border-radius: 12px !important; }
</style>""", unsafe_allow_html=True)

    header_html = render_chat_header(st.session_state.booking_data)
    st.markdown(header_html, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        config = {"configurable": {"thread_id": get_thread_id()}}
        input_state = {
            "messages": [HumanMessage(content=user_input)],
            "booking_data": st.session_state.booking_data,
            "current_section": st.session_state.current_section,
            "validation_errors": [],
            "booking_ref": st.session_state.get("booking_ref", ""),
        }

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Processing..."):
                try:
                    result = compiled_graph.invoke(input_state, config)
                    ai_response = ""
                    for msg in reversed(result["messages"]):
                        if isinstance(msg, AIMessage) and msg.content:
                            if not getattr(msg, "tool_calls", None):
                                ai_response = msg.content
                                break
                            else:
                                ai_response = msg.content
                                break
                    if not ai_response:
                        ai_response = "Could you please repeat that?"
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    st.session_state.booking_data = result.get("booking_data", {})
                    st.session_state.current_section = result.get("current_section", "greeting")
                    st.session_state.booking_ref = result.get("booking_ref", "")
                except Exception as e:
                    err = f"**Error:** `{str(e)[:200]}`\n\nMake sure Ollama is running: `ollama serve`"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})
        st.rerun()
