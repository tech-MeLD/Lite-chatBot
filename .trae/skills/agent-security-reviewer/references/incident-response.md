# AI Agent 安全应急响应清单

安全事件发生时的快速响应指南，覆盖 AI Agent 特有的安全场景。

---

## 1. 安全事件分类

### Agent 特有事件类型

| 事件代码 | 事件类型 | 严重级别 | 描述 |
|---------|---------|---------|------|
| AI-001 | Prompt Injection 攻击成功 | Critical | 攻击者成功绕过系统指令，控制了 Agent 行为 |
| AI-002 | 模型输出有害内容 | High/Critical | 模型输出涉黄/涉政/涉暴等违规内容 |
| AI-003 | API Key/Token 泄露 | Critical | 模型 API Key 在公开渠道暴露 |
| AI-004 | 知识库数据泄露 | Critical | 未授权用户访问到敏感知识库文档 |
| AI-005 | 模型服务 DDoS | High | 短时间大量请求导致推理服务不可用 |
| AI-006 | 训练数据投毒发现 | Critical | 发现微调数据集中存在恶意注入样本 |
| AI-007 | 用户数据泄露 | Critical | 对话历史、PII 等用户数据外泄 |
| AI-008 | 模型被盗/蒸馏 | High | 发现针对模型的系统性质询行为 |
| AI-009 | 异常 Token 消耗 | Medium | 某个 API Key 的 Token 消耗异常飙升 |
| AI-010 | RAG 检索投毒 | High | 外部文档被恶意修改，影响 RAG 检索结果 |

---

## 2. 应急响应流程

### 第一阶段: 检测与确认 (0-15 min)

```
【检测渠道】
├── 监控告警（Prometheus/Grafana Alert）
├── 用户反馈/投诉
├── 安全扫描报告
├── API 异常日志
└── 第三方安全通告

【确认步骤】
1. 验证告警是否为误报
2. 确定影响范围（哪些服务/用户/数据）
3. 初步定级（Critical/High/Medium/Low）
4. 通知安全响应负责人
```

### 第二阶段: 遏制 (15-60 min)

| 事件类型 | 立即遏制措施 |
|---------|-------------|
| Prompt Injection | 临时下线受影响 Agent；启用输入过滤增强规则 |
| 有害内容输出 | 紧急切换内容安全过滤器为最高严格模式；暂停自由对话模式 |
| API Key 泄露 | 立即吊销泄露 Key；生成新 Key；排查使用该 Key 的记录 |
| 知识库泄露 | 撤销相关 API Key 权限；断开 RAGFlow 外网访问 |
| 模型 DDoS | 启用 AI 网关紧急限流；扩容推理实例 |
| 数据投毒 | 冻结当前训练批次；回滚到上一个安全检查点 |
| 数据泄露 | 断开受影响数据库公网连接；确认泄露数据范围 |

**通用遏制操作清单**：
- [ ] 确认是否隔离受影响服务（若不确定，宁可过度隔离）
- [ ] 留存当前系统状态快照（日志、内存 dump、配置）
- [ ] 通知相关团队（开发、运维、法务、PR）
- [ ] 启动应急通讯渠道（专用 Slack/钉钉频道）

### 第三阶段: 根因分析 (1-4 hours)

```
1. 时间线还原
   - 事件首次发生时间
   - 攻击者/触发者的操作序列
   - 系统各组件在时间线上的状态

2. 攻击路径分析
   - 入口点识别（API/UI/第三方集成）
   - 权限提升路径（如有）
   - 横向移动证据（如有）

3. 影响面评估
   - 受影响用户数
   - 受影响数据量/类型
   - 受影响服务时长
   - 是否涉及合规问题
```

### 第四阶段: 修复与恢复 (4-24 hours)

```
修复优先级: Critical → High → Medium → Low

1. 安全修复
   - 修补漏洞（代码修复、配置修改、规则更新）
   - 增强监控（添加针对性告警规则）
   - 更新安全策略（防火墙规则、访问控制）

2. 服务恢复
   - 验证修复后在预发布环境测试
   - 灰度恢复受影响服务
   - 持续监控 24 小时确认无复发

3. 数据恢复
   - 从安全备份恢复受损数据
   - 通知受影响用户（如需）
```

