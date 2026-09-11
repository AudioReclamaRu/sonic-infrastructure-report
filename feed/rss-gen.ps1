# regenerate feed/rss.xml from feed/items.csv
# csv rows: TITLE~~~... | DESC~~~... | pubDate~~~title~~~description~~~link~~~guid
$src = Join-Path $PSScriptRoot 'items.csv'
$dst = Join-Path $PSScriptRoot 'rss.xml'

function Esc([string]$s) {
    $s.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;')
}

$title = 'Signals: voice market'
$desc = 'Verified voice-market signals, evidence, falsifiers (Audio-Reclama).'
$rows = Get-Content $src -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') }

foreach ($l in $rows) {
    $p = $l -split '~~~'
    if ($p[0] -eq 'TITLE') { $title = $p[1]; continue }
    if ($p[0] -eq 'DESC') { $desc = $p[1]; continue }
}

$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('<?xml version="1.0" encoding="UTF-8"?>')
[void]$sb.AppendLine('<rss version="2.0"><channel>')
[void]$sb.AppendLine('<title>' + (Esc $title) + '</title>')
[void]$sb.AppendLine('<link>https://audio-reclama.ru</link>')
[void]$sb.AppendLine('<description>' + (Esc $desc) + '</description>')
[void]$sb.AppendLine('<language>ru</language>')
foreach ($l in $rows) {
    $p = $l -split '~~~'
    if ($p[0] -eq 'TITLE' -or $p[0] -eq 'DESC') { continue }
    if ($p.Count -lt 5) { continue }
    [void]$sb.AppendLine('<item>')
    [void]$sb.AppendLine('<title>' + (Esc $p[1]) + '</title>')
    [void]$sb.AppendLine('<link>' + (Esc $p[3]) + '</link>')
    [void]$sb.AppendLine('<description>' + (Esc $p[2]) + '</description>')
    [void]$sb.AppendLine('<pubDate>' + $p[0] + '</pubDate>')
    [void]$sb.AppendLine('<guid isPermaLink="false">' + (Esc $p[4]) + '</guid>')
    [void]$sb.AppendLine('</item>')
}
[void]$sb.AppendLine('</channel></rss>')

[System.IO.File]::WriteAllText($dst, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
$n = ($rows | Where-Object { $_ -notmatch '^(TITLE|DESC)~~~' }).Count
Write-Output ("rss.xml regenerated: $n items")