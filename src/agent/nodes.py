"""Agent nodes."""

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from langchain_community.tools import DuckDuckGoSearchRun

from src.llm import get_llm, get_fast_llm
from src.rag import search
from src.agent.state import AgentState
from src.tools import ALL_TOOLS


web_search_tool = DuckDuckGoSearchRun()


def _extract_text(content) -> str:
    """Helper to extract text from LLM response (handling string or list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Gemini 3.0 can return list of content parts
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        return "".join(text_parts)
    return str(content)


class InputClassification(BaseModel):
    """Classification result for user input."""

    needs_rag: bool = Field(
        description="True if question needs document/knowledge lookup, False if it's a direct command like calculation"
    )
    reasoning: str = Field(description="One sentence explaining the classification")


def classify_input(state: AgentState) -> dict:
    """Classify input using LLM with structured output."""
    print("---CLASSIFY (LLM)---")

    llm = get_fast_llm().with_structured_output(InputClassification)

    prompt_text = f"""Classify this user input for a powerlifting coach assistant:

"{state.input}"

Answer:
- needs_rag=True: Questions about training plans, techniques, rules, advice, or retrieval from documents
- needs_rag=False: Direct commands, greetings, small talk, or simple calculation requests
"""
    messages = [HumanMessage(content=prompt_text)]
    result = llm.invoke(messages)
    print(f"Classification: {result}")

    input_type = "question" if result.needs_rag else "command"
    return {"input_type": input_type}


SYSTEM_PROMPT = """You are Boldi Nagy's powerlifting coach assistant.

## Guidelines
- Be direct, technical, and concise
- Use metric units (kg, cm) exclusively
- Reference IPF rules when discussing competition standards
- Structure responses with bullet points for programs/lists, markdown for clarity
- For calculations, show your work briefly

## Safety
- Always recommend consulting a medical professional for injury-related concerns
- Emphasize proper form and progressive overload principles
- Flag if a request involves potentially dangerous loads or techniques

## Knowledge Priority
1. User's uploaded documents and training logs
2. Personal notes and video transcripts from context
3. IPF rulebook and general powerlifting knowledge
4. Web search results (if other sources insufficient)

## Tool Usage Guidelines
- If a tool returns "No training data found" or an error, **DO NOT** call the same tool again with the same arguments.
- If you have already called a tool and got a result, use that result to formulate your answer. **Do not call the tool again.**
- Do not loop. If you are stuck, ask the user for clarification."""

PLAN_PROMPT = """You are a powerlifting coach planning how to answer a user's request.

Analyze the request and create a structured retrieval plan.

## Output Format
Return a brief plan with:
- **Keywords**: 3-5 key terms to search for in documents
- **Data needed**: What specific information is required (e.g., training logs, RPE data, PR history)
- **Calculation**: Any formulas or math needed (IPF points, percentages, plate loading)

## Example
Request: "What should my squat opener be based on my recent training?"

Plan:
- Keywords: squat, training, RPE, max, opener
- Data needed: Recent squat sessions, RPE ratings, rep maxes
- Calculation: Calculate ~90% of estimated 1RM for conservative opener

---
Request: {question}"""

GRADE_PROMPT = """Assess if the retrieved document is relevant to answering the user's powerlifting question.

Document is RELEVANT if it contains:
- Direct information about the topic asked
- Training data, exercises, or metrics mentioned in the question  
- Rules or guidelines applicable to the question

Document is NOT RELEVANT if it:
- Discusses completely unrelated topics
- Contains only generic information with no specific connection

