"""Agent entry point."""

from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph import build_graph


async def chat(user_input: str, chat_store=None, chat_history: list = None) -> str:
    """Run the agent graph with user input."""
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

    result = await app.ainvoke(inputs)
    return result["answer"]


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
