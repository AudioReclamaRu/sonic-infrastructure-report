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

# X12: domain -> event_geo heuristic (initial categorization; refined in lead-intent)
$script:domainGeoMap = @{
    'foxnews.com'='USA'; 'cnn.com'='USA'; 'latimes.com'='USA'
    'variety.com'='USA'; 'techcrunch.com'='USA'; 'theverge.com'='USA'
    'wired.com'='USA'; 'masslive.com'='USA'; 'business20channel.tv'='USA'
    'pulse2.com'='USA'; 'vff.ai'='USA'; 'pondero.ai'='USA'
    'radiofacts.media'='USA'; 'musicnews.com'='USA'
    'ssrs.com'='USA'; 'sagaftra.org'='USA'; 'aws.amazon.com'='USA'
    'elevenlabs.io'='USA'; 'voicecloneai.app'='USA'
    'thebusinessresearchcompany.com'='USA'; 'grandviewresearch.com'='USA'
    'globalgrowthinsights.com'='USA'; 'ringly.io'='USA'
    'assemblyai.com'='USA'; 'famulor.io'='USA'; 'sitebard.com'='USA'
    'bbc.com'='UK'; 'bbc.co.uk'='UK'; 'theguardian.com'='UK'
    'eur-lex.europa.eu'='EU'; 'fia-actors.com'='EU'
    'speko.ai'='GLOBAL'; 'github.com'='GLOBAL'; 'ecency.com'='GLOBAL'
    'news.un.org'='GLOBAL'
}
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

function Get-EventGeo([string]$url) {
    if (-not $url) { return 'UNDETERMINED' }
    $m = [regex]::Match($url, 'https?://([^/]+)')
    if (-not $m.Success) { return 'UNDETERMINED' }
    $hostName = $m.Groups[1].Value -replace '^www\.|^www2\.', ''
    $parts = $hostName.Split('.')
    $dom = ''
    if ($parts.Count -ge 2) { $dom = $parts[$parts.Count - 2] + '.' + $parts[$parts.Count - 1] }
    if ($script:domainGeoMap.ContainsKey($dom)) { return $script:domainGeoMap[$dom] }
    return 'UNDETERMINED'
}
function Get-SourceLang([string]$text) {
    if (-not $text) { return 'EN' }
    if ($text -match '[\u0400-\u04FF]') { return 'RU' }
    return 'EN'
}

function Add-MdLine([string]$t) {
    Add-Content -Path $mdPath -Value $t -Encoding UTF8
}

