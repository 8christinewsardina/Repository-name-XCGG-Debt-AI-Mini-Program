# 查询最近一次成功的 CI run 并下载 test-output-3.11/test-output-3.12 artifacts
# 依赖：gh CLI 已安装并已登录（有 repo 权限）
param(
    [string]$Repo = '8christinewsardina/Repository-name-XCGG-Debt-AI-Mini-Program'
)

$now = Get-Date -Format "yyyyMMdd-HHmmss"
$dest = Join-Path -Path (Get-Location) -ChildPath "gh_artifacts_$now"
New-Item -ItemType Directory -Path $dest | Out-Null

Write-Output "Looking up latest runs for $Repo using JSON output (databaseId)..."
# Use gh CLI JSON output to safely parse run ids and conclusions
try {
    $runsJson = gh run list --repo $Repo --json databaseId,conclusion -L 20 | ConvertFrom-Json
} catch {
    Write-Output "Failed to list runs via gh CLI (ensure gh is installed and authenticated).";
    Write-Output $_.Exception.Message
    exit 1
}

if (-not $runsJson -or $runsJson.Count -eq 0) {
    Write-Output "No runs found via gh run list --json. Raw output for debugging:"
    gh run list --repo $Repo -L 20 | Out-Host
    exit 1
}

# Prefer the most recent successful run, otherwise fall back to the first run
$successful = $runsJson | Where-Object { $_.conclusion -eq 'success' }
if ($successful -and $successful.Count -gt 0) {
    $runId = $successful[0].databaseId
} else {
    $runId = $runsJson[0].databaseId
}

Write-Output "Downloading artifacts from run $runId into $dest..."
try {
    gh run download $runId --repo $Repo -D $dest
} catch {
    Write-Output "gh run download failed:"
    Write-Output $_.Exception.Message
    exit 1
}

Write-Output "Done. Artifacts saved under: $dest"
Write-Output "Listing files:"
Get-ChildItem $dest -Recurse | Select-Object FullName,Length | Format-Table -AutoSize

# 读取并打印每个 test-output*.txt 的结尾摘要（最后 200 行）
Get-ChildItem $dest -Recurse -Filter "test-output.txt" | ForEach-Object {
    Write-Output "\n--- Summary for: $($_.FullName) ---"
    Get-Content $_.FullName -Tail 200 | Out-Host
}
