"""Agent state graph."""

from langgraph.graph import StateGraph, END
from src.agent.state import AgentState
from src.agent.nodes import retrieve, grade_documents, web_search, generate, plan_step


def build_graph():
    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("plan", plan_step)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate", generate)

    # Entry point
    workflow.set_entry_point("plan")

    # Edges
    workflow.add_edge("plan", "retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    def decide_to_search(state: AgentState):
        if state.web_search_needed:
            return "web_search"
        return "generate"

    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_search,
        {"web_search": "web_search", "generate": "generate"},
    )

    workflow.add_edge("web_search", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()
