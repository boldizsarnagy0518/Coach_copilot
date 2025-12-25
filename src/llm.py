"""LLM providers."""

from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings


def get_llm():
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
        )
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )
