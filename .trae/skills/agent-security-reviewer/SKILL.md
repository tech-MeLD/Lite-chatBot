---
name: "agent-security-reviewer"
description: "AI Agent 项目上线前安全审查，覆盖模型服务、知识库、数据闭环、应用安全、基础设施等 10 大安全域。Invoke when deploying AI agents, launching LLM-powered services, or auditing agent infrastructure for security vulnerabilities."
---

# Agent Security Reviewer

AI Agent 项目上线部署前的全面安全审查。覆盖模型推理服务、RAG 知识库、微调数据闭环、应用安全、身份认证、数据隐私、日志监控、供应链、基础设施及合规治理十大安全领域。

## Role Overview

Agent Security Reviewer 扮演安全审计专家角色，对 AI Agent 项目在部署前进行多维度安全检查，输出结构化的安全评估报告，识别风险等级（Critical / High / Medium / Low），并给出可落地的修复建议。

## When to Use

- AI Agent 项目即将上线部署，需要安全审查
- 自行搭建了 Ollama、vLLM、RAGFlow 等自托管 AI 基础设施
- 项目涉及用户数据收集、模型微调训练
- 引入了第三方 AI 模型或开源组件，需评估供应链风险
- 需要满足企业内部安全合规要求
- 项目发生过安全事件，需要进行全面安全排查

## Review Scope（十大安全域）

| # | 安全域 | 核心关注点 |
|---|--------|-----------|
| ❶ | 模型与推理服务安全 | Ollama/vLLM 服务隔离、API 鉴权、TLS 加密 |
| ❷ | RAGFlow 知识库安全 | 访问控制、网络隔离、默认凭证、数据脱敏 |
| ❸ | 微调数据闭环安全 | 反馈收集、数据标注清洗、人工校验、隐私保护 |
| ❹ | 应用安全 | Prompt Injection 防护、输入验证、XSS/CSRF |
| ❺ | 身份认证与访问控制 | MFA、最小权限、API Key 管理、会话安全 |
| ❻ | 数据安全与隐私 | 传输加密、存储加密、脱敏策略、备份恢复 |
| ❼ | 日志与监控 | 安全审计日志、异常检测、实时告警 |
| ❽ | 供应链与依赖安全 | 依赖漏洞扫描、容器镜像安全、SBOM |
| ❾ | 基础设施与部署安全 | Docker/K8s 安全配置、网络策略、密钥管理 |
| ❿ | 合规与安全治理 | 数据合规、安全测试(SAST/DAST)、应急响应 |

---

## Checklist ❶: 模型与推理服务安全

### 1.1 Ollama 服务隔离

- [ ] **绑定内网地址**: 设置 `OLLAMA_HOST=127.0.0.1`，禁止监听 `0.0.0.0`
  ```bash
  # systemd 或 docker-compose 中配置
  environment:
    - OLLAMA_HOST=127.0.0.1
  ```
- [ ] **禁用外网暴露**: 确认防火墙规则未开放 Ollama 默认端口 (11434)
- [ ] **反向代理鉴权**: 若必须对外暴露，通过 Nginx/Caddy 反向代理并添加认证层
  ```nginx
  # Nginx 反代示例
  location /ollama/ {
      auth_basic "Ollama API";
      auth_basic_user_file /etc/nginx/.htpasswd;
      proxy_pass http://127.0.0.1:11434/;
  }
  ```
- [ ] **验证**: `curl http://<公网IP>:11434/api/tags` 应从外网不可达

### 1.2 AI 网关鉴权

- [ ] **统一入口**: 引入 LiteLLM/openai-forward 等轻量级 AI 网关，作为访问所有模型的唯一入口
- [ ] **API Key 鉴权**: 网关层开启 API Key 验证，每个客户端/应用使用独立 Key
  ```yaml
  # LiteLLM Proxy 配置示例
  general_settings:
    master_key: os.environ/LITELLM_MASTER_KEY
  model_list:
    - model_name: gpt-4o
      litellm_params:
        model: openai/gpt-4o
        api_key: os.environ/OPENAI_API_KEY
  ```
