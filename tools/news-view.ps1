# news-view.ps1 - separate view of the NEWS each post will link to.
# Sources: feed/items.csv (posts), evidence/*.md (verified sources with primary URLs),
# reports/intel/intel-*.json (latest scan feed). Output: news-view.html.
$ErrorActionPreference = 'Continue'
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$base = 'F:\Pill\tmp\opencode'
$secrets = Join-Path $base 'secrets'
$repo = Join-Path $base 'sonic-repo'
$feed = Join-Path $repo 'feed'
$state = Join-Path $repo 'state'
$out = Join-Path $repo 'news-view.html'
$rc = [System.Globalization.CultureInfo]::InvariantCulture

# ---- posts ----
$posts = @()
foreach ($row in [System.IO.File]::ReadAllLines((Join-Path $feed 'items.csv'))) {
    if (-not $row -or $row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    $dt = $null
    try { $dt = [datetime]::ParseExact($p[0].Trim(), 'r', $rc) } catch { }
    if (-not $dt) { continue }
    $posts += ,[pscustomobject]@{ d = $dt; title = $p[1]; g = $p[4]; img = $p[5]; src = $p[3] }
}
$posts = @($posts | Sort-Object d)

# ---- evidence map ----
$evFiles = @(Get-ChildItem (Join-Path $repo 'evidence') -Filter 'E-*.md' -ErrorAction SilentlyContinue)
$evidence = @()
foreach ($f in $evFiles) {
    $txt = [System.IO.File]::ReadAllText($f.FullName)
    $lines = $txt -split "`r?`n"
    $title = ($lines | Where-Object { $_ -match '^# ' } | Select-Object -First 1) -replace '^#\s*', ''
    $desc = ''
    $inShort = $false
    foreach ($ln in $lines) {
        if ($ln -match '^Short statement') { $inShort = $true; continue }
        if ($inShort) {
            if ($ln -match '^Source') { $inShort = $false }
            elseif ($ln.Trim()) { $desc += $ln.Trim() + ' ' }
        }
    }
    $urls = @([regex]::Matches($txt, 'https?://[^\s)\]]+') |
        ForEach-Object { $_.Value.TrimEnd('.', ',') } |
        Where-Object { $_ -notmatch 'github.com/AudioReclamaRu' -and $_ -notmatch 'audio-reclama.ru' } |
        Select-Object -Unique)
    if ($urls.Count -eq 0) { $urls += ('https://github.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/evidence/' + $f.Name) }
    if (-not $desc) { $desc = $title }
    if ($desc.Length -gt 160) { $desc = $desc.Substring(0, 157) + '...' }
    $evidence += ,[pscustomobject]@{ file = $f.Name; title = $title; desc = $desc; urls = @($urls); raw = $txt }
}

# ---- relate posts to evidence ----
function Post-News([pscustomobject]$post) {
    $srcPath = ($post.src -replace 'https://github.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/', '')
    $srcName = ($srcPath -split '/')[-1]
    $hits = @()
    foreach ($e in $evidence) {
        if ($e.file -eq $srcName) { $hits += $e }
        elseif ($e.raw -match [regex]::Escape($srcPath)) { $hits += $e }
    }
    if ($hits.Count -eq 0) { $hits = @($evidence | Where-Object { $_.raw -match [regex]::Escape($srcName) }) }
    $news = @()
    $seen = @{}
    $seenHits = @{}
    $dedupHits = @()
    foreach ($hh in $hits) { if (-not $seenHits.ContainsKey($hh.file)) { $seenHits[$hh.file] = $true; $dedupHits += $hh } }
    foreach ($e in $dedupHits) {
        foreach ($u in $e.urls) {
            if ($seen.ContainsKey($u)) { continue }
            $seen[$u] = $true
            $news += ,[pscustomobject]@{ url = $u; title = $e.desc; file = $e.file; post = $post.title }
        }
    }
    if ($news.Count -eq 0) {
        $news += ,[pscustomobject]@{ url = $post.src; title = $post.title; file = $srcName; post = $post.title }
    }
    return ,$news
}

# ---- latest intel / scan feed ----
$intelLatest = @(Get-ChildItem (Join-Path $repo 'reports\intel') -Filter 'intel-*.json' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1)
$intelRows = @()
$intelDate = ''
if ($intelLatest) {
    try {
        $j = Get-Content $intelLatest.FullName -Raw | ConvertFrom-Json
        $intelDate = $j.date
        $intelRows = @($j.rows | Where-Object { $_.title } | Sort-Object score -Descending | Select-Object -First 15)
    } catch { }
}

$cardHtml = ''
foreach ($post in $posts) {
    $img = Join-Path (Join-Path $feed 'images') ($post.img + '.png')
    $thumb = ''
    if (Test-Path -LiteralPath $img) { $thumb = '<img class="th" src="feed/images/' + ([System.Net.WebUtility]::HtmlEncode($post.img)) + '.png" alt="">' }
    $news = Post-News $post
    $newsHtml = ''
    $seen2 = @{}
    foreach ($n in $news) {
        if ($seen2.ContainsKey($n.url)) { continue }
        $seen2[$n.url] = $true
        $evTxt = if ($n.file -match '^E-') { 'evidence ' + $n.file.TrimEnd('.md') } else { $n.file }
        $link = '<a href="' + ([System.Net.WebUtility]::HtmlEncode($n.url)) + '" target="_blank" rel="noopener">' + ([System.Net.WebUtility]::HtmlEncode($n.title)) + '</a>'
        $evLink = '<a class="ev" href="https://github.com/AudioReclamaRu/sonic-infrastructure-report/blob/main/evidence/' + ([System.Net.WebUtility]::HtmlEncode($n.file)) + '" target="_blank" rel="noopener">' + $evTxt + '</a>'
        $newsHtml += '<div class="news"><div class="nw">' + $link + '</div><div class="meta">' + $evLink + '</div></div>'
    }
    $cardHtml += '<div class="card"><div class="head"><span class="when">' + $post.d.ToString('dd.MM.yy HH:mm') + '</span><span>' + ([System.Net.WebUtility]::HtmlEncode($post.title)) + '</span></div><div class="body">' + $thumb + '<div class="newslist">' + $newsHtml + '</div></div></div>' + "`n"
}

$intelHtml = ''
foreach ($r in $intelRows) {
    $tier = if ($r.tier) { $r.tier } else { '' }
    $score = if ($r.score) { $r.score } else { '' }
    $src = if ($r.src) { $r.src } else { '' }
    $intelHtml += '<div class="in"><a class="iurl" href="' + ([System.Net.WebUtility]::HtmlEncode($r.url)) + '" target="_blank" rel="noopener">' + ([System.Net.WebUtility]::HtmlEncode($r.title)) + '</a><span class="itag">' + $src + ' t' + $tier + ' score ' + $score + '</span></div>' + "`n"
}

$nowLine = (Get-Date).ToString('dd.MM.yy HH:mm:ss')

$html = @"
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="120">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AudioReclama — новости под посты</title>
<style>
body{background:#0d1117;color:#c9d1d9;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:20px}
h1{font-size:18px;color:#f0f6fc;margin:0 0 2px 0}
.sub{color:#8b949e;font-size:12px;margin-bottom:14px}
a{color:#58a6ff;text-decoration:none}
a:hover{text-decoration:underline}
.nav{font-size:12px;margin-bottom:12px}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px;margin-bottom:12px}
.card .head{font-size:14px;font-weight:600;color:#f0f6fc;margin-bottom:8px}
.card .when{color:#8b949e;font-size:11px;margin-right:8px;font-weight:400}
.card .body{display:flex;gap:12px}
img.th{width:130px;border-radius:8px;flex-shrink:0}
.newslist{flex:1}
.news{padding:6px 0;border-bottom:1px solid #21262d}
.news:last-child{border-bottom:none}
.news .nw{font-size:13px}
.news .meta{margin-top:2px}
a.ev{color:#8b949e;font-size:11px}
h2{font-size:15px;color:#f0f6fc;margin:18px 0 8px 0}
.in{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:13px}
.itag{color:#8b949e;font-size:11px;margin-left:8px}
.foot{color:#484f58;font-size:11px;margin-top:14px}
</style>
</head>
<body>
<h1>AudioReclama — новости, на которые ссылаются посты</h1>
<div class="sub">обновлено $nowLine | авто-обновление каждые 120 c</div>
<div class="nav"><a href="calendar-view.html">&larr; календарь постов</a></div>
$cardHtml
<h2>Лента свежих сканов ($intelDate)</h2>
$intelHtml
<div class="foot">источники: feed/items.csv, evidence/E-*.md (первичные URL), reports/intel/intel-*.json. Генератор: tools/news-view.ps1.</div>
</body>
</html>
"@

[System.IO.File]::WriteAllText($out, $html, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("NEWSVIEW -> " + $out)
