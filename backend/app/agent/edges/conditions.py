from app.agent.state import AgentState


def route_by_intent(state: AgentState) -> str:
    error = state.get("error")
    if error is not None:
        return "fallback_reply"

    intent = state.get("intent", "")
    if intent == "chitchat":
        return "chitchat_reply"
    elif intent in ("knowledge", "complaint"):
        return "rag_retrieval"
    elif intent == "human_needed":
        return "fallback_reply"
    else:
        return "chitchat_reply"


def route_after_rag(state: AgentState) -> str:
    if state.get("error") is not None:
        return "fallback_reply"
    return "answer_generation"


def route_after_rewrite(state: AgentState) -> str:
    if state.get("rewrite_count", 0) >= 3:
        return "fallback_reply"
    return "rag_retrieval"
