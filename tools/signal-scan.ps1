# signal-scan.ps1 - daily market scan: HN Algolia + DuckDuckGo web search
# Writes: repo reports/scans/scans-<date>.md + tg scan json at $ScanDir/<date>.json
# ASCII-only source. Run daily via scheduled task.
$ErrorActionPreference = 'Continue'

$root = Split-Path -Parent $PSScriptRoot
$repo = 'F:\Pill\tmp\opencode\sonic-repo'
$scanMdDir = Join-Path $repo 'reports\scans'
$scanJsonDir = 'F:\Pill\tmp\opencode\tg\scan'
if (-not (Test-Path $scanMdDir)) { New-Item -ItemType Directory -Path $scanMdDir -Force | Out-Null }
if (-not (Test-Path $scanJsonDir)) { New-Item -ItemType Directory -Path $scanJsonDir -Force | Out-Null }

$todayMark = Get-Date -Format 'yyyy-MM-dd'
$mdPath = Join-Path $scanMdDir ("scans-" + $todayMark + '.md')
$jsonPath = Join-Path $scanJsonDir ($todayMark + '.json')

$hnQueries = @('voice AI market', 'AI voice cloning', 'elevenlabs', 'text to speech news', 'voice actor AI')
$webQueries = @('UMG ElevenLabs AI voice licensing', 'AI voice market 2026', 'voice cloning news')

$script:items = @()

function Add-MdLine([string]$t) {
    Add-Content -Path $mdPath -Value $t -Encoding UTF8
}

Add-MdLine ("# Market scan - " + $todayMark)
Add-MdLine ("Generated: " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Add-MdLine ''

function Parse-Hn([string]$query) {
    $u = 'https://hn.algolia.com/api/v1/search?query=' + [System.Uri]::EscapeDataString($query) + '&tags=story&hitsPerPage=6'
    $r = curl.exe --max-time 20 -s $u 2>$null
    $o = $null
    try { $o = $r | ConvertFrom-Json } catch { }
    if (-not $o -or -not $o.hits) { return }
    foreach ($h in $o.hits) {
        if (-not $h.title) { continue }
        if ($h.points -lt 10) { continue }
        $link = if ($h.url) { $h.url } else { 'https://news.ycombinator.com/item?id=' + $h.objectID }
        $dt = if ($h.created_at_i) { ([DateTimeOffset]::FromUnixTimeSeconds($h.created_at_i)).DateTime.ToString('yyyy-MM-dd HH:mm') } else { '' }
        $it = @{ src = 'HN'; title = $h.title; url = $link; points = $h.points; comments = $h.num_comments; ts = $dt; query = $query }
        $script:items += $it
    }
}

function Parse-Web([string]$query) {
    $tmp = Join-Path $env:TEMP ("ddg_" + [guid]::NewGuid().ToString('N') + '.json')
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'search-web.ps1') -Query $query -Out $tmp -Max 5 2>$null
    if (-not (Test-Path $tmp)) { return }
    $o = Get-Content $tmp -Raw -Encoding UTF8 | ConvertFrom-Json
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
foreach ($res in $o.results) {
        if (-not $res.url) { continue }
        if ($res.url -match 'duckduckgo\.com/y\.js|bing\.com/aclick|ad_domain=') { continue }
        $it = @{ src = 'WEB'; title = $res.title; url = $res.url; points = 0; comments = 0; ts = ''; snippet = $res.snippet; query = $query }
        $script:items += $it
    }
}

# DEDUPE helper
function Add-Item([hashtable]$it) {
    foreach ($e in $items) {
        if ($e.url -eq $it.url) { return }
    }
    $script:items += $it
}

foreach ($q in $hnQueries) { Parse-Hn $q; Start-Sleep -Seconds 2 }
foreach ($q in $webQueries) { Parse-Web $q; Start-Sleep -Seconds 5 }

# dedupe in place
$seen = @{}
$uniqueList = @()
foreach ($it in $items) {
    $key = $it.url
    if (-not $seen.ContainsKey($key)) {
        $seen[$key] = $true
        $uniqueList += $it
    }
}
$items = $uniqueList

Add-MdLine ("## HN (Hacker News, points>=10)")
Add-MdLine ''
$hnItems = $items | Where-Object { $_.src -eq 'HN' } | Sort-Object points -Descending
foreach ($i in $hnItems) {
    Add-MdLine ("- [" + $i.points + " pts | " + $i.comments + " cmt] " + $i.title + " (" + $i.url + ")  " + $i.ts)
}
Add-MdLine ''
Add-MdLine '## Web (DuckDuckGo)'
Add-MdLine ''
$webItems = $items | Where-Object { $_.src -eq 'WEB' }
foreach ($i in $webItems) {
    Add-MdLine ("- " + $i.title + "`n  " + $i.url + "  " + $i.snippet)
}
Add-MdLine ''

$jsonPayload = @{ date = $todayMark; total = $items.Count; items = $items }
[System.IO.File]::WriteAllText($jsonPath, ($jsonPayload | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("SCAN " + $todayMark + ": " + $items.Count + " items (HN=" + $hnItems.Count + " WEB=" + $webItems.Count + ") -> " + $mdPath)

