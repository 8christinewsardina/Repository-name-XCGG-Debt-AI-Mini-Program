# 查询最近一次成功的 CI run 并下载 test-output-3.11/test-output-3.12 artifacts
# 依赖：gh CLI 已安装并已登录（有 repo 权限）
param(
    [string]$Repo = '8christinewsardina/Repository-name-XCGG-Debt-AI-Mini-Program'
)

$now = Get-Date -Format "yyyyMMdd-HHmmss"
$dest = Join-Path -Path (Get-Location) -ChildPath "gh_artifacts_$now"
New-Item -ItemType Directory -Path $dest | Out-Null

Write-Output "Looking up latest runs for $Repo..."
$runs = gh run list --repo $Repo -L 20 | Select-String "^\S+\s+.+\s+CI\s+master\s+push\s+(\d+)" -AllMatches
if (-not $runs) {
    Write-Output "没有找到匹配的 runs，尝试 gh run list 原始输出..."
    gh run list --repo $Repo -L 10 | Out-Host
    exit 1
}

# 尝试取第一个成功的 run id
$runLines = gh run list --repo $Repo -L 20 | Out-String
$runId = ($runLines -split "\r?\n" | Where-Object { $_ -match "^\S+\s+.+\s+CI\s+master\s+push\s+(\d+)" } | ForEach-Object { ($_ -replace '^\S+\s+.+\s+CI\s+master\s+push\s+','').Trim() })[0]
if (-not $runId) {
    Write-Output "无法解析 run id。原始列表：`n$runLines"
    exit 1
}

Write-Output "Downloading artifacts from run $runId into $dest..."
gh run download $runId --repo $Repo -D $dest

Write-Output "Done. Artifacts saved under: $dest"
Write-Output "Listing files:"
Get-ChildItem $dest -Recurse | Select-Object FullName,Length | Format-Table -AutoSize

# 读取并打印每个 test-output*.txt 的结尾摘要（最后 200 行）
Get-ChildItem $dest -Recurse -Filter "test-output.txt" | ForEach-Object {
    Write-Output "\n--- Summary for: $($_.FullName) ---"
    Get-Content $_.FullName -Tail 200 | Out-Host
}
