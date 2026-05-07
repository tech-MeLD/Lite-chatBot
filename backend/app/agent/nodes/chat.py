from app.agent.state import AgentState
from app.llm.ollama_client import OllamaClient

CHITCHAT_PROMPT = """你是一个友好的客服助手。用亲切自然的语气回复用户的闲聊消息。

对话历史:
{history}

用户: {user_message}

请给出简短友好的回复（不超过100字）:"""


async def chitchat_node(state: AgentState, llm: OllamaClient) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"final_answer": "你好！有什么可以帮你的吗？"}

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    history = _format_history(messages[:-1])

    try:
        prompt = CHITCHAT_PROMPT.format(history=history, user_message=user_message)
        answer = await llm.chat(prompt)
    except Exception:
        answer = "你好！有什么可以帮你的吗？"

    return {"final_answer": answer.strip()}


def _format_history(messages: list) -> str:
    if not messages:
        return "无"
    lines = []
    for m in messages[-6:]:
        content = m.content if hasattr(m, 'content') else str(m)
        role = "用户" if "user" in str(type(m)).lower() else "助手"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)
