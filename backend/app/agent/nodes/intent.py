from app.agent.state import AgentState
from app.llm.ollama_client import OllamaClient

INTENT_CLASSIFICATION_PROMPT = """你是一个意图分类器。分析用户的最后一条消息，将意图分类为以下之一：

- chitchat: 闲聊、问候、无关话题
- knowledge: 产品咨询、业务知识问题
- complaint: 投诉、不满情绪
- human_needed: 需要转接人工处理的复杂问题

请只返回意图类别和置信度(0.0~1.0)，格式: intent|confidence

示例:
用户: "你好" → chitchat|0.95
用户: "如何退货？" → knowledge|0.90
用户: "太差了我要投诉" → complaint|0.92

用户消息: {user_message}

请分类（只返回 intent|confidence）:"""


async def intent_node(state: AgentState, llm: OllamaClient) -> dict:
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "chitchat", "intent_confidence": 0.5}

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])

    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(user_message=user_message)
        response = await llm.chat(prompt)

        parts = response.strip().split("|")
        if len(parts) == 2:
            intent = parts[0].strip()
            confidence = float(parts[1].strip())
        else:
            intent = "chitchat"
            confidence = 0.5
    except Exception:
        intent = "chitchat"
        confidence = 0.5

    return {"intent": intent, "intent_confidence": confidence}
