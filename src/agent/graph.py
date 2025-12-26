"""Agent state graph with tool calling."""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from src.agent.state import AgentState
from src.agent.nodes import (
    retrieve,
    grade_documents,
    generate,
    plan_step,
    agent_with_tools,
)
from src.tools import ALL_TOOLS


def should_use_tools(state: AgentState) -> str:
    """Decide if we need to call tools or go to generate."""
    # Check if the last message has tool calls
    messages = state.chat_history
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    return "generate"


def build_graph():
    """Build the agent workflow graph."""
    workflow = StateGraph(AgentState)

    # Create tool node
    tool_node = ToolNode(ALL_TOOLS)

    # Nodes
    workflow.add_node("plan", plan_step)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("agent", agent_with_tools) 
    workflow.add_node("tools", tool_node)
    workflow.add_node("generate", generate)

    # Entry point
    workflow.set_entry_point("plan")

    # Edges
    workflow.add_edge("plan", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    def decide_to_search(state: AgentState):
        if state.web_search_needed:
            return "agent" 
        return "generate"

    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_search,
        {"agent": "agent", "generate": "generate"},
    )

    # Agent can call tools or go to generate
    workflow.add_conditional_edges(
        "agent",
        should_use_tools,
        {"tools": "tools", "generate": "generate"},
    )

    # After tools, go back to agent to process results
    workflow.add_edge("tools", "agent")
    workflow.add_edge("generate", END)

    return workflow.compile()
