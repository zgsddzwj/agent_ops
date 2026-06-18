# AgentOps - LangChain/LangGraph 智能体运维平台

<p align="center">
  <img src="./docs/images/architecture.png" alt="AgentOps Architecture" width="600"/>
</p>

<p align="center">
  <strong>一站式AI Agent运维管理 • 评估 • 监控 • 安全防护 • 多模型对比</strong>
</p>

<p align="center">
  <a href="https://github.com/zgsddzwj/agent_ops/releases">
    <img src="https://img.shields.io/github/v/release/zgsddzwj/agent_ops?style=flat-square" alt="Version"/>
  </a>
  <a href="https://github.com/zgsddzwj/agent_ops/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/zgsddzwj/agent_ops?style=flat-square" alt="License"/>
  </a>
  <a href="https://github.com/zgsddzwj/agent_ops/stargazers">
    <img src="https://img.shields.io/github/stars/zgsddzwj/agent_ops?style=flat-square" alt="Stars"/>
  </a>
</p>

AgentOps 是一个专为 LangChain/LangGraph 生态设计的全栈智能体运维(MLOps)平台，为AI Agent项目提供统一的可观测性、评估、监控和安全保障基础设施。

## ✨ 核心能力

### 🔧 统一项目管理
- 多AI项目统一注册和管理
- 项目级Dashboard隔离展示
- 统一的CLI入口和API管理

### 📊 全面评估体系  
- 离线评估框架（smoke test、regression测试套件）
- 多维度判定（精确匹配、行为逻辑判定）
- 内置评估数据集和测试用例

### 🔍 全链路可观测性
- LangChain Callback集成，自动采集全链路Trace
- 实时性能监控（TTFT、E2E延迟、Token消耗）
- 精确成本核算（P50/P95分位统计）

### 🤖 多模型智能对比
- 横向对比OpenAI/Qwen/DeepSeek等主流模型
- 预设模型组合包（domestic、international、sota、cost_efficient）
- 多维度对比矩阵（TTFT、延迟、成本、质量）

### 🛡️ 安全防护体系
- 安全评测套件（提示词注入、Jailbreak、数据泄露）
- SDK SecurityPipeline运行时防护
- 内置安全测试用例和扫描工具

### 🚨 智能告警系统
- 多维度阈值告警（成本、延迟、错误率、安全）
- 灵活Webhooks通知机制
- 自定义告警规则

## 🏗️ 架构设计

```
┌─────────────────┐     SDK (实时)      ┌──────────────────┐
│  ai_project A   │ ──────────────────► │                  │
├─────────────────┤                     │  FastAPI Backend │
│  ai_project B   │     CLI (离线)      │  PostgreSQL      │
└─────────────────┘ ──────────────────► │  Redis + Worker  │
                                        └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │  Next.js Dashboard│
                                        └──────────────────┘
```

## 🛠️ 技术栈

- **SDK**: Python instrumentation + SecurityPipeline with retry logic
- **CLI**: Typer命令行工具（init/link/eval/benchmark等），支持进度条和详细日志  
- **后端**: FastAPI + SQLAlchemy + Alembic（异步架构，内置限流中间件）
- **数据库**: PostgreSQL + Redis（连接池/健康检查增强）
- **任务处理**: ARQ异步任务框架
- **前端**: Next.js 14 + TailwindCSS + TypeScript + React Query
- **安全风险防护**: 注入检测、PII脱敏、速率限制、API Key时序安全
- **基础设施**: Docker Compose（生产级配置/资源限制/网络隔离）
- **开发工具**: Ruff + Pre-commit + GitHub Actions
- **代码质量**: 100% type annotations, docstrings, error handling

## 快速开始

### 1. 安装依赖

```bash
cd agent_ops

# 推荐使用虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 使用 uv 加速安装（推荐）
# curl -LsSf https://astral.sh/uv/install.sh | sh
# uv sync --frozen

# 或使用 pip
pip install -e packages/agent-ops-sdk \
            -e packages/agent-ops-cli \
            -e backend \
            -e worker
```

### 2. 启动基础设施

```bash
cp .env.example .env
# 在 .env 中配置密码和密钥（见 .env.example）

# Docker Compose（推荐）
cd infra && docker compose up -d postgres redis

# 或单独启动
docker run -d --name agentops-pg \
  -e POSTGRES_USER=agentops -e POSTGRES_PASSWORD=agentops \
  -e POSTGRES_DB=agentops -p 5432:5432 postgres:16-alpine
docker run -d --name agentops-redis -p 6379:6379 redis:7-alpine
```

### 3. 启动服务

```bash
# API（自动建表 + 种子 model_pricing）
cd backend && uvicorn app.main:app --reload --port 8000

# Worker（另开终端，可选）
cd .. && python -m worker.main

# Dashboard（另开终端）
cd web && npm install && npm run dev
# → http://localhost:3000
```