- [ ] **速率限制**: 配置 token 消耗上限和请求频率限制 (Rate Limiting)
- [ ] **Token 用量监控**: 启用 Prometheus + Grafana 面板监控每个 Key 的 token 消耗
- [ ] **模型访问白名单**: 限制可供调用的模型列表，禁止访问未授权的模型
- [ ] **TLS 加密**: 网关对外接口强制 HTTPS，禁用 HTTP 明文传输

### 1.3 推理服务扩展安全

- [ ] **模型文件完整性**: 部署前校验模型文件的 SHA256 哈希值
- [ ] **推理超时限制**: 设置合理的请求超时，防止资源耗尽
- [ ] **上下文窗口限制**: 限制最大输入 token 数，防止滥用
- [ ] **GPU 资源隔离**: 使用 cgroups/GPU 虚拟化隔离不同租户

---

## Checklist ❷: RAGFlow 知识库安全

### 2.1 默认凭证与访问控制

- [ ] **首次登录改密**: 部署后立即修改 RAGFlow 默认管理员密码（强密码: 16+ 字符，含大小写字母、数字、特殊字符）
- [ ] **禁用默认账号**: 如存在 guest/demo 等测试账号，立即禁用或删除
- [ ] **RBAC 权限配置**: 为不同团队成员分配合适的角色权限（Admin / Editor / Viewer）
- [ ] **知识库权限**: 限制知识库的访问范围，敏感知识库仅授权必要人员

### 2.2 网络隔离与防火墙

- [ ] **私有网络部署**: RAGFlow 及其依赖组件（Elasticsearch/Infinity、MinIO、MySQL/PostgreSQL）均部署在受保护的私有网络或 VPC 中
- [ ] **防火墙白名单**: 仅允许客服应用服务的**特定内网 IP** 访问 RAGFlow API 端口
  ```bash
  # iptables 示例
  iptables -A INPUT -p tcp --dport 9380 -s 10.0.1.100 -j ACCEPT
  iptables -A INPUT -p tcp --dport 9380 -j DROP
  ```
- [ ] **Elasticsearch 安全**:
  - [ ] 开启 X-Pack Security 或等价认证机制
  - [ ] ES 绑定 `127.0.0.1` 或私有网络 IP
  - [ ] 禁用 ES 的动态脚本执行 (`script.allowed_types: none`)
- [ ] **MinIO/对象存储安全**:
  - [ ] 修改默认 Access Key 和 Secret Key
  - [ ] 启用桶策略，限制公开访问
  - [ ] 开启服务端加密 (SSE)

### 2.3 数据安全

- [ ] **文档上传校验**: 限制上传文件类型和白名单；扫描上传文件中的恶意内容
- [ ] **数据脱敏策略**: 知识库中的敏感信息（手机号、身份证、银行卡等）在上传前完成脱敏处理
- [ ] **检索结果过滤**: 实现检索结果的后处理过滤，防止敏感文档内容泄露给无权限用户
- [ ] **审计日志**: 开启 API 访问日志，记录知识库的增删改查操作

---

## Checklist ❸: 微调数据闭环安全

### 3.1 反馈收集机制

- [ ] **多维反馈入口**: 在 UI 中嵌入反馈组件
  - [ ] 点赞/踩（Thumbs Up/Down）
  - [ ] 会话评分（1-5 星）
  - [ ] 可选文字反馈输入框
- [ ] **反馈数据隐私**: 收集反馈时脱敏用户输入，不记录 PII（个人身份信息）
- [ ] **反馈防滥用**: 实施频率限制，防止恶意刷反馈数据

### 3.2 数据标注与清洗

- [ ] **高质量数据筛选**: 建立明确的数据质量标准（准确性、完整性、相关性、安全性）
- [ ] **数据分类导出**: 定期导出高质量与低质量对话，按类别归档
  ```
  data/
  ├── high_quality/
  │   ├── batch_2026-05/
  │   └── batch_2026-06/
  ├── low_quality/
  │   └── needs_review/
  └── edge_cases/
  ```
