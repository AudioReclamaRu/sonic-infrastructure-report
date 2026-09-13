# vk-cleanup.ps1 - analyze VK wall, delete posts without photos, remove duplicates,
# and list feed items (with image) missing from the wall (to be published next).
# Log: state/vk-cleanup.log. Outputs: state/vk-missing.txt
$ErrorActionPreference = 'Continue'
$secrets = 'F:\Pill\tmp\opencode\secrets'
$repo    = 'F:\Pill\tmp\opencode\sonic-repo'
$state   = Join-Path $repo 'state'
$token   = [System.IO.File]::ReadAllText((Join-Path $secrets 'vk_token.txt')).Trim()
$group   = [System.IO.File]::ReadAllText((Join-Path $secrets 'vk_group.txt')).Trim()
$proxy   = 'socks5h://127.0.0.1:10808'
$api     = 'https://api.vk.com/method'
$ver     = '5.199'
$ownerId = '-' + $group.TrimStart('-')
$logFile = Join-Path $state 'vk-cleanup.log'
function L([string]$m) { [System.IO.File]::AppendAllText($logFile, ((Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " " + $m + "`n"), (New-Object System.Text.UTF8Encoding($false))) }
Remove-Item $logFile -Force -ErrorAction SilentlyContinue
L "start owner=$ownerId"

function Vk([string]$method, [hashtable]$params) {
    $al = @('--max-time', '60', '-s', '-x', $proxy, '-G')
    foreach ($k in $params.Keys) { $al += '--data-urlencode'; $al += ("$k=" + $params[$k]) }
    $al += ($api + '/' + $method)
    $raw = (& curl.exe @al 2>$null)
    try { return ($raw | ConvertFrom-Json) } catch { return $null }
}

# ---- 1. fetch all wall posts ----
$all = @()
$offset = 0
$count = 100
while ($true) {
    $r = Vk 'wall.get' @{ owner_id = $ownerId; count = "$count"; offset = "$offset"; v = $ver }
    $items = @($r.response.items)
    if ($items.Count -eq 0) { break }
    $all += $items
    if ($items.Count -lt $count) { break }
    $offset += $count
    if ($offset -gt 2000) { break }
}
L ("fetched wall posts: " + $all.Count)
$all | ForEach-Object { $att = @($_.attachments); $ph = @($att | Where-Object { $_.type -eq 'photo' }).Count; $pin = if ($_.is_pinned) { 'PIN' } else { '' }; $txt = ($_.text -replace '\s+', ' ').Trim(); if (-not $txt) { $txt = '(repost)' }; L ("existing id=" + $_.id + " date=" + $_.date + " photo=" + $ph + " " + $pin + " :: " + $txt.Substring(0, [Math]::Min(90, $txt.Length))) }

# ---- 2. delete posts without a photo attachment (skip pinned) ----
$delNoImg = 0
foreach ($p in $all) {
    $att = @($p.attachments)
    $hasPhoto = @($att | Where-Object { $_.type -eq 'photo' }).Count -gt 0
    if ($p.is_pinned) { L ("KEEP pinned id=" + $p.id); continue }
    if (-not $hasPhoto) {
        $r = Vk 'wall.delete' @{ owner_id = $ownerId; post_id = "$($p.id)" }
        $ok = ($r.response -eq 1)
        L ("DELETE no-image id=" + $p.id + " -> " + $(if ($ok) { 'OK' } else { ('ERR ' + ($r.error.error_msg -join '; ')) }))
        if ($ok) { $delNoImg++ }
    }
}
L ("deleted no-image posts: " + $delNoImg)

# ---- 3. dedupe remaining posts by message text ----
$all2 = @($all | Where-Object { $_.is_pinned -ne $true -and (@($_.attachments | Where-Object { $_.type -eq 'photo' }).Count -gt 0) })
$groupBy = @{}
foreach ($p in $all2) {
    $key = $p.text.Trim().ToLower()
    if (-not $key) { continue }
    if (-not $groupBy.ContainsKey($key)) { $groupBy[$key] = @() }
    $groupBy[$key] += $p
}
$delDup = 0
foreach ($k in $groupBy.Keys) {
    $g = @($groupBy[$k])
    if ($g.Count -lt 2) { continue }
    $keep = $g | Sort-Object date, id | Select-Object -First 1
    foreach ($d in $g) {
        if ($d.id -eq $keep.id) { L ("KEEP dup survivor id=" + $d.id); continue }
        $r = Vk 'wall.delete' @{ owner_id = $ownerId; post_id = "$($d.id)" }
        $ok = ($r.response -eq 1)
        L ("DELETE duplicate id=" + $d.id + " keep=" + $keep.id + " -> " + $(if ($ok) { 'OK' } else { ('ERR ' + ($r.error.error_msg -join '; ')) }))
        if ($ok) { $delDup++ }
    }
}
L ("deleted duplicates: " + $delDup)

# ---- 4. figure which feed items with images are missing from the wall ----
$srcLabel = [System.IO.File]::ReadAllText((Join-Path $repo 'state\source-label.txt')).Trim()
$rows = [System.IO.File]::ReadAllLines((Join-Path $repo 'feed\items.csv'))
$missing = @()
$survivorTexts = @(($all2 | ForEach-Object { $_.text.Trim() }) + @($all | Where-Object { $_.is_pinned } | ForEach-Object { $_.text.Trim() }))
foreach ($row in $rows) {
    if (-not $row) { continue }
    if ($row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    $title = $p[1]; $desc = $p[2] -replace '\\n', "`n`n"; $link = $p[3]; $g = $p[4]; $imgName = $p[5]
    $imgFile = Join-Path (Join-Path $repo 'feed\images') ($imgName + '.png')
    if (-not (Test-Path -LiteralPath $imgFile)) { L ("SKIP no-image-file guid=" + $g); continue }
    $postText = "$title`n`n$desc`n`n$srcLabel $link"
    $pt = ($postText -replace '\s+', ' ').Trim()
    $found = $false
    foreach ($wt in $survivorTexts) {
        $wtn = ($wt -replace '\s+', ' ').Trim()
        if ($wtn -eq $pt -or $pt.StartsWith($wtn)) { $found = $true; break }
    }
    if (-not $found) { $missing += $g; L ("MISSING with-image guid=" + $g) } else { L ("ONWALL guid=" + $g) }
}
[System.IO.File]::WriteAllText((Join-Path $state 'vk-missing.txt'), (($missing | Sort-Object) -join "`n"), (New-Object System.Text.UTF8Encoding($false)))
L ("missing guids: " + $missing.Count)
L "DONE"