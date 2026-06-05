# AgentOps Demo Agent - Getting Started

这是一个完整的LangChain Agent示例项目，展示了如何集成AgentOps SDK进行全链路监控和评估。

## 📋 项目结构

```
demo-agent/
├── README.md                 # 项目说明
├── requirements.txt          # Python依赖
├── agent.py                  # Agent主逻辑
├── evaluate.py              # 评估脚本
├── config.yaml              # AgentOp疒配置
├── .env.example             # 环境变量示例
└── tests/                   # 测试用例
    ├── test_smoke.py
    └── test_security.py
```

## 🚀 快速开始

### 1. 环境设置

```bash
# 克隆项目
cd examples/
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r demo-agent/requirements.txt

# 复制环境变量
cp demo-agent/.env.example demo-agent/.env
# 编辑 .env 文件设置你的API密钥
```

### 2. 连接AgentOps

```bash
cd demo-agent/

# 注册并连接项目
agent-ops link ./
```

### 3. 运行示例

```bash
# 运行Agent
python agent.py

# 运行评估
python evaluate.py

# 或者使用AgentOps CLI
agent-ops eval run --suite smoke
agent-ops benchmark run --preset cost_efficient
agent-ops security scan
```

## 📊 查看结果

1. 启动AgentOps服务：
   ```bash
   docker compose -f ../infra/docker-compose.yml up
   ```

2. 访问Dashboard：http://localhost:3000

3. 查看指标：
   - **Overview**: 成本和延迟概览
   - **Traces**: 详细的调用链路
   - **Benchmarks**: 模型对比结果
   - **Security**: 安全扫描报告

## 🔧 自定义配置

### 修改Agent逻辑

```python
# agent.py
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType, initialize_agent
from agent_ops.callbacks import AgentOpsCallbackHandler

# 配置AgentOps回调
def create_agent():
    llm = ChatOpenAI(temperature=0)
    tools = []  # 添加你的工具
    
    # 创建AgentOps回调处理器
    client = # 你的AgentOps客户端
    handler = AgentOpsCallbackHandler(client)
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        callbacks=[handler]  # 添加回调
    )
    
    return agent
```

### 创建评估套件

```python
# create your own evaluation.py
eval_cases = [
    {
        "name": "数学计算",
        "input": "计算 2 + 2 等于多少？",
        "expected_output": "4",
        "judge_type": "exact_match"
    },
    {
        "name": "知识问答", 
        "input": "谁是爱因斯坦？",
        "expected_pattern": ".*相对论.*",
        "judge_type": "regex"
    }
]
```

## 🐛 故障排除

### 常见问题

1. **连接失败**
   ```bash
   # 检查环境变量
   echo $AGENT_OPS_API_URL
   echo $AGENT_OPS_API_KEY
   
   # 验证连接
   agent-ops status
   ```

2. **指标不显示**
   - 确认AgentOps服务正在运行
   - 检查项目是否已获得授权
   - 查看日志：`agent-ops logs`

3. **评估错误**
   - 确认评估数据文件格式正确
   - 检查API密钥是否有权限访问模型
   - 查看详细的错误日志

### 获取帮助

1. 查看AgentOps文档：`agent-ops docs`
2. 提交Issue：https://github.com/zgsddzwj/agent_ops/issues
3. 加入Discussions讨论

## 📈 最佳实践

### SDK集成

```python
# 推荐的项目结构
demo_agent/
├── agent/                  # Agent核心逻辑
├── evaluation/           # 评估套件和数据
├── config/               # 环境配置
└── metrics/              # 自定义指标收集
```

### 监控建议

1. **成本优化**
   - 使用benchmark比较不同模型的成本效益
   - 设置成本告警阈值
   - 监控Token使用模式

2. **性能监控**
   - 跟踪P95延迟指标
   - 监控错误率
   - 分析长尾延迟用例

3. **安全评估**
   - 定期运行安全扫描
   - 启用实时安全防护
   - 监控异常行为模式

## 🔄 持续集成

### GitHub Actions配置示例

```yaml
# .github/workflows/agent-ops.yml
name: AgentOps CI

on: [push, pull_request]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install agent-ops-cli
        
    - name: Smoke test
      run: |
        agent-ops eval run --suite smoke
        
    - name: Security scan
      run: |
        agent-ops security scan

    - name: Check quality gate
      run: |
        python check_quality.py
```

### 质量门禁示例

```python
# check_quality.py
import requests
import os

API_URL = os.getenv('AGENT_OPS_API_URL', 'http://localhost:8000')
API_KEY = os.getenv('AGENT_OPS_API_KEY')

def check_quality_gates():
    headers = {'X-API-Key': API_KEY}
    
    # 获取最新评估结果
    resp = requests.get(f"{API_URL}/v1/eval/runs", headers=headers)
    eval_data = resp.json()
    
    # 获取安全扫描结果  
    resp = requests.get(f"{API_URL}/v1/security/scans", headers=headers)
    security_data = resp.json()
    
    # 质量检查
    latest_eval = eval_data[0]
    latest_security = security_data[0]
    
    success_rate = latest_eval.get('metrics', {}).get('success_rate', 0)
    security_score = latest_security.get('metrics', {}).get('pass_rate', 0)
    
    if success_rate < 0.8:
        print(f"❌ 成功率低于阈值: {success_rate:.2%}")
        return False
        
    if security_score < 0.9:
        print(f"❌ 安全评分低于阈值: {security_score:.2%}")
        return False
        
    print("✅ 质量检查通过")
    return True

if __name__ == "__main__":
    import sys
    if check_quality_gates():
        sys.exit(0)
    else:
        sys.exit(1)
```

## 🎯 下一步

1. **深入学习**：查看 [AgentOps官方文档](../../README.md)
2. **加入社区**：在Discussions分享你的用例
3. **贡献代码**：提交改进的示例或新疒评估套件
4. **企业部署**：查看 [运维部署指南](../../docs/deployment.md)

---

这个Dem疒项目展示了AgentOps的核心功能。跟随示例，在你自己的项目中快速上手AI Agent监控和评估！