Gemini 集成说明（示例）
=========================

概述
----
本文件提供将 `GeminiClientHTTP` 注入到 `CFPAgent` 的示例代码与安全注意事项。示例为模板；实际调用时请在私有环境变量中存放 API Key，避免将密钥提交到仓库。

环境变量
---------
- GEMINI_API_KEY: 你的 Gemini API Key
- GEMINI_BASE_URL: API 基础地址（可选，默认在 `model_clients.py` 中提供）

示例：在生产服务器或 CI 中导入密钥

Linux / macOS:
```bash
export GEMINI_API_KEY="sk-..."
export GEMINI_BASE_URL="https://api.gemini.vendor/v1"
```

Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY = "sk-..."
$env:GEMINI_BASE_URL = "https://api.gemini.vendor/v1"
```

注入示例代码
--------------
下面示例演示如何从环境创建客户端并注入 `CFPAgent`。

```python
from app.services.model_clients import create_gemini_client_from_env, GeminiClientHTTP
from app.services.cfp_agent import CFPAgent

# 尝试从环境创建（若未配置则返回 None）
client = create_gemini_client_from_env()

if client is None:
    # 退回到本地模拟客户端（便于开发和测试）
    from app.services.model_clients import DummyModelClientLocal
    client = DummyModelClientLocal()

agent = CFPAgent(model_client=client)
result = agent.analyze(financial_statement)
```

安全与可靠性说明
------------------
- 仅在受信任环境中保存 `GEMINI_API_KEY`（环境变量、云密钥管理服务）。
- 在 CI 中使用 secrets 管理并在运行时注入，不要将密钥写入仓库。
- 对模型响应做超时与重试控制。
- 推荐在 agent 层增加输入/输出 schema 验证，确保模型返回可解析 JSON。

模拟与本地测试
----------------
在开发阶段可使用 `DummyModelClientLocal` 或 `DummyModelClient` 进行离线测试，避免外网调用。
