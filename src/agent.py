"""Simple coach agent with few-shot prompting."""

import re
from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatPromptTemplate
from src.llm import get_llm
from src.rag import search
from src.tools import e1rm, ipf_gl, plates


EXAMPLES = [
    {
        "input": "How deep should I squat?",
        "output": "Hip crease must pass below the top of the knee. In IPF competition, three referees judge this - two white lights required for a good lift.",
    },
    {
        "input": "Calculate 140kg for 5 reps",
        "output": "E1RM: 163.3 kg (Epley formula: 140 × (1 + 5/30))",
    },
    {
        "input": "What plates for 200kg?",
        "output": "Per side: 2×25kg, 1×20kg, 1×15kg, 1×5kg. Actual: 200kg with 20kg bar.",
    },
    {
        "input": "My squat is stuck at 180kg",
        "output": "Common fixes: 1) Add paused squats at 70% for positional strength. 2) Check bar position - low bar allows more hip drive. 3) Strengthen weak point: quads (front squat) or glutes (hip thrust). What specifically fails - out of the hole or at lockout?",
    },
]

SYSTEM = """You are Boldi Nagy's powerlifting coach assistant. Be direct, technical, concise.
Use metric units. Reference IPF rules when relevant. For calculations, show the formula briefly.
You have access to knowledge from Boldi's YouTube channel (@boldinagy) covering training programming,
technique for squat/bench/deadlift, competition prep, and recovery."""


def detect_calculation(text: str) -> str | None:
    text_lower = text.lower()

    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg)?\s*[x×@]\s*(\d+)", text_lower)
    if match or "e1rm" in text_lower or "1rm" in text_lower:
        if match:
            w, r = float(match.group(1)), int(match.group(2))
            result = e1rm(w, r)
            return f"E1RM: {result} kg (Epley: {w} × (1 + {r}/30))"

    if "plates" in text_lower or "load" in text_lower:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg)?", text_lower)
        if match:
            target = float(match.group(1))
            result = plates(target)
            plate_str = ", ".join(f"{c}×{w}kg" for w, c in result["plates"].items())
            return f"Per side: {plate_str}. Actual: {result['actual']}kg"

    if "ipf" in text_lower or "gl" in text_lower or "points" in text_lower:
        nums = re.findall(r"(\d+(?:\.\d+)?)", text_lower)
        if len(nums) >= 2:
            total, bw = float(nums[0]), float(nums[1])
            is_male = "female" not in text_lower
            result = ipf_gl(total, bw, is_male)
            return f"IPF GL: {result} points"

    return None


def build_prompt():
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{output}"),
        ]
    )

    few_shot = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=EXAMPLES,
    )

    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM),
            few_shot,
            ("placeholder", "{chat_history}"),
            ("system", "Context from knowledge base:\n{context}"),
            ("human", "{input}"),
        ]
    )


async def chat(user_input: str, chat_store=None, chat_history: list = None) -> str:
    calc_result = detect_calculation(user_input)
    if calc_result:
        return calc_result

    base_context = search(user_input)
    chat_context = search(user_input, store=chat_store) if chat_store else ""
    context = f"{base_context}\n{chat_context}".strip() or "No relevant context found."

    llm = get_llm()
    prompt = build_prompt()
    chain = prompt | llm

    response = await chain.ainvoke(
        {"input": user_input, "context": context, "chat_history": chat_history or []}
    )
    return response.content
