# regenerate feed/rss.xml from feed/items.csv
# rows: pubDate~~~title~~~description~~~link~~~guid
$src = Join-Path $PSScriptRoot 'items.csv'
$dst = Join-Path $PSScriptRoot 'rss.xml'

function Esc([string]$s) {
    $s.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;')
}

$items = Get-Content $src -Encoding UTF8 | Where-Object { $_ -and -not $_.StartsWith('#') }
$sb = New-Object System.Text.StringBuilder
[void]$sb.AppendLine('<?xml version="1.0" encoding="UTF-8"?>')
[void]$sb.AppendLine('<rss version="2.0">')
[void]$sb.AppendLine('<channel>')
[void]$sb.AppendLine('<title>Культура голоса - сигналы рынка, evidence, вердикты</title>')
[void]$sb.AppendLine('<link>https://audio-reclama.ru</link>')
[void]$sb.AppendLine('<description>Проверяемые сигналы голосового рынка: evidence, фальсификаторы, вердикты (Audio-Reclama).</description>')
[void]$sb.AppendLine('<language>ru</language>')
foreach ($l in $items) {
    $p = $l -split '~~~'
    [void]$sb.AppendLine('<item>')
    [void]$sb.AppendLine('<title>' + (Esc $p[1]) + '</title>')
    [void]$sb.AppendLine('<link>' + (Esc $p[3]) + '</link>')
    [void]$sb.AppendLine('<description>' + (Esc $p[2]) + '</description>')
    [void]$sb.AppendLine('<pubDate>' + $p[0] + '</pubDate>')
    [void]$sb.AppendLine('<guid isPermaLink="false">' + (Esc $p[4]) + '</guid>')
    [void]$sb.AppendLine('</item>')
}
[void]$sb.AppendLine('</channel>')
[void]$sb.AppendLine('</rss>')
[System.IO.File]::WriteAllText($dst, $sb.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Output "rss.xml regenerated ($($items.Count) items)"