Add-MdLine ("# Market scan - " + $todayMark)
Add-MdLine ("Generated: " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
Add-MdLine ''

function Parse-Hn([string]$query) {
    $u = 'https://hn.algolia.com/api/v1/search?query=' + [System.Uri]::EscapeDataString($query) + '&tags=story&hitsPerPage=6'
    $r = Invoke-Curl ("--max-time 20 -s `"$u`"")
    $o = $null
    try { $o = $r | ConvertFrom-Json } catch { }
    if (-not $o -or -not $o.hits) { return }
    foreach ($h in $o.hits) {
        if (-not $h.title) { continue }
        if ($h.points -lt 10) { continue }
        $link = if ($h.url) { $h.url } else { 'https://news.ycombinator.com/item?id=' + $h.objectID }
        $dt = if ($h.created_at_i) { ([DateTimeOffset]::FromUnixTimeSeconds($h.created_at_i)).DateTime.ToString('yyyy-MM-dd HH:mm') } else { '' }
        $it = @{ src = 'HN'; title = $h.title; url = $link; points = $h.points; comments = $h.num_comments; ts = $dt; query = $query; event_geo = Get-EventGeo $link; source_language = Get-SourceLang $h.title }
        $script:items += $it
    }
}

function Parse-Web([string]$query) {
    $tmp = Join-Path $env:TEMP ("ddg_" + [guid]::NewGuid().ToString('N') + '.json')
    & powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'search-web.ps1') -Query $query -Out $tmp -Max 5 2>$null
    if (-not (Test-Path $tmp)) { return }
    $o = Get-Content $tmp -Raw -Encoding UTF8 | ConvertFrom-Json
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
foreach ($res in $o.results) {
        if (-not $res.url) { continue }
        if ($res.url -match 'duckduckgo\.com/y\.js|bing\.com/aclick|ad_domain=') { continue }
        $it = @{ src = 'WEB'; title = $res.title; url = $res.url; points = 0; comments = 0; ts = ''; snippet = $res.snippet; query = $query; event_geo = Get-EventGeo $res.url; source_language = Get-SourceLang $res.title }
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
    Add-MdLine ("- [" + $i.points + " pts | " + $i.comments + " cmt] " + $i.title + " (" + $i.url + ")  " + $i.ts + "  event_geo=" + $i.event_geo + " source_language=" + $i.source_language)
}
Add-MdLine ''
Add-MdLine '## Web (DuckDuckGo)'
Add-MdLine ''
$webItems = $items | Where-Object { $_.src -eq 'WEB' }
foreach ($i in $webItems) {
    Add-MdLine ("- " + $i.title + "  event_geo=" + $i.event_geo + " source_language=" + $i.source_language + "`n  " + $i.url + "  " + $i.snippet)
}
Add-MdLine ''

$jsonPayload = @{ date = $todayMark; total = $items.Count; items = $items }
[System.IO.File]::WriteAllText($jsonPath, ($jsonPayload | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))

# ---- connect scan to feed: append NEW leads (dedupe vs evidence/items/leads) ----
function New-CollectKnownLinks {
    $known = @{}
    $evDir = Join-Path $repo 'evidence'
    if (Test-Path $evDir) {
        foreach ($f in (Get-ChildItem $evDir -Filter '*.md')) {
            $txt = [System.IO.File]::ReadAllText($f.FullName)
            foreach ($m in ([regex]::Matches($txt, 'https?://[^\s\)\]>]+'))) {
                $known[$m.Value.TrimEnd('.', ',', ')', ']', '>')] = $true
            }
        }
    }
    $csv = Join-Path $repo 'feed\items.csv'
    if (Test-Path $csv) {
        foreach ($row in [System.IO.File]::ReadAllLines($csv)) {
            $p = $row -split '~~~'
            if ($p.Count -ge 4 -and $p[3] -match '^https?://') { $known[$p[3].Trim()] = $true }
        }
    }
    $leads = Join-Path $repo 'feed\leads.csv'
    if (Test-Path $leads) {
        foreach ($row in [System.IO.File]::ReadAllLines($leads)) {
            $p = $row -split '~~~'
            if ($p.Count -ge 1 -and $p[0] -match '^https?://') { $known[$p[0].Trim()] = $true }
        }
    }
    return $known
}
$knownLinks = New-CollectKnownLinks
$leadsPath = Join-Path $repo 'feed\leads.csv'
if (-not (Test-Path $leadsPath)) {
    [System.IO.File]::WriteAllText($leadsPath, "URL~~~TITLE~~~SRC~~~POINTS~~~TS`n", (New-Object System.Text.UTF8Encoding($false)))
}
$newLeads = 0
foreach ($i in $items) {
    $u = $i.url.Trim()
    if ($knownLinks.ContainsKey($u)) { continue }
    $title = (($i.title -replace '\s+', ' ').Trim())
    [System.IO.File]::AppendAllText($leadsPath, ($u + '~~~' + $title + '~~~' + $i.src + '~~~' + $i.points + '~~~' + $i.ts + "`n"), (New-Object System.Text.UTF8Encoding($false)))
    $knownLinks[$u] = $true
    $newLeads++
}

Write-Output ("SCAN " + $todayMark + ": " + $items.Count + " items (HN=" + $hnItems.Count + " WEB=" + $webItems.Count + " NEW_LEADS=" + $newLeads + ") -> " + $mdPath)

