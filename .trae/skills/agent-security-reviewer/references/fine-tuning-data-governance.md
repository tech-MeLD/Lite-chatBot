# 微调数据治理最佳实践

指导 Agent 项目建立从反馈收集到模型迭代的安全数据闭环。

---

## 1. 数据闭环全景

```
┌─────────────────────────────────────────────────────────────────┐
│                       微调数据闭环                               │
│                                                                  │
│  生产环境                   数据平台                 训练平台     │
│  ┌──────────┐    ┌─────────────────────┐    ┌──────────────┐    │
│  │  用户反馈  │───▶│ 反馈收集 & 脱敏      │    │              │    │
│  │  点赞/踩   │    │                       │    │              │    │
│  │  会话评分  │    │         ▼             │    │              │    │
│  └──────────┘    │  自动标注 & 初筛       │    │              │    │
│                    │                       │    │              │    │
│  ┌──────────┐    │         ▼             │    │  模型微调     │    │
│  │  对话日志  │───▶│  人工复核 (HITL)      │───▶│  (SFT/RLHF)  │    │
│  │  (脱敏后)  │    │                       │    │              │    │
│  └──────────┘    │         ▼             │    │              │    │
│                    │  数据集构建 & 版本化   │    │              │    │
│  ┌──────────┐    │  (train/val/test)     │    │              │    │
│  │  评测指标  │◀───│                       │◀───│              │    │
│  │  效果报告  │    └─────────────────────┘    └──────────────┘    │
│  └──────────┘                                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 反馈收集设计

### 2.1 UI 反馈组件规范

```typescript
interface FeedbackData {
    sessionId: string;
    messageId: string;
    rating: 1 | 2 | 3 | 4 | 5;           // 会话评分
    thumbsUp: boolean | null;              // 点赞/踩
    category?: 'helpful' | 'inaccurate' | 'harmful' | 'irrelevant' | 'other';
    comment?: string;                      // 文字反馈 (需脱敏后传输)
    timestamp: number;
    // 注意：不收集任何 PII!
}
```

### 2.2 反馈防滥用机制

```python
class FeedbackRateLimiter:
    """防止恶意刷反馈数据"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.window_seconds = 60
        self.max_requests = 10

    async def is_allowed(self, user_id: str, session_id: str) -> bool:
        key = f"feedback:rate:{user_id}:{session_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, self.window_seconds)
        return current <= self.max_requests
```

---

## 3. 数据筛选与清洗

### 3.1 数据质量评分规则

```python
def score_conversation_quality(conversation: dict) -> int:
    """
    评分维度：完整性、准确性、相关性、安全性、流畅性
    每项 0-2 分，总分 10 分为满分
    """
    score = 0

    # 1. 完整性 (0-2): 回答是否完整解决问题
    if conversation.get('resolved', False):
        score += 2
    elif len(conversation.get('answer', '')) > 50:
        score += 1

    # 2. 准确性 (0-2): 事实是否经校验
    if conversation.get('fact_verified', False):
        score += 2

    # 3. 相关性 (0-2): 回答是否围绕问题
    if conversation.get('relevance_score', 0) > 0.8:
        score += 2
    elif conversation.get('relevance_score', 0) > 0.5:
        score += 1

    # 4. 安全性 (0-2): 无有害或违规内容
    if conversation.get('safety_passed', True):
        score += 2

    # 5. 流畅性 (0-2): 语言表达自然
    if conversation.get('fluency_score', 0) > 0.8:
        score += 2

    return score

def select_high_quality(conversations: list, threshold=8) -> list:
    """筛选高质量对话（≥8 分）"""
    return [c for c in conversations if score_conversation_quality(c) >= threshold]
```

### 3.2 数据去重与去噪

```python
from datasketch import MinHash, MinHashLSH

class DeduplicationPipeline:
    """对话数据去重"""

    def __init__(self, similarity_threshold=0.85):
        self.lsh = MinHashLSH(threshold=similarity_threshold)
        self.threshold = similarity_threshold

    def minhash_signature(self, text: str, num_perm=128) -> MinHash:
        m = MinHash(num_perm=num_perm)
        for shingle in self._ngrams(text, n=3):
            m.update(shingle.encode('utf8'))
        return m

    def is_duplicate(self, text: str, text_id: str) -> bool:
        minhash = self.minhash_signature(text)
        results = self.lsh.query(minhash)
        if results:
            return True
        self.lsh.insert(text_id, minhash)
        return False

    @staticmethod
    def _ngrams(text: str, n=3):
        tokens = text.split()
        return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]
```

---

## 4. 人工校验 (Human-in-the-Loop)

### 4.1 标注工作流

```
  自动标注 ────▶ 置信度高 (>0.9) ────▶ 直接入高质量数据集
       │
       ▼
  置信度中 (0.5-0.9) ────▶ 人工审核队列
       │
       ├── 审核通过 ────▶ 入高质量数据集
       └── 审核不通过 ──▶ 入待修正队列
       │
       ▼
  置信度低 (<0.5) ────▶ 人工标注队列 ────▶ 多人标注 ────▶ 仲裁
```

### 4.2 标注质量度量

```python
from sklearn.metrics import cohen_kappa_score

def calculate_iaa(annotations_a: list, annotations_b: list) -> float:
    """计算标注者间一致性 (Inter-Annotator Agreement)"""
    kappa = cohen_kappa_score(annotations_a, annotations_b)

    if kappa < 0.4:
        level = "差 — 需要重新设计标注指南"
    elif kappa < 0.6:
        level = "一般 — 需要更多培训和校准"
    elif kappa < 0.8:
        level = "良好 — 可接受的一致性"
    else:
        level = "优秀 — 高度一致"

    return kappa  # 目标: ≥ 0.6
```

### 4.3 抽样策略

| 回答类型 | 审核比例 | 原因 |
|---------|---------|------|
| 安全/合规相关 | 100% | 零容忍，直接涉及安全 |
| 医疗/健康建议 | 100% | 涉及人身安全，高度敏感 |
| 金融/法律建议 | 100% | 涉及重大利益决策 |
| 技术/产品咨询 | 10-20% | 常规业务 |
| 一般闲聊 | 5% | 低风险 |

---

## 5. 隐私保护

### 5.1 差分隐私训练配置

```python
# 使用 Opacus 进行差分隐私微调
from opacus import PrivacyEngine

privacy_engine = PrivacyEngine()
model, optimizer, data_loader = privacy_engine.make_private(
    module=model,
    optimizer=optimizer,
    data_loader=data_loader,
    noise_multiplier=1.1,       # 噪声乘数
    max_grad_norm=1.0,          # 梯度裁剪阈值
)

# ε 值建议:
# ε < 1: 强隐私保护（推荐处理用户数据时使用）
# 1 ≤ ε < 10: 中等保护
# ε ≥ 10: 弱保护（仅内部测试数据可使用）
```

### 5.2 数据脱敏清单

在微调数据集中，必须移除或替换以下信息：

- [ ] 姓名、身份证号、护照号
- [ ] 手机号、座机号、传真号
- [ ] 邮箱地址
- [ ] 家庭地址、工作地址
- [ ] 银行卡号、信用卡号
- [ ] IP 地址、MAC 地址
- [ ] 车牌号
- [ ] URL 中的 Token 和 Session ID
- [ ] 公司内部机密信息
- [ ] API Key、密码凭证

---

## 6. 数据集版本管理

```bash
# 数据集版本管理目录结构
datasets/
├── v1.0.0/
│   ├── train.jsonl         # 训练集
│   ├── val.jsonl           # 验证集
│   ├── test.jsonl          # 测试集
│   ├── dataset_card.md     # 数据集说明
│   └── checksums.sha256    # 完整性校验
├── v1.1.0/
│   └── ...
└── CHANGELOG.md            # 变更记录

# 数据集卡片 template
# dataset_card.md
---
version: 1.1.0
date: 2026-05-07
source: 生产环境反馈 + 人工标注
size: 15,230 samples
language: zh-CN
license: Internal Use Only
privacy: 已脱敏，通过差分隐私检查
annotators: 5 人标注 + 1 人仲裁
kappa: 0.72
quality_score: 8.5/10
---
```
