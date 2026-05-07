from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_id: str
    intent: str
    intent_confidence: float
    rag_context: list[str]
    user_memories: list[str]
    rewrite_count: int
    final_answer: str
    needs_human: bool
    error: str | None
