"""Agent entry point."""

from langchain_core.messages import HumanMessage, SystemMessage
from src.agent.graph import build_graph
from src.tools.calculators import e1rm, ipf_gl, plates
import re


async def chat(user_input: str, chat_store=None, chat_history: list = None) -> str:
    text_lower = user_input.lower()

    # E1RM matches
    e1rm_keywords = [
        "e1rm",
        "1rm",
        "estimated one rep max",
        "one rep max",
        "estimated one rap max",
        "one rap max",
    ]
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg)?\s*[x×@]\s*(\d+)", text_lower)
    if match or any(keyword in text_lower for keyword in e1rm_keywords):
        if match:
            w, r = float(match.group(1)), int(match.group(2))
            result = e1rm(w, r)
            return f"E1RM: {result} kg (Epley: {w} × (1 + {r}/30))"

    # Plate matches
    if "plates" in text_lower or "load" in text_lower:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg)?", text_lower)
        if match:
            target = float(match.group(1))
            result = plates(target)
            plate_str = ", ".join(f"{c}×{w}kg" for w, c in result["plates"].items())
            return f"Per side: {plate_str}. Actual: {result['actual']}kg"

    # IPF matches
    if "ipf" in text_lower or "gl" in text_lower or "points" in text_lower:
        nums = re.findall(r"(\d+(?:\.\d+)?)", text_lower)
        if len(nums) >= 2:
            total, bw = float(nums[0]), float(nums[1])
            is_male = "female" not in text_lower
            result = ipf_gl(total, bw, is_male)
            return f"IPF GL: {result} points"

    # 2. Run LangGraph
    app = build_graph()

    # Convert history
    lc_history = []
    if chat_history:
        for role, text in chat_history:
            if role == "human":
                lc_history.append(HumanMessage(content=text))
            elif role == "ai":
                lc_history.append(SystemMessage(content=text))

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
