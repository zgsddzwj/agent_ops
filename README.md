# AgentOps - 智能体运维平台

面向 **LangChain / LangGraph** 的多项目 AgentOps 平台。将任意外部 `ai_project` 注册接入，统一完成评估、可观测性、性能/成本/延迟监控、安全评测与多模型对比。

## 核心能力

| 能力 | 说明 |
|------|------|
| **多项目接入** | `agent-ops init/link` 注册外部项目，Dashboard 按 project 隔离 |
| **评估框架** | 离线 Eval、smoke/regression 套件、精确匹配与行为判定 |
| **可观测性** | LangChain Callback 采集 LLM/Tool/Chain 全链路 Trace |
| **性能监控** | TTFT、E2E 延迟、Token 用量、成本核算（P50/P95） |
| **模型对比** | 同一项目下对比 OpenAI / Qwen / DeepSeek 等模型表现 |
| **安全评测** | 提示词注入、Jailbreak、数据泄露等测试套件 |
| **运行时加固** | SDK `SecurityPipeline`：输入过滤、注入检测、PII 脱敏、限流 |
| **告警** | 成本/延迟/错误率/安全通过率阈值 + Webhook |

## 架构

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

```
agent_ops/
├── packages/
│   ├── agent-ops-sdk/       # instrumentation + SecurityPipeline
│   └── agent-ops-cli/       # init, link, eval, benchmark, security, check
├── backend/                 # FastAPI + SQLAlchemy + Alembic
├── worker/                  # ARQ 异步任务（eval / benchmark / security / 聚合）
├── web/                     # Next.js 14 Dashboard
├── evals/                   # 内置 smoke / regression 数据集
├── security/                # 安全测试用例 + 扫描器
├── benchmarks/              # 模型对比预设（domestic / sota / …）
├── examples/demo-agent/     # 可运行的示例 ai_project
└── infra/                   # Docker Compose + Dockerfile
```

## 环境要求

- Python 3.11+
- Node.js 20+（Dashboard）
- Docker（PostgreSQL + Redis，推荐）
- LangChain / LangGraph 项目（被测 Agent）

## 快速开始

### 1. 安装依赖

```bash
cd agent_ops

# 推荐使用虚拟环境
python3 -m venv .venv
source .venv/bin/activate

pip install -e packages/agent-ops-sdk \
            -e packages/agent-ops-cli \
            -e backend
```

### 2. 启动基础设施

```bash
cp .env.example .env

# 方式 A：Docker Compose（推荐）
cd infra && docker compose up -d postgres redis

# 方式 B：单独启动
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

验证：`curl http://localhost:8000/health`

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

## 测试

```bash
source .venv/bin/activate
pytest tests/ -v
```

## 常见问题

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
