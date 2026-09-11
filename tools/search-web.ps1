# search-web.ps1 - web search via DuckDuckGo HTML (no API key), works with 403-blocked
# search providers. Writes results to a UTF-8 JSON file.
# Usage: powershell -File search-web.ps1 -Query "UMG ElevenLabs AI" -Out results.json [-Max 8] [-Proxy socks5h://127.0.0.1:10808]
param(
    [Parameter(Mandatory = $true)][string]$Query,
    [Parameter(Mandatory = $true)][string]$Out,
    [int]$Max = 8,
    [string]$Proxy = ''
)

$script:ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

function Invoke-DdgSearch([string]$qenc, [string]$proxy) {
    $url = 'https://html.duckduckgo.com/html/?q=' + $qenc
    if ($proxy) {
        return & curl.exe --max-time 20 -s -x $proxy -A $script:ua $url 2>$null
    }
    return & curl.exe --max-time 20 -s -A $script:ua $url 2>$null
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

$qenc = [System.Uri]::EscapeDataString($Query)
$res = @()
for ($try = 0; $try -lt 2 -and $res.Count -eq 0; $try++) {
    $html = Invoke-DdgSearch $qenc $Proxy
    $res = Get-Results $html
    Start-Sleep -Seconds 3
}
if (-not $Proxy) {
    foreach ($fallback in @('socks5h://127.0.0.1:10808')) {
        if ($res.Count -gt 0) { break }
        $html = Invoke-DdgSearch $qenc $fallback
        $res = Get-Results $html
    }
}
if ($res.Count -gt $Max) { $res = $res | Select-Object -First $Max }
$payload = @{ query = $Query; provider = 'duckduckgo-html'; ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); count = $res.Count; results = $res }
$json = $payload | ConvertTo-Json -Depth 4 -Compress
[System.IO.File]::WriteAllText($Out, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Output ("SEARCH '" + $Query + "' -> " + $res.Count + " results -> " + $Out)