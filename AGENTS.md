# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## 项目概述

基于 LangGraph + RAGFlow + Qwen2.5 的在线智能客服对话系统。提供 Tauri 桌面客户端（React + TypeScript），后端通过 Docker Compose 部署在阿里云 ECS。

## 技术栈

| 环节 | 方案 | 说明 |
|------|------|------|
| AI 模型 | Qwen2.5-1.5B-Instruct | 通过 Ollama 本地部署 |
| Embedding | bge-m3 | 通过 Ollama 部署，长期记忆向量化 |
| RAG 框架 | RAGFlow | Docker 部署，全文检索 + 向量检索混合策略 |
| Agent 引擎 | LangGraph | 图状态机，条件边路由，状态持久化 |
| 后端框架 | FastAPI | 异步高性能，提供 RESTful API |
| 异步任务 | Celery + Redis | 人工审核分流、长任务调度 |
| 数据库 | PostgreSQL + pgvector | 结构化数据 + 向量存储合一 |
| 认证 | 微信 OAuth 2.0 | Mock 模式（开发）/ 真实 OAuth（生产） |
| 桌面端 | Tauri v2 + React 18 + TypeScript + Tailwind CSS | Windows 11，打包 .msi/.exe |
| 容器化 | Docker Compose | 一键部署 Ollama / RAGFlow / FastAPI / PostgreSQL / Celery |

## 构建与运行

### 环境准备

```bash
cd backend
cp .env.example .env        # 编辑 .env 中的密钥和密码
```

> 国内网络需配置 Docker 镜像加速：Docker Desktop → Settings → Docker Engine → 添加 `registry-mirrors`，推荐 `https://docker.1ms.run`。

### 启动后端所有服务

```bash
cd backend
docker compose up -d
```

### 拉取 AI 模型（首次）

```bash
docker exec -it backend-ollama-1 ollama pull qwen2.5:1.5b
docker exec -it backend-ollama-1 ollama pull bge-m3
```

### 启动桌面客户端

```bash
cd tauri-app

# 安装依赖（首次）
npm install

# 浏览器开发模式
npm run dev                    # → http://127.0.0.1:1420

# Tauri 桌面窗口开发
npm run tauri:dev

# 打包 Windows 安装包
npm run tauri:build            # → .msi + .exe
```

### 运行测试

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

### 数据库迁移

```bash
cd backend
alembic revision --autogenerate -m "init"
alembic upgrade head
```

