使用说明：

脚本：scripts/fetch_latest_artifacts.ps1
用途：查询最近的 CI run 并下载 `test-output-3.11`/`test-output-3.12` artifact 到本地带时间戳的目录。
依赖：需要安装并登录 `gh` CLI，且有 repo 读取权限。

使用示例：

PowerShell:

    cd ai_financial_advisor
    .\scripts\fetch_latest_artifacts.ps1

脚本会在当前目录下创建 `gh_artifacts_YYYYMMDD-HHMMSS` 目录并保存 artifacts。
