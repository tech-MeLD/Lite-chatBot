# 架构设计

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Tauri 桌面端 (Windows)                │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Backend :8000                 │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Auth     │  │ Chat (SSE)   │  │ Session / Feed-  │  │
│  │ Service  │  │ Service      │  │ back API         │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬─────────┘  │
│       │               │                    │             │
│  ┌────┴───────────────┴────────────────────┴─────────┐  │
│  │              LangGraph Agent Engine               │  │
│  │  ┌─────────┐  ┌──────┐  ┌─────────┐  ┌────────┐  │  │
│  │  │ Intent  │→│ RAG  │→│ Generate│→│ Fall-  │  │  │
│  │  │ Classify│  │Retrv.│  │ Answer  │  │ back   │  │  │
│  │  └─────────┘  └──┬───┘  └─────────┘  └────────┘  │  │
│  │                  │ ↕ Query Rewrite (≤3)            │  │
│  │             ┌────┴────┐                            │  │
│  │             │PostgreSQL│ ← Checkpointer + Memory   │  │
│  │             │+pgvector │                            │  │
│  │             └─────────┘                            │  │
│  └────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│   Ollama :11434    RAGFlow :9380    Redis :6379         │
│   (Qwen2.5-1.5B)   (知识库引擎)     (Celery Broker)     │
│   (bge-m3 embed)                                        │
└─────────────────────────────────────────────────────────┘
```

## LangGraph 图结构

整个客服 Agent 被建模为一个**有向图状态机**，每个节点是独立的处理单元，边定义了状态流转规则。

### AgentState（共享状态）

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]      # 对话历史（LangGraph add_messages reducer）
    user_id: str                     # 当前用户
    session_id: str                  # 当前会话
    intent: str                      # 意图分类结果
    intent_confidence: float         # 置信度 0~1
    rag_context: list[str]           # RAG 检索片段
    user_memories: list[str]         # 长期记忆
    rewrite_count: int               # 查询重写次数
    final_answer: str                # 最终回复
    needs_human: bool                # 是否需要转人工
    error: str | None                # 错误状态
```

### 决策流程图

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                  ┌──────▼──────┐
                  │ intent_     │
                  │ classifier  │
                  └──────┬──────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     "chitchat"    "knowledge"    "human_needed"
          │         "complaint"        │
          │              │              │
  ┌───────▼──────┐ ┌────▼─────┐  ┌─────▼──────┐
  │ chitchat_    │ │ rag_     │  │ fallback_   │
  │ reply        │ │ retrieval│  │ reply       │
  └───────┬──────┘ └────┬─────┘  └────────────┘
          │              │
          │         ┌────┼────┐
          │   成功 ←┘    │    └→ 超时/失败
          │         ┌────▼─────┐  ┌────────────┐
          │         │ answer_   │  │ fallback_  │
          │         │ generation│  │ reply      │
          │         └────┬─────┘  └────────────┘
          │              │
          └──────┬───────┘
                 │
          ┌──────▼──────┐
          │    END      │
          └─────────────┘

    查询重写循环（最多3次）:
    rag_retrieval → 不理想 → query_rewrite → rag_retrieval → ...
                       ↑                    │
                       └── rewrite_count<3 ─┘
                       rewrite_count≥3 → fallback
```

### 条件边路由

三个路由函数是纯函数，输入 `AgentState`，返回下一节点名称：

- `route_by_intent` — 按 intent 分岔
- `route_after_rag` — 按 error 状态分流
- `route_after_rewrite` — 按重写次数熔断

详见 [app/agent/edges/conditions.py](../backend/app/agent/edges/conditions.py)

---

## Checkpoint 持久化

### 颗粒度选择

| 颗粒度 | 优缺点 | 本项目 |
|--------|--------|--------|
| 每 token | 恢复精细，但 I/O 压力巨大 | ❌ |
| **每节点** | 平衡恢复精度与性能 | ✅ |
| 每请求 | 恢复太粗，中断需重跑 | ❌ |

LangGraph 在每个节点执行后自动创建状态快照到 PostgreSQL。

### 存储开销

- 每个快照约 5-20 KB
- 默认保留最近 100 个快照
- 单会话千轮对话约 2-20 MB

---

## 动态中断恢复

### 中断场景
1. 服务重启（崩溃、OOM、升级）
2. 网络超时（用户断网）
3. 人工审核挂起

### 恢复机制

LangGraph 通过 `thread_id` 维护快照链。新消息到达时自动加载最新 checkpoint，从 `intent_classifier` 开始重新执行，对话历史完整保留。

参见 [chat_service.py](../backend/app/services/chat_service.py)

---

## 异常处理：四层防护

| 层级 | 机制 | 时间 |
|------|------|------|
| Layer 1 | RAG 检索节点 `asyncio.wait_for(5s)` | 5s |
| Layer 2 | 查询重写 `rewrite_count >= 3` 熔断 | ~15s |
| Layer 3 | 全图 `asyncio.wait_for(30s)` | 30s |
| Layer 4 | FastAPI 全局异常处理 → 500（含 CORS 头） | ∞ |

---

## 双重记忆系统

### 短期记忆
LangGraph Checkpointer → PostgreSQL 定期快照会话状态

### 长期记忆
pgvector 存储用户偏好向量，LLM 自动从对话提取，语义检索匹配

详见 [memory-system.md](memory-system.md)
