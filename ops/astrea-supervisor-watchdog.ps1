# astrea-supervisor-watchdog.ps1 - keeps ASTRAEA science supervisor alive.
# Runs via Task Scheduler (PT1M) through a VBS wrapper (fixed flashing windows,
# pattern 8.9): wscript.exe -> this script -> hidden python supervisor.py.
# Does NOT touch the live canary trader: supervisor is ADOPT-ONLY for the
# astrea_trader slot, so it re-adopts a running live instance on start.
# IMPORTANT: OPENBLAS_NUM_THREADS=1 BEFORE any python (memory safety).
$logFile  = 'F:\Pill\tmp\opencode\sonic-repo\logs\astrea-supervisor-watchdog.log'
$logDir   = Split-Path $logFile -Parent
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

# --- live supervisor? ---
$lock   = 'E:\ASTRAEA_V10\science\supervisor.lock'
$alive  = $false
if (Test-Path $lock) {
    $pid2 = (Get-Content $lock -Raw -ErrorAction SilentlyContinue).Trim()
    if ($pid2 -and $pid2 -match '^\d+$') {
        $alive = [bool](Get-Process -Id ([int]$pid2) -ErrorAction SilentlyContinue)
    }
}
if (-not $alive) {
    # belt+suspenders: scan cmdline too (lock could be stale but process kicked)
    $running = Get-CimInstance Win32_Process -Filter "Name like 'python%'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'supervisor\.py' }
    if (-not $running) {
        $env:OPENBLAS_NUM_THREADS = '1'
        $proc = Start-Process -FilePath 'C:\Python314\python.exe' `
            -ArgumentList @('E:\ASTRAEA_V10\science\supervisor.py') `
            -WorkingDirectory 'E:\ASTRAEA_V10' `
            -WindowStyle Hidden -PassThru
        Add-Content -Path $logFile -Value ("{0} WATCHDOG supervisor DOWN, started pid={1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $proc.Id) -Encoding UTF8
    } else {
        Add-Content -Path $logFile -Value ("{0} WATCHDOG lock stale but supervisor running (pid={1}), no action" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $running[0].ProcessId) -Encoding UTF8
    }
}