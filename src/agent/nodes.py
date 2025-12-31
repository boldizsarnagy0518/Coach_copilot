"""Agent nodes."""

from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from langchain_community.tools import DuckDuckGoSearchRun

from src.llm import get_llm, get_fast_llm
from src.agent.state import AgentState
from src.agent.reformulate_agent import reformulate_agent
from src.tools import ALL_TOOLS
from src.prompts import SYSTEM_PROMPT, PLAN_PROMPT

from typing import Literal
from src.utils.instructor_client import get_instructor_client
from src.config import settings


class Grade(BaseModel):
    """Relevance grade."""

    score: Literal["yes", "no"] = Field(description="Relevance score 'yes' or 'no'")


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

    input_type: str = Field(
        description="One of: 'small_talk' (greetings/thanks/casual), 'command' (user's data, calculations, sheets), 'question' (general knowledge)"
    )
    reasoning: str = Field(description="One sentence explaining the classification")


def reformulate_query(state: AgentState) -> dict:
    """Reformulate ambiguous queries using PydanticAI agent."""
    print("---REFORMULATE (PydanticAI)---")

    try:
        # Run the agent synchronously
        result = reformulate_agent.run_sync(state.input)
        print(
            f"Reformulation: changed={result.data.was_changed}, query='{result.data.reformulated}'"
        )
        return {"reformulated_input": result.data.reformulated}
    except Exception as e:
        print(f"---REFORMULATE ERROR: {e}, using original input---")
        return {"reformulated_input": state.input}


def classify_input(state: AgentState) -> dict:
    """Classify input using heuristics and LLM (via Instructor)."""
    print("---CLASSIFY---")

    query = (state.reformulated_input or state.input).lower().strip()

    # 1. Fast Heuristics for Small Talk
    small_talk_keywords = [
        "hello",
        "hi",
        "hey",
        "hola",
        "greetings",
        "good morning",
        "good evening",
        "thanks",
        "thank you",
        "thx",
        "bye",
        "goodbye",
        "cya",
        "cool",
        "ok",
        "okay",
        "great",
    ]
    if query in small_talk_keywords or (
        len(query) < 10 and any(k in query for k in ["hi", "hey", "hello"])
    ):
        print("Classification (Heuristic): small_talk")
        return {"input_type": "small_talk"}

    # 2. LLM Classification with Instructor
    print("---CLASSIFY (Instructor)---")

    try:
        client = get_instructor_client()
        prompt_text = f"""Classify this user input for a powerlifting coach assistant:

"{state.reformulated_input or state.input}"

Categories:
- small_talk: Greetings, thanks, goodbye, emojis, casual chat (NO data needed)
- command: ANY request about the USER's personal data, training, sheets, calculations, PRs, schedule
- question: ONLY general powerlifting knowledge NOT about the user (definitions, rules, techniques)

KEY DISTINCTION: If the user asks about THEIR data ("my", "I", schedule, training block), it's COMMAND.

Examples:
- "Hello!" → small_talk
- "Thanks" → small_talk
- "What was my best squat?" → command
- "Summarize my training block" → command
- "What is RPE?" → question

When uncertain, default to 'command'."""

        # Use fast model for classification
        result = client.chat.completions.create(
            model=settings.ollama_fast_model,
            response_model=InputClassification,
            messages=[{"role": "user", "content": prompt_text}],
            max_retries=2,
        )
        print(f"Classification: {result}")
        return {"input_type": result.input_type}

    except Exception as e:
        print(f"---CLASSIFY ERROR: {e}, defaulting to command---")
        # Fallback: reasonable defaults
        if any(
            w in query for w in ["my", "i", "schedule", "training", "sheet", "program"]
        ):
            return {"input_type": "command"}
        return {"input_type": "question"}


