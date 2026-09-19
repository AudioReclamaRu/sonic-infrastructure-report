# watchman.ps1 – autonomous publisher (Редакция). Source of truth: feed/items.csv.
# Runs on schedule (hidden). Publishes due posts per platform with daily caps.
# Idempotent by guid. Logs to state/, heartbeat for dead-man's switch.
param(
    [string]$FeedsFile = 'F:\Pill\tmp\opencode\sonic-repo\feed\items.csv',
    [int]$TgCap = 2,
    [int]$FbCap = 1
)
$ErrorActionPreference = 'Continue'
$repo   = 'F:\Pill\tmp\opencode\sonic-repo'
$state  = Join-Path $repo 'state'
$tgDir  = 'F:\Pill\tmp\opencode\tg'
$tools  = Join-Path $repo 'tools'
$now    = Get-Date
$stamp  = $now.ToString('yyyy-MM-ddTHH:mm:ssK')

# --- parse "DOW, DD Mon YYYY HH:MM:SS GMT" (RFC1123, invariant) ---
function Parse-FeedDate([string]$s) {
    try { return [datetime]::ParseExact($s.Trim(), 'r', [System.Globalization.CultureInfo]::InvariantCulture) }
    catch { return $null }
}

if (-not (Test-Path $state)) { New-Item -ItemType Directory -Path $state -Force | Out-Null }
$log = Join-Path $state 'watchman.log'
function WLog([string]$msg) {
    Add-Content -Path $log -Value ("{0} {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $msg) -Encoding UTF8
}

# --- load feed ---
$rows = @{}
foreach ($row in [System.IO.File]::ReadAllLines($FeedsFile)) {
    if (-not $row -or $row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    $rows[$p[4]] = $p
}

# --- published sets (seed once from existing trackers, then state logs are truth) ---
function Get-Tracked([string]$tracker) {
    $set = @{}
    if (Test-Path $tracker) {
        foreach ($ln in [System.IO.File]::ReadAllLines($tracker)) {
            if ($ln -and -not $ln.StartsWith('#')) { $set[$ln.Trim()] = $true }
        }
    }
    (Join-Path $state (Split-Path $tracker -Leaf)) | Out-Null
    return $set
}

function Get-PublishedFromState([string]$platform) {
    $set = @{}
    $f = Join-Path $state ($platform + '.log')
    if (Test-Path $f) {
        foreach ($ln in [System.IO.File]::ReadAllLines($f)) {
            if ($ln -match 'pin fb (\S+)') { }
            if ($ln -match 'published (\S+)') { $set[$Matches[1]] = $true }
        }
    }
    return $set
}

function Count-PublishedToday([string]$platform) {
    $n = 0
    $f = Join-Path $state ($platform + '.log')
    if (Test-Path $f) {
        $today = (Get-Date).ToString('yyyy-MM-dd')
        foreach ($ln in [System.IO.File]::ReadAllLines($f)) {
            if ($ln -match 'published (\S+) (\d{4}-\d\d-\d\d)') {
                if ($Matches[2] -eq $today) { $n++ }
            }
        }
    }
    return $n
}

function Publish-Group([string]$platform, [string]$script, [string]$guids, [string[]]$guidList) {
    $already = Get-PublishedFromState $platform
    $todo = @(foreach ($g in $guidList) { if (-not $already.ContainsKey($g)) { $g } })
    if ($todo.Count -eq 0) { WLog ("$platform nothing due"); return @{ ok = 0; fail = 0 } }
    $out = & powershell -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $script -Guids ($todo -join ',') 2>&1 | Out-String
    $plog = Join-Path $state ($platform + '.log')
    $ok = 0; $fail = 0
    foreach ($line in ($out -split "`r?`n")) {
        if ($line -match '^(SENT|OK) guid=(\S+)') {
            $g = $Matches[2]
            Add-Content -Path $plog -Value ("published $g " + (Get-Date).ToString('yyyy-MM-dd')) -Encoding UTF8
            $ok++
        } elseif ($line -match '^FAIL guid=(\S+)') {
            $fail++
        }
    }
    WLog ("$platform sent=$ok fail=$fail guids=" + ($todo -join ','))
    return @{ ok = $ok; fail = $fail }
}

# --- pick due guids respecting per-platform published and caps ---
function Select-Due([hashtable]$published, [int]$cap) {
    $cands = @()
    foreach ($g in $rows.Keys) {
        if ($published.ContainsKey($g)) { continue }
        $d = Parse-FeedDate $rows[$g][0]
        if ($d -and $d -le $now) { $cands += [pscustomobject]@{ g = $g; d = $d } }
    }
    $cands = $cands | Sort-Object d
    $todayCnt = 0
    $sel = @()
    foreach ($c in $cands) {
        if ($todayCnt -ge $cap) { break }
        $sel += $c.g; $todayCnt++
    }
    return ,$sel
}

# --- TG (seed once from tg_published.txt) ---
$tgPub = Get-Tracked (Join-Path $tgDir 'tg_published.txt')
$tgDue = Select-Due $tgPub $TgCap
if ($tgDue.Count -gt 0) {
    Publish-Group 'tg' (Join-Path $tgDir 'tg-autopublish.ps1') ($tgDue -join ',') $tgDue | Out-Null
} else {
    WLog 'tg nothing due'
}

# --- FB (seed once from secrets/fb_published.txt) ---
$fbPub = Get-Tracked (Join-Path 'F:\Pill\tmp\opencode\secrets\fb_published.txt')
$fbDue = Select-Due $fbPub $FbCap
if ($fbDue.Count -gt 0) {
    Publish-Group 'fb' (Join-Path $tools 'fb-autopublish.ps1') ($fbDue -join ',') $fbDue | Out-Null
} else {
    WLog 'fb nothing due'
}

# --- heartbeat ---
[System.IO.File]::WriteAllText((Join-Path $state 'heartbeat.txt'), $stamp, (New-Object System.Text.UTF8Encoding($false)))
WLog "cycle done (tg=$($tgDue.Count) fb=$($fbDue.Count))"