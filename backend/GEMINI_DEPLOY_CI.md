Gemini 在 CI / 部署 环境中的安全注入说明

1) 概览
- 推荐在 CI 与生产环境中使用 Secrets 管理 `GEMINI_API_KEY`。
- 只有当环境变量 `GEMINI_ENABLED` 被设置为 `true` 时，应用才会尝试创建 Gemini 客户端。

2) GitHub Actions 示例
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install deps
        run: python -m pip install -r backend/requirements.txt
      - name: Run tests
        env:
          GEMINI_ENABLED: 'true'
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          cd backend
          python run_report_test_with_gemini.py
```

3) Docker / Production
- 在容器启动时通过环境变量注入 `GEMINI_ENABLED=true` 与 `GEMINI_API_KEY`。
- 推荐使用云提供商的秘密管理服务，例如 AWS Secrets Manager / Azure Key Vault / GCP Secret Manager。

4) 安全提示
- 不要将 API Key 写入代码或提交到仓库。
- 在日志中避免打印完整的 API Key。
- 对模型响应做严格的 schema 校验（CFPAgent 已包含 Pydantic 验证）。
