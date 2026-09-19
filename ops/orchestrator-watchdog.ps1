# orchestrator-watchdog.ps1 - keeps the unified publishing loop alive.
# Since 16.09.2026 the loop is publisher.py (python). If dead, spawns it hidden.
# Idempotent via pid lock. Run every 5 minutes by a scheduled task.
param(
    [int]$StaleMinutes = 12
)
$ErrorActionPreference = 'Continue'
$base   = 'F:\Pill\tmp\opencode'
$repo   = Join-Path $base 'sonic-repo'
$state  = Join-Path $repo 'state'
$hb     = Join-Path $state 'heartbeat.txt'
$pidLock = Join-Path $state 'orchestrator.pid'
$publisher = Join-Path $repo 'publisher.py'

function Get-Alive-Pid {
    if (-not (Test-Path $pidLock)) { return $null }
    $ps = 0
    if (-not [int]::TryParse([System.IO.File]::ReadAllText($pidLock).Trim(), [ref]$ps)) { return $null }
    try {
        $p = Get-Process -Id $ps -ErrorAction Stop
        if ($p.ProcessName -like 'python*') { return $ps }
    } catch { }
    return $null
}

$alive = Get-Alive-Pid
if ($alive) {
    Write-Output ("RUNNING pid=" + $alive)
    exit 0
}

# no live process - check heartbeat age as extra signal (log only)
$age = 99999
if (Test-Path $hb) {
    try { $age = [math]::Round(((Get-Date) - [datetime]::Parse([System.IO.File]::ReadAllText($hb).Trim())).TotalMinutes, 1) } catch { }
}
if ($age -lt $StaleMinutes) {
    # heartbeat is fresh but we lost the pid reference - do not spawn a twin
    Write-Output ("FRESH_NO_PID age=" + $age)
    exit 0
}

$pi = Start-Process -FilePath 'C:\Python314\python.exe' -ArgumentList @($publisher, '--loop') -PassThru -WindowStyle Hidden
[System.IO.File]::WriteAllText($pidLock, $pi.Id.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("SPAWNED pid=" + $pi.Id + " age=" + $age)