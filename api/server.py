"""FastAPI server — serves frontend, login, chat, session persistence."""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from langchain_core.messages import HumanMessage, AIMessage

from db.database import init_db, SessionLocal
from db.models import User, ChatSession, ChatMessage
from agent.graph import compiled_graph

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
ASSETS_DIR = Path(__file__).resolve().parent.parent / "ui" / "assets"

app = FastAPI(title="LogiBot API")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

init_db()


# ---- Models ----

class LoginRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None


class LoginResponse(BaseModel):
    user_id: int
    name: str
    is_new: bool


class ChatRequest(BaseModel):
    session_id: str
    user_id: int
    message: str
    booking_data: dict = {}
    current_section: str = "greeting"
    booking_ref: str = ""


class ChatResponse(BaseModel):
    reply: str
    booking_data: dict
    current_section: str
    booking_ref: str
    session_id: str


class SessionResponse(BaseModel):
    found: bool
    session_id: str = ""
    booking_data: dict = {}
    current_section: str = "greeting"
    booking_ref: str = ""
    messages: list = []


# ---- Pages ----

@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/chat")
async def chat_page():
    return FileResponse(FRONTEND_DIR / "chat.html")


# ---- Login ----

@app.post("/api/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == req.phone.strip()).first()
        if user:
            # Update name/email if provided
            if req.name:
                user.name = req.name
            if req.email:
                user.email = req.email
            db.commit()
            return LoginResponse(user_id=user.id, name=user.name, is_new=False)
        else:
            user = User(
                name=req.name.strip(),
                phone=req.phone.strip(),
                email=req.email.strip() if req.email else None,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return LoginResponse(user_id=user.id, name=user.name, is_new=True)
    finally:
        db.close()


# ---- Session Resume ----

@app.get("/api/session/{user_id}", response_model=SessionResponse)
async def get_session(user_id: int):
    db = SessionLocal()
    try:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id, ChatSession.is_complete == False)
            .order_by(ChatSession.updated_at.desc())
            .first()
        )
        if not session:
            return SessionResponse(found=False)

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        booking_data = json.loads(session.booking_data_json) if session.booking_data_json else {}

        return SessionResponse(
            found=True,
            session_id=session.session_id,
            booking_data=booking_data,
            current_section=session.current_section or "greeting",
            booking_ref=session.booking_ref or "",
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
    finally:
        db.close()


# ---- Chat ----

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    db = SessionLocal()
    try:
        # Ensure session exists in DB
        session = db.query(ChatSession).filter(ChatSession.session_id == req.session_id).first()
        if not session:
            session = ChatSession(
                session_id=req.session_id,
                user_id=req.user_id,
                booking_data_json=json.dumps(req.booking_data),
                current_section=req.current_section,
            )
            db.add(session)
            db.commit()

        # Save user message
        db.add(ChatMessage(session_id=req.session_id, role="user", content=req.message))
        db.commit()

        # Run agent
        config = {"configurable": {"thread_id": req.session_id}}
        input_state = {
            "messages": [HumanMessage(content=req.message)],
            "booking_data": req.booking_data,
            "current_section": req.current_section,
            "validation_errors": [],
            "booking_ref": req.booking_ref,
        }

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

            new_booking_data = result.get("booking_data", {})
            new_section = result.get("current_section", "greeting")
            new_ref = result.get("booking_ref", "")

        except Exception as e:
            ai_response = f"Error: {str(e)[:300]}. Make sure Ollama is running."
            new_booking_data = req.booking_data
            new_section = req.current_section
            new_ref = req.booking_ref

        # Save bot reply
        db.add(ChatMessage(session_id=req.session_id, role="bot", content=ai_response))

        # Update session state
        session.booking_data_json = json.dumps(new_booking_data)
        session.current_section = new_section
        session.booking_ref = new_ref
        if new_section == "confirmed":
            session.is_complete = True
        session.updated_at = datetime.now(timezone.utc)
        db.commit()

        return ChatResponse(
            reply=ai_response,
            booking_data=new_booking_data,
            current_section=new_section,
            booking_ref=new_ref,
            session_id=req.session_id,
        )
    finally:
        db.close()
