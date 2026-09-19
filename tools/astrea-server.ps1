param([switch]$NoOpen)
# astrea-server.ps1 — Astrea: единое приложение AudioReclama.
# Backend: hidden loop + mini HTTP server on 127.0.0.1:18826.
#   GET /               -> single-page frontend (calendar + news + live status)
#   GET /api/state.json -> live backend state (rebuilt per request)
#   GET /img/<name>     -> post thumbnails from feed/images
# Frontend polls /api/state.json every 10 s (no page reload).
$Port = 18826
$bind = '127.0.0.1'
$ErrorActionPreference = 'Continue'

$base    = 'F:\Pill\tmp\opencode'
$repo    = Join-Path $base 'sonic-repo'
$secrets = Join-Path $base 'secrets'
$feed    = Join-Path $repo 'feed'
$state   = Join-Path $repo 'state'
$rc      = [System.Globalization.CultureInfo]::InvariantCulture

$script:startedAt = Get-Date
$script:requests  = 0
$script:vkProbe   = $null
$script:vkProbeAt = $null

function Get-DateStr([datetime]$d) { return $d.ToString('dd.MM.yy HH:mm:ss') }

# ---------- posts ----------
function Get-Posts {
    $all = @()
    foreach ($row in [System.IO.File]::ReadAllLines((Join-Path $feed 'items.csv'))) {
        if (-not $row -or $row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
        $p = $row -split '~~~'
        if ($p.Count -lt 6) { continue }
        $dt = $null
        try { $dt = [datetime]::ParseExact($p[0].Trim(), 'r', $rc) } catch { }
        if (-not $dt) { continue }
        $all += ,[pscustomobject]@{
            d = $dt; title = $p[1]; desc = $p[2]; src = $p[3]; g = $p[4]; img = $p[5]
        }
    }
    return @($all | Sort-Object d)
}

# ---------- published trackers ----------
function Read-Set([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return @{} }
    $h = @{}
    foreach ($l in [System.IO.File]::ReadAllLines($path)) {
        if ($l) { $h[$l.Trim()] = $true }
    }
    return $h
}

# ---------- evidence ----------
function Get-Evidence {
    $out = @()
    foreach ($f in @(Get-ChildItem (Join-Path $repo 'evidence') -Filter 'E-*.md' -ErrorAction SilentlyContinue)) {
        $txt = [System.IO.File]::ReadAllText($f.FullName)
        $lines = $txt -split "`r?`n"
        $desc = ''
        $inShort = $false
        foreach ($ln in $lines) {
            if ($ln -match '^Short statement') { $inShort = $true; continue }
            if ($inShort) {
                if ($ln -match '^Source') { $inShort = $false }
                elseif ($ln.Trim()) { $desc += $ln.Trim() + ' ' }
            }
        }
        if (-not $desc) { $desc = $f.Name }
        if ($desc.Length -gt 140) { $desc = $desc.Substring(0, 137) + '...' }
        $urls = @([regex]::Matches($txt, 'https?://[^\s)\]]+') |
            ForEach-Object { $_.Value.TrimEnd('.', ',') } |
            Where-Object { $_ -notmatch 'github.com/AudioReclamaRu' -and $_ -notmatch 'audio-reclama.ru' } |
            Select-Object -Unique)
        if ($urls.Count -eq 0) { $urls += $f.Name }
        $out += ,[pscustomobject]@{ file = $f.Name; desc = $desc; urls = @($urls); raw = $txt }
    }
    return @($out)
}

function Get-PostNews([pscustomobject]$post, [array]$evList) {
    $srcPath = ($post.src -replace 'https://github.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/', '')
    $srcName = ($srcPath -split '/')[-1]
    $hits = @()
    foreach ($e in $evList) {
        if ($e.file -eq $srcName) { $hits += $e }
        elseif ($e.raw -match [regex]::Escape($srcPath)) { $hits += $e }
    }
    if ($hits.Count -eq 0) { $hits = @($evList | Where-Object { $_.raw -match [regex]::Escape($srcName) }) }
    $news = @(); $seen = @{}; $seenH = @{}; $dedH = @()
    foreach ($h in $hits) { if (-not $seenH.ContainsKey($h.file)) { $seenH[$h.file] = $true; $dedH += $h } }
    foreach ($e in $dedH) {
        foreach ($u in $e.urls) {
            if ($seen.ContainsKey($u)) { continue }
            $seen[$u] = $true
            $news += ,[pscustomobject]@{ url = $u; title = $e.desc; file = $e.file }
        }
    }
    if ($news.Count -eq 0) {
        $news += ,[pscustomobject]@{ url = $post.src; title = $post.title; file = $srcName }
    }
    return ,$news
}

# ---------- intel ----------
function Get-Intel {
    $lat = @(Get-ChildItem (Join-Path $repo 'reports\intel') -Filter 'intel-*.json' -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1)
    if (-not $lat) { return @{ date = ''; rows = @() } }
    try {
        $j = Get-Content $lat.FullName -Raw | ConvertFrom-Json
        $rows = @($j.rows | Where-Object { $_.title } | Sort-Object score -Descending | Select-Object -First 20 |
            ForEach-Object {
                [pscustomobject]@{ title = $_.title; url = $_.url; src = $_.src; tier = $_.tier; score = $_.score }
            })
        return @{ date = $j.date; rows = @($rows) }
    } catch {
        return @{ date = $lat.BaseName; rows = @() }
    }
}

# ---------- heartbeat ----------
function Get-Heartbeat {
    $hb = Join-Path $state 'heartbeat.txt'
    if (-not (Test-Path -LiteralPath $hb)) { return @{ alive = $false; age = -1 } }
    try {
        $ts = [datetime]::Parse([System.IO.File]::ReadAllText($hb).Trim())
        $age = [int]((Get-Date) - $ts).TotalSeconds
        return @{ alive = ($age -lt 900); age = $age }
    } catch {
        return @{ alive = $false; age = -1 }
    }
}

# ---------- vk token probe (cached 15 min) ----------
function Invoke-Curl([string]$curlArgs) {
    $outF = Join-Path $env:TEMP ("curl_out_" + [guid]::NewGuid().ToString('N') + ".txt")
    $errF = Join-Path $env:TEMP ("curl_err_" + [guid]::NewGuid().ToString('N') + ".txt")
    $p = Start-Process -FilePath 'C:\WINDOWS\system32\curl.exe' `
        -ArgumentList $curlArgs `
        -RedirectStandardOutput $outF -RedirectStandardError $errF `
        -WindowStyle Hidden -Wait -PassThru
    Remove-Item $errF -Force -ErrorAction SilentlyContinue
    if (Test-Path $outF) {
        $data = [System.IO.File]::ReadAllText($outF)
        Remove-Item $outF -Force -ErrorAction SilentlyContinue
        return $data
    }
    return ''
}

function Get-VkProbe {
    $tokF = Join-Path $secrets 'vk_token.txt'
    if (-not (Test-Path $tokF)) { return 'no-token' }
    if ($script:vkProbe -and ((Get-Date) - $script:vkProbeAt).TotalMinutes -lt 15) { return $script:vkProbe }
    $tok = [System.IO.File]::ReadAllText($tokF).Trim()
    $o = (Invoke-Curl ("--max-time 15 -s -x 'socks5h://127.0.0.1:10808' `"https://api.vk.com/method/groups.getTokenPermissions?access_token=$tok&v=5.199`"")) | ConvertFrom-Json
    $perms = @($o.response.permissions | ForEach-Object { $_.name })
    if ($o -and $o.error) {
        $script:vkProbe = 'err-' + $o.error.error_code
    } elseif ($perms -contains 'wall') {
        $script:vkProbe = 'ok'
    } elseif ($o -and $o.response) {
        $script:vkProbe = 'no-wall'
    } else {
        $script:vkProbe = 'unknown'
    }
    $script:vkProbeAt = Get-Date
    return $script:vkProbe
}

# ---------- next hourly schedule ----------
function Get-NextHourly([int]$minute) {
    $n = Get-Date
    $cand = $n.Date.AddHours($n.Hour).AddMinutes($minute)
    if ($cand -le $n) { $cand = $cand.AddHours(1) }
    return $cand.ToString('HH:mm')
}

function Build-State {
    $script:requests++
    $posts    = Get-Posts
    $evList   = Get-Evidence
    $intel    = Get-Intel
    $hb       = Get-Heartbeat
    $tgSet    = Read-Set (Join-Path $base 'tg\tg_published.txt')
    $fbSet    = Read-Set (Join-Path $secrets 'fb_published.txt')
    $vkSet    = Read-Set (Join-Path $secrets 'vk_published.txt')
    $igSet    = Read-Set (Join-Path $secrets 'ig_published.txt')
    $now      = Get-Date
    $todayMark = $now.ToString('yyyy-MM-dd')

    $dzenFlag = Join-Path $state 'dzen-linked.ok'
    $dzenLinked = $false
    $dzenLinkedAt = $null
    if (Test-Path -LiteralPath $dzenFlag) {
        $dzx = [System.IO.File]::ReadAllText($dzenFlag).Trim()
        if ($dzx -match '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}') {
            $dzenLinked = $true
            try { $dzenLinkedAt = [datetime]::Parse($Matches[0]) } catch { $dzenLinkedAt = $null }
        }
    }
    $script:dzenSince = 0

    $postList = @()
    foreach ($p in $posts) {
        $postList += ,[pscustomobject]@{
            d    = $p.d.ToString('yyyy-MM-ddTHH:mm:sszzz')
            date = $p.d.ToString('dd.MM.yy HH:mm')
            title = $p.title
            guid = $p.g
            img  = $p.img
            desc = $p.desc
            ch   = @{ tg = ($tgSet.ContainsKey($p.g)); fb = ($fbSet.ContainsKey($p.g)); vk = ($vkSet.ContainsKey($p.g)); ig = ($igSet.ContainsKey($p.g)); dz = ($dzenLinked -and $tgSet.ContainsKey($p.g)) }
            news = @(Get-PostNews $p $evList)
        }
        if ($dzenLinked -and $dzenLinkedAt -and $tgSet.ContainsKey($p.g) -and ($p.d -gt $dzenLinkedAt.ToUniversalTime())) { $script:dzenSince++ }
    }

    $upcoming = @($postList | Where-Object { [datetime]::Parse($_.d) -gt $now }).Count
    $posted   = @($postList | Where-Object { $_.ch.tg }).Count

    return [pscustomobject]@{
        now       = $now.ToString('yyyy-MM-ddTHH:mm:ss'+'zzz')
        generated = Get-DateStr $now
        backend   = [pscustomobject]@{
            upSince = Get-DateStr $script:startedAt
            requests = $script:requests
            port    = $Port
        }
        heartbeat = [pscustomobject]@{ alive = $hb.alive; ageSec = $hb.age }
        channels  = [pscustomobject]@{
            tg = $tgSet.Count; fb = $fbSet.Count; vk = $vkSet.Count; ig = $igSet.Count; dzen = $tgSet.Count
        }
        dzen      = [pscustomobject]@{
            linked  = $dzenLinked
            linkedAt = $(if ($dzenLinkedAt) { $dzenLinkedAt.ToString('dd.MM.yy HH:mm') } else { '' })
            tgTotal = $tgSet.Count
            since   = $script:dzenSince
        }
        counts    = [pscustomobject]@{ total = $postList.Count; posted = $posted; upcoming = $upcoming }
        scan      = [pscustomobject]@{
            lastDate  = $intel.date
            todayDone = ($intel.date -eq $todayMark)
            rows      = $intel.rows.Count
            evidence  = $evList.Count
            nextScan  = Get-NextHourly 5
            nextIntel = Get-NextHourly 20
        }
        vk        = [pscustomobject]@{ probe = Get-VkProbe }
        posts     = @($postList)
        intel     = @($intel.rows)
    }
}

# ============================== FRONTEND ==============================
function Get-FrontendHtml {
    return @'
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Astrea — AudioReclama</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--txt:#c9d1d9;--head:#f0f6fc;--muted:#8b949e;--acc:#58a6ff;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--off:#484f58}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:14px/1.45 "Segoe UI",Arial,sans-serif;padding:16px}
h1{font-size:18px;color:var(--head);margin:0 0 2px}
.sub{color:var(--muted);font-size:12px;margin-bottom:12px}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.chip{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:4px 12px;font-size:12px}
.chip b{color:var(--head)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}
.ok{background:var(--ok)}.warn{background:var(--warn)}.bad{background:var(--bad)}.off{background:#484f58}
.tabs{display:flex;gap:6px;margin-bottom:12px}
.tab{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:6px 14px;cursor:pointer;color:var(--muted)}
.tab.on{color:var(--head);border-color:var(--acc)}
.pane{display:none}.pane.on{display:block}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.month{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:14px}
.mt-empty{opacity:.45}
.mtitle{color:var(--head);font-weight:600;margin-bottom:8px}
.wd,.day{display:inline-flex;vertical-align:top;width:13.6%;min-height:64px;margin:2px 0;border:1px solid var(--line);border-radius:6px;padding:4px;position:relative;overflow:hidden}
.wd{min-height:auto;color:var(--muted);font-size:11px;text-align:center}
.empt{border-color:transparent}
.day .num{position:absolute;top:3px;right:6px;color:var(--muted);font-size:11px}
.day.today{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc) inset}
.pcell{font-size:10px;color:var(--head);padding:10px 2px 2px;word-break:break-word}
.chan{display:inline-block;width:7px;height:7px;border-radius:2px;margin:0 1px}
img.th{width:100%;max-height:56px;object-fit:cover;border-radius:4px;display:block;margin-top:2px}
.item{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin-bottom:8px}
.item .tt{font-size:13px}
.tag{color:var(--muted);font-size:11px;margin-left:6px}
.newsrow{border-top:1px solid var(--line);padding-top:6px;margin-top:6px;font-size:12px}
.newsrow .src{color:var(--muted);font-size:11px}
.upd{color:var(--warn)}
.pulse{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
.topbar{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-bottom:10px}
.swbtn{background:var(--acc);border:none;color:#fff;border-radius:8px;padding:8px 18px;font-size:14px;font-weight:600;cursor:pointer;white-space:nowrap}
.swbtn:hover{filter:brightness(1.12)}
.view{display:block}
.view.hidden{display:none}
.pubhead{color:var(--head);font-weight:600;margin:12px 0 8px;font-size:15px}
.scGrid{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.sc{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:118px}
.sc b{display:block;font-size:20px;color:var(--head)}
.sc span{font-size:11px;color:var(--muted)}
.pubtbl{width:100%;border-collapse:collapse;font-size:12px;background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.pubtbl th,.pubtbl td{border-bottom:1px solid var(--line);padding:6px 10px;text-align:left}
.pubtbl th{color:var(--muted);font-weight:600}
.pubtbl td.pst{font-weight:600;color:var(--head)}
.view[data-active="1"]{display:block}
.view[data-active="0"]{display:none}
</style>
</head>
<body>
<div id="view-main" class="view" data-active="1">
<div class="topbar">
  <div>
    <h1>Astrea <span style="color:var(--muted);font-size:12px">— единая панель AudioReclama</span></h1>
    <div class="sub">
      <span id="clk"></span> · бэкенд PID <span id="upSince"></span> · запросов <span id="req"></span>
      · сервер <span id="port"></span> · авто-опрос 10 c
    </div>
  </div>
  <div style="display:flex;gap:8px;flex-shrink:0">
    <button class="swbtn" id="btnWin" data-next="view-me">Календарь и публикации</button>
  </div>
</div>

<div class="chips" id="chips"></div>

<div class="tabs">
  <div class="tab on" data-t="cal">Календарь</div>
  <div class="tab" data-t="news">Новости</div>
  <div class="tab" data-t="posts">Посты</div>
  <div class="tab" data-t="scan">Лента сканов</div>
</div>

<div id="p-cal" class="pane on"></div>
<div id="p-news" class="pane"></div>
<div id="p-posts" class="pane"></div>
<div id="p-scan" class="pane"></div>
</div>

<div id="view-me" class="view" data-active="0">
  <div class="topbar">
    <div><h1>Публикации <span style="color:var(--muted);font-size:12px">— календарь и табло</span></h1>
    <div class="sub" id="meSub"></div></div>
    <div style="display:flex;gap:8px;flex-shrink:0">
      <button class="swbtn" id="btnMeBack">← Назад</button>
    </div>
  </div>
  <div class="pubhead">Табло</div>
  <div class="scGrid" id="meScore"></div>
  <div class="pubhead">Расписание и статусы по каналам</div>
  <div id="meTbl"></div>
  <div class="pubhead">Предпросмотр ближайших</div>
  <div id="mePrev"></div>
  <div class="pubhead">Календарь публикаций</div>
  <div id="meCal"></div>
</div>

<script>
var S = { posts:[], intel:[], channels:{}, scan:{}, heartbeat:{} };
var lastLen = 0;
function arr(x){ return Array.isArray(x) ? x : (x ? [x] : []); }
function esc(s){ return (s==null?'':String(s)).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
function chWrap(stateTitle){var c=stateTitle;return '<span class="chan" style="background:var(--'+c+')"></span>';}

function renderChips(){
  var h='';
  function chip(k,label,on){ return '<span class="chip"><span class="dot '+((S.channels[k]>0||on)?'ok':'off')+'"></span><b>'+label+'</b> '+ (+S.channels[k]||0)+'</span>'; }
  h += chip('tg','Telegram');
  var dz = S.dzen||{};
  h += '<span class="chip"><span class="dot '+(dz.linked?'ok':'off')+'"></span><b>Дзен</b> '+(dz.linked?('автокросс TG→Дзен активен с '+esc(dz.linkedAt)):'не связан')+'</span>';
  h += '<div class="sub" style="margin:8px 0 12px">Дзен — авто-зеркало Telegram на платформе Дзен (зеркалятся посты TG, включая подтянутые площадкой). Точные показы/CTR/дочиты — только в панели Дзен: у нас нет их API. Задержка репоста — платформенная.</div>';
  h += '<span class="chip"><span class="dot '+(S.heartbeat.alive?'ok':'bad')+'"></span><b>оркестратор</b> '+(S.heartbeat.alive?('жив '+S.heartbeat.ageSec+' c'):'МЁРТВ')+'</span>';
  h += '<span class="chip"><span class="dot '+(S.scan.todayDone?'ok':'warn')+'"></span><b>intel</b> '+esc(S.scan.lastDate||'—')+' ('+S.scan.rows+' строк)'+(S.scan.todayDone?'': '<span class="upd"> нет скана за сегодня</span>')+'</span>';
  h += '<span class="chip"><span class="dot '+(S.scan.nextScan?'ok':'off')+'"></span><b>скан</b> каждый час → '+esc(S.scan.nextScan)+' · intel '+esc(S.scan.nextIntel)+'</span>';
  h += '<span class="chip"><span class="dot ok"></span><b>всего постов</b> '+S.counts.total+' (на постинг '+S.counts.upcoming+', опубликовано '+S.counts.posted+')</span>';
  document.getElementById('chips').innerHTML = h;
}

function calendarHtml(){
  var mono = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
  var byMonth = {};
  S.posts.forEach(function(p){ var d=new Date(p.d); var k=d.getFullYear()+'-'+(d.getMonth()+1); (byMonth[k]=byMonth[k]||[]).push(p); });
  var today = new Date();
  var yr = today.getFullYear();
  var out = '';
  for(var mon=0; mon<12; mon++){
    var k = yr+'-'+(mon+1);
    var first=new Date(yr,mon,1); var offset=((first.getDay()+6)%7);
    var dim = new Date(yr, mon+1, 0).getDate();
    var days = (byMonth[k]||[]).slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);});
    var map={}; days.forEach(function(p){ var dd=new Date(p.d).getDate(); map[dd]=map[dd]||[]; map[dd].push(p); });
    var isEmpty = !days.length;
    out += '<div class="month'+(isEmpty?' mt-empty':'')+'"><div class="mtitle">'+mono[mon]+' '+yr+'</div>';
    ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'].forEach(function(w){ out += '<span class="wd">'+w+'</span>'; });
    for(var i=0;i<offset;i++){ out += '<span class="day empt"></span>'; }
    for(var d=1; d<=dim; d++){
      var now=new Date(yr,mon,d);
      var isToday = now.toDateString()===today.toDateString();
      out += '<span class="day'+(isToday?' today':'')+'"><span class="num">'+d+'</span>';
      (map[d]||[]).forEach(function(p){
        var chans='';
        if(p.ch.tg)chans+=chWrap('ok'); else chans+=chWrap('off');
        if(p.ch.dz)chans+=chWrap('ok'); else chans+=chWrap('off');
        var img='';
        if(p.img){ img='<img class="th" src="/img/'+esc(p.img)+'.png" alt="">'; }
        out += '<div class="pcell">'+chans+' '+esc(p.title)+img+'</div>';
      });
      out += '</span>';
    }
    out += '</div>';
  }
  return out;
}

function renderCalendar(){
  document.getElementById('p-cal').innerHTML = calendarHtml();
}

function scoreHtml(){
  var now=new Date();
  var out='';
  var posted=0,toPub=0,missed=0;
  S.posts.forEach(function(p){
    var any=p.ch.tg||p.ch.dz;
    if(any)posted++;
    else if(new Date(p.d)>now)toPub++;
    else missed++;
  });
  out+='<div class="sc"><b>'+posted+'</b><span>опубликовано</span></div>';
  out+='<div class="sc"><b>'+toPub+'</b><span>в очереди</span></div>';
  out+='<div class="sc"><b>'+missed+'</b><span>пропущено</span></div>';
  out+='<div class="sc"><b>'+S.posts.length+'</b><span>всего</span></div>';
  return out;
}

function renderMe(){
  document.getElementById('meScore').innerHTML = scoreHtml();
  document.getElementById('meTbl').innerHTML = renderMeTbl();
  document.getElementById('mePrev').innerHTML = renderMePrev();
  document.getElementById('meCal').innerHTML = calendarHtml();
}

function renderMeTbl(){
  var out='<table class="pubtbl"><tr><th>Дата</th><th>Пост</th><th>TG</th><th>ДЗ</th></tr>';
  S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).forEach(function(p){
    function cell(on){return '<span class="chan" style="width:10px;height:10px;background:var(--'+(on?'ok':'off')+')"></span>';}
    var now=new Date();
    var dat = new Date(p.d);
    out+= '<tr><td'+((dat>now)?' style="color:var(--acc)"':'')+'>'+esc(p.date)+'</td><td class="pst">'+esc(p.title)+'</td>';
    out+= '<td>'+cell(p.ch.tg)+'</td><td>'+cell(p.ch.dz)+'</td>';
    out+= '</tr>';
  });
  out+='</table>';
  return out;
}

function renderMePrev(){
  var out='';
  var now=new Date();
  var next = S.posts.slice()
    .sort(function(a,b){return new Date(a.d)-new Date(b.d);})
    .filter(function(p){ return !(p.ch.tg||p.ch.dz) && new Date(p.d)>=new Date(now.getTime()-86400000); })
    .slice(0,3);
  if(!next.length){ next = S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).slice(0,3); }
  next.forEach(function(p){
    out += '<div class="item" style="overflow:hidden">';
    if(p.img){ out += '<img style="width:150px;border-radius:6px;float:left;margin-right:12px" src="/img/'+esc(p.img)+'.png" alt="">'; }
    out += '<div class="tt">'+esc(p.title)+'</div>';
    out += '<div style="font-size:11px;color:var(--muted);margin:2px 0 4px">'+esc(p.date)+' · '+esc(p.guid)+'</div>';
    var ds = p.desc ? p.desc.replace(/\\n/g,' ') : '';
    if(ds.length>400){ ds = ds.slice(0,397)+'...'; }
    out += '<div style="font-size:12px;color:var(--head)">'+esc(ds)+'</div>';
    out += '</div>';
  });
  if(!next.length){ out='<div class="sub">постов нет</div>'; }
  return out;
}

function renderNews(){
  var out='<div class="sub">первоисточники, на которые ссылаются посты (из evidence)</div>';
  S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).forEach(function(p){
    var n = arr(p.news);
    out += '<div class="item"><div class="tt">'+esc(p.date)+' · '+esc(p.title)+'</div>';
    n.forEach(function(x){
      out += '<div class="newsrow"><a href="'+esc(x.url)+'" target="_blank" rel="noopener">'+esc(x.title)+'</a> <span class="src">· '+esc(x.file)+'</span></div>';
    });
    out += '</div>';
  });
  document.getElementById('p-news').innerHTML = out;
}

function renderPosts(){
  var out='';
  S.posts.slice().sort(function(a,b){return new Date(a.d)-new Date(b.d);}).forEach(function(p){
    var chans='';
    function cd(k,nm){ return '<span class="chip"><span class="dot '+((p.ch[k])?'ok':'off')+'"></span>'+nm+'</span>'; }
    chans=cd('tg','TG')+cd('dz','ДЗ');
    var img='';
    if(p.img){ img='<img style="width:110px;border-radius:6px;float:left;margin-right:10px" src="/img/'+esc(p.img)+'.png" alt="">'; }
    out += '<div class="item" style="overflow:hidden">'+img+'<div class="tt">'+esc(p.title)+'</div><div style="font-size:11px;color:var(--muted);margin:2px 0 4px">'+esc(p.date)+' · '+esc(p.guid)+'</div>'+chans+'</div>';
  });
  document.getElementById('p-posts').innerHTML = out;
}

function renderScan(){
  var out='<div class="sub">свежие сканы (intel · '+esc(S.scan.lastDate||'—')+') · '+S.scan.rows+' строк · evidence '+esc(S.scan.evidence)+'</div>';
  arr(S.intel).forEach(function(r){
    out += '<div class="item"><a href="'+esc(r.url)+'" target="_blank" rel="noopener">'+esc(r.title)+'</a><span class="tag">'+esc(r.src)+' · t'+esc(r.tier)+' · score '+esc(r.score)+'</span></div>';
  });
  document.getElementById('p-scan').innerHTML = out;
}

function renderAll(){
  renderChips(); renderCalendar(); renderNews(); renderPosts(); renderScan(); renderMe();
  var g=S.generated||S.now||'';
  var u=document.querySelector('.sub');
  document.getElementById('clk').textContent = new Date().toLocaleTimeString('ru-RU')+' · обновлено '+g;
  document.getElementById('upSince').textContent = S.backend?S.backend.upSince:'';
  document.getElementById('req').textContent = S.backend?S.backend.requests:'';
  document.getElementById('port').textContent = S.backend?S.backend.port:'';
  document.getElementById('meSub').textContent = 'сводка на '+new Date().toLocaleString('ru-RU')+' · обновлено '+g+ (S.backend?' · бэкенд PID '+S.backend.upSince:'');
}

function poll(){
  fetch('/api/state.json').then(function(r){return r.json();}).then(function(s){
    var sig=JSON.stringify(s).length;
    if(sig!==lastLen){ lastLen=sig; S=s; renderAll(); }
  }).catch(function(){ });
}

document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('on');});
    document.querySelectorAll('.pane').forEach(function(x){x.classList.remove('on');});
    t.classList.add('on');
    document.getElementById('p-'+t.getAttribute('data-t')).classList.add('on');
  });
});

