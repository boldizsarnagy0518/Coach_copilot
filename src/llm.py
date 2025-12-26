"""LLM providers."""

from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings


def get_llm():
    """Main LLM for generation tasks."""
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
        )
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )


def get_fast_llm():
    """Fast LLM for classification tasks."""
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_fast_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )
    return ChatOllama(
        model=settings.ollama_fast_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )
