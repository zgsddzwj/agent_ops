# AgentOps 使用指南

## 快速开始

### 环境准备

1. **安装依赖**
   ```bash
   # 推荐使用 uv 加速安装
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync --frozen
   ```

2. **启动基础设施**
   ```bash
   # 使用Docker Compose启动
   cd infra && docker compose up -d postgres redis
   ```

### 项目初始化

1. **初始化项目**
   ```bash
   agent-ops init ./my-agent
   ```

2. **注册到平台**
   ```bash
   agent-ops link ./my-agent
   ```

3. **配置API密钥**
   ```bash
   export AGENT_OPS_API_KEY="你的API密钥"
   ```

## 核心功能

### 评估

运行评估套件：
```bash
agent-ops eval run --project ./my-agent --suite smoke
```

### 安全扫描

执行安全扫描：
```bash
agent-ops security scan --project ./my-agent
```

### 模型对比

进行多模型性能对比：
```bash
agent-ops benchmark run --project ./my-agent --preset cost_efficient
```

## 最佳实践

### 性能优化

- 使用连接池配置数据库连接
- 合理设置缓存策略
- 启用gzip压缩

### 安全性建议

- 不要在生产环境中使用默认密钥
- 使用环境变量管理敏感信息
- 定期轮换API密钥

### 监控和告警

- 配置适当的健康检查
- 设置异常告警阈值
- 定期审查安全日志