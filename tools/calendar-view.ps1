# calendar-view.ps1 - full-year visual posts calendar across all networks.
# Source of truth: feed/items.csv (+ trackers for DONE). Output: calendar-view.html (auto-refresh 60s).
# Usage: powershell -File tools/calendar-view.ps1 [-Year 2026]
param([int]$Year = (Get-Date).Year)
$ErrorActionPreference = 'Continue'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$base = 'F:\Pill\tmp\opencode'
$secrets = Join-Path $base 'secrets'
$repo = Join-Path $base 'sonic-repo'
$feed = Join-Path $repo 'feed'
$state = Join-Path $repo 'state'
$out = Join-Path $repo 'calendar-view.html'
$rc = [System.Globalization.CultureInfo]::InvariantCulture

$tgSet = @()
if (Test-Path (Join-Path $base 'tg\tg_published.txt')) { $tgSet = @([System.IO.File]::ReadAllLines((Join-Path $base 'tg\tg_published.txt')) | Where-Object { $_ -ne '' }) }
$fbSet = @()
if (Test-Path (Join-Path $secrets 'fb_published.txt')) { $fbSet = @([System.IO.File]::ReadAllLines((Join-Path $secrets 'fb_published.txt')) | Where-Object { $_ -ne '' }) }
$vkSet = @()
if (Test-Path (Join-Path $secrets 'vk_published.txt')) { $vkSet = @([System.IO.File]::ReadAllLines((Join-Path $secrets 'vk_published.txt')) | Where-Object { $_ -ne '' }) }
$igSet = @()
if (Test-Path (Join-Path $secrets 'ig_published.txt')) { $igSet = @([System.IO.File]::ReadAllLines((Join-Path $secrets 'ig_published.txt')) | Where-Object { $_ -ne '' }) }

