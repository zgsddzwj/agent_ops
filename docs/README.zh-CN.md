# AgentOps - 智能体运维平台 (简体中文)

## 项目简介

AgentOps 是一个为 LangChain/LangGraph 生态打造的一站式智能体运维管理平台，专注于AI Agent项目的管理、评估、监控和安全防护。

### 🎯 核心功能

#### 统一管理
- 支持多项目接入和注册
- 项目级隔离的Dashboard

#### 评估监控
- 离线评估框架（smoke/regression测试）
- 全链路性能监控（延迟、成本、Token使用）
- LangChain回调集成

#### 多模型对比
- 支持OpenAI/Qwen/DeepSeek等主流模型
- 预设模型组合包
- 性能对比矩阵

#### 安全评测
- 提示词注入检测
- Jailbreak攻击防护
- 数据泄露防护

#### 智能告警
- 多维度阈值告警
- Webhook通知机制

### 🔧 安装使用

#### 快速开始
```bash
# 1. 安装依赖
cd agent_ops
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/agent-ops-sdk packages/agent-ops-cli backend

# 2. 启动服务
cd infra && docker compose up -d postgres redis
cd backend && uvicorn app.main:app --reload --port 8000
cd web && npm install && npm run dev
```

#### 接入自定义项目
```bash
# 初始化项目
agent-ops init ./my-agent

# 注册项目
agent-ops link ./my-agent

# 运行评估
texport AGENT_OPS_API_KEY=ao_...  
agent-ops eval run --project ./my-agent --suite smoke
agent-ops security scan --project ./my-agent
agent-ops benchmark run --project ./my-agent --preset domestic
```

### 🏗️ 技术架构

- **SDK**: Python SDK + LangChain Callbacks
- **CLI**: Typer命令行工具
- **后端**: FastAPI + SQLAlchemy
- **前端**: Next.js + TailwindCSS
- **数据库**: PostgreSQL + Redis
- **任务队列**: ARQ异步处理

### 📁 项目结构

```
agent_ops/
├── packages/              # SDK和CLI包
│   ├── agent-ops-sdk/    # Python SDK
│   └── agent-ops-cli/    # 命令行工具
├── backend/              # FastAPI后端服务
├── web/                  # Next.js前端
├── worker/               # ARQ后台任务
├── evals/                # 评估数据集
├── security/             # 安全测试用例
├── benchmarks/           # 性能基准预设
├── examples/             # 示例项目
└── infra/                # 基础设施配置
```

### 📋 API接口

认证方式：`X-API-Key: ao_...`

- `POST /v1/projects` - 创建项目
- `GET /v1/projects` - 项目列表 
- `POST /v1/traces/ingest` - 上报数据
- `GET /v1/metrics/summary` - 指标汇总
- `GET /v1/benchmarks/{id}/compare` - 模型对比结果

### 🖥️ Dashboard功能

- `/` - 概览（成本、延迟、错误率）
- `/traces` - Trace浏览器
- `/evals` - 评估历史和结果
- `/benchmarks` - 模型对比
- `/security` - 安全扫描报告
- `/alerts` - 告警管理

### 🚀 适用场景

- **AI公司/团队**: 统一管理多个AI项目
- **研究团队**: 模型选型和技术评估
- **企业应用**: CI/CD集成和运维监控

### 📚 文档导航

- [快速入门](./quickstart.md)
- [SDK集成指南](./sdk-guide.md)
- [CLI命令手册](./cli-reference.md)
- [API参考文档](./api-reference.md)
- [部署运维指南](./deployment.md)

### 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 📄 开源协议

MIT License - 详见 [LICENSE](../LICENSE) 文件

### 🔗 相关资源

- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [报告Bug](https://github.com/zgsddzwj/agent_ops/issues)
- [功能建议](https://github.com/zgsddzwj/agent_ops/discussions)