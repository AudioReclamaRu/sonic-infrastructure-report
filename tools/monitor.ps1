# monitor.ps1 - unified status of search/publish system.
# Aggregates: trackers, quotas, heartbeat, logs, scan outcomes, evidence,
# leads, feed, secrets presence, Dzen linker state.
# Outputs: reports/status.html (standalone dashboard), reports/status.md (digest).
# Usage:
#   powershell -File monitor.ps1            (write status.html + status.md)
#   powershell -File monitor.ps1 -NotifyTg  (also send digest to the feed channel)
param(
    [switch]$NotifyTg
)
$ErrorActionPreference = 'Continue'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)

$base    = 'F:\Pill\tmp\opencode'
$secrets = Join-Path $base 'secrets'
$repo    = Join-Path $base 'sonic-repo'
$feed    = Join-Path $repo 'feed'
$state   = Join-Path $repo 'state'
$report  = Join-Path $repo 'reports'
$today   = Get-Date -Format 'yyyy-MM-dd'

$statusHtml = Join-Path $report 'status.html'
$statusMd   = Join-Path $report ('status-' + $today + '.md')

function Esc([string]$s) { return [System.Net.WebUtility]::HtmlEncode($s) }
function Read-List([string]$f) {
    if (-not (Test-Path $f)) { return @() }
    return @([System.IO.File]::ReadAllLines($f) | Where-Object { $_ -ne '' })
}
function LastWrite([string]$f) {
    if (Test-Path $f) { return (Get-Item $f).LastWriteTime.ToString('dd.MM HH:mm') }
    return 'n/a'
}

# ---- heartbeat age ----
$hb = Join-Path $state 'heartbeat.txt'
$hbAgeMin = -1
if (Test-Path $hb) {
    $stamp = [System.IO.File]::ReadAllText($hb).Trim()
    try { $hbAgeMin = [math]::Round(((Get-Date) - ([datetime]::Parse($stamp))).TotalMinutes, 0) } catch { }
}

# ---- trackers ----
$tgSet = @(Read-List (Join-Path $base 'tg\tg_published.txt'))
$fbSet = @(Read-List (Join-Path $secrets 'fb_published.txt'))
$vkSet = @(Read-List (Join-Path $secrets 'vk_published.txt'))
$igSet = @(Read-List (Join-Path $secrets 'ig_published.txt'))
$unq = { param($a) @($a | Select-Object -Unique) }

# ---- quota today ----
$quotaPath = Join-Path $state ("quota-" + $today + '.json')
$quota = @{ tg = '-'; fb = '-'; vk = '-'; ig = '-' }
if (Test-Path $quotaPath) {
    try { $q = Get-Content $quotaPath -Raw | ConvertFrom-Json; $quota.tg = $q.tg; $quota.fb = $q.fb; $quota.vk = $q.vk; $quota.ig = $q.ig } catch { }
}

