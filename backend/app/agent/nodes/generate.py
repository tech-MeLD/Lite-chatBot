from app.agent.state import AgentState
from app.llm.ollama_client import OllamaClient

GENERATE_PROMPT = """你是一个专业的客服助手。根据检索到的知识库内容和用户的历史偏好回答用户问题。

知识库参考内容:
{rag_context}

用户历史偏好与信息:
{user_memories}

对话历史:
{history}

用户问题: {user_message}

请给出专业、准确的回答（不超过300字）。优先参考知识库内容，结合用户历史偏好提供个性化服务。如果知识库内容不足以回答问题，请诚实说明。"""


async def generate_node(state: AgentState, llm: OllamaClient) -> dict:
    messages = state.get("messages", [])
    rag_context = state.get("rag_context", [])
    user_memories = state.get("user_memories", [])

    if not messages:
        return {"final_answer": "抱歉，我没有收到您的问题。"}

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    history = _format_history(messages[:-1])
    rag_text = _format_rag_context(rag_context)
    memories_text = _format_memories(user_memories)

    try:
        prompt = GENERATE_PROMPT.format(
            rag_context=rag_text,
            user_memories=memories_text,
            history=history,
            user_message=user_message,
        )
        answer = await llm.chat(prompt)
    except Exception:
        answer = "抱歉，系统暂时无法处理您的问题，请稍后再试。"

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


def _format_rag_context(context: list[str]) -> str:
    if not context:
        return "无相关知识库内容"
    return "\n---\n".join(context[:5])


def _format_memories(memories: list[str]) -> str:
    if not memories:
        return "暂无用户历史信息"
    return "\n".join(f"- {m}" for m in memories[:5])
