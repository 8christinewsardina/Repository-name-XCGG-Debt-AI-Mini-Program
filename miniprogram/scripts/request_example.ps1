# PowerShell 示例：向后端提交异步分析任务并轮询结果
# 用法：在 PowerShell 中运行 .\request_example.ps1

$baseUrl = 'https://api.example.com'
$startUrl = "$baseUrl/api/v1/reports/start"

$payload = @{
    assets = 100000
    liabilities = 20000
    income = 10000
    expenses = 5000
} | ConvertTo-Json

Write-Host "提交任务到 $startUrl"
try {
    $resp = Invoke-RestMethod -Uri $startUrl -Method Post -Body $payload -ContentType 'application/json'
} catch {
    Write-Error "请求失败: $_"
    exit 1
}

if (-not $resp.job_id) {
    Write-Error "未收到 job_id: $($resp | ConvertTo-Json -Depth 5)"
    exit 1
}

$jobId = $resp.job_id
Write-Host "任务已提交，job_id=$jobId"

$pollUrl = "$baseUrl/api/v1/reports/$jobId"
for ($i=0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2
    try {
        $job = Invoke-RestMethod -Uri $pollUrl -Method Get
    } catch {
        Write-Warning "轮询失败，重试： $_"
        continue
    }

    Write-Host "状态: $($job.status)"
    if ($job.status -eq 'done') {
        Write-Host "结果:"
        $job.result | ConvertTo-Json -Depth 5 | Write-Host
        break
    } elseif ($job.status -eq 'error') {
        Write-Error "任务出错: $($job | ConvertTo-Json -Depth 5)"
        break
    }
}

if ($i -ge 60) { Write-Warning "超过轮询上限仍未完成。" }
