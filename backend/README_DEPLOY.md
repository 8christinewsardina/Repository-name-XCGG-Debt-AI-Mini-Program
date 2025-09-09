部署与 Gemini 说明

1. 环境变量

- GEMINI_ENABLED: 是否启用 Gemini 调用（true/false）。
- GEMINI_API_KEY: Gemini API Key，应存放于 CI secrets 或安全的 KMS 中。
- GEMINI_BASE_URL: Gemini API 基础 URL（默认为占位值）。
- GEMINI_TIMEOUT: HTTP 超时（秒）。

2. CI gating

- 在 GitHub Actions 中，只在 secrets 可用时启用真实 Gemini 相关测试与作业。
- 在 workflow 中使用 step-level 条件检查 `secrets.GEMINI_API_KEY` 或环境变量 `GEMINI_ENABLED`。

3. 本地运行

- 复制 `.env.example` 为 `.env` 并根据需要设置 GEMINI_ENABLED=false 以避免真实调用。
- 运行：

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

4. 审计

- 所有 agent 输出与输入会记录到 `backend/logs/audit.log`（json-lines），请在部署时保证该文件夹可写且合规保留周期。
