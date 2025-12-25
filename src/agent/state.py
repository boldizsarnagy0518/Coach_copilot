"""Agent state definition using Pydantic."""

from typing import List
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


class AgentState(BaseModel):
    """The state of the agent graph."""

    input: str = Field(description="User question")
    plan: str = Field(default="", description="Execution plan")
    chat_history: List[BaseMessage] = Field(
        default_factory=list, description="Chat history"
    )
    context: str = Field(default="", description="Retrieved context")
    web_search_needed: bool = Field(
        default=False, description="Whether to fall back to web search"
    )
    chat_store: object = Field(default=None, description="Chat-specific vector store")

    class Config:
        arbitrary_types_allowed = True

    answer: str = Field(default="", description="Final answer")
