"""Agent entry point."""

from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph import build_graph
from typing import Callable, Optional

# User-friendly step names (no emojis per user request)
STEP_NAMES = {
    "reformulate": "Understanding query...",
    "classify": "Analyzing intent...",
    "plan": "Planning response...",
    "retrieve": "Searching documents...",
    "grade_documents": "Evaluating relevance...",
    "call_agent": "Processing...",
    "tools": "Using tools...",
    "generate": "Writing response...",
    "small_talk": "Responding...",
}


async def chat(
    user_input: str,
    chat_store=None,
    chat_history: list = None,
    include_thinking: bool = False,
    on_step: Optional[Callable[[str], None]] = None,
) -> str | dict:
    """Run the agent graph with user input.

    Args:
        user_input: The user's question
        chat_store: Optional chat-specific vector store
        chat_history: Optional conversation history
        include_thinking: If True, returns dict with 'answer' and 'thinking' steps
        on_step: Optional callback called with user-friendly step name on each step

    Returns:
        str: Just the answer (default)
        dict: {'answer': str, 'thinking': list} if include_thinking=True
    """
    app = build_graph()

    # Convert history to LangChain format
    lc_history = []
    if chat_history:
        for role, text in chat_history:
            if role == "human":
                lc_history.append(HumanMessage(content=text))
            elif role == "ai":
                lc_history.append(AIMessage(content=text))

    inputs = {
        "input": user_input,
        "chat_history": lc_history,
        "chat_store": chat_store,
    }

    # Stream through steps to capture thinking
    thinking_steps = []
    result = None

    async for event in app.astream(inputs, stream_mode="updates"):
        for node_name, state_update in event.items():
            # Call real-time callback if provided
            if on_step:
                friendly_name = STEP_NAMES.get(node_name, node_name)
                on_step(friendly_name)

            # Capture each step for thinking display
            step_info = {"node": node_name}

            if "reformulated_input" in state_update:
                step_info["reformulated"] = state_update["reformulated_input"]
            if "input_type" in state_update:
                step_info["classified_as"] = state_update["input_type"]
            if "plan" in state_update and state_update["plan"]:
                step_info["plan"] = (
                    state_update["plan"][:200] + "..."
                    if len(state_update.get("plan", "")) > 200
                    else state_update.get("plan", "")
                )
            if "web_search_needed" in state_update:
                step_info["web_search_needed"] = state_update["web_search_needed"]
            if "answer" in state_update:
                result = state_update

            thinking_steps.append(step_info)

    answer = result.get("answer", "") if result else ""

    if include_thinking:
        return {"answer": answer, "thinking": thinking_steps}
    return answer


def generate_graph_image(path: str = "agent_graph.png"):
    """Generate the graph visualization."""
    app = build_graph()
    try:
        image_data = app.get_graph().draw_mermaid_png()
        with open(path, "wb") as f:
            f.write(image_data)
        print(f"Graph saved to {path}")
    except Exception as e:
        print(f"Could not draw graph: {e}")
