# AI 智能客服系统

基于 **LangGraph + RAGFlow + Qwen2.5** 的在线智能客服对话系统。以 LangGraph 图状态机为核心引擎，串联意图识别、RAG 知识检索、答案生成与人工兜底，支持对话状态持久化与中断恢复，面向私有化部署场景。

## 快速开始

### 1. 环境要求

- Docker Desktop（Windows / macOS / Linux）
- Python 3.12（本地开发/测试用）

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 中的 SECRET_KEY 和数据库密码
```

> 国内网络需配置 Docker 镜像加速：Docker Desktop → Settings → Docker Engine → 添加 `registry-mirrors: ["https://docker.1ms.run"]`

### 3. 一键启动

```bash
docker compose up -d
```

### 4. 拉取 AI 模型（首次必须）

```bash
docker exec -it backend-ollama-1 ollama pull qwen2.5:1.5b
```

### 5. 验证

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 6. 测试对话

```bash
# 1. 登录获取 token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code":"test123"}'

# 2. 创建会话
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer <token>"

# 3. 发送消息 (SSE 流式)
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<session_id>","content":"如何退货？"}'
```

---

## 技术架构

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
│  │             │PostgreSQL│ ← Checkpointer 持久化      │  │
│  │             │+pgvector │                            │  │
│  │             └─────────┘                            │  │
│  └────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│   Ollama :11434    RAGFlow :9380    Redis :6379         │
│   (Qwen2.5-1.5B)   (知识库引擎)     (Celery Broker)     │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

| 组件 | 方案 | 说明 |
|------|------|------|
| AI 模型 | Qwen2.5-1.5B-Instruct | Ollama 本地部署，资源占用小 |
| RAG 引擎 | RAGFlow | 深度文档解析，混合检索（全文+向量） |
| Agent 框架 | LangGraph | 图状态机，条件边路由，内置持久化 |
| 后端 | FastAPI | 异步高性能，SSE 流式推送 |
| 数据库 | PostgreSQL + pgvector | 结构化数据 + 向量存储合一 |
| 任务队列 | Celery + Redis | 人工审核异步解耦 |
| 认证 | 微信 OAuth 2.0 | Mock 模式（开发）/ 真实 OAuth（生产） |
| 容器化 | Docker Compose | 6 服务一键部署 |

---

## LangGraph 图结构：带决策逻辑的工作流引擎

整个客服 Agent 被建模为一个**有向图状态机**，每个节点是独立的处理单元，边定义了状态流转规则。这是一种带决策逻辑的图结构，而非线性流水线。

### 核心决策流程图

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                  ┌──────▼──────┐
                  │  意图识别    │
                  │  (intent)   │
                  └──────┬──────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     "chitchat"    "knowledge"    "human_needed"
          │         "complaint"        │
          │              │              │
  ┌───────▼──────┐ ┌────▼─────┐  ┌─────▼──────┐
  │  闲聊回复    │ │ RAG 检索 │  │  兜底回复   │
  │  (chitchat)  │ │(retrieval)│  │  /转人工    │
  └───────┬──────┘ └────┬─────┘  └────────────┘
          │              │
          │         ┌────┼────┐
          │   成功 ←┘    │    └→ 超时/失败
          │         ┌────▼─────┐  ┌────────────┐
          │         │ 答案生成  │  │  兜底回复   │
          │         │(generate) │  │  /转人工    │
          │         └────┬─────┘  └────────────┘
          │              │
          └──────┬───────┘
                 │
          ┌──────▼──────┐
          │    END      │
          └─────────────┘

    查询重写循环（最多3次）:
    RAG检索 → 结果不理想 → 查询重写 → RAG检索 → ...
                        ↑                    │
                        └── rewrite_count<3 ─┘
                        rewrite_count≥3 → 兜底回复
```

### 节点职责

| 节点 | 输入 | 输出 | 关键逻辑 |
|------|------|------|---------|
| `intent_classifier` | 用户消息 | `intent`, `intent_confidence` | 零样本分类：chitchat / knowledge / complaint / human_needed |
| `chitchat_reply` | 对话历史 | `final_answer` | 直接 LLM 闲聊回复 |
| `rag_retrieval` | 用户问题 | `rag_context` | 调用 RAG 接口，**5 秒超时** |
| `query_rewrite` | 用户问题 | `rag_context`（清空）, `rewrite_count += 1` | LLM 改写查询，**最多循环 3 次** |
| `answer_generation` | 对话历史 + RAG 片段 | `final_answer` | 融合检索上下文生成答案 |
| `fallback_reply` | `error` 字段 | `final_answer`, `needs_human` | 根据错误类型返回兜底话术 |

---

## Checkpoint 持久化：颗粒度选择

LangGraph 的持久化机制在每个**节点执行后**自动创建状态快照（checkpoint），而非在每个 token 或每个请求级别。

### 颗粒度设计理由

