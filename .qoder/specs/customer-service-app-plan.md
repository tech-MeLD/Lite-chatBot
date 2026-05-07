# AI 智能客服系统 — 实施计划

> **状态**: 已完成 (2026-05-08)
> Phase 1-6 全部完成，Phase 7 Tauri 桌面端已完成。

## Context

基于 提示词.md 的技术方案，开发一个基于 LangGraph + RAGFlow + Qwen2.5 的在线智能客服对话系统。项目从零开始，当前完全为空。

## 用户决策

- 开发顺序：后端优先，Tauri 桌面端后做
- 微信认证：Mock 模式开发，生产切换真实 OAuth
- RAGFlow：Docker 配置 + Mock 封装，RAG_MODE 环境变量切换
- 微调管线：核心先做，数据收集集成到对话流程，训练脚本后做

---

## 1. 项目目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # pydantic-settings 配置
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py          # 路由聚合
│   │       ├── auth.py            # POST /login (Mock 微信)
│   │       ├── chat.py            # SSE 流式对话
│   │       ├── session.py         # 会话 CRUD
│   │       └── feedback.py        # 反馈收集 & 统计
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # Base + TimestampMixin
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   └── feedback.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── session.py
│   │   └── feedback.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── chat_service.py
│   │   └── feedback_service.py
│   ├── agent/                     # LangGraph 核心
│   │   ├── __init__.py
│   │   ├── state.py               # AgentState TypedDict
│   │   ├── graph.py               # StateGraph 构建编译
│   │   ├── checkpointer.py        # AsyncPostgresSaver 工厂
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── intent.py          # 意图识别
│   │   │   ├── chat.py            # 闲聊回复
│   │   │   ├── rag.py             # RAG检索（含timeout）
│   │   │   ├── rewrite.py         # 查询重写（≤3次）
│   │   │   ├── generate.py        # 答案生成
│   │   │   └── fallback.py        # 兜底/转人工
│   │   └── edges/
│   │       ├── __init__.py
│   │       └── conditions.py      # 条件边路由
│   ├── rag/                       # RAG 抽象层
│   │   ├── __init__.py
│   │   ├── base.py                # AbstractRAGClient (ABC)
│   │   ├── ragflow.py             # RAGFlow 真实实现
│   │   └── mock.py                # Mock (开发/测试)
│   ├── llm/
│   │   ├── __init__.py
│   │   └── ollama_client.py       # Ollama HTTP 封装
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py          # Celery 实例配置
│       └── human_review.py        # 人工审核任务
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_chat.py
│   ├── test_agent.py
│   └── test_rag.py
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 2. 数据库模型设计

### ER 关系

```
User 1 ─── N Session 1 ─── N Message 1 ─── 0..1 Feedback
```

### 表结构

#### users
| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| wx_openid | VARCHAR(128) UNIQUE | 微信 OpenID (Mock 模式用随机串) |
| nickname | VARCHAR(64) | |
| avatar_url | VARCHAR(512) | |
| is_active | BOOLEAN | |
| created_at / updated_at | TIMESTAMP | |

#### sessions
| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| user_id | UUID FK → users | |
| title | VARCHAR(256) | 会话标题 |
| status | ENUM(active/paused/closed) | |
| langgraph_thread_id | VARCHAR(128) UNIQUE | 关联 LangGraph Checkpointer |
| metadata | JSONB | |
| created_at / updated_at | TIMESTAMP | |

#### messages
| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → sessions | |
| role | ENUM(user/assistant/system) | |
| content | TEXT | |
| intent | VARCHAR(32) NULLABLE | 意图标签（数据分析用） |
| metadata | JSONB | |
| created_at | TIMESTAMP | |

#### feedbacks
| 列 | 类型 | 说明 |
|---|---|---|
| id | UUID PK | |
| message_id | UUID FK → messages UNIQUE | |
| user_id | UUID FK → users | |
| rating | SMALLINT CHECK(1-5) | |
| is_liked | BOOLEAN NULLABLE | 点赞/踩 |
| comment | TEXT NULLABLE | |
| created_at | TIMESTAMP | |

---

## 3. LangGraph 图结构

### 3.1 AgentState (state.py)

```
AgentState:
  messages: list[dict]            # 对话历史
  user_id: str
  session_id: str
  intent: str                     # 意图分类
  intent_confidence: float
  rag_context: list[str]          # RAG 检索片段
  rewrite_count: int              # 重写次数 (max=3)
  final_answer: str
  needs_human: bool
  error: str | None
```

### 3.2 节点与路由

```
START → intent_classifier
              │
    ┌─────────┼─────────┐
  chitchat  knowledge  human/complex
              │            │
         rag_retrieval  query_rewrite
              │         (loop ≤3 → rag)
              │            │
         answer_gen    fallback/转人工
              │            │
              └─────┬──────┘
                   END
```

### 3.3 条件边

