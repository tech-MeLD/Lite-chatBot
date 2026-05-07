# AGENTS.md 创建计划

## Context
项目当前处于**预开发阶段**，仅有需求文档 `提示词.md` 和 `.trae/` 技能目录，无任何应用代码。需要创建 AGENTS.md 文件，为后续 Qoder 实例在此仓库中工作提供指南。

## AGENTS.md 内容规划

### 需要包含的内容：

1. **项目概述**
   - 项目目标：基于 LangGraph + RAGFlow + Qwen2.5 的在线智能客服对话系统
   - 桌面端使用 Tauri 框架，后端 Docker 部署在阿里云 ECS

2. **技术栈说明**
   - AI模型：Qwen2.5-1.5B-Instruct，通过 Ollama 部署
   - RAG框架：RAGFlow（Docker部署，混合检索策略）
   - Agent引擎：LangGraph（图状态机，条件边路由，状态持久化）
   - 后端：FastAPI + Celery + Redis（异步任务）
   - 数据库：PostgreSQL + pgvector（结构化 + 向量存储）
   - 认证：微信 OAuth 2.0
   - 桌面端：Tauri（Windows 11，打包 .msi/.exe）
   - 容器化：Docker Compose 一键部署

3. **架构设计要点**（来自提示词.md）
   - LangGraph 工作流：条件边设计（智能路由）、状态传递与并行上下文合并、异常处理
   - 双重记忆系统：短期记忆（LangGraph Checkpointer → PostgreSQL）+ 长期记忆（pgvector）
   - 数据飞轮：对话反哺 → LoRA 微调 → 模型迭代
   - 超时熔断与递归限制机制

4. **安全要求**（来自提示词.md Checklist）
   - Ollama 服务隔离（127.0.0.1）
   - LiteLLM API KEY 网关鉴权
   - RAGFlow 默认密码修改 + 网络隔离
   - 全链路数据加密

5. **可用的 .trae Skills**
   - requirement-analyst, system-architect, task-planner, spec-coder（开发流水线）
   - agent-security-reviewer（AI Agent 安全审计）
   - design, design-system, brand, ui-styling, slides, banner-design（UI/设计相关）

6. **构建与运行命令**（项目尚未创建，预留占位符）
   - Docker Compose 命令
   - Tauri 构建命令（npm run tauri dev/build）
   - 测试命令

7. **关键约束**
   - 避免过度工程化
   - 资源有限的私有化部署场景
   - 项目完成后需产出技术方案细节文档和 README

## 需要修改的文件
- 创建 `d:\AI_projects\test_project\test01\AGENTS.md`（新文件，项目根目录不存在此文件）

## 验证方式
- 确认 AGENTS.md 文件在项目根目录正确创建
- 确认内容涵盖技术栈、架构、安全、可用技能等关键信息
- 确认不包含通用开发实践建议和冗余信息