function switchWin(showId){
  var wins = ['view-main','view-me'];
  wins.forEach(function(w){
    var el = document.getElementById(w);
    if(w===showId){ el.setAttribute('data-active','1'); }
    else { el.setAttribute('data-active','0'); }
  });
  document.getElementById('btnWin').dataset.next = (showId==='view-me' ? 'view-main' : 'view-me');
}
document.getElementById('btnWin').addEventListener('click', function(){
  var nxt = document.getElementById('btnWin').dataset.next || 'view-me';
  switchWin(nxt);
});
document.getElementById('btnMeBack').addEventListener('click', function(){ switchWin('view-main'); });
poll();
setInterval(poll, 10000);
</script>
</body>
</html>
'@
}

# ============================== HTTP SERVER ==============================
function Send-Raw([System.Net.Sockets.NetworkStream]$ns, [string]$status, [string]$ctype, [byte[]]$body) {
    $heads = "HTTP/1.1 $status`r`nConnection: close`r`nContent-Type: $ctype`r`nContent-Length: $($body.Length)`r`nCache-Control: no-store`r`n`r`n"
    $hb = [System.Text.Encoding]::ASCII.GetBytes($heads)
    $ns.Write($hb, 0, $hb.Length)
    $ns.Write($body, 0, $body.Length)
    $ns.Flush()
}

