"""RAG with per-chat document support."""
import os

import uuid
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.config import settings

_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)


def get_embeddings():
    if settings.embedding_provider == "gemini" and settings.gemini_api_key:
        return GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.gemini_api_key,
        )
    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )


def get_base_vectorstore():
    """Main knowledge base (rules, notes)."""
    return Chroma(
        collection_name="knowledge",
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_persist_directory),
    )


def create_chat_vectorstore(chat_id: str = None):
    """Ephemeral vectorstore for uploaded documents in a chat session."""
    chat_id = chat_id or str(uuid.uuid4())[:8]
    return Chroma(
        collection_name=f"chat_{chat_id}",
        embedding_function=get_embeddings(),
    )


def load_pdf(path: str) -> list[Document]:
    loader = PyPDFLoader(path)
    return _splitter.split_documents(loader.load())


def load_text(text: str, source: str = "upload") -> list[Document]:
    doc = Document(page_content=text, metadata={"source": source})
    return _splitter.split_documents([doc])


def index_base_knowledge(force: bool = False):
    """Index PDFs from data/rules and markdown from data/notes.

    Args:
        force: If True, re-index even if data already exists.
               Can also be set via FORCE_REINDEX env var.
    """

    force = force or os.getenv("FORCE_REINDEX", "").lower() in ("true", "1", "yes")

    store = get_base_vectorstore()

    # Check if already indexed (skip for fast startup)
    if not force:
        try:
            count = store._collection.count()
            if count > 0:
                print(
                    f"Knowledge base already has {count} documents. Skipping indexing."
                )
                print("Set FORCE_REINDEX=true to rebuild.")
                return 0
        except Exception:
            pass

    docs = []

    rules_dir = Path("data/rules")
    if rules_dir.exists():
        for pdf in rules_dir.glob("*.pdf"):
            docs.extend(load_pdf(str(pdf)))

    notes_dir = Path("data/notes")
    if notes_dir.exists():
        for md in notes_dir.glob("*.md"):
            text = md.read_text(encoding="utf-8")
            docs.extend(load_text(text, source=md.name))

    if docs:
        if force:
            print("Force re-indexing enabled. Clearing old data...")
            try:
                store._collection.delete(where={})
            except Exception:
                pass
        print(f"Indexing {len(docs)} chunks into knowledge base...")
        store.add_documents(docs)
    return len(docs)


def search(query: str, store: Chroma = None, k: int = 3) -> str:
    store = store or get_base_vectorstore()
    results = store.similarity_search(query, k=k)
    if not results:
        return ""
    return "\n\n---\n\n".join(doc.page_content for doc in results)
