# Register a Windows Scheduled Task to run the artifact fetch script every 5 minutes
# Usage: run this script in an elevated PowerShell or as the current user (no elevation usually required for creating tasks for current user)

$scriptPath = "$PWD\scripts\fetch_latest_artifacts.ps1"
$taskName = "FetchGitHubArtifacts"
$action = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"$scriptPath\""

Write-Output "Registering scheduled task '$taskName' to run every 5 minutes calling: $action"

# schtasks is more universally available; create or update the task
$schtasksCmd = "schtasks /Create /SC MINUTE /MO 5 /TN \"$taskName\" /TR \"$action\" /F"
Write-Output "Running: $schtasksCmd"
Invoke-Expression $schtasksCmd

Write-Output "If the task was created successfully, use 'schtasks /Query /TN \"$taskName\" /V /FO LIST' to inspect it. To delete: schtasks /Delete /TN \"$taskName\" /F"