function Get-RequestPath([System.Net.Sockets.NetworkStream]$ns) {
    $sb = New-Object System.Text.StringBuilder
    $buf = New-Object byte[] 8192
    $read = $false
    $mp = $false
    while (-not $read) {
        try {
            $n = $ns.Read($buf, 0, $buf.Length)
        } catch { return '' }
        if ($n -le 0) { return '' }
        [void]$sb.Append([System.Text.Encoding]::ASCII.GetString($buf, 0, $n))
        $s = $sb.ToString()
        $eoh = $s.IndexOf("`r`n`r`n")
        if ($eoh -ge 0) { $headOnly = $s.Substring(0, $eoh); $read = $true }
        if ($s.Length -gt 65536) { $mp = $true; $read = $true }
    }
    $first = ($headOnly -split "`r`n")[0]
    $parts = $first -split ' '
    if ($parts.Count -lt 2) { return '' }
    return $parts[1]
}

function Serve-Client([System.Net.Sockets.TcpClient]$client) {
    try {
        $ns = $client.GetStream()
        $path = Get-RequestPath $ns
        if (-not $path) { $client.Close(); return }
        $bodyHead = $null
        if ($path -eq '/' -or $path -eq '/index.html') {
            $html = Get-FrontendHtml
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($html)
            Send-Raw $ns '200 OK' 'text/html; charset=utf-8' $bytes
        }
        elseif ($path -eq '/api/state.json') {
            $st = Build-State
            $json = $st | ConvertTo-Json -Depth 8 -Compress
            $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
            Send-Raw $ns '200 OK' 'application/json; charset=utf-8' $bytes
        }
        elseif ($path -match '^/img/([A-Za-z0-9_\-\.]+)$') {
            $name = $Matches[1]
            if ($name -match '\.\.') { Send-Raw $ns '403 Forbidden' 'text/plain' ([System.Text.Encoding]::UTF8.GetBytes('forbidden')) }
            else {
                $img = Join-Path (Join-Path $feed 'images') $name
                if (Test-Path -LiteralPath $img) {
                    $bytes = [System.IO.File]::ReadAllBytes($img)
                    Send-Raw $ns '200 OK' 'image/png' $bytes
                } else {
                    Send-Raw $ns '404 Not Found' 'text/plain' ([System.Text.Encoding]::UTF8.GetBytes('not found'))
                }
            }
        }
        else {
            Send-Raw $ns '404 Not Found' 'text/plain' ([System.Text.Encoding]::UTF8.GetBytes('not found'))
        }
    } catch { }
    try { $client.Close() } catch { }
}

Write-Output ("ASTREA listening on http://" + $bind + ":" + $Port)
$listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Parse('127.0.0.1'), $Port)
$listener.Start()
if (-not $NoOpen) { try { Start-Process ('http://127.0.0.1:' + $Port) } catch { } }
while ($true) {
    try {
        $client = $listener.AcceptTcpClient()
        Serve-Client $client
    } catch { Start-Sleep -Milliseconds 200 }
}