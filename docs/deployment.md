# 部署指南

## 开发环境

### 1. 环境要求

- Docker Desktop（Windows / macOS / Linux）
- Python 3.12（本地开发/测试用）

### 2. 配置

```bash
cd backend
cp .env.example .env
# 编辑 .env，至少修改 SECRET_KEY
```

> 国内网络需配置 Docker 镜像加速：Docker Desktop → Settings → Docker Engine → 添加 `registry-mirrors: ["https://docker.1ms.run"]`

### 3. 启动

```bash
cd backend
docker compose up -d
```

### 4. 拉取模型

```bash
# 对话模型（首次必须）
docker exec -it backend-ollama-1 ollama pull qwen2.5:1.5b

# Embedding 模型（长期记忆功能需要）
docker exec -it backend-ollama-1 ollama pull bge-m3
```

### 5. 验证

```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

### 6. 开发模式特性

- `RAG_MODE=mock` — 使用内置 Mock 知识库，无需启动 RAGFlow
- `WECHAT_MOCK_ENABLED=true` — 任意 `code` 字符串即可登录

---

## 生产环境

### 1. 修改环境变量

编辑 `backend/.env`：

```env
APP_ENV=production
SECRET_KEY=<随机强密钥，至少32位>
JWT_EXPIRE_MINUTES=1440

RAG_MODE=ragflow
RAGFLOW_API_KEY=<RAGFlow API KEY>

WECHAT_MOCK_ENABLED=false
WECHAT_APP_ID=<微信 AppID>
WECHAT_APP_SECRET=<微信 AppSecret>
```

### 2. 启用 RAGFlow

取消 `docker-compose.yml` 中 RAGFlow 服务的注释：

```yaml
  ragflow:
    image: infiniflow/ragflow:latest
    ports:
      - "127.0.0.1:9380:80"
    volumes:
      - ragflow_data:/ragflow
    environment:
      - TZ=Asia/Shanghai
```

### 3. 网络隔离

移除以下服务的公开端口映射（仅容器内网访问）：

```yaml
# 删除或限制为 localhost
  postgres:
    ports:
      - "127.0.0.1:5432:5432"

  ollama:
    # 生产环境完全移除 ports，仅容器内网访问
    environment:
      - OLLAMA_HOST=127.0.0.1
```

### 4. HTTPS 反向代理

使用 Nginx 作为反向代理并配置 HTTPS：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 120s;
    }
}
```

### 5. 启动

```bash
docker compose up -d
```

---

## 阿里云 ECS 部署

### 1. 安全组配置

| 端口 | 方向 | 来源 | 说明 |
|------|------|------|------|
| 22 | 入 | 管理 IP | SSH 管理 |
| 443 | 入 | 0.0.0.0/0 | HTTPS |
| 80 | 入 | 0.0.0.0/0 | HTTP（重定向到 HTTPS） |

### 2. 服务器初始化

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | bash
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 拉取项目
git clone <repo-url> /opt/customer-service
cd /opt/customer-service/backend

# 配置环境变量
cp .env.example .env
vim .env  # 修改密钥和密码
```

### 3. 部署

```bash
docker compose up -d
docker exec -it backend-ollama-1 ollama pull qwen2.5:1.5b
docker exec -it backend-ollama-1 ollama pull bge-m3
```

### 4. 自动重启

Docker Compose 服务已配置健康检查。添加 systemd 服务确保开机自启：

```ini
# /etc/systemd/system/customer-service.service
[Unit]
Description=Customer Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/customer-service/backend
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable customer-service
```

---

## 安全清单

部署前必须确认：

- [ ] `SECRET_KEY` 已修改为随机强密钥
- [ ] 数据库密码已修改为非默认值
- [ ] Ollama 未暴露公网端口
- [ ] RAGFlow 默认管理员密码已修改
- [ ] 生产环境启用 LiteLLM API KEY 网关
- [ ] HTTPS 已配置
- [ ] 防火墙仅开放 443 端口
- [ ] 定期备份 PostgreSQL 数据
