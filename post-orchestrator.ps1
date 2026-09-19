# post-orchestrator.ps1 - THE unified autonomous publishing loop.
# Platforms: TG only (decision 16.09.2026: канал живёт в TG, автопостинг в
# Дзен через связку TG<->Dzen; FB/VK/IG отключены и не восстанавливаются).
# Idempotent by guid. Per-platform daily caps.
# Usage:
#   powershell -File post-orchestrator.ps1 -Loop              (continuous, watchdog keeps it alive)
#   powershell -File post-orchestrator.ps1 -Once              (single cycle, exits)
#   powershell -File post-orchestrator.ps1 -Once -TgCap 4
# Outputs: register.csv, calendar.html, state/heartbeat.txt, state/orchestrator.log
param(
    [switch]$Once,
    [switch]$Loop,
    [switch]$Now,
    [int]$TgCap = 4,
    [int]$Interval = 300
)
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)

# RFC1123: "Thu, 11 Sep 2026 07:00:00 GMT" -> DateTime
$rfc1123 = @{ Culture = 'en-US'; Format = 'r' }
function Parse-Date([string]$s) {
    return [datetime]::ParseExact($s, $rfc1123.Format, (New-Object System.Globalization.CultureInfo($rfc1123.Culture)))
}

$base    = 'F:\Pill\tmp\opencode'
$secrets = Join-Path $base 'secrets'
$repo    = Join-Path $base 'sonic-repo'
$feed    = Join-Path $repo 'feed'
$tools   = Join-Path $repo 'tools'
$state   = Join-Path $repo 'state'
$itemsCsv  = Join-Path $feed 'items.csv'
$registry  = Join-Path $repo 'register.csv'
$calendar  = Join-Path $repo 'calendar.html'
$tplFile   = Join-Path $repo 'calendar.tpl'
$tgTracker = Join-Path $base 'tg\tg_published.txt'
$fbTracker = Join-Path $secrets 'fb_published.txt'
$vkTracker = Join-Path $secrets 'vk_published.txt'
$igTracker = Join-Path $secrets 'ig_published.txt'
$tgScript = Join-Path $base 'tg\tg-autopublish.ps1'
$fbScript = Join-Path $tools 'fb-autopublish.ps1'
$vkScript = Join-Path $tools 'vk-autopublish.ps1'
$igScript = Join-Path $base 'ig\ig-autopublish.ps1'

if (-not (Test-Path $state)) { New-Item -ItemType Directory -Path $state -Force | Out-Null }
$heartbeat = Join-Path $state 'heartbeat.txt'
$orqLog    = Join-Path $state 'orchestrator.log'

function OLog([string]$msg) {
    [System.IO.File]::AppendAllText($orqLog, ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " " + $msg + "`n"), (New-Object System.Text.UTF8Encoding($false)))
}

function Get-Seen([string]$file) {
    if (-not (Test-Path -LiteralPath $file)) { return @() }
    return @([System.IO.File]::ReadAllLines($file) | Where-Object { $_ -ne '' })
}
function Add-Unique([string]$file, [string]$line) {
    if (-not (Test-Path -LiteralPath $file)) {
        [System.IO.File]::WriteAllText($file, '', (New-Object System.Text.UTF8Encoding($false)))
    }
    $cur = @(Get-Seen $file)
    if ($cur -contains $line) { return }
    [System.IO.File]::AppendAllText($file, $line + "`n", (New-Object System.Text.UTF8Encoding($false)))
}

