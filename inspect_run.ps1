$hdr=@{ 'User-Agent'='PowerShell' }
$uri = "https://api.github.com/repos/8christinewsardina/Repository-name-XCGG-Debt-AI-Mini-Program/actions/runs/17577234270/jobs"
$jobs = Invoke-RestMethod -Headers $hdr -Uri $uri
foreach ($j in $jobs.jobs) {
    Write-Output "JOB: $($j.name) ($($j.id)) - $($j.status) / $($j.conclusion)"
    foreach ($s in $j.steps) {
        Write-Output "  STEP: $($s.number) - $($s.name) - $($s.status) / $($s.conclusion)"
    }
}