- `route_by_intent`: 按 intent 分岔到 chitchat / rag / fallback
- `route_after_rag`: 有 error → fallback，无 → answer_gen
- `route_after_rewrite`: count < 3 → rag_retrieval (循环)，≥ 3 → fallback (熔断)

### 3.4 超时与限制

- RAG 检索: `asyncio.wait_for(..., timeout=5s)`，超时设 error
- 全图: `asyncio.wait_for(graph.ainvoke(), timeout=30s)`
- 递归: `rewrite_count >= 3` → 强制 fallback

### 3.5 持久化

使用 LangGraph 内置 `AsyncPostgresSaver`，不自建快照表。`sessions.langgraph_thread_id` 桥接业务会话与 LangGraph 状态。

---

## 4. API 设计

```
Base: /api/v1

认证 (Mock 微信):
  POST /auth/login           → JWT token
  GET  /auth/me              → 用户信息

对话 (SSE):
  POST /chat/send            → SSE 事件流 (intent/thinking/token/rag_sources/done/error)

会话:
  GET    /sessions           → 会话列表
  POST   /sessions           → 新建会话
  GET    /sessions/{id}      → 详情
  GET    /sessions/{id}/messages → 历史消息
  PATCH  /sessions/{id}      → 状态更新

反馈:
  POST /feedback             → 提交评价
  GET  /feedback/stats       → 统计数据
```

---

## 5. Docker Compose 服务编排

| 服务 | 镜像 | 端口(内网) | 说明 |
|---|---|---|---|
| ollama | ollama/ollama | 11434 | Qwen2.5-1.5B 模型 |
| ragflow | infiniflow/ragflow | 9380 | 知识库引擎 |
| postgres | pgvector/pg16 | 5432 | 结构化 + 向量 |
| redis | redis:7-alpine | 6379 | Celery broker |
| backend | 自建 Dockerfile | 8000 | FastAPI |
| celery_worker | 同 backend 镜像 | - | 异步任务 |

环境变量通过 `.env` 注入，`RAG_MODE=mock` 切换 Mock/真实。

---

## 6. 开发阶段

### Phase 1：项目骨架 + 数据库
- 创建目录结构，requirements.txt
- config.py (pydantic-settings)
- SQLAlchemy 模型（5张表）
- Alembic 初始迁移
- docker-compose.yml (postgres + redis + ollama)
- 验证：docker compose up → 表创建成功

### Phase 2：LangGraph Agent 核心
- AgentState 定义
- RAG 抽象层 (ABC + Mock)
- Ollama LLM 客户端
- 6 个节点实现
- 3 个条件路由函数
- StateGraph 构建编译 + AsyncPostgresSaver
- 单元测试：Mock 模式全链路走通
- 验证：图可 ainvoke，暂停后可恢复

### Phase 3：FastAPI 路由 + 认证
- 依赖注入 (deps.py)
- /auth/login + /auth/me
- /chat/send (SSE 流式)
- /sessions CRUD + /messages
- 集成测试
- 验证：curl 发送消息，收到 SSE 回复

### Phase 4：RAGFlow 真实集成
- docker-compose 加入 RAGFlow
- ragflow.py 实现
- 环境变量切换
- 验证：上传文档 → 提问 → 带引用答案

### Phase 5：反馈收集 + 人工审核
- /feedback 提交/统计
- Celery 配置 + human_review 任务
- 难问题入队、会话暂停/恢复
- 验证：难问题 → 队列 → 会话暂停

### Phase 6：安全加固
- LiteLLM 网关（生产环境）
- Ollama 127.0.0.1 绑定
- RAGFlow 密码修改
- Rate Limiting

### Phase 7+：Tauri 桌面端、LoRA 微调管线

---

## 架构决策记录

| 决策 | 选择 | 理由 |
|---|---|---|
| ORM | SQLAlchemy 2.0 async + asyncpg | FastAPI 原生异步 |
| Checkpointer | LangGraph 内置 AsyncPostgresSaver | 不自建，避免版本兼容问题 |
| RAG 抽象 | ABC + 环境变量切换 | 简单实用 |
| 超时策略 | 节点级(5s) + 图级(30s) 双层 | 检索+全链路兜底 |
| Celery 粒度 | 仅人工审核 | 保持对话实时性 |
| 推送方式 | SSE (非 WebSocket) | 单向流式推送够用 |

---

## 验证方式

每个 Phase 结束后：
1. Phase 1: `docker compose up` → 数据库表创建
2. Phase 2: `pytest tests/test_agent.py` → Mock 模式流程图走通
3. Phase 3: `curl -X POST /api/v1/chat/send` → SSE 流式回复
4. Phase 4: RAGFlow 上传文档 → 提问得到引用
5. Phase 5: 难问题 → Celery 队列 → 会话 paused
6. 全局: `docker compose up` → 一键启动所有服务
