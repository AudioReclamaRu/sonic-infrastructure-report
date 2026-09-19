# vk-publish.ps1 - publish a post to a VKontakte group wall.
# Token: secrets/vk_token.txt (NOT in git). Text: UTF-8 file. Proxy: socks5h.
# Usage:
#   powershell -File vk-publish.ps1 -Text post.txt [-Image cover.jpg] [-Group <groupId>] [-Date <unix>]
# Output: VK_POSTED post_id=NNN / VK_FAIL <error>  (parseable, idempotent tracker handled by caller)
param(
    [string]$Text,
    [string]$Image,
    [string]$Group,
    [long]$Date
)
$ErrorActionPreference = 'Continue'

$secrets = 'F:\Pill\tmp\opencode\secrets'
$tokenFile = Join-Path $secrets 'vk_token.txt'
if (-not (Test-Path $tokenFile)) { Write-Output 'NO_TOKEN'; exit 1 }
$token = [System.IO.File]::ReadAllText($tokenFile).Trim()
$proxy = 'socks5h://127.0.0.1:10808'
$api = 'https://api.vk.com/method'
$ver = '5.199'

if (-not $Text) { Write-Output 'NO_TEXT'; exit 1 }
$message = [System.IO.File]::ReadAllText($Text)
if ($message.Length -gt 1900) { $message = $message.Substring(0, 1897) + '...' }

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

# 1) resolve group owner id (negative for groups)
if (-not $Group) {
    $gFile = Join-Path $secrets 'vk_group.txt'
    if (Test-Path $gFile) { $Group = [System.IO.File]::ReadAllText($gFile).Trim() }
}
if (-not $Group) { Write-Output 'NO_GROUP'; exit 1 }
$ownerId = $Group
if ($ownerId -notmatch '^-') { $ownerId = '-' + $ownerId }

# 2) upload image if present (photos.getWallUploadServer -> saveWallPhoto)
$photoRef = ''
if ($Image -and (Test-Path -LiteralPath $Image)) {
    $svg = (Invoke-Curl ("--max-time 30 -s -x `"$proxy`" `"$api/photos.getWallUploadServer?group_id=$($ownerId.TrimStart('-'))&access_token=$token&v=$ver`"")) | ConvertFrom-Json
    if ($svg -and $svg.response -and $svg.response.upload_url) {
        $uploadUrl = $svg.response.upload_url
        $up = (Invoke-Curl ("--max-time 60 -s -x `"$proxy`" -F `"photo=@$Image;type=image/jpeg`" `"$uploadUrl`"")) | ConvertFrom-Json
        if ($up -and $up.server -and $up.photo -and $up.hash) {
            $saved = (Invoke-Curl ("--max-time 30 -s -x `"$proxy`" -G --data-urlencode `"group_id=$($ownerId.TrimStart('-'))`" --data-urlencode `"server=$($up.server)`" --data-urlencode `"photo=$($up.photo)`" --data-urlencode `"hash=$($up.hash)`" --data-urlencode `"access_token=$token`" --data-urlencode `"v=$ver`" `"$api/photos.saveWallPhoto`"")) | ConvertFrom-Json
            if ($saved -and @($saved.response).Count -gt 0) {
                $ph = @($saved.response)[0]
                $photoRef = "photo$($ph.owner_id)_$($ph.id)"
            }
        }
    }
    if (-not $photoRef) { Write-Output 'PHOTO_UPLOAD_SKIP no-image' }
}

# 3) post to wall (scheduled via -Date if given)
$argsStr = "--max-time 60 -s -x `"$proxy`" -G --data-urlencode `"owner_id=$ownerId`" --data-urlencode from_group=1 --data-urlencode `"message=$message`""
if ($photoRef) { $argsStr += " --data-urlencode `"attachments=$photoRef`"" }
$argsStr += " --data-urlencode `"access_token=$token`" --data-urlencode v=$ver"
if ($Date -gt 0) { $argsStr += " --data-urlencode publish_date=$Date" }
$argsStr += " `"$api/wall.post`""

$resp = Invoke-Curl $argsStr
$o = $resp | ConvertFrom-Json
if ($o -and $o.response -and $o.response.post_id) {
    Write-Output ("VK_POSTED post_id=" + $o.response.post_id)
} elseif ($o -and $o.error) {
    Write-Output ("VK_FAIL code=" + $o.error.error_code + " " + $o.error.error_msg)
} else {
    Write-Output ("VK_FAIL " + $resp)
}