| 颗粒度 | 优缺点 | 本项目选择 |
|--------|--------|-----------|
| **每 token** | 恢复最精细，但写入压力巨大，磁盘 I/O 成为瓶颈 | ❌ 不采用 |
| **每节点**（当前方案） | LangGraph 内置默认行为，平衡恢复精度与性能 | ✅ 采用 |
| **每请求** | 恢复粒度太粗，中断后需要重跑整个流程 | ❌ 不采用 |

### 实现方式

```python
# backend/app/agent/checkpointer.py
checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
await checkpointer.setup()

# graph.py — 编译时注入
graph = builder.compile(checkpointer=checkpointer)
```

LangGraph 自动管理 `checkpoints` 和 `checkpoint_writes` 两张表。每个 `thread_id` 对应一个会话的快照链，支持父子关系（分支对话）。

### 存储开销控制

- 默认保留最近 100 个快照（LangGraph 内置策略，可通过 `max_history` 调整）
- 每个快照约 5-20 KB（取决于对话长度），单会话千轮对话约 2-20 MB

---

## 动态中断恢复：优雅的状态恢复

### 中断场景

1. **服务重启**：容器崩溃、OOM、版本升级
2. **网络超时**：用户断网、客户端关闭
3. **人工审核挂起**：难问题转人工，会话主动暂停

### 恢复机制

```
中断前:
  Thread: "session_abc123"
  Checkpoint #5 (latest)
    ├── messages: [...]          # 完整对话历史
    ├── intent: "knowledge"
    ├── rag_context: [...]       # 上一轮检索结果
    ├── rewrite_count: 1
    └── final_answer: ""         # ← 中断时未生成

恢复后（用户发送新消息）:
  graph.astream(initial_state, {"configurable": {"thread_id": "session_abc123"}})
  → LangGraph 自动加载 Checkpoint #5
  → 从 intent_classifier 节点重新开始（而非从断点中间恢复）
  → 对话历史完整保留，用户无感知
```

关键代码在 [chat_service.py](backend/app/services/chat_service.py:30-32)：

```python
thread_id = f"session_{session_id}"
config = {"configurable": {"thread_id": thread_id}}
# LangGraph 自动从此 thread 的最新 checkpoint 恢复
async for event in self._graph.astream(initial_state, config, ...):
```

### 会话暂停/恢复（人工审核场景）

```python
# 难问题 → 推送人工队列 → 暂停会话
session.status = SessionStatus.paused
await db.flush()

# 人工处理完毕 → 恢复
session.status = SessionStatus.active
# 下次用户交互时，LangGraph 自动从最新 checkpoint 继续
```

---

## 条件边设计：智能路由决策

条件边是 LangGraph 的核心——它不是硬编码的流程，而是**基于状态的动态路由函数**。

### 三个路由函数 ([conditions.py](backend/app/agent/edges/conditions.py))

```python
def route_by_intent(state: AgentState) -> str:
    """意图路由：根据意图分类结果选择下一节点"""
    if state["error"]:
        return "fallback_reply"
    if state["intent"] == "chitchat":
        return "chitchat_reply"
    elif state["intent"] in ("knowledge", "complaint"):
        return "rag_retrieval"
    else:
        return "fallback_reply"

def route_after_rag(state: AgentState) -> str:
    """检索后路由：成功→生成答案，失败→兜底"""
    if state["error"]:
        return "fallback_reply"
    return "answer_generation"

def route_after_rewrite(state: AgentState) -> str:
    """重写后路由：<3次→重新检索，≥3次→熔断"""
    if state["rewrite_count"] >= 3:
        return "fallback_reply"
    return "rag_retrieval"
```

这些函数是**纯函数**——输入 `AgentState`，输出字符串——易于测试和推理。

---

## 状态传递与并行上下文合并

### 状态传递机制

所有节点通过 `AgentState`（TypedDict）共享状态，而非通过参数传递或全局变量。每个节点返回 `dict`，LangGraph 自动合并到全局状态：

```python
# 节点返回部分更新
async def intent_node(state, llm) -> dict:
    return {"intent": "knowledge", "intent_confidence": 0.92}
    # ↑ 只返回变更的字段，LangGraph 自动合并

async def rag_node(state, rag_client) -> dict:
    return {"rag_context": ["文档片段1", "文档片段2"]}
```

### 并行上下文合并策略

当多个节点并行执行时（如多个 RAG 库同时检索），LangGraph 默认**追加合并**列表字段。这会导致 `rag_context` 出现重复。

**解决方案**：在 [state.py](backend/app/agent/state.py) 中使用自定义 reducer：

```python
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]     # LangGraph 内置去重合并
    rag_context: Annotated[list, replace_reducer]  # 每次覆盖，避免重复
```

当前实施方案中，节点串行执行（未使用并行分支），`rag_context` 在下游节点 `answer_generation` 中直接消费：

