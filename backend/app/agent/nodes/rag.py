import asyncio
from app.agent.state import AgentState
from app.rag.base import AbstractRAGClient


async def rag_node(state: AgentState, rag_client: AbstractRAGClient) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"rag_context": []}

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])

    try:
        results = await asyncio.wait_for(
            rag_client.search(user_message),
            timeout=5.0,
        )
        return {"rag_context": results}
    except asyncio.TimeoutError:
        return {"error": "rag_timeout", "rag_context": []}
    except Exception:
        return {"error": "rag_error", "rag_context": []}
