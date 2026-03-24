"""Node functions for the LangGraph booking agent."""

import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import ToolNode

from agent.prompts import SYSTEM_PROMPT, build_dynamic_prompt
from agent.tools import ALL_TOOLS
from config import OLLAMA_BASE_URL, MODEL_NAME, SECTIONS, SECTION_FIELDS

logger = logging.getLogger(__name__)

# Initialize the LLM with tool binding
llm = ChatOllama(
    model=MODEL_NAME,
    base_url=OLLAMA_BASE_URL,
    temperature=0.3,
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

# Prebuilt tool executor
tool_node = ToolNode(ALL_TOOLS)


def conversation_node(state: dict) -> dict:
    """Call the LLM with current context and tools."""
    current_section = state.get("current_section", "greeting")
    booking_data = state.get("booking_data", {})
    validation_errors = state.get("validation_errors", [])

    # Build dynamic system prompt
    dynamic = build_dynamic_prompt(current_section, booking_data, validation_errors)
    full_prompt = SYSTEM_PROMPT + dynamic

    # Get messages, prepend system prompt
    messages = state["messages"]
    system_msg = SystemMessage(content=full_prompt)

    # Filter to keep only recent messages to avoid context overflow for small model
    # Keep system + last 20 messages
    recent_messages = messages[-20:] if len(messages) > 20 else messages
    llm_messages = [system_msg] + recent_messages

    try:
        response = llm_with_tools.invoke(llm_messages)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        response = AIMessage(content="I'm having trouble connecting to my language model. Please try again in a moment.")

    return {
        "messages": [response],
        "validation_errors": [],  # clear errors after communicating them
    }


def tool_executor_node(state: dict) -> dict:
    """Execute tool calls from the LLM response with fallback parsing."""
    try:
        result = tool_node.invoke(state)
        return result
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        # Return error as tool message so the LLM can retry
        last_msg = state["messages"][-1]
        error_messages = []
        if hasattr(last_msg, "tool_calls"):
            for tc in last_msg.tool_calls:
                error_messages.append(
                    ToolMessage(
                        content=f"Tool call failed: {str(e)}. Please try again with correct arguments.",
                        tool_call_id=tc["id"],
                    )
                )
        if not error_messages:
            error_messages = [AIMessage(content="I encountered an error processing that. Let me try again.")]
        return {"messages": error_messages}


def state_updater_node(state: dict) -> dict:
    """Update booking_data from tool results and advance sections."""
    messages = state["messages"]
    booking_data = dict(state.get("booking_data", {}))
    current_section = state.get("current_section", "greeting")
    validation_errors = list(state.get("validation_errors", []))

    # Process recent tool messages
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue

        try:
            result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(result, dict):
            continue

        # Handle store_field results
        if result.get("stored") and "field" in result and "value" in result:
            booking_data[result["field"]] = result["value"]
            continue

        # Handle validation results
        if "valid" in result:
            if not result["valid"]:
                error = result.get("error") or result.get("suggestion", "Validation failed")
                validation_errors.append(error)

        # Handle phone validation - store formatted number
        if "formatted" in result and result.get("valid"):
            # Determine which phone field based on current section
            if current_section == "shipper":
                booking_data["shipper_phone"] = result["formatted"]
            elif current_section == "consignee":
                booking_data["consignee_phone"] = result["formatted"]

        # Handle email validation
        if "normalized" in result and result.get("valid"):
            if current_section == "shipper":
                booking_data["shipper_email"] = result["normalized"]
            elif current_section == "consignee":
                booking_data["consignee_email"] = result["normalized"]

        # Handle rate calculation
        if "total_cost" in result and result.get("available"):
            booking_data["estimated_cost"] = result["total_cost"]
            booking_data["rate_card_id"] = result.get("rate_card_id")

        # Handle booking save
        if "booking_ref" in result and result.get("success"):
            return {
                "booking_data": booking_data,
                "booking_ref": result["booking_ref"],
                "current_section": "confirmed",
                "validation_errors": [],
            }

    # Extract field values from store_field tool calls and other tool call arguments
    for msg in messages[-10:]:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                args = tc.get("args", {})
                # store_field — primary mechanism for field storage
                if tc["name"] == "store_field":
                    fname = args.get("field_name", "")
                    fval = args.get("field_value", "")
                    if fname and fval:
                        booking_data[fname] = fval
                # save_booking
                elif tc["name"] == "save_booking" and "booking_data" in args:
                    bd = args["booking_data"]
                    if isinstance(bd, dict):
                        booking_data.update(bd)
                # format_summary
                elif tc["name"] == "format_summary" and "booking_data" in args:
                    bd = args["booking_data"]
                    if isinstance(bd, dict):
                        booking_data.update(bd)
                # calculate_shipping_rate
                elif tc["name"] == "calculate_shipping_rate":
                    for k, bk in [("transport_mode", "transport_mode"), ("service_type", "service_type"),
                                   ("weight_kg", "total_weight_kg"), ("num_packages", "num_packages")]:
                        if k in args:
                            booking_data[bk] = args[k]

    # Check if current section is complete -> advance
    if current_section in SECTION_FIELDS:
        required = SECTION_FIELDS[current_section]
        if required:
            filled = all(booking_data.get(f) for f in required)
        else:
            # Optional-only sections advance after one turn
            filled = True

        if filled and not validation_errors:
            # Advance to next section
            try:
                idx = SECTIONS.index(current_section)
                if idx + 1 < len(SECTIONS):
                    current_section = SECTIONS[idx + 1]
            except ValueError:
                pass

    return {
        "booking_data": booking_data,
        "current_section": current_section,
        "validation_errors": validation_errors,
    }


def route_after_llm(state: dict) -> str:
    """Route after LLM response: to tools if tool calls exist, else end turn."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tool_executor"
    return "__end__"


def route_after_tools(state: dict) -> str:
    """Route after tool execution: always go to state updater."""
    return "state_updater"


def route_after_state_update(state: dict) -> str:
    """Route after state update: back to conversation or end."""
    current_section = state.get("current_section", "greeting")
    if current_section == "confirmed":
        return "__end__"
    # If there are validation errors, go back to conversation to communicate them
    if state.get("validation_errors"):
        return "conversation"
    return "__end__"
