# fb-autopublish.ps1 — publish list of feed items to FB one by one (caller passes items)
# Usage: powershell -File fb-autopublish.ps1 -Guids "guid1,guid2"
# For each guid: reads items.csv, builds text, publishes with image if present, marks published.
param(
    [string]$Guids
)
$ErrorActionPreference = 'Stop'
$secrets = 'F:\Pill\tmp\opencode\secrets'
$feed = 'F:\Pill\tmp\opencode\sonic-repo\feed'
$published = Join-Path $secrets 'fb_published.txt'
$script = 'F:\Pill\tmp\opencode\sonic-repo\tools\fb-publish.ps1'

if (-not (Test-Path $published)) { [System.IO.File]::WriteAllText($published, '', (New-Object System.Text.UTF8Encoding($false))) }
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
    $desc = $p[2] -replace '\\n', "`n`n"
    $link = $p[3]
    $imgName = $p[5]

    $postText = "$title`n`n$desc`n`nИсточник: $link"
    $tmp = Join-Path $env:TEMP ("fb_ap_" + [guid]::NewGuid().ToString('N') + '.txt')
    [System.IO.File]::WriteAllText($tmp, $postText, (New-Object System.Text.UTF8Encoding($false)))

    $imgFile = Join-Path (Join-Path $feed 'images') ($imgName + '.png')
    $hasImg = (Test-Path -LiteralPath $imgFile)

    $argList = @('-Text', $tmp)
    if ($hasImg) { $argList += '-Image'; $argList += $imgFile }

    Write-Output ("PUBLISH $g ...")
    $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $script @argList 2>&1 | Out-String
    if ($out -match 'FB_POSTED id=(\S+)') {
        $postId = $Matches[1]
        [System.IO.File]::AppendAllText($published, "$g`n", (New-Object System.Text.UTF8Encoding($false)))
        Write-Output ("OK $g -> $postId")
        $ok++
    } else {
        Write-Output ("FAIL $g -> " + $out.Trim())
        $fail++
    }
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
}
Write-Output ("DONE ok=$ok skip=$skip fail=$fail")