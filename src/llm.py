"""LLM providers with LangFuse observability."""

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings

load_dotenv()
_langfuse_handler = None


def _get_langfuse_handler():
    """Get LangFuse callback handler for tracing (lazy initialization)."""
    global _langfuse_handler
    if _langfuse_handler is None:
        try:
            # Use the official LangChain integration from langfuse.langchain
            from langfuse.langchain import CallbackHandler

            _langfuse_handler = CallbackHandler()
            print("---LangFuse tracing enabled---")
        except Exception as e:
            print(f"---LangFuse not configured: {e}---")
            _langfuse_handler = False  # Mark as unavailable
    return _langfuse_handler if _langfuse_handler else None


def get_llm():
    """Main LLM for generation tasks."""
    callbacks = []
    handler = _get_langfuse_handler()
    if handler:
        callbacks.append(handler)

    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            callbacks=callbacks if callbacks else None,
        )
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        callbacks=callbacks if callbacks else None,
    )


def get_fast_llm():
    """Fast LLM for classification tasks."""
    callbacks = []
    handler = _get_langfuse_handler()
    if handler:
        callbacks.append(handler)

    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_fast_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,
            callbacks=callbacks if callbacks else None,
        )
    return ChatOllama(
        model=settings.ollama_fast_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        callbacks=callbacks if callbacks else None,
    )
