# ig-token-guard.ps1 - weekly check of the IG page token lifetime.
# If the IG token is missing  -> logs PENDING (nothing to do yet).
# If it expires within 7 days -> runs ig-ensure-token.ps1 -Refresh (extends ~60 days).
# Otherwise                   -> logs OK, does nothing (avoids useless API calls).
# Log: state/ig-refresh.log (ASCII).
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$secrets = 'F:\Pill\tmp\opencode\secrets'
$state   = 'F:\Pill\tmp\opencode\sonic-repo\state'
$tokFile = Join-Path $secrets 'fb_token_ig.txt'
$stFile  = Join-Path $secrets 'ig_state.json'
$logFile = Join-Path $state 'ig-refresh.log'
$okFile  = Join-Path $secrets 'fb_page_token_ig.txt'

function Log([string]$m) {
    [System.IO.File]::AppendAllText($logFile, ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " " + $m + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}

if (-not (Test-Path $tokFile) -or -not (Test-Path $okFile) -or -not (Test-Path $stFile)) {
    Log 'PENDING ig (no IG token yet)'
    Write-Output 'IG_GUARD PENDING'
    exit 0
}

$expires = 0
try {
    $st = Get-Content $stFile -Raw | ConvertFrom-Json
    $expires = [int]$st.expires_at
} catch { $expires = 0 }

if ($expires -le 0) {
    Log 'OK ig (non-expiring token)'
    Write-Output 'IG_GUARD OK non-expiring'
    exit 0
}

$expDt = [DateTimeOffset]::FromUnixTimeSeconds($expires).ToLocalTime()
$daysLeft = [math]::Round(($expDt - (Get-Date)).TotalDays, 1)
if ($daysLeft -gt 7) {
    Log ("OK ig (expires " + $expDt.ToString('dd.MM.yy') + ", days left " + $daysLeft + ")")
    Write-Output ("IG_GUARD OK expires=" + $expDt.ToString('dd.MM.yy'))
    exit 0
}

Log ("REFRESH ig (expires " + $expDt.ToString('dd.MM.yy HH:mm') + ", days left " + $daysLeft + ")")
$out = & powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File 'F:\Pill\tmp\opencode\ig\ig-ensure-token.ps1' -Refresh 2>&1 | Out-String
Log ("REFRESH_RESULT " + ($out.Trim() -replace "`r?`n", ' | '))
Write-Output ("IG_GUARD REFRESH -> " + ($out.Trim() -replace "`r?`n", ' | '))