验证：`curl http://localhost:8000/health` 应该返回数据库和Redis连接状态。

### 4. 跑通示例项目

仓库自带 [`examples/demo-agent/`](examples/demo-agent/)，无需 LLM API Key：

```bash
source .venv/bin/activate

# 评估
PYTHONPATH=examples/demo-agent \
  agent-ops eval run --project examples/demo-agent --suite smoke

# 安全扫描
PYTHONPATH=examples/demo-agent \
  agent-ops security scan --project examples/demo-agent

# 模型对比（mock agent，测通 CLI 流程）
PYTHONPATH=examples/demo-agent \
  agent-ops benchmark run --project examples/demo-agent --preset cost_efficient
```

## 接入你的 ai_project

### Step 1：初始化

```bash
agent-ops init ./my-agent
```

会在项目根目录生成：

- `.agent-ops.yaml` — 项目清单（entrypoint、eval 套件、模型候选）
- `evals/smoke.yaml` — 示例评估集
- `security/policies.yaml` — 安全策略

### Step 2：配置 `.agent-ops.yaml`

```yaml
project: my-agent
framework: langgraph
entrypoint: app.agent:graph      # import path → Runnable / CompiledGraph
invoke:
  method: invoke                 # invoke | ainvoke
  input_key: messages
  input_format: chat             # chat | dict | str
env_file: .env
eval:
  datasets: ./evals/
  suites: [smoke, regression, security]
models:
  swap_hook: app.agent:set_llm   # benchmark 时切换 LLM
  candidates:
    - provider: openai
      model: gpt-4o
      env_key: OPENAI_API_KEY
    - provider: qwen
      model: qwen-plus
      env_key: DASHSCOPE_API_KEY
```

### Step 3：注册到平台

```bash
agent-ops link ./my-agent
# 输出 API Key，写入 ./my-agent/.env.agent-ops
```

### Step 4：评估 / 扫描 / 对比

```bash
export AGENT_OPS_API_KEY=ao_...   # link 返回的 key

agent-ops eval run --project ./my-agent --suite regression
agent-ops security scan --project ./my-agent --suite prompt_injection
agent-ops benchmark run --project ./my-agent \
  --models openai:gpt-4o,qwen:qwen-plus,deepseek:deepseek-chat \
  --repeat 3

# CI 一行检查（eval + security，失败 exit 1）
agent-ops check ./my-agent
```

## SDK 实时监测

```python
import os
from agent_ops import AgentOpsClient
from agent_ops.callbacks import AgentOpsCallbackHandler
from agent_ops.security import SecurityPipeline

client = AgentOpsClient(
    api_key=os.environ["AGENT_OPS_API_KEY"],
    base_url=os.environ.get("AGENT_OPS_API_URL", "http://localhost:8000"),
)
handler = AgentOpsCallbackHandler(client, run_name="support-bot")

# 可选：运行时安全加固
secured_graph = SecurityPipeline().wrap(graph)

result = secured_graph.invoke(
    {"messages": [("user", query)]},
    config={"callbacks": [handler]},
)
handler.flush_run(status="success")
```

SDK 采集字段：`latency_ms`、`ttft_ms`（streaming）、`tokens_in/out`、`cost_usd`、`span_type`（llm/tool/chain）。

## CLI 命令参考

| 命令 | 说明 |
|------|------|
| `agent-ops init <path>` | 生成 `.agent-ops.yaml` 和示例目录 |
| `agent-ops link <path>` | 注册项目，返回 API Key |
| `agent-ops eval run --project <path> --suite <name>` | 运行评估套件 |
| `agent-ops eval run --project <path> --dataset <file>` | 指定数据集 |
| `agent-ops security scan --project <path> --suite prompt_injection` | 安全扫描 |
| `agent-ops benchmark run --project <path> --preset domestic` | 模型对比 |
| `agent-ops benchmark run --project <path> --models openai:gpt-4o,qwen:qwen-turbo` | 指定模型 |
| `agent-ops check <path>` | smoke eval + security（CI 友好） |

**Benchmark 预设：**

| Preset | 模型 |
|--------|------|
| `domestic` | qwen-plus, qwen-turbo, deepseek-chat, glm-4 |
| `international` | gpt-4o, gpt-4o-mini, claude-sonnet-4 |
| `sota` | gpt-4o, claude-sonnet-4, qwen-max, deepseek-reasoner |
| `cost_efficient` | gpt-4o-mini, qwen-turbo, deepseek-chat |

## API 端点