> 注意：开发环境启动时自动执行 `Base.metadata.create_all`，无需手动迁移。

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口，lifespan 自动建表，CORS/安全头/全局异常
│   │   ├── config.py                  # pydantic-settings，所有配置从 .env 读取
│   │   ├── api/
│   │   │   ├── deps.py                # 依赖注入：get_current_user, get_rag_client, get_chat_service
│   │   │   ├── rate_limit.py          # IP 速率限制器
│   │   │   └── v1/
│   │   │       ├── router.py          # /api/v1 路由聚合
│   │   │       ├── auth.py            # POST /auth/login + GET /auth/me (Mock微信→JWT)
│   │   │       ├── chat.py            # POST /chat/send (SSE 流式对话 + 内存提取)
│   │   │       ├── session.py         # /sessions CRUD + DELETE + 消息历史
│   │   │       └── feedback.py        # /feedback 提交 + 统计
│   │   ├── models/                    # SQLAlchemy ORM (User, Session, Message, Feedback, LongTermMemory)
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── services/                  # 业务逻辑层 (Auth, Chat, Feedback, Memory)
│   │   ├── agent/                     # LangGraph 核心引擎
│   │   │   ├── state.py               # AgentState TypedDict 定义
│   │   │   ├── graph.py               # StateGraph 构建+编译，依赖注入 LLM/RAG
│   │   │   ├── checkpointer.py        # AsyncPostgresSaver 工厂（生产环境持久化）
│   │   │   ├── nodes/                 # 6 个节点：intent, chat, rag, rewrite, generate, fallback
│   │   │   └── edges/conditions.py    # 3 个条件路由函数
│   │   ├── rag/                       # RAG 抽象层
│   │   │   ├── base.py                # AbstractRAGClient (ABC)
│   │   │   ├── mock.py                # MockRAGClient (开发/测试，内置示例知识库)
│   │   │   └── ragflow.py             # RAGFlowClient (生产，调用 RAGFlow REST API)
│   │   ├── llm/
│   │   │   ├── ollama_client.py       # Ollama HTTP API 封装 (chat + chat_stream)
│   │   │   └── embedding_client.py    # bge-m3 Embedding 封装
│   │   └── tasks/                     # Celery 异步任务 (human_review)
│   ├── alembic/                       # 数据库迁移
│   ├── tests/                         # pytest 测试
│   ├── docker-compose.yml             # 5 服务编排 (ollama, postgres, redis, backend, celery)
│   ├── Dockerfile                     # Backend 镜像 (python:3.12-slim)
│   ├── requirements.txt
│   ├── finetune/                      # LoRA 微调管线（5 个脚本）
│   └── .env.example
│
├── tauri-app/
│   ├── src/
│   │   ├── main.tsx                   # React 入口
│   │   ├── App.tsx                    # React Router + AuthContext
│   │   ├── api/client.ts              # HTTP 客户端 + SSE (fetch + ReadableStream)
│   │   ├── hooks/useChat.ts           # SSE 流式消息 hook
│   │   ├── contexts/AuthContext.tsx    # JWT + 用户状态
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx          # Mock 微信登录
│   │   │   └── ChatPage.tsx           # 主聊天界面（会话管理 + 删除）
│   │   ├── components/
│   │   │   ├── SessionList.tsx        # 左侧会话列表（悬停删除按钮）
│   │   │   ├── ChatWindow.tsx         # 右侧对话窗口
│   │   │   ├── MessageBubble.tsx      # 消息气泡
│   │   │   ├── ChatInput.tsx          # 输入框 (Enter/Shift+Enter)
│   │   │   └── FeedbackBar.tsx        # 点赞/踩 + 1-5 星评分
│   │   ├── types.ts                   # TypeScript 类型
│   │   └── index.css                  # Tailwind 入口
│   ├── src-tauri/
│   │   ├── tauri.conf.json            # 窗口 1200x800，nsis + wix 打包
│   │   ├── Cargo.toml
│   │   └── src/lib.rs + main.rs       # Tauri Rust 入口
│   ├── vite.config.ts                 # Vite + Tauri 配置，VITE_API_BASE 注入
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
│
├── docs/
│   ├── api.md                         # REST API 完整参考
│   ├── deployment.md                  # 部署指南（含桌面端构建）
│   ├── architecture.md                # 架构设计
│   └── memory-system.md               # 双重记忆系统
├── CHANGELOG/                         # 更新报告（按日期归档）
├── .gitignore                         # Python + Node + Rust + Docker 忽略规则
├── README.md
└── AGENTS.md                          # 本文件
```

## 架构设计要点

### LangGraph 工作流

- **条件边（Conditional Edges）**: `route_by_intent` 根据意图分岔到 chitchat / rag_retrieval / fallback；`route_after_rag` 检索后按 error 状态分流；`route_after_rewrite` 按重写次数熔断
- **状态传递**: 通过共享 `AgentState`（TypedDict）在各节点间传递上下文
- **超时熔断**: `rag_node` 内 `asyncio.wait_for(..., timeout=5s)`，超时设 `error="rag_timeout"` → 条件边路由到 fallback
- **递归限制**: `rewrite_count >= 3` → 强制 fallback；全图 `asyncio.wait_for(30s)` 兜底
- **状态持久化**: 开发环境 MemorySaver，生产环境通过 `checkpointer.py` 创建 `AsyncPostgresSaver` 快照到 PostgreSQL

### 双重记忆系统

- **短期记忆**: LangGraph Checkpointer → PostgreSQL 定期快照会话状态（`sessions.langgraph_thread_id` 桥接）
- **长期记忆**: pgvector 存储用户偏好向量，`MemoryService` 在每次对话 done 事件后自动提取和存储

### RAG 切换机制

通过环境变量 `RAG_MODE=mock` / `RAG_MODE=ragflow` 切换。`api/deps.py` 中 `get_rag_client()` 为单例模式。

### Mock 微信登录

开发环境 `WECHAT_MOCK_ENABLED=true`，任意 `code` 字符串生成 `mock_openid_XXXXXX`，自动创建用户并签发 JWT。

### 数据飞轮

对话反哺链路：`/feedback` 提交评分/点赞 → `feedbacks` + `messages` 联合查询 → 微调数据集 → LoRA 微调 → 模型迭代

### 人工审核解耦

`fallback_node` 返回 `needs_human=True` → Celery 异步任务推送人工队列 → 会话状态 `paused` → 审核完成后恢复

### SSE 流式对话（桌面端）

桌面端使用 `fetch` + `ReadableStream` 手动解析 SSE 格式（而非 `EventSource`，因为需要 POST 方法 + Authorization header）。事件类型：`intent` → `thinking` → `done`。后端在 `yield` done 事件后执行 `await asyncio.sleep(0)` 确保 flush。

## 关键文件（修改时优先阅读）

| 文件 | 作用 |
|------|------|
| `backend/app/agent/graph.py` | LangGraph 图构建与节点编排 |
| `backend/app/agent/state.py` | AgentState 类型契约 |
| `backend/app/agent/edges/conditions.py` | 条件路由逻辑 |
| `backend/app/services/chat_service.py` | 对话主流程：astream 调用 + SSE 事件生成 |
| `backend/app/api/v1/chat.py` | SSE 端点，消息入库，内存提取 |
| `backend/app/api/v1/session.py` | 会话 CRUD + DELETE（级联删除 feedbacks/messages） |
| `backend/app/rag/base.py` | RAG 接口定义 |
| `backend/docker-compose.yml` | 全栈服务编排 |
| `tauri-app/src/api/client.ts` | 前端 API 客户端 + SSE ReadableStream 解析 |
| `tauri-app/src/hooks/useChat.ts` | SSE 流式消息 hook |
| `tauri-app/src/pages/ChatPage.tsx` | 桌面端主界面编排 |
| `tauri-app/src-tauri/tauri.conf.json` | 打包和窗口配置 |

## 安全要求

部署前必须完成以下检查：

- **Ollama 服务隔离**: 生产环境移除 `docker-compose.yml` 中 Ollama 的 `ports` 映射，仅容器内网访问
- **AI 网关鉴权**: 引入 LiteLLM 作为模型访问唯一入口，开启 API KEY 鉴权
- **RAGFlow 安全**: 首次登录后修改默认管理员密码；部署在私有网络
- **全链路加密**: 生产环境加 Nginx 反向代理 + Let's Encrypt HTTPS
- **JWT 密钥**: 修改 `.env` 中 `SECRET_KEY` 为随机强密钥

## 文档

| 文档 | 路径 | 内容 |
|------|------|------|
| API 文档 | [docs/api.md](docs/api.md) | 完整 REST API 参考（认证、对话、会话、反馈） |
| 部署指南 | [docs/deployment.md](docs/deployment.md) | 开发/生产部署流程，阿里云 ECS 部署，桌面端构建，安全清单 |
| 架构设计 | [docs/architecture.md](docs/architecture.md) | LangGraph 图结构、Checkpoint 持久化、异常处理 |
| 记忆系统 | [docs/memory-system.md](docs/memory-system.md) | 短期+长期双重记忆系统详解 |
| 微调管线 | [backend/finetune/README.md](backend/finetune/README.md) | LoRA 微调：数据导出、格式化、训练、评估、部署 |
| 更新报告 | [CHANGELOG/](CHANGELOG/) | 按日期归档的问题与解决方案 |

## .trae Skills

| Skill | 用途 |
|-------|------|
| `requirement-analyst` | 需求分析 |
| `system-architect` | 架构设计 |
| `task-planner` | 任务拆解 |
| `spec-coder` | 按规格实现代码 |
| `agent-security-reviewer` | AI Agent 10 域安全审计 |
| `design` / `design-system` / `brand` / `ui-styling` | UI 设计与样式系统 |

## 关键约束

- **避免过度工程化**: 资源有限的私有化部署场景，不做不必要的抽象
- **RAG 模式**: 开发用 Mock（内置知识库），生产切换到 RAGFlow
- **认证模式**: 开发用 Mock 微信登录，生产配置真实微信 OAuth
- **桌面端通信**: 使用 `fetch` + `ReadableStream`（非 EventSource），因为需要 POST + Authorization header
