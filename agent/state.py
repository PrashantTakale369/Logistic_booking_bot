"""LangGraph state definition for the booking agent."""

from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class BookingState(TypedDict):
    """State schema for the parcel booking agent graph."""

    # Chat message history (auto-appended via add_messages reducer)
    messages: Annotated[list[BaseMessage], add_messages]

    # Accumulated booking field values, starts as {}
    booking_data: dict

    # Current questionnaire section
    # One of: greeting, shipper, consignee, shipment, service,
    #         documentation, payment, additional, summary, confirmed
    current_section: str

    # Validation errors from the last tool execution
    validation_errors: list[str]

    # Set after booking is saved
    booking_ref: str
