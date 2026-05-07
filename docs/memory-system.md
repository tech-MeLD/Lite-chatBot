# 双重记忆系统

## 概述

客服系统包含两层记忆机制，确保 Agent 能记住对话上下文和用户长期偏好。

---

## 短期记忆：LangGraph Checkpointer

### 工作原理

每次对话中，LangGraph 在**每个节点执行后**自动将 `AgentState` 完整快照到 PostgreSQL。

```
轮次1: 用户问"如何退货"
  → intent_classifier → checkpoint#1 (intent="knowledge")
  → rag_retrieval     → checkpoint#2 (retrieved 3 docs)
  → answer_generation → checkpoint#3 (final_answer="7天无理由退货...")

轮次2: 用户追问"需要保留包装吗"
  → LangGraph 自动加载 checkpoint#3
  → 对话历史完整保留: [用户:"如何退货", 助手:"7天无理由退货...", 用户:"需要保留包装吗"]
  → 新的检索基于完整上下文
```

### 技术细节

- 后端: `AsyncPostgresSaver`（LangGraph 内置）
- 表: `checkpoints`, `checkpoint_writes`（自动管理）
- 桥接: `sessions.langgraph_thread_id` ↔ `thread_id`
- 保留策略: 最近 100 个快照
- 恢复: 新消息触发 `graph.astream(initial_state, config)`，自动加载最新快照

---

## 长期记忆：pgvector 语义存储

### 工作原理

系统自动从对话中提取用户偏好和事实，存储为带 embedding 的记忆向量，后续对话时通过语义相似度检索。

```
对话完成
  ↓
LLM 提取: "用户偏好顺丰快递", "用户是VIP会员", "用户上次购买了X产品"
  ↓
Embedding: bge-m3 模型生成 1024 维向量
  ↓
存储: long_term_memories 表 (pgvector)

下次对话:
  ↓
用户问题 embedding → 余弦相似度检索最相关记忆
  ↓
融入 generate_node prompt → 个性化回复
```

### 数据库表

```sql
CREATE TABLE long_term_memories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    embedding vector(1024),       -- bge-m3 embedding
    memory_type VARCHAR(32),      -- preference / fact / behavior
    content JSONB,                -- {"text": "...", "type": "preference"}
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX ON long_term_memories USING ivfflat (embedding vector_cosine_ops);
```

### 记忆类型

| 类型 | 示例 | 触发条件 |
|------|------|---------|
| `preference` | "用户偏好顺丰快递" | 用户明确表达偏好 |
| `fact` | "用户公司地址在北京市朝阳区" | 用户提供的事实信息 |
| `behavior` | "用户经常咨询退货相关问题" | 从对话模式推断 |

### 检索策略

- 使用余弦距离（`<=>` 操作符）进行最近邻检索
- 默认返回 top-3 最相关记忆
- 在 `generate_node` 中优先参考记忆提供个性化服务

### 代码位置

| 文件 | 职责 |
|------|------|
| [app/models/memory.py](../backend/app/models/memory.py) | 数据模型 |
| [app/llm/embedding_client.py](../backend/app/llm/embedding_client.py) | bge-m3 embedding |
| [app/services/memory_service.py](../backend/app/services/memory_service.py) | 存储、检索、提取 |
| [app/api/v1/chat.py](../backend/app/api/v1/chat.py) | 集成到对话流程 |
