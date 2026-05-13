# API 文档

Base URL: `http://localhost:8000/api/v1`

## 认证

所有需要认证的端点需在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

### POST /auth/login

Mock 微信登录，返回 JWT Token。

**请求体**
```json
{
  "code": "任意字符串（开发模式）"
}
```

**响应**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "nickname": "用户0001",
    "avatar_url": null,
    "is_active": true
  }
}
```

### GET /auth/me

获取当前登录用户信息。

**响应**
```json
{
  "id": "uuid",
  "nickname": "用户0001",
  "avatar_url": null,
  "is_active": true
}
```

---

## 对话

### POST /chat/send

SSE 流式对话。响应类型为 `text/event-stream`。

**请求体**
```json
{
  "session_id": "uuid",
  "content": "如何退货？"
}
```

**SSE 事件流**

| 事件类型 | 数据格式 | 触发时机 |
|---------|---------|---------|
| `intent` | `{"intent":"knowledge", "confidence":0.9}` | 意图识别完成 |
| `thinking` | `{"message":"正在生成回复..."}` | AI 开始生成 |
| `error` | `{"message":"系统繁忙..."}` | 异常发生时 |
| `done` | `{"answer":"...", "message_id":"uuid", "needs_human":false}` | 回复完成 |

**示例响应**
```
data: {"type":"intent","data":{"intent":"knowledge","confidence":0.92}}

data: {"type":"thinking","data":{"message":"正在生成回复..."}}

data: {"type":"done","data":{"answer":"根据退货政策，支持7天无理由退货...","message_id":"uuid","needs_human":false}}
```

---

## 会话管理

### GET /sessions

获取当前用户的会话列表。

**查询参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 20 | 每页数量（最大100） |
| offset | int | 0 | 偏移量 |

**响应**
```json
[
  {
    "id": "uuid",
    "title": "退货咨询",
    "status": "active",
    "created_at": "2026-05-07T10:00:00Z",
    "updated_at": "2026-05-07T10:05:00Z"
  }
]
```

### POST /sessions

创建新会话。

**请求体**
```json
{
  "title": "退货咨询"
}
```

**响应** (同 GET /sessions/:id)

### GET /sessions/{session_id}

获取会话详情。

### GET /sessions/{session_id}/messages

获取会话历史消息。

**查询参数**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| limit | int | 50 | 每页数量（最大200） |
| offset | int | 0 | 偏移量 |

**响应**
```json
[
  {
    "id": "uuid",
    "role": "user",
    "content": "如何退货？",
    "intent": "knowledge",
    "created_at": "2026-05-07T10:00:00Z"
  },
  {
    "id": "uuid",
    "role": "assistant",
    "content": "根据退货政策...",
    "intent": null,
    "created_at": "2026-05-07T10:00:05Z"
  }
]
```

### PATCH /sessions/{session_id}

更新会话状态或标题。

**请求体**
```json
{
  "status": "closed",
  "title": "已解决-退货咨询"
}
```

**状态值**: `active` | `paused` | `closed`

### DELETE /sessions/{session_id}

删除会话（级联删除关联的 feedbacks 和 messages）。

**响应**: `204 No Content`

---

## 反馈

### POST /feedback

提交对话反馈。

**请求体**
```json
{
  "message_id": "uuid",
  "rating": 4,
  "is_liked": true,
  "comment": "回答很详细"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| message_id | UUID | 是 | 被评价的消息 ID |
| rating | int | 是 | 评分 1-5 |
| is_liked | bool | 否 | 点赞/踩 |
| comment | string | 否 | 文字反馈 |

### GET /feedback/stats

获取反馈统计数据。

**响应**
```json
{
  "total_feedback": 128,
  "average_rating": 4.2,
  "total_likes": 96
}
```

---

## 健康检查

### GET /health

无需认证。

**响应**
```json
{"status": "ok"}
```
