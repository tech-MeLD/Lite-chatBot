# AI 智能客服系统

基于 **LangGraph + RAGFlow + Qwen2.5** 的在线智能客服对话系统。以 LangGraph 图状态机为核心引擎，串联意图识别、RAG 知识检索、答案生成与人工兜底，支持对话状态持久化与中断恢复，面向私有化部署场景。

提供 **Tauri 桌面客户端**（Windows .msi/.exe），React + TypeScript 构建，SSE 流式对话体验。

## 快速开始

### 1. 环境要求

| 环境           | 用途             |
| -------------- | ---------------- |
| Docker Desktop | 后端服务运行     |
| Python 3.12    | 本地开发/测试    |
| Node.js 18+    | 桌面端前端开发   |
| Rust 1.70+     | Tauri 桌面端编译 |

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 中的 SECRET_KEY 和数据库密码
```

> 国内网络需配置 Docker 镜像加速：Docker Desktop → Settings → Docker Engine → 添加 `registry-mirrors: ["https://docker.1ms.run"]`

### 3. 启动后端服务

```bash
cd backend
docker compose up -d
```

### 4. 拉取 AI 模型（首次必须）

```bash
docker exec -it backend-ollama-1 ollama pull qwen2.5:1.5b
docker exec -it backend-ollama-1 ollama pull bge-m3
```

### 5. 验证

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 6. 启动桌面客户端

```bash
cd tauri-app

# 浏览器开发模式
npm install && npm run dev
# → http://127.0.0.1:1420

# Tauri 桌面窗口模式
npm run tauri:dev

# 打包 Windows 安装包
npm run tauri:build
# → src-tauri/target/release/bundle/msi/*.msi
# → src-tauri/target/release/bundle/nsis/*.exe
```

### 7. 测试对话

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

## 技术栈

| 组件       | 方案                                            |
| ---------- | ----------------------------------------------- |
| AI 模型    | Qwen2.5-1.5B-Instruct (Ollama)                  |
| Embedding  | bge-m3 (Ollama)                                 |
| RAG 引擎   | RAGFlow（混合检索）或 Mock（开发）              |
| Agent 框架 | LangGraph（图状态机 + 条件边 + 持久化）         |
| 后端       | FastAPI（SSE 流式 + Celery 异步任务）           |
| 数据库     | PostgreSQL + pgvector                           |
| 记忆系统   | Checkpointer（短期）+ pgvector（长期）          |
| 桌面端     | Tauri v2 + React 18 + TypeScript + Tailwind CSS |
| 容器化     | Docker Compose                                  |

## 文档

| 文档                           | 说明                                                      |
| ------------------------------ | --------------------------------------------------------- |
| [API 文档](docs/api.md)           | 完整 REST API 参考（认证、对话、会话、反馈）              |
| [部署指南](docs/deployment.md)    | 开发/生产/ECS 部署流程，Docker 镜像加速，安全清单         |
| [架构设计](docs/architecture.md)  | LangGraph 图结构、Checkpoint 持久化、条件边路由、异常处理 |
| [记忆系统](docs/memory-system.md) | Checkpointer 短期记忆 + pgvector 长期记忆详解             |

## 项目交付物

- [X] LangGraph 工作流引擎（条件边、状态传递、超时熔断、递归限制）
- [X] Checkpoint 持久化到 PostgreSQL
- [X] 动态中断恢复机制
- [X] RAG 抽象层（Mock + RAGFlow 可切换）
- [X] Mock 微信登录 + JWT 认证
- [X] SSE 流式对话
- [X] 反馈收集（数据飞轮基础）
- [X] Celery 人工审核解耦
- [X] pgvector 长期记忆（用户偏好提取、语义检索）
- [X] Docker Compose 一键部署
- [X] 安全中间件与速率限制
- [X] LoRA 微调管线（数据导出、格式化、QLoRA 训练、评估、Ollama 部署）
- [X] Tauri 桌面端（登录、会话管理、SSE 流式对话、反馈、.msi/.exe 打包）

## 更新报告

问题和修复记录在 [CHANGELOG/](CHANGELOG/) 目录，按日期归档。