# ---- feed/items + register ----
$items = @()
if (Test-Path (Join-Path $feed 'items.csv')) {
    foreach ($row in [System.IO.File]::ReadAllLines((Join-Path $feed 'items.csv'))) {
        if (-not $row -or $row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
        $p = $row -split '~~~'
        if ($p.Count -lt 6) { continue }
        $items += ,@($p[0], $p[1], $p[4])
    }
}
$imgCount = 0
$imgsDir = Join-Path $feed 'images'
if (Test-Path $imgsDir) { $imgCount = @(Get-ChildItem $imgsDir -File | Where-Object { $_.Extension -eq '.png' }).Count }

# ---- scans / signals ----
$scansDir = Join-Path $report 'scans'
$scanToday = (Test-Path (Join-Path $scansDir ("scans-" + $today + '.md')))
if (Test-Path $scansDir) { $scanTotal = @(Get-ChildItem $scansDir -Filter 'scans-*.md' | Where-Object { $_.Name -match 'scans-\d{4}-\d\d-\d\d\.md' }).Count } else { $scanTotal = 0 }

# --- leads ----
$leadsPath = Join-Path $feed 'leads.csv'
$leads = @()
if (Test-Path $leadsPath) { $leads = @([System.IO.File]::ReadAllLines($leadsPath) | Where-Object { $_ -and $_ -notmatch '^URL~~~|^#|^GUID' }) }

# ---- evidence ----
$evDir = Join-Path $repo 'evidence'
$evCount = 0
if (Test-Path $evDir) { $evCount = @(Get-ChildItem $evDir -Filter '*.md').Count }

# ---- secrets ----
$vkTok = Test-Path (Join-Path $secrets 'vk_token.txt')
$fbTok = Test-Path (Join-Path $secrets 'fb_token.txt')
$vkGrp = ''
$vkg = Join-Path $secrets 'vk_group.txt'
if (Test-Path $vkg) { $vkGrp = ([System.IO.File]::ReadAllText($vkg).Trim()) }
$dzenCode = Test-Path (Join-Path $secrets 'dzen_token.txt')
$dzenLinked = Test-Path (Join-Path $state 'dzen-linked.ok')
$dzenState = if ($dzenLinked) { 'LINKED' } elseif ($dzenCode) { 'WAITING_LINK' } else { 'NO_CODE' }

# ---- rss ----
$rssCount = 0
$rssPath = Join-Path $feed 'rss.xml'
if (Test-Path $rssPath) {
    $rssRaw = [System.IO.File]::ReadAllText($rssPath)
    $rssCount = ([regex]::Matches($rssRaw, '<item>')).Count
}

# ---- orchestrator log tail ----
$orqLog = Join-Path $state 'orchestrator.log'
$orqTail = @()
if (Test-Path $orqLog) { $orqTail = @([System.IO.File]::ReadAllLines($orqLog) | Select-Object -Last 8) }

# ---- human digest ----
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine("Sonic status " + (Get-Date -Format 'dd.MM.yy HH:mm'))
[void]$sb.AppendLine("Heartbeat: " + $(if ($hbAgeMin -ge 0) { "$hbAgeMin min ago" } else { 'none' }))
[void]$sb.AppendLine("Posted: TG=" + @(& $unq $tgSet).Count + " FB=" + @(& $unq $fbSet).Count + " VK=" + @(& $unq $vkSet).Count + " IG=" + @(& $unq $igSet).Count + " | today tg=" + $quota.tg + " fb=" + $quota.fb + " vk=" + $quota.vk + " ig=" + $quota.ig)
[void]$sb.AppendLine("Upcoming: " + $(@($items | Where-Object { [datetime]::ParseExact($_[0], 'r', [System.Globalization.CultureInfo]::InvariantCulture) -gt (Get-Date) }).Count) + " of " + $items.Count)
[void]$sb.AppendLine("Search: scans=" + $scanTotal + " today=" + $scanToday + " leads=" + $leads.Count + " evidence=" + $evCount)
[void]$sb.AppendLine("Channels: VK=" + $vkGrp + " | Dzen=" + $dzenState)
$digest = $sb.ToString().TrimEnd("`r", "`n")

# ---- status.html ----
$tgU = @(& $unq $tgSet); $fbU = @(& $unq $fbSet); $vkU = @(& $unq $vkSet); $igU = @(& $unq $igSet)
$ork = ''
foreach ($l in $orqTail) { $ork += "<div>" + ([System.Net.WebUtility]::HtmlEncode($l)) + "</div>`n" }

function Chip([string]$v, [string]$state) {
    $st = if ($state -eq 'ok') { 'ok' } else { 'no' }
    return ('<span class="chip ' + $st + '">' + $v + '</span>')
}

$rows = ''
foreach ($it in ($items | ForEach-Object {
    $d = [datetime]::ParseExact($_[0], 'r', [System.Globalization.CultureInfo]::InvariantCulture)
    [pscustomobject]@{ d = $d; title = $_[1]; g = $_[2] }
} | Sort-Object d)) {
    $cls = ''
    if ($it.d.Date -eq (Get-Date).Date) { $cls = ' class="today"' }
    elseif ($it.d -gt (Get-Date)) { $cls = ' class="future"' }
    $tg = if ($tgU -contains $it.g) { 'TG' } else { '-' }
    $fb = if ($fbU -contains $it.g) { 'FB' } else { '-' }
    $vk = if ($vkU -contains $it.g) { 'VK' } else { '-' }
    $ig = if ($igU -contains $it.g) { 'IG' } else { '-' }
    $tgC = if ($tgU -contains $it.g) { 'ok' } else { 'no' }
    $fbC = if ($fbU -contains $it.g) { 'ok' } else { 'no' }
    $vkC = if ($vkU -contains $it.g) { 'ok' } else { 'no' }
    $igC = if ($igU -contains $it.g) { 'ok' } else { 'no' }
    $rows += ('<tr' + $cls + '><td>' + $it.d.ToString('dd.MM.yy HH:mm') + '</td><td>' + ([System.Net.WebUtility]::HtmlEncode($it.title)) + '</td><td>' + (Chip $tg $tgC) + '</td><td>' + (Chip $fb $fbC) + '</td><td>' + (Chip $vk $vkC) + '</td><td>' + (Chip $ig $igC) + '</td></tr>' + "`n")
}

$hbColor = if ($hbAgeMin -ge 0 -and $hbAgeMin -le 15) { 'ok' } else { 'bad' }
$html = @"
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AudioReclama sonic status</title>
<style>
body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:24px;font-size:14px}
h1{font-size:16px;color:#f0f6fc;margin:0 0 4px 0}
.sub{color:#8b949e;font-size:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 12px}
.card .k{color:#8b949e;font-size:11px;text-transform:uppercase}
.card .v{font-size:20px;font-weight:600;color:#f0f6fc;margin-top:2px}
.v.ok{color:#3fb950}.v.bad{color:#f85149}
table{border-collapse:collapse;width:100%;margin-top:8px}
td,th{border:1px solid #30363d;padding:6px 10px;font-size:13px;text-align:left}
tr.today td{background:#1f6feb22}
tr.future td{opacity:.55}
.chip{display:inline-block;min-width:28px;text-align:center;padding:2px 6px;border-radius:10px;font-weight:700;font-size:11px}
.chip.ok{background:#238636;color:#fff}
.chip.no{background:#21262d;color:#484f58}
.log{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;margin-top:12px;font-size:11px;color:#8b949e;white-space:pre-wrap}
.foot{color:#484f58;font-size:11px;margin-top:12px}
</style>
</head>
<body>
<h1>AudioReclama sonic status</h1>
<div class="sub">Generated $(Get-Date -Format 'dd.MM.yy HH:mm:ss') | VK group $vkGrp | Dzen $dzenState</div>
<div class="cards">
  <div class="card"><div class="k">Heartbeat</div><div class="v $(if ($hbAgeMin -ge 0) { if ($hbAgeMin -le 15) { 'ok' } else { 'bad' } } else { 'bad' })">$(if ($hbAgeMin -ge 0) { "$hbAgeMin min" } else { 'n/a' })</div></div>
  <div class="card"><div class="k">TG posted</div><div class="v">$($tgU.Count)</div></div>
  <div class="card"><div class="k">FB posted</div><div class="v">$($fbU.Count)</div></div>
  <div class="card"><div class="k">VK posted</div><div class="v">$($vkU.Count)</div></div>
  <div class="card"><div class="k">IG posted</div><div class="v">$($igU.Count)</div></div>
  <div class="card"><div class="k">Today tg/fb/vk/ig</div><div class="v">$($quota.tg)/$($quota.fb)/$($quota.vk)/$($quota.ig)</div></div>
  <div class="card"><div class="k">Evidence</div><div class="v">$evCount</div></div>
  <div class="card"><div class="k">Leads</div><div class="v">$($leads.Count)</div></div>
  <div class="card"><div class="k">Scans</div><div class="v">$scanTotal</div></div>
  <div class="card"><div class="k">RSS items</div><div class="v">$rssCount</div></div>
</div>
<table>
<tr><th>Date</th><th>Post</th><th>TG</th><th>FB</th><th>VK</th><th>IG</th></tr>
$rows</table>
<h2 style="font-size:14px;margin-top:16px">Orchestrator log (tail)</h2>
<div class="log">$ork</div>
<div class="foot">data sources: trackers in secrets/ and tg/, register.csv, state/, reports/scans/, evidence/, feed/. Dashboard generated by tools/monitor.ps1.</div>
</body>
</html>
"@
[System.IO.File]::WriteAllText($statusHtml, $html, (New-Object System.Text.UTF8Encoding($false)))
[System.IO.File]::WriteAllText($statusMd, $digest + "`n", (New-Object System.Text.UTF8Encoding($false)))
$calView = Join-Path $repo 'tools\calendar-view.ps1'
if (Test-Path -LiteralPath $calView) { & powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $calView 2>&1 | Out-Null }
$newsView = Join-Path $repo 'tools\news-view.ps1'
if (Test-Path -LiteralPath $newsView) { & powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $newsView 2>&1 | Out-Null }
Write-Output ("MONITOR ok -> " + $statusHtml)
Write-Output $digest

if ($NotifyTg) {
    $fl = Join-Path $base 'tg\feed_channel.txt'
    $chat = ''
    foreach ($ln in @([System.IO.File]::ReadAllLines($fl))) {
        if ($ln -and -not $ln.StartsWith('#')) { $chat = $ln.Trim(); break }
    }
    if ($chat) {
        & powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File (Join-Path $base 'tg\send-tg.ps1') -Chat $chat -Text $digest 2>&1 | Out-Null
        Write-Output 'NOTIFY_SENT'
    } else {
        Write-Output 'NOTIFY_NO_CHAT'
    }
}