### 第五阶段: 复盘与改进 (1-7 days)

```
复盘会议议程：
1. 事件时间线回顾
2. 根因确认
3. 响应过程评估（是否及时发现、遏制、修复）
4. 改进措施讨论
   - 技术改进：新增/增强哪些安全措施
   - 流程改进：响应流程哪里可以更快
   - 监控改进：盲区在哪里
5. 更新安全检查清单和应急预案
6. 必要时进行相关团队安全培训
```

---

## 3. 关键联系人模板

```
【安全应急联系人卡】

安全负责人:   [姓名] [手机] [微信]
备份安全负责人: [姓名] [手机] [微信]

运维负责人:   [姓名] [手机]
AI/模型负责人: [姓名] [手机]
法务负责人:   [姓名] [手机]
PR 负责人:    [姓名] [手机]

模型供应商紧急支持:
  - OpenAI:  [联系方式]
  - 其他:    [联系方式]

云服务商支持:
  - [服务商] 紧急热线: [电话]
```

---

## 4. AI Agent 专项应急工具

### 4.1 紧急 API Key 吊销

```bash
# LiteLLM 网关紧急吊销 Key
curl -X POST "https://llm-gateway.internal/key/block" \
  -H "Authorization: Bearer ${MASTER_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"key": "sk-leaked-key"}'

# 确认吊销
curl "https://llm-gateway.internal/key/info?key=sk-leaked-key" \
  -H "Authorization: Bearer ${MASTER_KEY}"
```

### 4.2 紧急内容过滤切换

```bash
# 启用最高严格级别过滤
curl -X POST "https://agent-api.internal/admin/safety-filter" \
  -H "Authorization: Bearer ${ADMIN_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"level": "maximum", "reason": "security_incident_AI-002"}'
```

### 4.3 紧急服务隔离

```bash
# K8s 中将受影响 Pod 从 Service 中移除
kubectl label pods -l app=agent security-status=quarantined
kubectl patch deployment agent-deploy \
  -p '{"spec":{"selector":{"matchLabels":{"app":"agent","security-status":"clean"}}}}'

# Docker 紧急停止特定容器
docker stop $(docker ps -q --filter "label=com.example.service=agent") --time 10
```

### 4.4 日志收集脚本

```bash
#!/bin/bash
# collect-incident-evidence.sh
INCIDENT_ID=$1
OUTPUT_DIR="incident_${INCIDENT_ID}_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

# AI 网关请求日志
kubectl logs -l app=llm-gateway --since=4h > "$OUTPUT_DIR/gateway_logs.txt"

# Agent 应用日志
kubectl logs -l app=agent --since=4h > "$OUTPUT_DIR/agent_logs.txt"

# 数据库审计日志
pg_dump -t audit_log --data-only > "$OUTPUT_DIR/audit_logs.sql"

# 系统资源快照
top -b -n 1 > "$OUTPUT_DIR/system_snapshot.txt"

# 网络连接快照
ss -tulnp > "$OUTPUT_DIR/network_connections.txt"

echo "证据已保存至: $OUTPUT_DIR/"
tar -czf "${OUTPUT_DIR}.tar.gz" "$OUTPUT_DIR"
```

---

## 5. 定期演练计划

| 演练频率 | 演练类型 | 参与方 |
|---------|---------|--------|
| 每季度 | 桌面推演（模拟 AI-001 Prompt Injection 事件）| 安全 + 开发 + 模型团队 |
| 每半年 | 实操演练（模拟 API Key 泄露全流程）| 安全 + 运维 |
| 每半年 | 实操演练（模拟有害内容输出事件）| 安全 + 内容审核 + PR |
| 每年 | 全面红蓝对抗演练 | 全员 |

### 桌面推演模板

```
【演练场景】：Prompt Injection 导致 Agent 执行非授权操作
【发现渠道】：监控告警 - 用户反馈 Agent 返回恶意引导内容
【演练目标】：
  1. 5 分钟内完成事件确认和初步定级
  2. 15 分钟内完成服务遏制
  3. 1 小时内完成根因初步分析
  4. 4 小时内完成修复方案制定

【评估标准】：
  - 响应时间是否达标
  - 信息传递是否准确完整
  - 遏制措施是否有效
  - 是否存在之前未发现的流程盲区
```
