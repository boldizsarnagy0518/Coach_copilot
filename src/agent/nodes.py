"""Agent nodes."""

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from src.llm import get_llm
from src.rag import search
from src.agent.state import AgentState

# Fix for DuckDuckGoSearchRun if needed, or we implement simple wrapper
try:
    web_search_tool = DuckDuckGoSearchRun()
except Exception:
    # Fallback to simple print if init fails (debugging)
    web_search_tool = None

SYSTEM_PROMPT = """You are Boldi Nagy's powerlifting coach assistant. Be direct, technical, concise.
Use metric units. Reference IPF rules when relevant.
You rely on the provided context (documents, training logs, video transcripts) to answer.
If context is missing, use general powerlifting knowledge and web search results."""

PLAN_PROMPT = """You are a powerlifting coach planning how to answer a user's request.
Break down the request into key concepts to look up or partial calculations.
Return a concise plan as a bulleted list.

Request: {question}"""

GRADE_PROMPT = """You are a grader assessing relevance of a retrieved document to a user question. 
If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. 
Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""


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
    return {"plan": response.content}


def retrieve(state: AgentState) -> dict:
    """Retrieve documents from vector store."""
    print("---RETRIEVE---")
    question = state.input

    # We can enhance search by appending plan keywords if we wanted
    # For now, let's stick to the question but maybe print the plan
    print(f"Executing Plan:\n{state.plan}")

    # Potential upgrade: generate better queries based on plan
    context_text = search(question)

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

    # Heuristic: Rag returns "No relevant context found." if empty
    has_docs = "No relevant context found" not in context_text

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
    score = response.content.lower()

    if "yes" in score:
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
    return {"answer": response.content}