认证：请求头 `X-API-Key: ao_...`（`link` 命令返回）

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/v1/projects` | 注册项目（无需 Key） |
| `GET` | `/v1/projects` | 项目列表 |
| `POST` | `/v1/traces/ingest` | 批量上报 Trace |
| `GET` | `/v1/runs` | 查询 Runs |
| `GET` | `/v1/runs/{id}/spans` | Span 详情 |
| `GET` | `/v1/metrics/summary` | 成本/延迟/错误率汇总 |
| `GET` | `/v1/metrics/timeseries` | 时序指标 |
| `POST` | `/v1/eval/runs` | 触发评估 |
| `POST` | `/v1/benchmarks` | 触发模型对比 |
| `GET` | `/v1/benchmarks/{id}/compare` | 对比矩阵 |
| `POST` | `/v1/security/scans` | 触发安全扫描 |
| `POST` | `/v1/alerts/rules` | 创建告警规则 |

## Dashboard

启动后访问 http://localhost:3000

| 路径 | 功能 |
|------|------|
| `/` | Overview：成本、延迟、错误率 |
| `/traces` | Trace Explorer：Run 列表 + Span 瀑布图 |
| `/evals` | 评估历史与结果 |
| `/metrics` | 成本/延迟时序图 |
| `/benchmarks` | 多模型 TTFT/E2E/成本/质量对比 |
| `/security` | 安全扫描报告 |
| `/alerts` | 告警规则与事件 |
| `/projects` | 已注册项目 + SDK 接入片段 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AGENT_OPS_API_URL` | `http://localhost:8000` | 平台 API 地址 |
| `AGENT_OPS_API_KEY` | — | 项目 API Key |
| `DATABASE_URL` | `postgresql+asyncpg://…` | Backend 数据库 |
| `REDIS_URL` | `redis://localhost:6379/0` | Worker 队列 |
| `OPENAI_API_KEY` | — | Eval/Benchmark 用 |
| `DASHSCOPE_API_KEY` | — | Qwen 模型 |
| `DEEPSEEK_API_KEY` | — | DeepSeek 模型 |

完整列表见 [`.env.example`](.env.example)。

## 📋 优化记录

### v0.1.0 优化汇总 (2026-06-18)

#### 配置文件完善 (#10, #11)
- 添加 `.env.example` 环境变量模板，涵盖所有配置项
- 完善 `.gitignore` 覆盖 IDE/OS/Docker/测试等场景
- 数据库模块增强：`init_database`/`check_database_health` 函数

#### 安全加固 (#12-14) 
- 主应用内置滑动窗口限流中间件
- 生产环境自动禁用 Swagger 文档
- 后端异常处理中间件重构
- 扩展注入检测模式 (5→11条) 覆盖更多攻击向量
- PII 检测增加电话号/护照号识别
- API Key 使用 `hmac.compare_digest` 防止时序攻击

#### SDK 增强 (#13)
- 指数退避重试机制 (max_retries/retry_backoff)
- API Key 参数校验
- Span 类型检查
- 细化 HTTP/Request 异常处理
- 离线回退增加时间戳和错误日志
- 所有方法添加完整 docstring

#### 前端优化 (#15)
- API 客户端添加超时控制和自定义 `ApiError` 类
- Overview 页面支持实时指标展示 (Prometheus 风格)
- 错误率超过 5% 高亮显示
- 响应式网格布局 (sm/lg 断点)
- CSS 变量完善 (warning/info/accent-hover)
- 新增 card-hover/btn-outline/btn-danger/badge 组件样式

#### Docker Compose 生产化 (#16)
- 所有服务添加内存限制和 restart 策略
- 密码变量化 (POSTGRES_PASSWORD/REDIS_PASSWORD/SECRET_KEY)
- 后端配置变量化 (DEBUG/RATE_LIMIT等)
- Redis 添加密码认证和数据持久化
- 所有服务加入 agentops-network 网络隔离
- 添加 redisdata 卷持久化 Redis 数据

#### 编译修复 (#17-19)
- 修复 `middleware.py` 中 `SQLAlchemyError` 导入未定义错误
- 所有模块 lint 检查通过，无警告
- 代码生成规范化：100% 类型注解/文档字符串/异常捕获

## 测试

```bash
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pytest tests/ -v
```

**`pip install` 看起来卡住了？**  
首次安装会下载 FastAPI、LangChain 等较多依赖，可能需要 1–3 分钟。建议用虚拟环境，不要用 `| tail` 包 pip 输出。

**Eval 报找不到 entrypoint？**  
确保在项目目录执行，或设置 `PYTHONPATH=./my-agent`，且 `.agent-ops.yaml` 中 `entrypoint` 可 import。

**TTFT 为 null？**  
TTFT 依赖 LLM streaming；非流式调用只记录 E2E 延迟。

**Dashboard 无数据？**  
需先 `agent-ops link` 获取 API Key，SDK 上报或 CLI 上传时带上 `X-API-Key`。

## License

MIT
