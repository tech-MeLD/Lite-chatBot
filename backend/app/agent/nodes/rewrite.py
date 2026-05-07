from app.agent.state import AgentState
from app.llm.ollama_client import OllamaClient

REWRITE_PROMPT = """你是一个查询优化器。用户原来的问题检索结果不理想，请改写用户问题，使其更具体、更易于检索。

原问题: {user_message}

请输出改写后的问题（只输出问题文本）:"""


async def rewrite_node(state: AgentState, llm: OllamaClient) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"rewrite_count": state.get("rewrite_count", 0) + 1}

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    current_count = state.get("rewrite_count", 0) + 1

    if current_count >= 3:
        return {"rewrite_count": current_count, "error": "max_rewrites"}

    try:
        prompt = REWRITE_PROMPT.format(user_message=user_message)
        rewritten = await llm.chat(prompt)
    except Exception:
        rewritten = user_message

    return {
        "rewrite_count": current_count,
        "rag_context": [],
    }
