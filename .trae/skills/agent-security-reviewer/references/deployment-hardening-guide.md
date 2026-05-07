# 部署安全加固实操指南

覆盖 Docker、Kubernetes、网络层及密钥管理的具体加固配置。

---

## 1. Docker 安全加固

### 1.1 Dockerfile 安全模板

```dockerfile
# 安全 Dockerfile 模板
FROM python:3.12-slim@sha256:<known-good-digest>

# 安全原则: 非 root 用户，最小权限
RUN groupadd -r -g 1000 appgroup && \
    useradd -r -m -u 1000 -g appgroup appuser

WORKDIR /app

# 先复制依赖文件（利用 Docker cache 分层）
COPY --chown=appuser:appgroup requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY --chown=appuser:appgroup . .

# 切换到非 root 用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "main.py"]
```

### 1.2 docker-compose 安全配置

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    # 安全配置
    read_only: true                          # 只读根文件系统
    tmpfs:
      - /tmp:noexec,nosuid,nodev             # 需要写入的目录用 tmpfs
    security_opt:
      - no-new-privileges:true               # 禁止权限提升
    cap_drop:
      - ALL                                   # 删除所有 capabilities
    cap_add:
      - NET_BIND_SERVICE                      # 仅加回必需的
    # 资源限制
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
    # 网络配置
    networks:
      - internal
    # 环境变量（绝不在此处放密钥值）
    environment:
      - DB_HOST=${DB_HOST}
    secrets:
      - db_password
      - api_key

  # Ollama 服务安全配置
  ollama:
    image: ollama/ollama:0.4.7
    environment:
      - OLLAMA_HOST=127.0.0.1              # 仅绑定内网
      - OLLAMA_NUM_PARALLEL=1               # 限制并发
    cap_drop:
      - ALL
    read_only: true
    networks:
      - internal

networks:
  internal:
    internal: true                           # 内部网络，外部不可达

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt
```

### 1.3 容器镜像扫描

```bash
# Trivy 扫描
trivy image --severity HIGH,CRITICAL myapp:latest

# Docker Scout 扫描
docker scout quickview myapp:latest
docker scout cves myapp:latest

# 仅在无 HIGH/CRITICAL 漏洞时构建
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest
```

---

## 2. Kubernetes 安全加固

### 2.1 Pod Security Context

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-agent-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: agent
      image: myapp:latest
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
      resources:
        limits:
          cpu: "2"
          memory: "2Gi"
        requests:
          cpu: "1"
          memory: "512Mi"
```

### 2.2 Network Policy

```yaml
# 仅允许来自应用 Pod 的请求访问 RAGFlow
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ragflow-access-policy
spec:
  podSelector:
    matchLabels:
      app: ragflow
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: customer-service   # 仅允许客服应用
      ports:
        - protocol: TCP
          port: 9380
```

### 2.3 Secrets 管理

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: agent-secrets
type: Opaque
stringData:                 # 开发环境使用，生产环境建议用 External Secrets Operator
  DATABASE_URL: "postgresql://user:pass@db:5432/mydb"
  OPENAI_API_KEY: "sk-..."
---
# Pod 中挂载 Secret
spec:
  containers:
    - name: app
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: DATABASE_URL
```

---

## 3. 网络层安全

### 3.1 Nginx 反代安全配置

```nginx
server {
    listen 443 ssl http2;
    server_name agent.example.com;

    # TLS 配置
    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # API 速率限制
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/m;

    location /api/ {
        limit_req zone=api_limit burst=10 nodelay;
        proxy_pass http://agent-backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3.2 防火墙规则

```bash
# UFW 规则示例
ufw default deny incoming
ufw default allow outgoing

# 仅开放必要端口
ufw allow 22/tcp              # SSH (限制来源IP更佳)
ufw allow 443/tcp             # HTTPS
ufw allow from 10.0.0.0/8 to any port 8000  # 内网 API

# 确认 Ollama 端口未对外开放
ufw deny 11434/tcp
ufw deny 9380/tcp             # RAGFlow
ufw deny 9200/tcp             # Elasticsearch

ufw enable
```

---

## 4. 密钥管理

### 4.1 环境变量注入（开发环境）

```bash
# .env (绝不提交到 Git!)
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://...
SECRET_KEY=$(openssl rand -hex 32)  # 生成强随机密钥

# .gitignore
.env
*.env
secrets/
credentials.json
```

### 4.2 预提交检测

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

### 4.3 生产环境密钥管理

```bash
# HashiCorp Vault 示例
vault kv put secret/myapp/config \
    OPENAI_API_KEY="sk-xxx" \
    DATABASE_URL="postgresql://..."

# 部署时通过 Vault Agent 注入
```

---

## 5. 安全检查脚本

```bash
#!/bin/bash
# deploy-security-check.sh — 部署前安全检查

echo "=== 部署安全检查 ==="

# 1. 检查关键端口暴露
echo "[1/7] 检查服务绑定地址..."
ss -tlnp | grep -E '11434|9380|9200' && echo "  WARNING: 发现关键端口！" || echo "  PASS"

# 2. 检查 Docker 容器权限
echo "[2/7] 检查 Docker 容器权限..."
docker ps -q | while read cid; do
    privileged=$(docker inspect "$cid" | jq '.[].HostConfig.Privileged')
    user=$(docker inspect "$cid" | jq -r '.[].Config.User')
    if [ "$privileged" = "true" ] || [ "$user" = "" ] || [ "$user" = "root" ]; then
        echo "  WARNING: 容器 $cid (privileged=$privileged, user=$user)"
    fi
done

# 3. 检查 .env 是否被提交
echo "[3/7] 检查敏感文件是否泄露到 Git..."
git log --all --full-history --diff-filter=A -- .env 2>/dev/null && echo "  WARNING: .env 已提交！" || echo "  PASS"

# 4. 检查 TLS 证书
echo "[4/7] 检查 TLS 证书..."
curl -sI https://localhost:443 2>/dev/null | grep -q "HTTP" && echo "  PASS" || echo "  WARNING: HTTPS 未配置"

# 5. 依赖漏洞扫描
echo "[5/7] 依赖漏洞扫描..."
pip-audit 2>/dev/null || echo "  pip-audit 未安装，跳过"

# 6. 镜像漏洞扫描
echo "[6/7] 容器镜像扫描..."
docker images --format '{{.Repository}}:{{.Tag}}' | head -5 | while read img; do
    trivy image --severity HIGH,CRITICAL --quiet "$img" 2>/dev/null || true
done

# 7. 检查防火墙规则
echo "[7/7] 检查防火墙规则..."
ufw status 2>/dev/null || iptables -L -n 2>/dev/null || echo "  无法检测防火墙状态"

echo "=== 检查完毕 ==="
```
