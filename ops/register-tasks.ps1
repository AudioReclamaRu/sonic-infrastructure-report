# register-tasks.ps1 - create/update all publisher scheduled tasks.
# Run once after deployment or to re-sync triggers.
# Tasks created:
#   SonicSearchMorning / Evening  - daily web+HN signal scans
#   SonicMonitorDaily             - status dashboard + optional TG digest
#   SonicOrchestratorWatchdog     - 5-min heartbeat check, respawns loop
#   SonicPostOrchestratorLoop     - one-shot launch of the -Loop process
# All tasks run hidden, idempotent (-Force).
param(
    [switch]$SkipOrchestratorLaunch
)
$ErrorActionPreference = 'Stop'
$repo   = 'F:\Pill\tmp\opencode\sonic-repo'
$tools  = Join-Path $repo 'tools'
$ops    = Join-Path $repo 'ops'

function Def-Action([string]$file, [string]$args = '') {
    $a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $file + '"' + $(if ($args) { " $args" } else { '' }))
    return $a
}
function Def-Settings([int]$timeoutMin = 60) {
    if ($timeoutMin -eq 0) { return New-ScheduledTaskSettingsSet -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries }
    return New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes $timeoutMin) -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries
}

# ---- search scans ----
$searchScript = Join-Path $tools 'signal-scan.ps1'

$triggerAM = New-ScheduledTaskTrigger -Daily -At '09:00'
$taskAM = Get-ScheduledTask -TaskName 'SonicSearchMorning' -ErrorAction SilentlyContinue
if ($taskAM) { Unregister-ScheduledTask -TaskName 'SonicSearchMorning' -Confirm:$false }
Register-ScheduledTask -TaskName 'SonicSearchMorning' -Action (Def-Action $searchScript) -Trigger $triggerAM -Settings (Def-Settings 30) -Force | Out-Null
Write-Output 'OK SonicSearchMorning 09:00'

$triggerPM = New-ScheduledTaskTrigger -Daily -At '18:00'
$taskPM = Get-ScheduledTask -TaskName 'SonicSearchEvening' -ErrorAction SilentlyContinue
if ($taskPM) { Unregister-ScheduledTask -TaskName 'SonicSearchEvening' -Confirm:$false }
Register-ScheduledTask -TaskName 'SonicSearchEvening' -Action (Def-Action $searchScript) -Trigger $triggerPM -Settings (Def-Settings 30) -Force | Out-Null
Write-Output 'OK SonicSearchEvening 18:00'

# ---- monitor ----
$monitorScript = Join-Path $tools 'monitor.ps1'
$triggerMon = New-ScheduledTaskTrigger -Daily -At '08:30'
Register-ScheduledTask -TaskName 'SonicMonitorDaily' -Action (Def-Action $monitorScript '-NotifyTg') -Trigger $triggerMon -Settings (Def-Settings 30) -Force | Out-Null
Write-Output 'OK SonicMonitorDaily 08:30'

# ---- orchestrator watchdog (via wscript VBS: Task Scheduler shows console for -WindowStyle Hidden powershell) ----
$watchdogVbs = Join-Path $ops 'orchestrator-watchdog-launch.vbs'
$triggerWd = New-ScheduledTaskTrigger -Daily -At '00:00'
$triggerWd.Repetition = (New-CimInstance -CimClass (Get-CimClass -Namespace 'Root/Microsoft/Windows/TaskScheduler' -ClassName 'MSFT_TaskRepetitionPattern') -Property @{ Interval = 'PT5M'; Duration = 'PT24H'; StopAtDurationEnd = $false } -ClientOnly)
$wdAction = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('"' + $watchdogVbs + '"')
Register-ScheduledTask -TaskName 'SonicOrchestratorWatchdog' -Action $wdAction -Trigger $triggerWd -Settings (Def-Settings 2) -Force | Out-Null
Write-Output 'OK SonicOrchestratorWatchdog every 5m (wscript hidden)'

# ---- orchestrator loop (one-shot to start the long-running hidden process) ----
if (-not $SkipOrchestratorLaunch) {
    # legacy broken task (used -Loop when script had no such param) is superseded
    $legacy = Get-ScheduledTask -TaskName 'SonicPostOrchestrator' -ErrorAction SilentlyContinue
    if ($legacy) { Unregister-ScheduledTask -TaskName 'SonicPostOrchestrator' -Confirm:$false }

    $publisherVbs = Join-Path $ops 'publisher-loop-launch.vbs'
    $at = (Get-Date).AddMinutes(2)
    $triggerOrch = New-ScheduledTaskTrigger -Once -At $at
    $vbsAction = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('"' + $publisherVbs + '"')
    Register-ScheduledTask -TaskName 'SonicPostOrchestratorLoop' -Action $vbsAction -Trigger $triggerOrch -Settings (Def-Settings 0) -Force | Out-Null
    Write-Output ("OK SonicPostOrchestratorLoop launched at " + $at.ToString('HH:mm:ss') + " (python hidden loop via VBS)")
}

# ---- IG token refresh guard (weekly) ----
$igGuardScript = Join-Path $ops 'ig-token-guard.ps1'
$triggerIg = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At '09:00'
Register-ScheduledTask -TaskName 'SonicIgTokenGuard' -Action (Def-Action $igGuardScript) -Trigger $triggerIg -Settings (Def-Settings 10) -Force | Out-Null
Write-Output 'OK SonicIgTokenGuard Monday 09:00'

Write-Output 'ALL_TASKS_REGISTERED'