# search-web.ps1 - web search: Bing News RSS (primary) with DuckDuckGo HTML fallback.
# No API key. Writes results to a UTF-8 JSON file.
# All direct HTML engines (DDG, Mojeek) are anti-bot challenged (HTTP 202 / altcha);
# Bing News RSS is reliable via xray-proxy and returns real publisher links + pubDate.
# DDG is kept as an opt-in fallback for broad (non-news) results: -Provider auto|bing|ddg.
# Usage: powershell -File search-web.ps1 -Query "UMG ElevenLabs AI" -Out results.json [-Max 8] [-Proxy socks5h://127.0.0.1:10808] [-Provider auto]
param(
    [Parameter(Mandatory = $true)][string]$Query,
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$Max = 8,
    [string]$Proxy = '',
    [string]$Provider = 'auto',
    [string]$Market = ''
)

$script:ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

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

function Invoke-DdgSearch([string]$qenc, [string]$proxy) {
    $url = 'https://html.duckduckgo.com/html/?q=' + $qenc
    if ($proxy) {
        return Invoke-Curl ("--max-time 20 -s -x `"$proxy`" -A `"$script:ua`" `"$url`"")
    }
    return Invoke-Curl ("--max-time 20 -s -A `"$script:ua`" `"$url`"")
}

function Get-Results([string]$html) {
    $out = @()
    if (-not $html) { return $out }
    $titleMatches = [regex]::Matches($html, '<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', 'Singleline')
    $snippetMatches = [regex]::Matches($html, '<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', 'Singleline')
    for ($i = 0; $i -lt $titleMatches.Count; $i++) {
        $href = [System.Net.WebUtility]::HtmlDecode($titleMatches[$i].Groups[1].Value)
        if ($href -match '^//duckduckgo\.com/l/\?uddg=([^&]+)') {
            $href = [System.Net.WebUtility]::UrlDecode($Matches[1])
        }
        $title = [System.Net.WebUtility]::HtmlDecode($titleMatches[$i].Groups[2].Value)
        $title = [regex]::Replace($title, '<[^>]+>', '')
        $title = ($title -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ' '
        $snippet = ''
        if ($i -lt $snippetMatches.Count) {
            $snippet = [System.Net.WebUtility]::HtmlDecode($snippetMatches[$i].Groups[1].Value)
            $snippet = [regex]::Replace($snippet, '<[^>]+>', ' ')
            $snippet = ($snippet -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ' '
        }
        $t = @{ title = $title; url = $href; snippet = $snippet }
        $out += $t
    }
    return $out
}

function Invoke-BingNews([string]$qenc, [string]$proxy, [string]$market) {
    $url = 'https://www.bing.com/news/search?q=' + $qenc + '&format=RSS'
    if ($market) { $url += '&mkt=' + $market }
    if ($proxy) {
        return Invoke-Curl ("--max-time 25 -s -x `"$proxy`" -A `"$script:ua`" `"$url`"")
    }
    return Invoke-Curl ("--max-time 25 -s -A `"$script:ua`" `"$url`"")
}

function Get-BingResults([string]$xml) {
    $out = @()
    if (-not $xml -or $xml.Length -lt 200) { return $out }
    try { $doc = [xml]$xml } catch { return $out }
    $items = $doc.rss.channel.item
    if (-not $items) { return $out }
    foreach ($it in $items) {
        $link = [string]$it.link
        if (-not $link) { continue }
        if ($link -match 'url=([^&]+)') { $link = [System.Net.WebUtility]::UrlDecode($Matches[1]) }
        $title = [string]$it.title
        $snippet = [string]$it.description
        $snippet = [regex]::Replace($snippet, '<[^>]+>', ' ')
        $snippet = ($snippet -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ' '
        $date = ''
        $d = [DateTime]::MinValue
        if ([DateTime]::TryParse(([string]$it.pubDate), [ref]$d)) { $date = $d.ToString('yyyy-MM-dd HH:mm:ss') }
        $src = ''
        try { if ($it.Source) { $src = [string]$it.Source.'#text' } } catch {}
        if (-not $src -and $it.Source) { $src = [string]$it.Source }
        $out += @{ title = $title; url = $link; snippet = $snippet; date = $date; source = $src }
    }
    return $out
}

$qenc = [System.Uri]::EscapeDataString($Query)
$script:defaultProxy = 'socks5h://127.0.0.1:10808'
$useProxy = $Proxy
if (-not $useProxy) { $useProxy = $script:defaultProxy }
$res = @()
$provUsed = ''

if ($Provider -eq 'bing' -or $Provider -eq 'auto') {
    $xml = Invoke-BingNews $qenc $useProxy $Market
    $res = @(Get-BingResults $xml)
    if ($res.Count -gt 0) { $provUsed = 'bing-news-rss' }
}

if ($res.Count -eq 0 -and ($Provider -eq 'ddg' -or $Provider -eq 'auto')) {
    foreach ($px in @($Proxy, $script:defaultProxy)) {
        if ($res.Count -gt 0) { break }
        $html = Invoke-DdgSearch $qenc $px
        $res = @(Get-Results $html)
        if ($res.Count -gt 0) { $provUsed = 'duckduckgo-html'; break }
    }
}

if ($res.Count -gt $Max) { $res = @($res | Select-Object -First $Max) }
$payload = @{ query = $Query; provider = $provUsed; ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); count = $res.Count; results = $res }
$json = $payload | ConvertTo-Json -Depth 4 -Compress
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("SEARCH '" + $Query + "' -> " + $res.Count + " results (" + $provUsed + ") -> " + $Out)