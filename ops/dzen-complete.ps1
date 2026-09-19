# dzen-complete.ps1 - mark the Telegram<->Dzen channel link as completed.
# Run AFTER the channel owner pasted the pairing code to the Dzen bot in Telegram.
# Writes state/dzen-linked.ok; monitor.ps1 then shows DZEN LINKED.
# Usage: powershell -File dzen-complete.ps1
$ErrorActionPreference = 'Stop'
$state  = 'F:\Pill\tmp\opencode\sonic-repo\state'
$flag   = Join-Path $state 'dzen-linked.ok'
$stamp  = Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'

if (-not (Test-Path $state)) { New-Item -ItemType Directory -Path $state -Force | Out-Null }
[System.IO.File]::WriteAllText($flag, ("linked " + $stamp + "`n"), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("DZEN_LINKED " + $stamp)