Respond with ONLY 'yes' or 'no'. No other text."""


def plan_step(state: AgentState) -> dict:
    """Plan the response strategy."""
    print("---PLAN---")
    question = state.input
    llm = get_llm()
    planner = (
        ChatPromptTemplate.from_messages(
            [("system", PLAN_PROMPT), ("human", "{question}")]
        )
        | llm
    )
    response = planner.invoke({"question": question})
    return {"plan": _extract_text(response.content)}


def retrieve(state: AgentState) -> dict:
    """Retrieve documents from vector store."""
    print("---RETRIEVE---")
    question = state.input

    # Enhance search query with plan keywords
    print(f"Executing Plan:\n{state.plan}")

    # Extract keywords from plan to enhance retrieval
    enhanced_query = question
    if state.plan:
        # Combine question with plan for better semantic search
        enhanced_query = f"{question} {state.plan}"

    context_text = search(enhanced_query)

    # Search uploaded documents if available
    if state.chat_store:
        try:
            print("---SEARCHING UPLOADED DOCS---")
            docs = state.chat_store.similarity_search(question, k=3)
            if docs:
                uploaded_context = "\n\n".join([d.page_content for d in docs])
                context_text = f"Uploaded Documents:\n{uploaded_context}\n\nGeneral Knowledge:\n{context_text}"
        except Exception as e:
            print(f"Chat store search failed: {e}")

    # RAG returns empty string if no results found
    has_docs = bool(context_text and context_text.strip())

    return {"context": context_text, "web_search_needed": not has_docs}


def grade_documents(state: AgentState) -> dict:
    """Grade relevance of retrieved documents."""
    print("---CHECK RELEVANCE---")
    if state.web_search_needed:
        return {"web_search_needed": True}  # Already failed at retrieve step

    question = state.input
    context = state.context

    llm = get_llm()
    grader_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GRADE_PROMPT),
            (
                "human",
                "Retrieved document: \n\n {context} \n\n User question: {question}",
            ),
        ]
    )

    grader = grader_prompt | llm
    response = grader.invoke({"question": question, "context": context})
    score = _extract_text(response.content).strip().lower()

    if score == "yes":
        print("---DOCUMENTS RELEVANT---")
        return {"web_search_needed": False}
    else:
        print("---DOCUMENTS NOT RELEVANT---")
        return {"web_search_needed": True}


def web_search(state: AgentState) -> dict:
    """Search the web."""
    print("---WEB SEARCH---")
    question = state.input

    # Optimize search query based on plan?
    # For now check question
    try:
        # Wrapper to handle potential import errors at runtime
        if web_search_tool:
            results = web_search_tool.invoke(question)
        else:
            # Manual fallback or error
            from duckduckgo_search import DDGS

            results = str(list(DDGS().text(question, max_results=3)))

        return {"context": f"Web Search Results:\n{results}"}
    except Exception as e:
        return {"context": f"Web search failed: {e}"}


def generate(state: AgentState) -> dict:
    """Generate answer."""
    print("---GENERATE---")
    question = state.input
    context = state.context
    plan = state.plan
    history = state.chat_history

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
    ]
    messages.extend(history)
    messages.append(
        HumanMessage(
            content=f"Plan:\n{plan}\n\nContext:\n{context}\n\nQuestion: {question}"
        )
    )

    response = llm.invoke(messages)
    return {"answer": _extract_text(response.content)}


def agent_with_tools(state: AgentState) -> dict:
    """Agent node that can call tools. Used when context is insufficient."""
    print("---AGENT WITH TOOLS---")

    question = state.input
    context = state.context
    plan = state.plan
    history = state.chat_history

    llm = get_llm()

    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    messages = [
        SystemMessage(
            content=SYSTEM_PROMPT
            + """

You have access to the following tools:
- calculate_e1rm: Calculate estimated 1 rep max
- calculate_ipf_gl: Calculate IPF Goodlift points
- calculate_plates: Calculate plates needed for a target weight
- read_training_sheet: Read training data from Google Sheets
- update_training_cell: Update a cell in the training sheet
- list_training_sheets: List available training sheets
- load_youtube_transcript: Load transcript from a YouTube video
- search_web: Search the web for information

Use tools when you need specific calculations or data. If you have enough context, answer directly."""
        ),
    ]
    messages.extend(history)
    messages.append(
        HumanMessage(
            content=f"Plan:\n{plan}\n\nContext:\n{context}\n\nQuestion: {question}"
        )
    )

    response = llm_with_tools.invoke(messages)

    # If the response has tool calls, we need to add it to chat history
    # so the tool node can process it
    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"chat_history": list(history) + [response]}

    # If no tool calls, return the answer directly
    return {"answer": _extract_text(response.content)}
