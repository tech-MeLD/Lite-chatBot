# AGENTS.md

This file provides guidance to Qoder (qoder.com) when working with code in this repository.

## 项目概述

基于 LangGraph + RAGFlow + Qwen2.5 的在线智能客服对话系统。桌面端使用 Tauri（Windows 11），后端通过 Docker Compose 部署在阿里云 ECS。

## 技术栈

| 环节 | 方案 | 说明 |
|------|------|------|
| AI 模型 | Qwen2.5-1.5B-Instruct | 通过 Ollama 本地部署 |
| RAG 框架 | RAGFlow | Docker 部署，全文检索 + 向量检索混合策略 |
| Agent 引擎 | LangGraph | 图状态机，条件边路由，状态持久化 |
| 后端框架 | FastAPI | 异步高性能，提供 RESTful API |
| 异步任务 | Celery + Redis | 人工审核分流、长任务调度 |
| 数据库 | PostgreSQL + pgvector | 结构化数据 + 向量存储合一 |
| 认证 | 微信 OAuth 2.0 | 标准协议 |
| 桌面端 | Tauri | Windows 11，打包 .msi/.exe |
| 容器化 | Docker Compose | 一键部署 Ollama / RAGFlow / FastAPI / PostgreSQL / Celery |

## 架构设计要点

### LangGraph 工作流

- **条件边（Conditional Edges）**: 根据意图识别结果智能路由，如闲聊 → 闲聊回复节点，业务问题 → RAG 检索节点
- **状态传递**: 通过共享 `AgentState`（TypedDict）在各节点间传递上下文
- **并行上下文合并**: 多 RAG 节点并行执行时，输出默认追加合并到 State，下游节点需做去重处理
- **超时熔断**: 关键节点（如检索）必须包含超时控制，超时后走兜底回复
- **递归限制**: 查询重写等循环节点设置最大重试次数（如 `max_iterations=3`），超过后强制走兜底或转人工
- **状态持久化**: 使用 LangGraph Checkpointer 定期快照到 PostgreSQL，支持对话中断后无缝恢复

### 双重记忆系统

- **短期记忆**: LangGraph Checkpointer → PostgreSQL 定期快照会话状态
- **长期记忆**: pgvector 存储用户偏好、历史行为向量，跨会话记忆

### 数据飞轮

对话反哺链路：用户反馈收集 → 数据标注与清洗 → 人工校验 → LoRA 微调 → 模型迭代

### 人工审核解耦

难问题通过 Celery 异步任务队列推送人工，主流程立即保存状态快照并暂停会话。审核完成后通过快照恢复任务，与用户交互完全解耦。

## 安全要求

部署前必须完成以下检查：

- **Ollama 服务隔离**: 设置 `OLLAMA_HOST=127.0.0.1`，仅内网访问，禁止暴露公网
- **AI 网关鉴权**: 引入 LiteLLM 作为模型访问唯一入口，开启 API KEY 鉴权，监控 token 消耗和请求频率
- **RAGFlow 安全**: 首次登录后修改默认管理员密码；部署在私有网络，仅允许客服应用服务 IP 访问
- **全链路加密**: 用户数据全链路加密传输与存储

## .trae Skills

本项目预置以下可复用的 Agent Skills，位于 `.trae/skills/` 目录：

| Skill | 用途 |
|-------|------|
| `requirement-analyst` | 需求分析 → 输出 REQUIREMENT.md |
| `system-architect` | 架构设计 → 输出 DESIGN.md |
| `task-planner` | 任务拆解 → 输出 TODO.md |
| `spec-coder` | 按规格实现代码 |
| `agent-security-reviewer` | AI Agent 10 域安全审计（Ollama, RAGFlow, 微调等） |
| `design` / `design-system` / `brand` / `ui-styling` | UI 设计与样式系统 |

参考数据位于 `.trae/src/ui-ux-pro-max/`，包含跨技术栈的 UI/UX 参考数据。

## 关键约束

- **避免过度工程化**: 控制在资源有限的私有化部署场景内，不做不必要的抽象
- **项目交付物**: 完成后需产出技术方案细节文档（checkpoint 持久化、动态中断恢复、并行上下文合并等）和 README
