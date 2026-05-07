from app.agent.state import AgentState

FALLBACK_REPLIES = {
    "rag_timeout": "系统繁忙，请稍后再试。",
    "rag_error": "抱歉，知识库服务暂时不可用，请稍后再试。",
    "max_rewrites": "您的问题比较复杂，正在为您转接人工客服。",
    "human_needed": "正在为您转接人工客服，请稍候。",
}


async def fallback_node(state: AgentState) -> dict:
    error = state.get("error", "")
    intent = state.get("intent", "")

    reply = FALLBACK_REPLIES.get(error, "抱歉，系统暂时无法处理您的问题。")
    needs_human = error in ("max_rewrites", "human_needed") or intent == "human_needed"

    return {
        "final_answer": reply,
        "needs_human": needs_human,
    }