```python
# generate.py — 取前5个片段，自然去重
def _format_rag_context(context: list[str]) -> str:
    if not context:
        return "无相关知识库内容"
    return "\n---\n".join(context[:5])
```

---

## 异常处理：多层防护体系

```
Layer 1: 节点级超时
  rag_retrieval: asyncio.wait_for(5s)
  → TimeoutError → error="rag_timeout" → 条件边 → fallback_reply

Layer 2: 递归限制
  query_rewrite: rewrite_count >= 3
  → error="max_rewrites" → 条件边 → fallback_reply

Layer 3: 全图超时
  graph.ainvoke(): asyncio.wait_for(30s)
  → 整体兜底

Layer 4: FastAPI 全局异常处理
  @app.exception_handler(Exception)
  → 500 Internal server error (不泄露内部细节)
```

### 具体实现

```python
# rag.py — 节点级超时
async def rag_node(state, rag_client) -> dict:
    try:
        results = await asyncio.wait_for(
            rag_client.search(user_message),
            timeout=5.0,
        )
        return {"rag_context": results}
    except asyncio.TimeoutError:
        return {"error": "rag_timeout", "rag_context": []}
```

```python
# fallback.py — 分级兜底
FALLBACK_REPLIES = {
    "rag_timeout": "系统繁忙，请稍后再试。",
    "rag_error": "抱歉，知识库服务暂时不可用。",
    "max_rewrites": "您的问题比较复杂，正在为您转接人工客服。",
}
```

---

## 数据飞轮：对话反哺微调

```
用户对话 → 点赞/踩/评分 → feedbacks + messages 表
    ↓
定期导出高质量/低质量对话
    ↓
数据标注与清洗 → 人工校验
    ↓
SFT 格式数据集 → LoRA 微调 → 模型迭代
    ↓
效果提升 → 更多用户 → 更多数据
```

反馈收集已集成到对话流程中，微调管线和训练脚本为后续实现。

---

## API 文档

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/login` | Mock 微信登录 → JWT |
| GET | `/api/v1/auth/me` | 当前用户信息 |

### 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat/send` | SSE 流式对话 |

SSE 事件类型：

| 事件 | 数据 | 说明 |
|------|------|------|
| `intent` | `{"intent":"...", "confidence":0.9}` | 意图识别结果 |
| `thinking` | `{"message":"正在生成回复..."}` | 处理进度提示 |
| `error` | `{"message":"..."}` | 错误事件 |
| `done` | `{"answer":"...", "message_id":"...", "needs_human":false}` | 最终回复 |

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/sessions` | 会话列表（分页） |
| POST | `/api/v1/sessions` | 创建新会话 |
| GET | `/api/v1/sessions/{id}` | 会话详情 |
| GET | `/api/v1/sessions/{id}/messages` | 消息历史（分页） |
| PATCH | `/api/v1/sessions/{id}` | 更新状态/标题 |

### 反馈

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/feedback` | 提交评分/点赞 |
| GET | `/api/v1/feedback/stats` | 汇总统计 |

---

## 部署

### 开发环境

```bash
docker compose up -d
```

开发模式下：
- `RAG_MODE=mock`：使用内置 Mock 知识库，无需启动 RAGFlow
- `WECHAT_MOCK_ENABLED=true`：任意 code 即可登录

### 生产环境

1. 修改 `.env`：
   ```
   APP_ENV=production
   SECRET_KEY=<随机强密钥>
   RAG_MODE=ragflow
   RAGFLOW_API_KEY=<RAGFlow API KEY>
   WECHAT_MOCK_ENABLED=false
   WECHAT_APP_ID=<真实 AppID>
   WECHAT_APP_SECRET=<真实 AppSecret>
   ```

2. 取消 `docker-compose.yml` 中 RAGFlow 服务的注释

3. 移除 Ollama 和 PostgreSQL 的 `ports` 映射（仅内网访问）

4. 前置 Nginx 反向代理 + Let's Encrypt HTTPS

### 安全清单

- [ ] `SECRET_KEY` 已修改为随机强密钥
- [ ] Ollama 仅内网访问（移除 ports 映射）
- [ ] RAGFlow 默认密码已修改
- [ ] 生产环境启用 LiteLLM API KEY 网关
- [ ] HTTPS 已配置

---

## 项目交付物

- [x] LangGraph 工作流引擎（条件边、状态传递、超时熔断、递归限制）
- [x] Checkpoint 持久化到 PostgreSQL
- [x] 动态中断恢复机制
- [x] RAG 抽象层（Mock + RAGFlow 可切换）
- [x] Mock 微信登录 + JWT 认证
- [x] SSE 流式对话
- [x] 反馈收集（数据飞轮基础）
- [x] Celery 人工审核解耦
- [x] Docker Compose 一键部署
- [x] 安全中间件与速率限制
- [ ] Tauri 桌面端（Phase 7+）
- [ ] LoRA 微调管线（Phase 7+）
- [ ] pgvector 长期记忆（Phase 7+）
