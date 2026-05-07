from functools import partial

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from app.agent.state import AgentState
from app.agent.nodes.intent import intent_node
from app.agent.nodes.chat import chitchat_node
from app.agent.nodes.rag import rag_node
from app.agent.nodes.rewrite import rewrite_node
from app.agent.nodes.generate import generate_node
from app.agent.nodes.fallback import fallback_node
from app.agent.edges.conditions import route_by_intent, route_after_rag, route_after_rewrite
from app.llm.ollama_client import OllamaClient
from app.rag.base import AbstractRAGClient


def build_graph(
    llm: OllamaClient,
    rag_client: AbstractRAGClient,
    checkpointer: BaseCheckpointSaver | None = None,
) -> StateGraph:
    builder = StateGraph(AgentState)

    # Wrap nodes with their dependencies
    intent = partial(intent_node, llm=llm)
    chitchat = partial(chitchat_node, llm=llm)
    rag = partial(rag_node, rag_client=rag_client)
    rewrite = partial(rewrite_node, llm=llm)
    generate = partial(generate_node, llm=llm)

    # Add nodes
    builder.add_node("intent_classifier", intent)
    builder.add_node("chitchat_reply", chitchat)
    builder.add_node("rag_retrieval", rag)
    builder.add_node("query_rewrite", rewrite)
    builder.add_node("answer_generation", generate)
    builder.add_node("fallback_reply", fallback_node)

    # Add edges
    builder.add_edge(START, "intent_classifier")
    builder.add_conditional_edges("intent_classifier", route_by_intent, {
        "chitchat_reply": "chitchat_reply",
        "rag_retrieval": "rag_retrieval",
        "fallback_reply": "fallback_reply",
    })
    builder.add_conditional_edges("rag_retrieval", route_after_rag, {
        "answer_generation": "answer_generation",
        "fallback_reply": "fallback_reply",
    })
    builder.add_conditional_edges("query_rewrite", route_after_rewrite, {
        "rag_retrieval": "rag_retrieval",
        "fallback_reply": "fallback_reply",
    })
    builder.add_edge("answer_generation", END)
    builder.add_edge("chitchat_reply", END)
    builder.add_edge("fallback_reply", END)

    graph = builder.compile(checkpointer=checkpointer)
    return graph
