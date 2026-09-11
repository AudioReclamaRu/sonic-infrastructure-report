# fb-publish.ps1 - publish a post to a Facebook Page (and linked Instagram).
# Token: secrets/fb_token.txt (NOT in git). Text: UTF-8 file (no inline cyrillic).
# Usage:
#   powershell -File fb-publish.ps1 -Text post.txt [-Image cover.jpg] [-Page <pageId>] [-Ig]
param(
    [string]$Text,
    [string]$Image,
    [string]$Page,
    [switch]$Ig
)
$ErrorActionPreference = 'Continue'

$secrets = 'F:\Pill\tmp\opencode\secrets'
$tokenFile = Join-Path $secrets 'fb_token.txt'
if (-not (Test-Path $tokenFile)) { Write-Output 'NO_TOKEN'; exit 1 }
$userToken = [System.IO.File]::ReadAllText($tokenFile).Trim()
$proxy = 'socks5h://127.0.0.1:10808'
$api = 'https://graph.facebook.com/v21.0'

if (-not $Text) { Write-Output 'NO_TEXT'; exit 1 }
$message = [System.IO.File]::ReadAllText($Text)

function Invoke-Graph([string]$url) {
    return & curl.exe --max-time 30 -s -x $proxy $url 2>$null
}

# 1) resolve page + page token
if (-not $Page) {
    $acc = Invoke-Graph ("$api/me/accounts?fields=id,name,access_token&access_token=$userToken") | ConvertFrom-Json
    if ($acc -and @($acc.data).Count -gt 0) {
        $pg = $acc.data[0]
        $Page = $pg.id
        $pageToken = $pg.access_token
    } else {
        $pg = (Invoke-Graph ("$api/319271621473482?fields=access_token&access_token=$userToken") | ConvertFrom-Json)
        $Page = '319271621473482'
        $pageToken = $pg.access_token
    }
} else {
    $pg = (Invoke-Graph ("$api/$Page?fields=access_token&access_token=$userToken") | ConvertFrom-Json)
    $pageToken = $pg.access_token
}
Write-Output ("PAGE=" + $Page)

# 2) publish text post
if ($Image) {
    $resp = & curl.exe --max-time 60 -s -x $proxy -F "source=@$Image" -F "message=$message" -F "access_token=$pageToken" "$api/$Page/photos" 2>$null
} else {
    $plFile = Join-Path $env:TEMP ("fb_" + [guid]::NewGuid().ToString('N') + '.json')
    $msgShielded = $message | ForEach-Object { $_ } # keep plain
    $payload = @{ message = $message; access_token = $pageToken } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($plFile, $payload, (New-Object System.Text.UTF8Encoding($false)))
    $resp = & curl.exe --max-time 30 -s -x $proxy -H 'Content-Type: application/json' --data-binary "@$plFile" "$api/$Page/feed" 2>$null
    Remove-Item $plFile -Force -ErrorAction SilentlyContinue
}
$o = $resp | ConvertFrom-Json
if ($o.id) {
    Write-Output ("FB_POSTED id=" + $o.id)
} else {
    Write-Output ("FB_FAIL " + $resp)
    if ($Ig) { exit 1 }
}

# 3) optional Instagram publication (business account linked to the page)
if ($Ig) {
    if (-not $Image) { Write-Output 'IG_NEEDS_IMAGE'; exit 1 }
    $pgDet = Invoke-Graph ("$api/$Page?fields=instagram_business_account{id,username}&access_token=$pageToken") | ConvertFrom-Json
    $igId = $null
    if ($pgDet.instagram_business_account) { $igId = $pgDet.instagram_business_account.id }
    if (-not $igId) { Write-Output 'NO_IG_ACCOUNT'; exit 1 }
    $cm = & curl.exe --max-time 60 -s -x $proxy -F "image_url=file://$Image" -F "caption=$message" -F "access_token=$pageToken" "$api/$igId/media" 2>$null
    $cmO = $cm | ConvertFrom-Json
    if (-not $cmO.id) { Write-Output ("IG_CONTAINER_FAIL " + $cm); exit 1 }
    $pub = & curl.exe --max-time 60 -s -x $proxy -F "creation_id=$($cmO.id)" -F "access_token=$pageToken" "$api/$igId/media_publish" 2>$null
    $pubO = $pub | ConvertFrom-Json
    if ($pubO.id) { Write-Output ("IG_POSTED id=" + $pubO.id) } else { Write-Output ("IG_PUB_FAIL " + $pub) }
}