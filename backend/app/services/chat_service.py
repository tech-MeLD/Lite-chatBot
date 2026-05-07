import asyncio
import json
import uuid
from typing import AsyncGenerator

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from app.agent.state import AgentState
from app.agent.graph import build_graph
from app.llm.ollama_client import OllamaClient
from app.rag.base import AbstractRAGClient
from app.rag.mock import MockRAGClient
from app.models.message import Message, MessageRole


class ChatService:
    def __init__(self, llm: OllamaClient, rag_client: AbstractRAGClient):
        self.llm = llm
        self.rag_client = rag_client
        self._checkpointer = MemorySaver()
        self._graph = build_graph(llm, rag_client, checkpointer=self._checkpointer)

    async def send_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
    ) -> AsyncGenerator[str, None]:
        thread_id = f"session_{session_id}"
        config = {"configurable": {"thread_id": thread_id}}

        initial_state: AgentState = {
            "messages": [HumanMessage(content=content)],
            "user_id": user_id,
            "session_id": session_id,
            "intent": "",
            "intent_confidence": 0.0,
            "rag_context": [],
            "rewrite_count": 0,
            "final_answer": "",
            "needs_human": False,
            "error": None,
        }

        nodes_visited = []

        async for event in self._graph.astream(initial_state, config, stream_mode="values"):
            if isinstance(event, dict):
                node_name = event.get("current_node", "")
                nodes_visited.append(node_name)

                intent = event.get("intent", "")
                if intent and "intent" not in nodes_visited[:-1]:
                    yield f"data: {json.dumps({'type': 'intent', 'data': {'intent': intent, 'confidence': event.get('intent_confidence', 0)}})}\n\n"

                error = event.get("error")
                if error:
                    yield f"data: {json.dumps({'type': 'error', 'data': {'message': error}})}\n\n"

        final_state = await self._graph.aget_state(config)
        if final_state and final_state.values:
            answer = final_state.values.get("final_answer", "")
            needs_human = final_state.values.get("needs_human", False)
            
            yield f"data: {json.dumps({'type': 'done', 'data': {'answer': answer, 'needs_human': needs_human}})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'data': {'message': 'no response'}})}\n\n"