def generate_small_talk(state: AgentState) -> dict:
    """Fast response for greetings and casual chat without tools."""
    print("---SMALL TALK (FAST)---")

    try:
        llm = get_fast_llm()
        messages = [
            SystemMessage(
                content="You are a friendly powerlifting coach assistant. Respond briefly and warmly to greetings and casual messages."
            ),
            HumanMessage(content=state.input),
        ]
        response = llm.invoke(messages)
        return {"answer": _extract_text(response.content)}
    except Exception as e:
        print(f"---SMALL TALK ERROR: {e}---")
        return {
            "answer": f"I'm having trouble connecting to my brain (LLM Error: {str(e)[:100]}). Please check if Ollama is running and the model is pulled."
        }


def generate(state: AgentState) -> dict:
    """Generate answer."""
    print("---GENERATE---")
    question = state.input
    context = state.context
    plan = state.plan
    history = state.chat_history

    try:
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
    except Exception as e:
        print(f"---GENERATE ERROR: {e}---")
        return {
            "answer": f"I encountered an error generating the response: {str(e)[:200]}. Please check your configuration."
        }


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
    """Retrieve documents from vector store with relevance scoring."""
    print("---RETRIEVE---")

    # Use reformulated input if available
    question = state.reformulated_input or state.input

    # Enhance search query with plan keywords
    print(f"Executing Plan:\n{state.plan}")

    enhanced_query = question
    if state.plan:
        enhanced_query = f"{question} {state.plan}"

    try:
        # Use scored search with top 5 documents
        from src.rag import search_with_scores, format_scored_results

        results = search_with_scores(enhanced_query)
        context_text = format_scored_results(results)

        if results:
            print(
                f"---RETRIEVED {len(results)} docs, scores: {[f'{s:.2f}' for _, s in results]}---"
            )
    except Exception as e:
        print(f"---RETRIEVE ERROR: {e}, falling back to basic search---")
        from src.rag import search

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
    """Grade relevance of retrieved documents using Instructor."""
    print("---CHECK RELEVANCE (Instructor)---")
    if state.web_search_needed:
        return {"web_search_needed": True}  # Already failed at retrieve step

    question = state.input
    context = state.context

    # Skip grading if context is empty
    if not context or not context.strip():
        return {"web_search_needed": True}

    try:
        client = get_instructor_client()

        # We construct the prompt content manually for the message
        prompt_content = f"""You are a grader assessing relevance of a retrieved document to a user question.

Retrieved document:
{context}

User question: {question}

If the document contains keyword(s) or semantic meaning related to the user question, grade it as 'yes'.
It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

        grade = client.chat.completions.create(
            model=settings.ollama_fast_model,  # Use fast model for grading
            response_model=Grade,
            messages=[{"role": "user", "content": prompt_content}],
            max_retries=2,
        )

        score = grade.score
        print(f"Grade: {score}")

        if score == "yes":
            print("---DOCUMENTS RELEVANT---")
            return {"web_search_needed": False}
        else:
            print("---DOCUMENTS NOT RELEVANT---")
            return {"web_search_needed": True}

    except Exception as e:
        print(f"---GRADING ERROR: {e}, assuming relevant---")
        return {"web_search_needed": False}


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

CRITICAL RULES:
1. For GREETINGS ("Hello", "Hi"): DO NOT USE ANY TOOLS. Just reply friendly.
2. If you already received tool results in the conversation, USE THAT DATA to answer. DO NOT call the same tool again.
3. If you have enough information to answer, RESPOND DIRECTLY without calling tools.
4. Only call a tool if you genuinely lack the information needed."""
        ),
    ]
    messages.extend(history)
    messages.append(
        HumanMessage(
            content=f"Plan:\n{plan}\n\nContext:\n{context}\n\nQuestion: {question}"
        )
    )

    response = llm_with_tools.invoke(messages)

    has_tools = hasattr(response, "tool_calls") and response.tool_calls
    print(
        f"---LLM Response: has_tools={has_tools}, content_len={len(str(response.content)) if response.content else 0}---"
    )

    if has_tools:
        print(f"---Tool calls: {[t['name'] for t in response.tool_calls]}---")
        return {"chat_history": list(history) + [response]}
    return {"answer": _extract_text(response.content)}
