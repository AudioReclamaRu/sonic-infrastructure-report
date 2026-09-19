# astrea-guard.ps1 - starts the Astrea server in background IF it is not already
# listening on 127.0.0.1:18826. Never duplicates and never opens new browser tabs.
# Intended to run from Task Scheduler (ONLOGON + hourly keepalive).
$ErrorActionPreference = 'Continue'
$port = 18826
$portBusy = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0
if ($portBusy) {
    Write-Output "ASTREA ok (already listening :$port)"
    exit 0
}
$server = 'F:\Pill\tmp\opencode\sonic-repo\tools\astrea-server.ps1'
try {
    Start-Process powershell.exe -ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-ExecutionPolicy','Bypass','-File',$server,'-NoOpen') -WindowStyle Hidden
    Start-Sleep -Seconds 2
    $now = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count -gt 0
    if ($now) { Write-Output "ASTREA started :$port" } else { Write-Output 'ASTREA start failed' }
} catch {
    Write-Output ("ASTREA error: " + $_.Exception.Message)
    exit 1
}