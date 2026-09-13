# vk-autopublish.ps1 - publish list of feed items to VK wall one by one (caller passes guids).
# Usage: powershell -File vk-autopublish.ps1 -Guids "guid1,guid2"
# For each guid: reads items.csv, publishes via vk-publish.ps1, marks published, records post_id.
param(
    [string]$Guids
)
$ErrorActionPreference = 'Stop'

$secrets = 'F:\Pill\tmp\opencode\secrets'
$repo    = 'F:\Pill\tmp\opencode\sonic-repo'
$feed    = Join-Path $repo 'feed'
$published = Join-Path $secrets 'vk_published.txt'
$vkstate   = Join-Path $secrets 'vk_state.txt'
$low   = Join-Path $repo 'tools\vk-publish.ps1'
$srcLabel = [System.IO.File]::ReadAllText((Join-Path $repo 'state\source-label.txt')).Trim()

if (-not (Test-Path $published)) {
    [System.IO.File]::WriteAllText($published, '', (New-Object System.Text.UTF8Encoding($false)))
}
$done = @([System.IO.File]::ReadAllLines($published) | Where-Object { $_ -ne '' })
$targets = @($Guids -split ',' | Where-Object { $_ -ne '' })

$rows = [System.IO.File]::ReadAllLines((Join-Path $feed 'items.csv'))
$rowsMap = @{}
foreach ($row in $rows) {
    if (-not $row) { continue }
    if ($row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    $rowsMap[$p[4]] = $p
}

$ok = 0; $skip = 0; $fail = 0
foreach ($g in $targets) {
    if ($done -contains $g) { Write-Output ("SKIP already published: $g"); $skip++; continue }
    if (-not $rowsMap.ContainsKey($g)) { Write-Output ("SKIP guid not in csv: $g"); $skip++; continue }
    $p = $rowsMap[$g]
    $title = $p[1]
    $desc  = $p[2] -replace '\\n', "`n`n"
    $link  = $p[3]
    $imgName = $p[5]

    $postText = "$title`n`n$desc`n`n$srcLabel $link"
    $tmp = Join-Path $env:TEMP ("vk_" + [guid]::NewGuid().ToString('N') + '.txt')
    [System.IO.File]::WriteAllText($tmp, $postText, (New-Object System.Text.UTF8Encoding($false)))

    $imgFile = Join-Path (Join-Path $feed 'images') ($imgName + '.png')
    $hasImg  = (Test-Path -LiteralPath $imgFile)

    $argList = @('-Text', $tmp)
    if ($hasImg) { $argList += '-Image'; $argList += $imgFile }

    Write-Output ("PUBLISH $g ...")
    $out = & powershell -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File $low @argList 2>&1 | Out-String
    if ($out -match 'VK_POSTED post_id=(\S+)') {
        $postId = $Matches[1]
        [System.IO.File]::AppendAllText($published, "$g`n", (New-Object System.Text.UTF8Encoding($false)))
        [System.IO.File]::AppendAllText($vkstate, "$g`t$postId`n", (New-Object System.Text.UTF8Encoding($false)))
        Write-Output ("OK $g -> $postId")
        $ok++
    } else {
        Write-Output ("FAIL $g -> " + $out.Trim())
        $fail++
    }
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
Write-Output ("DONE ok=$ok skip=$skip fail=$fail")