$items = @()
foreach ($row in [System.IO.File]::ReadAllLines((Join-Path $feed 'items.csv'))) {
    if (-not $row -or $row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    $dt = $null
    try { $dt = [datetime]::ParseExact($p[0].Trim(), 'r', $rc) } catch { }
    if (-not $dt) { continue }
    $items += ,[pscustomobject]@{ d = $dt; title = $p[1]; g = $p[4]; img = $p[5] }
}

$now = Get-Date
$dowRu = @('Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб')
$monRu = @('', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь')
$monRuGen = @('', 'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря')
$monRu2 = @('', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')

function Chip([string]$label, [bool]$on) {
    $cls = if ($on) { 'ok' } else { 'no' }
    return '<span class="ch c-' + $label.ToLower() + ' ' + $cls + '">' + $label + '</span>'
}

function Post-Cell([pscustomobject]$it, [bool]$isToday) {
    $cls = if ($isToday) { 'post today' } else { 'post' }
    $img = Join-Path (Join-Path $feed 'images') ($it.img + '.png')
    $thumb = ''
    if (Test-Path -LiteralPath $img) { $thumb = '<img class="th" src="feed/images/' + ([System.Net.WebUtility]::HtmlEncode($it.img)) + '.png" alt="">' }
    $tg = Chip 'TG' ($tgSet -contains $it.g)
    $fb = Chip 'FB' ($fbSet -contains $it.g)
    $vk = Chip 'VK' ($vkSet -contains $it.g)
    $ig = Chip 'IG' ($igSet -contains $it.g)
    return '<div class="' + $cls + '">' + $thumb + '<div class="t">' + ([System.Net.WebUtility]::HtmlEncode($it.title)) + '</div><div class="chs">' + $tg + $fb + $vk + $ig + '</div></div>'
}

function Grid-Month([int]$y, [int]$m) {
    $mStart = (Get-Date -Year $y -Month $m -Day 1)
    $mDays = [DateTime]::DaysInMonth($y, $m)
    $inner = ''
    foreach ($it in @($items | Where-Object { $_.d.Year -eq $y -and $_.d.Month -eq $m } | Sort-Object d)) {
        $inner += Post-Cell $it (($it.d.Date) -eq (Get-Date).Date)
    }
    $gridHtml = ''
    $firstIdx = [int]$mStart.DayOfWeek
    $mondayIdx = (($firstIdx + 6) % 7)
    $gridHtml += '<tr>'
    for ($i = 0; $i -lt $mondayIdx; $i++) { $gridHtml += '<td class="empty"></td>' }
    for ($di = 1; $di -le $mDays; $di++) {
        $day = $mStart.AddDays($di - 1)
        $isToday = ($day.Date -eq (Get-Date).Date)
        $wk = [int]$day.DayOfWeek
        $wIdx = (($wk + 6) % 7)
        $dayPosts = @($items | Where-Object { $_.d.Date -eq $day.Date })
        $cell = '<div class="dnum' + $(if ($isToday) { ' today' } else { '' }) + '">' + $di.ToString() + '<span>' + $dowRu[$wk] + '</span></div>'
        if ($dayPosts.Count -eq 0) {
            $cellCls = if ($isToday) { 'td tod' } elseif ($day -gt (Get-Date)) { 'td fut' } else { 'td pas' }
            $gridHtml += '<td class="' + $cellCls + '">' + $cell + '</td>'
        } else {
            $cellCls = if ($isToday) { 'td has tod' } else { 'td has' }
            $inner2 = $cell
            foreach ($p in $dayPosts) { $inner2 += Post-Cell $p $isToday }
            $gridHtml += '<td class="' + $cellCls + '">' + $inner2 + '</td>'
        }
        if ($wIdx -eq 6) { $gridHtml += '</tr><tr>' }
    }
    $gridHtml += '</tr>'
    return '<div class="month"><h2>' + $monRu[$m] + ' ' + $y + '<span class="mcnt">' + $inner + '</span></h2><table>' + $gridHtml + '</table></div>'
}

$monthsHtml = ''
for ($mi = 1; $mi -le 12; $mi++) { $monthsHtml += (Grid-Month -y $Year -m $mi) }

$tot = $items.Count
$yPostedTg = @($items | Where-Object { $tgSet -contains $_.g }).Count
$yPostedFb = @($items | Where-Object { $fbSet -contains $_.g }).Count
$yPostedVk = @($items | Where-Object { $vkSet -contains $_.g }).Count
$yPostedIg = @($items | Where-Object { $igSet -contains $_.g }).Count
$nowLine = $now.ToString('dd.MM.yy HH:mm:ss')

# timeline of all posts (full archive, no truncation)
$tlHtml = ''
foreach ($it in @($items | Sort-Object d)) {
    $done = if ($tgSet -contains $it.g) { 'posted' } else { 'planned' }
    $img = Join-Path (Join-Path $feed 'images') ($it.img + '.png')
    $tt = ''
    if (Test-Path -LiteralPath $img) { $tt = '<img class="thm" src="feed/images/' + ([System.Net.WebUtility]::HtmlEncode($it.img)) + '.png" alt="">' }
    $tlHtml += '<div class="plist ' + $done + '">' + $tt + '<span class="pdate">' + $it.d.ToString('dd.MM.yy') + '</span> – ' + ([System.Net.WebUtility]::HtmlEncode($it.title)) + ' ' + (Chip 'TG' ($tgSet -contains $it.g)) + (Chip 'FB' ($fbSet -contains $it.g)) + (Chip 'VK' ($vkSet -contains $it.g)) + (Chip 'IG' ($igSet -contains $it.g)) + '</div>'
}

$html = @"
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="60">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AudioReclama post calendar — $Year</title>
<style>
body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:20px}
h1{font-size:18px;color:#f0f6fc;margin:0 0 2px 0}
.sub{color:#8b949e;font-size:12px;margin-bottom:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:14px}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 10px}
.card .k{color:#8b949e;font-size:10px;text-transform:uppercase}
.card .v{font-size:18px;font-weight:600;color:#f0f6fc}
table{width:100%;border-collapse:separate;border-spacing:3px;table-layout:fixed}
td{border:1px solid #30363d;border-radius:8px;background:#0f1419;vertical-align:top;padding:6px;height:92px}
td.empty{border:none;background:none}
td.tod{outline:2px solid #1f6feb;background:#1f6feb11}
td.fut{opacity:.92}
td.pas{opacity:.55}
td.has{background:#161b2208}
.dnum{color:#f0f6fc;font-size:14px;font-weight:700}
.dnum span{color:#8b949e;font-size:10px;font-weight:400;margin-left:4px}
.dnum.today{color:#58a6ff}
.post{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:6px;margin-top:6px}
.post.today{border-color:#1f6feb}
.post .t{font-size:11px;line-height:1.35;color:#c9d1d9}
.post .chs{margin-top:4px}
.ch{display:inline-block;min-width:20px;text-align:center;padding:1px 4px;border-radius:8px;font-weight:700;font-size:9px;margin-right:2px}
.ch.ok{background:#21262d}
.ch.tg.ok{color:#3fb950}.ch.tg.no{color:#2d333b}
.ch.fb.ok{color:#58a6ff}.ch.fb.no{color:#2d333b}
.ch.vk.ok{color:#e3b341}.ch.vk.no{color:#2d333b}
.ch.ig.ok{color:#f778ba}.ch.ig.no{color:#2d333b}
img.th{width:100%;border-radius:6px;display:block;margin-bottom:4px}
h2{font-size:14px;color:#f0f6fc;margin:18px 0 6px 0}
.month{margin-bottom:6px}
.mcnt{color:#8b949e;font-size:11px;font-weight:400;margin-left:8px}
.plist{font-size:12px;padding:5px 0;display:flex;align-items:center;gap:8px}
.plist .pdate{color:#8b949e;font-weight:600}
.plist.posted{opacity:1}
.plist.planned{opacity:.65}
img.thm{width:44px;border-radius:6px}
.foot{color:#484f58;font-size:11px;margin-top:14px}
a{color:#58a6ff}
</style>
</head>
<body>
<h1>AudioReclama — календарь постов <span style="color:#8b949e">($Year)</span></h1>
<div class="sub">обновлено $nowLine | авто-обновление каждые 60 c | <a href="news-view.html">новости под посты &rarr;</a></div>
<div class="cards">
  <div class="card"><div class="k">Постов всего</div><div class="v">$tot</div></div>
  <div class="card"><div class="k">TG posted / $Year</div><div class="v">$yPostedTg</div></div>
  <div class="card"><div class="k">FB posted / $Year</div><div class="v">$yPostedFb</div></div>
  <div class="card"><div class="k">VK posted / $Year</div><div class="v">$yPostedVk</div></div>
  <div class="card"><div class="k">IG posted / $Year</div><div class="v">$yPostedIg</div></div>
</div>
$monthsHtml
<h2>Все посты по датам</h2>
$tlHtml
<div class="foot">источник: feed/items.csv + трекеры (tg_published.txt, fb_published.txt, vk_published.txt, ig_published.txt). Генератор: tools/calendar-view.ps1 -Year $Year.</div>
</body>
</html>
"@

[System.IO.File]::WriteAllText($out, $html, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("CALENDAR -> " + $out)