- [ ] **数据清洗流程**:
  - [ ] 去重：移除重复或高度相似的对话对
  - [ ] 去噪：剔除无意义的、截断的、格式错误的对话
  - [ ] 去偏：识别并纠正有害偏见内容
  - [ ] 脱敏：移除/替换所有 PII 数据
- [ ] **数据反哺闭环**: 确保"数据收集 → 标注清洗 → 模型微调 → 效果评估 → 线上部署"形成正向循环

### 3.3 人工校验 (Human-in-the-Loop)

- [ ] **自动标注 + 人工复核**: 自动标注流程后，关键数据必须经过人工抽检复核
- [ ] **抽样策略**: 高风险类别（安全、合规相关回答）100% 人工审核；常规类别不低于 10% 抽检
- [ ] **标注一致性校验**: 多人标注同一批数据，计算标注一致性 (Cohen's Kappa ≥ 0.6)
- [ ] **争议处理机制**: 建立标注争议的仲裁流程，由资深审核人员最终裁决

### 3.4 训练数据安全

- [ ] **差分隐私训练**: 在微调中引入差分隐私 (DP-SGD)，降低训练数据泄露风险
- [ ] **数据分区存储**: 微调数据与生产数据物理隔离，不同项目的数据逻辑隔离
- [ ] **访问审计**: 记录所有对微调数据集的访问和操作
- [ ] **数据保留策略**: 设定数据保留期限，超期数据安全销毁

---

## Checklist ❹: 应用安全 (LLM 应用专项)

### 4.1 Prompt Injection 防护

- [ ] **输入分隔**: 使用特殊分隔符将系统指令与用户输入隔开
  ```
  System: <system prompt here>
  User: #### USER INPUT START ####
  {user_input}
  #### USER INPUT END ####
  ```
- [ ] **输出指令过滤**: 检查模型输出是否包含类似系统指令的内容，防止间接注入
- [ ] **角色分离**: 将"指令遵循"与"内容生成"的上下文严格分离
- [ ] **输入清理**: 移除用户输入中的特殊控制字符和编码绕过尝试
- [ ] **结构化输出**: 尽量使用 JSON Mode / Function Calling，减少自由文本注入面

### 4.2 输入验证与输出过滤

- [ ] **输入长度限制**: 限制用户输入的最大字符数/Token 数
- [ ] **内容安全审查**: 集成内容安全 API 检测有害输入（涉黄、涉政、涉暴等）
- [ ] **输出审查**: 对模型输出进行内容安全审查后再返回给用户
- [ ] **敏感词过滤**: 维护敏感词库，对输入输出进行关键词匹配和语义检测
- [ ] **CORS 配置**: 仅允许受信任的域名跨域访问 API

### 4.3 前端安全

- [ ] **XSS 防护**: 模型输出渲染前进行 HTML 实体转义，使用 DOMPurify 等库清理
- [ ] **CSP 策略**: 配置严格的 Content-Security-Policy 头
- [ ] **CSRF Token**: 所有状态变更请求携带 CSRF Token
- [ ] **iframe 防护**: 设置 `X-Frame-Options: DENY` 防止点击劫持

---

## Checklist ❺: 身份认证与访问控制

- [ ] **多因素认证 (MFA)**: 管理后台及高权限操作强制开启 MFA
- [ ] **最小权限原则**: 每个服务账号仅拥有完成其功能所需的最小权限
- [ ] **API Key 安全管理**:
  - [ ] Key 通过环境变量或密钥管理服务注入，禁止硬编码
  - [ ] Key 支持按应用/用户粒度创建和吊销
  - [ ] 定期轮换长期有效的 Key（建议 90 天）
- [ ] **JWT Token 安全**:
  - [ ] 设置合理的过期时间 (Access Token ≤ 15min, Refresh Token ≤ 7d)
  - [ ] 使用 RS256/ES256 算法签名，禁用 `alg: none`
  - [ ] 登出时使 Token 失效（维护黑名单或使用短期 Token）
- [ ] **会话管理**:
  - [ ] 会话超时自动退出（建议闲置 30 分钟）
  - [ ] 限制同一账号的并发会话数
  - [ ] 使用 HttpOnly + Secure + SameSite Cookie

---

## Checklist ❻: 数据安全与隐私

- [ ] **传输加密**: 所有外部通信强制 TLS 1.2+，禁用弱加密套件
- [ ] **静态加密**: 数据库、文件存储、备份开启静态加密 (AES-256)
- [ ] **敏感数据脱敏**: 日志、监控中自动脱敏手机号/邮箱/IP/身份证等字段
- [ ] **用户数据隔离**: 多租户场景下，确保用户间数据严格隔离
- [ ] **数据备份**: 实施定期自动备份策略（数据库每日增量备份，全量每周备份）
- [ ] **备份恢复演练**: 每季度至少执行一次备份恢复演练
- [ ] **数据删除**: 支持用户数据删除请求（被遗忘权），确保所有副本均被清除
- [ ] **数据分类分级**: 对存储的数据进行分类（公开/内部/机密/绝密）并对应保护等级

---

## Checklist ❼: 日志与监控

- [ ] **安全审计日志**: 记录所有认证事件（登录/登出/失败）、权限变更、敏感数据访问
- [ ] **API 请求日志**: 记录每个 API 请求的来源 IP、User-Agent、请求体（脱敏后）、响应状态
- [ ] **异常行为检测**: 基于规则或 ML 检测异常调用模式（如短时间大量请求、非工作时间异常操作）
- [ ] **实时告警**:
  - [ ] 失败登录次数超过阈值告警
  - [ ] API Key 泄露风险告警（如在 Git 仓库中发现）
  - [ ] 模型输出异常（反复拒绝、生成有害内容）
- [ ] **日志存储安全**: 日志中禁止记录明文密码/Token/API Key
- [ ] **日志保留策略**: 安全审计日志保留 ≥ 180 天，操作日志保留 ≥ 90 天

---

## Checklist ❽: 供应链与依赖安全

- [ ] **依赖漏洞扫描**:
  - [ ] Python: `pip-audit` 或 `safety check`
  - [ ] JavaScript/Node.js: `npm audit` 或 `pnpm audit`
  - [ ] CI 流程中集成自动扫描 (如 Dependabot / Renovate)
- [ ] **依赖锁定**: 使用 `requirements.txt` (含 hash) / `package-lock.json` / `poetry.lock` 锁定依赖版本
- [ ] **容器镜像安全**:
  - [ ] 使用官方或可信基础镜像 (如 `python:3.12-slim`)
  - [ ] 扫描镜像漏洞 (`docker scan` / `trivy`)
  - [ ] 固定镜像 Tag，避免使用 `:latest`
- [ ] **SBOM 生成**: 为每次发布生成软件物料清单 (Software Bill of Materials)
- [ ] **第三方模型审查**: 评估所使用开源模型的来源可信度、许可证合规性和已知漏洞

---

## Checklist ❾: 基础设施与部署安全

### 9.1 容器安全

- [ ] **非 root 运行**: 容器内应用以非 root 用户运行
  ```dockerfile
  RUN useradd -m -u 1000 appuser && chown -R appuser /app
  USER appuser
  ```
- [ ] **只读文件系统**: 尽可能使用只读根文件系统 (`readOnlyRootFilesystem: true`)
- [ ] **资源限制**: 设置 CPU/内存的 requests 和 limits
- [ ] **Seccomp/AppArmor**: 为容器配置安全配置文件
- [ ] **特权模式**: 禁止容器以特权模式运行 (`privileged: false`)
- [ ] **Capabilities 裁剪**: 删除所有不必要的 Linux Capabilities

### 9.2 网络安全

- [ ] **最小端口暴露**: 仅暴露必要的服务端口，管理端口仅对内部开放
- [ ] **网络策略**: K8s 环境中配置 NetworkPolicy 限制 Pod 间通信
- [ ] **WAF 接入**: 生产环境前端接入 Web 应用防火墙
- [ ] **DDoS 防护**: 配置 CDN / Anti-DDoS 服务

### 9.3 密钥管理

- [ ] **集中式密钥管理**: 使用 HashiCorp Vault / AWS Secrets Manager / K8s Secrets 管理密钥
- [ ] **密钥注入**: 通过环境变量或挂载卷注入，禁止在镜像中嵌入密钥
- [ ] **`.env` 文件防护**: `.env` 文件加入 `.gitignore` 和 `.dockerignore`
- [ ] **密钥轮换**: 建立定期密钥轮换机制，紧急泄露时可立即吊销

### 9.4 CI/CD 安全

- [ ] **CI/CD 变量安全**: CI/CD 中的密钥变量使用 Masked/Protected 模式
- [ ] **制品签名**: 对构建产物进行数字签名验证
- [ ] **分支保护**: 主分支开启 PR Review + Status Check 强制要求
- [ ] **部署审批**: 生产环境部署需要人工审批
- [ ] **灰度发布**: 新版本先进行金丝雀/灰度发布，观察无异常后再全量上线

---

## Checklist ❿: 合规与安全治理

- [ ] **数据合规**: 确认项目符合适用的数据保护法规（如 GDPR, PIPL, CCPA）
- [ ] **隐私政策**: 项目有完整的隐私政策和用户协议，明确说明数据收集和使用方式
- [ ] **安全测试**:
  - [ ] SAST: 集成静态应用安全测试到 CI 流程 (如 Bandit, Semgrep, CodeQL)
  - [ ] DAST: 对预发布环境执行动态应用安全测试 (如 OWASP ZAP)
  - [ ] 依赖扫描已集成 (见 Checklist ❽)
- [ ] **渗透测试**: 上线前完成至少一轮渗透测试，修复高危及以上所有漏洞
- [ ] **安全应急响应计划**:
  - [ ] 定义安全事件的分类和严重级别
  - [ ] 明确各角色的响应职责
  - [ ] 建立事件上报和升级通道
  - [ ] 每年至少进行一次应急演练
- [ ] **定期安全审计**: 建立定期安全审计日程（建议每季度一次轻量审查，每年一次全面审计）

---

## Deliverables

审查完成后，生成以下交付物：

### **SECURITY_REVIEW_REPORT.md**

包含以下章节的结构化安全审查报告：

```
# AI Agent 安全审查报告

## 1. 项目概述
- 项目名称、版本、审查日期
- 审查范围（覆盖的安全域）
- 审查人员和参与方

## 2. 总体安全评分
- 综合评分（百分制）及各域评分
- 安全态势概括

## 3. 风险汇总
| ID | 安全域 | 风险级别 | 问题描述 | 影响 | 修复建议 | 状态 |
|----|--------|---------|---------|------|---------|------|

## 4. 逐域审查详情
（每个 Checklist 逐项检查结果：✅ 已通过 / ❌ 未通过 / ⚠️ 部分通过 / N/A 不适用）

## 5. 优先修复建议
按紧急程度排序（Critical → High → Medium → Low）

## 6. 附录
- 检查清单完整对照表
- 配置示例参考
- 工具和命令速查
```

---

## Workflow

### Step 1: 项目信息收集
- 了解项目架构、技术栈、部署方式
- 确定审查覆盖范围（全部 10 个域或按需裁剪）
- 获取必要的配置文件和部署文档访问权限

### Step 2: 清单逐域审查
- 按优先级依次审查（建议从 ❶ → ❿ 顺序）
- 每个 Checklist 项标注状态：✅ 已通过 / ❌ 未通过 / ⚠️ 部分通过 / N/A 不适用
- 对 ❌ 和 ⚠️ 项记录详细发现和风险级别

### Step 3: 风险定级与汇总
- 按照标准为每个发现评定风险级别：
  - **Critical**: 可直接导致系统被完全控制、数据大规模泄露
  - **High**: 可导致重要数据泄露或服务中断
  - **Medium**: 可被利用但影响有限
  - **Low**: 最佳实践偏离，暂无直接利用路径

### Step 4: 生成审查报告
- 按 Deliverables 章节的模板组织内容
- 为每个未通过项提供具体的修复方案和验证方法
- 按风险级别排序优先修复建议

### Step 5: 报告交付与跟进
- 向项目团队交付审查报告
- 沟通优先修复项
- 设定复查时间节点

---

## Quick Start

```bash
# 1. 检查 Ollama 服务绑定地址
curl http://127.0.0.1:11434/api/tags  # 应能访问
curl http://<公网IP>:11434/api/tags    # 应无法访问

# 2. 检查 RAGFlow 默认端口暴露
nmap -p 9380,9200,9000 <服务器IP>

# 3. 依赖漏洞扫描
pip-audit                    # Python
npm audit                    # Node.js
trivy image <image:tag>      # 容器镜像

# 4. 检查 .env 文件是否被提交
git log --all --full-history -- .env

# 5. 检查 Docker 容器权限
docker inspect <container> | jq '.[].HostConfig.Privileged'
docker inspect <container> | jq '.[].Config.User'
```

---

## Best Practices

1. **安全左移**: 安全审查不应等到上线前夕才进行，应在项目启动阶段就建立安全检查基线
2. **自动化优先**: 将可自动化的检查项（依赖扫描、密钥检测、配置审计）集成到 CI/CD 管道中
3. **分层防御**: 不依赖单一安全措施，构建从网络层、应用层、数据层到业务层的纵深防御体系
4. **持续监控**: 上线后持续运行安全监控，安全问题不是一次审查就一劳永逸
5. **最小暴露面**: 每一个端口、每个 API、每个服务账号都应确认其必要性，不必要的一律关闭
6. **默认拒绝**: 防火墙、IAM、RBAC 等访问控制策略应遵循"默认拒绝，显式允许"原则
7. **定期复盘**: 每个安全事件发生后进行复盘，更新检查清单和防护措施

---

## References

| 标准/指南 | 说明 |
|-----------|------|
| [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) | LLM 应用 OWASP 十大安全风险 |
| [OWASP API Security Top 10](https://owasp.org/API-Security/) | API 安全十大风险 |
| [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker) | Docker 安全配置基线 |
| [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes) | Kubernetes 安全配置基线 |
| [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) | NIST AI 风险管理框架 |
| [Google SAIF](https://saif.google/) | Google 安全 AI 框架 |
| [MITRE ATLAS](https://atlas.mitre.org/) | AI 系统对抗威胁全景 |

---

## Security Review Checklist Quick Reference

### Risk Level Definitions

| Level | Symbol | Definition |
|-------|--------|------------|
| Critical | 🔴 | 可导致系统完全被控、大规模数据泄露、服务不可用 |
| High | 🟠 | 可导致重要数据泄露、权限提升、服务降级 |
| Medium | 🟡 | 可能被利用但有前置条件，影响范围有限 |
| Low | 🟢 | 安全最佳实践偏离，暂无明确利用路径 |
| Info | 🔵 | 建议性优化，不构成安全风险 |

### Quick Assessment Score

| 分数 | 评级 | 建议 |
|------|------|------|
| 90-100 | A - 优秀 | 可以上线部署 |
| 80-89 | B - 良好 | 可以上线，但 High 级别问题需在首次迭代中修复 |
| 70-79 | C - 一般 | 修复所有 Critical 和 High 问题后方可上线 |
| 60-69 | D - 较差 | 存在严重安全风险，不建议上线 |
| < 60 | F - 危险 | 必须全面整改后重新审查 |
