"""Agent state graph with tool calling and smart routing."""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage, HumanMessage
from src.agent.state import AgentState
from src.agent.nodes import (
    retrieve,
    grade_documents,
    generate,
    plan_step,
    agent_with_tools,
    classify_input,
    generate_greeting,
)
from src.tools import ALL_TOOLS


def should_use_tools(state: AgentState) -> str:
    """Decide if we need to call tools or go to generate."""
    messages = state.chat_history

    tool_count = 0
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            break
        if isinstance(m, ToolMessage):
            tool_count += 1

    if tool_count > 3:
        return "generate"

    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    return "generate"


def build_graph():
    """Build the agent workflow graph."""
    workflow = StateGraph(AgentState)

    tool_node = ToolNode(ALL_TOOLS, messages_key="chat_history")

    workflow.add_node("classify", classify_input)
    workflow.add_node("plan", plan_step)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("agent", agent_with_tools)
    workflow.add_node("tools", tool_node)
    workflow.add_node("generate", generate)
    workflow.add_node("greeting", generate_greeting)

    workflow.set_entry_point("classify")

    def route_by_type(state: AgentState):
        if state.input_type == "greeting":
            return "greeting"
        if state.input_type == "command":
            return "agent"
        return "plan"

    workflow.add_conditional_edges(
        "classify",
        route_by_type,
        {"greeting": "greeting", "agent": "agent", "plan": "plan"},
    )

    # Greeting goes straight to END
    workflow.add_edge("greeting", END)

    # RAG path: Plan → Retrieve → Grade → Generate
    workflow.add_edge("plan", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    def decide_after_grade(state: AgentState):
        if state.web_search_needed:
            return "agent"
        return "generate"

    workflow.add_conditional_edges(
        "grade_documents",
        decide_after_grade,
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
