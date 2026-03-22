"""LangGraph StateGraph definition for the booking agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import BookingState
from agent.nodes import (
    conversation_node,
    tool_executor_node,
    state_updater_node,
    route_after_llm,
    route_after_state_update,
)

# Build the graph
workflow = StateGraph(BookingState)

# Add nodes
workflow.add_node("conversation", conversation_node)
workflow.add_node("tool_executor", tool_executor_node)
workflow.add_node("state_updater", state_updater_node)

# Set entry point
workflow.set_entry_point("conversation")

# Add conditional edges after conversation node
workflow.add_conditional_edges(
    "conversation",
    route_after_llm,
    {
        "tool_executor": "tool_executor",
        "__end__": END,
    },
)

# After tool execution -> always go to state updater
workflow.add_edge("tool_executor", "state_updater")

# After state update -> back to conversation (for errors) or end turn
workflow.add_conditional_edges(
    "state_updater",
    route_after_state_update,
    {
        "conversation": "conversation",
        "__end__": END,
    },
)

# Compile with memory checkpointer for session persistence
memory = MemorySaver()
compiled_graph = workflow.compile(checkpointer=memory)