# ---------- items (from csv rows: date~~~title~~~desc~~~source~~~guid~~~image) ----------
$rows = [System.IO.File]::ReadAllLines($itemsCsv)
$items = @()
foreach ($row in $rows) {
    if (-not $row) { continue }
    if ($row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    $items += ,@($p[0], $p[1], $p[2], $p[3], $p[4], $p[5])
}

# ---------- daily quota (state/quota-<date>.json) ----------
function Get-QuotaFile() { return Join-Path $state ("quota-" + (Get-Date -Format 'yyyy-MM-dd') + '.json') }

function Get-Quota {
    $q = Get-QuotaFile
    if (Test-Path $q) {
        try { return (Get-Content $q -Raw | ConvertFrom-Json) } catch { }
    }
    $o = [pscustomobject]@{ ts = (Get-Date -Format 'yyyy-MM-dd'); tg = 0; fb = 0; vk = 0; ig = 0 }
    return $o
}
function Inc-Quota([string]$key) {
    $q = Get-Quota
    if ($key -eq 'tg') { $q.tg = [int]$q.tg + 1 }
    if ($key -eq 'fb') { $q.fb = [int]$q.fb + 1 }
    if ($key -eq 'vk') { $q.vk = [int]$q.vk + 1 }
    if ($key -eq 'ig') { $q.ig = [int]$q.ig + 1 }
    [System.IO.File]::WriteAllText((Get-QuotaFile), ($q | ConvertTo-Json -Compress), (New-Object System.Text.UTF8Encoding($false)))
    OLog ("QUOTA inc " + $key + " => tg=" + $q.tg + " fb=" + $q.fb + " vk=" + $q.vk + " ig=" + $q.ig)
}

# ---------- platform registry (TG only; FB/VK/IG off per 16.09.2026 decision) ----------
$platforms = @(
    @{ key = 'tg'; cap = $TgCap; tracker = $tgTracker; script = $tgScript; okpat = 'SENT guid=';    failpat = 'FAIL' }
)

# ---------- единый сводный реестр по guid ----------
function Build-Registry {
    $tg = @(Get-Seen $tgTracker)
    $fb = @(Get-Seen $fbTracker)
    $vk = @(Get-Seen $vkTracker)
    $ig = @(Get-Seen $igTracker)
    $lines = @('GUID~~~TITLE~~~DATE~~~TG~~~FB~~~IG~~~VK')
    foreach ($it in $items) {
        $g = $it[4]
        $tgSt = if ($tg -contains $g) { 'DONE' } else { '--' }
        $fbSt = if ($fb -contains $g) { 'DONE' } else { '--' }
        $igSt = if ($ig -contains $g) { 'DONE' } else { '--' }
        $vkSt = if ($vk -contains $g) { 'DONE' } else { '--' }
        $lines += ($g + '~~~' + $it[1] + '~~~' + $it[0] + '~~~' + $tgSt + '~~~' + $fbSt + '~~~' + $igSt + '~~~' + $vkSt)
    }
    [System.IO.File]::WriteAllLines($registry, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

# ---------- календарь-статус: шаблон или встроенный вид ----------
function Build-Calendar {
    $tg = @(Get-Seen $tgTracker)
    $fb = @(Get-Seen $fbTracker)
    $vk = @(Get-Seen $vkTracker)
    $ig = @(Get-Seen $igTracker)
    $sorted = $items | Sort-Object { Parse-Date $_[0] }
    $sb = New-Object System.Text.StringBuilder
    foreach ($it in $sorted) {
        $dt = Parse-Date $it[0]
        $g = $it[4]
        $isToday = ($dt.Date -eq (Get-Date).Date)
        $isFuture = ($dt -gt (Get-Date))
        $cls = if ($isToday) { ' class="today"' } elseif ($isFuture) { ' class="future"' } else { '' }
        $t1 = if ($tg -contains $g) { '<span class="tg ok">TG</span>' } else { '<span class="tg no">-</span>' }
        $t2 = if ($fb -contains $g) { '<span class="fb ok">FB</span>' } else { '<span class="fb no">-</span>' }
        $t3 = if ($ig -contains $g) { '<span class="ig ok">IG</span>' } else { '<span class="ig no">-</span>' }
        $t4 = if ($vk -contains $g) { '<span class="vk ok">VK</span>' } else { '<span class="vk no">-</span>' }
        $esc = [System.Net.WebUtility]::HtmlEncode($it[1])
        [void]$sb.AppendLine(('<tr{0}><td>{1:dd.MM.yy HH:mm}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6}</td></tr>' -f $cls, $dt, $esc, $t1, $t2, $t3, $t4))
    }
    $rowsHtml = $sb.ToString()
    $tpl = $null
    if (Test-Path -LiteralPath $tplFile) {
        $tpl = [System.IO.File]::ReadAllText($tplFile)
        $tpl = $tpl.Replace('@@ROWS@@', $rowsHtml)
        $tpl = $tpl.Replace('@@GENERATED@@', (Get-Date -Format 'dd.MM.yy HH:mm'))
    }
    if (-not $tpl) {
        $tpl = @'
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AudioReclama publish calendar</title>
<style>
body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:24px}
h1{font-size:18px;color:#f0f6fc}
table{border-collapse:collapse;width:100%;margin-top:12px}
td,th{border:1px solid #30363d;padding:6px 10px;font-size:13px;text-align:left}
tr.today td{background:#1f6feb22}
tr.future td{opacity:.55}
.ok{color:#3fb950;font-weight:600}
.no{color:#484f58}
.fb.ok{color:#58a6ff}.ig.ok{color:#f778ba}.vk.ok{color:#e3b341}.tg.ok{color:#3fb950}
.foot{color:#484f58;font-size:11px;margin-top:10px}
</style>
</head>
<body>
<h1>AudioReclama - publish calendar</h1>
<table>
<tr><th>Date</th><th>Post</th><th>TG</th><th>FB</th><th>IG</th><th>VK</th></tr>
</table>
</body>
</html>
'@
        $tpl = $tpl.Replace('<table>', '<table>' + $rowsHtml)
    }
    [System.IO.File]::WriteAllText($calendar, $tpl, (New-Object System.Text.UTF8Encoding($false)))
}

# ---------- публикация одного guid на платформу (идемпотентно) ----------
function Publish-One([string]$g, [hashtable]$p) {
    $seen = @(Get-Seen $p.tracker)
    if ($seen -contains $g) { return 'SKIP' }
    $out = & powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $p.script -Guids $g 2>&1 | Out-String
    if ($out -notmatch $p.failpat -and ($out -match $p.okpat -or $out -match 'DONE ok=[1-9]')) {
        Add-Unique $p.tracker $g
        Inc-Quota $p.key
        $pLog = Join-Path $state ($p.key + '.log')
        [System.IO.File]::AppendAllText($pLog, ("published " + $g + " " + (Get-Date -Format 'yyyy-MM-dd') + "`n"), (New-Object System.Text.UTF8Encoding($false)))
        OLog ("OK " + $p.key + " " + $g)
        return 'OK'
    } else {
        OLog ("FAIL " + $p.key + " " + $g + " :: " + $out.Trim())
        return 'FAIL'
    }
}

# ---------- главный цикл ----------
function Run-Cycle {
    $now = Get-Date
    Build-Registry
    Build-Calendar

    $due = @(foreach ($it in $items) {
        $dt = Parse-Date $it[0]
        if ($dt -le $now) { [pscustomobject]@{ g = $it[4]; d = $dt } }
    })
    $due = @($due | Sort-Object d)

    $quota = Get-Quota
    $summ = @()
    foreach ($p in $platforms) {
        if ($p.key -eq 'ig') {
            if (-not (Test-Path (Join-Path $secrets 'fb_page_token_ig.txt')) -or -not (Test-Path (Join-Path $secrets 'ig_state.json'))) {
                OLog ("PENDING ig (no IG token - run ig/ig-ensure-token.ps1)"); continue
            }
        }
        $used = [int]$quota.($p.key)
        $slots = [Math]::Max(0, $p.cap - $used)
        if ($slots -eq 0) { OLog ("CAP " + $p.key + " (" + $used + "/" + $p.cap + ")"); continue }
        $done = @(Get-Seen $p.tracker)
        $cands = @($due | Where-Object { $done -notcontains $_.g } | Select-Object -First $slots)
        $r = @{ key = $p.key; ok = 0; fail = 0; skip = 0 }
        foreach ($c in $cands) {
            $st = Publish-One $c.g $p
            if ($st -eq 'OK') { $r.ok++ } elseif ($st -eq 'FAIL') { $r.fail++ } else { $r.skip++ }
            Start-Sleep -Seconds 2
        }
        $summ += ($p.key + "=" + $r.ok + "/" + $r.fail)
    }

    [System.IO.File]::WriteAllText($heartbeat, (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'), (New-Object System.Text.UTF8Encoding($false)))
    OLog ("CYCLE " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " :: " + ($summ -join ' '))
    Write-Output ("CYCLE " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " :: " + ($summ -join ' '))
    Write-Output 'CYCLE_DONE'
}

if ($Loop) {
    [System.IO.File]::WriteAllText((Join-Path $state 'orchestrator.pid'), $PID.ToString(), (New-Object System.Text.UTF8Encoding($false)))
    while ($true) {
        try { Run-Cycle } catch { OLog ("WATCHDOG_ERR " + $_.Exception.Message); Write-Output ("WATCHDOG_ERR " + $_.Exception.Message) }
        Start-Sleep -Seconds $Interval
    }
} else {
    Run-Cycle
}