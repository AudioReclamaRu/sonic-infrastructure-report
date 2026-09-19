# vk-token-fetch.ps1 - get a USER access token via VK official mobile API (password grant).
# Scopes: wall, photos, groups, offline (offline => token does not expire).
# Usage:
#   powershell -File vk-token-fetch.ps1 -Login <phone/email> -Password <pass>
# Writes the USER token to secrets/vk_user_token.txt (keeps community key in vk_token.txt intact).
# On success outputs VK_TOKEN_OK user_id=...
param(
    [string]$Login,
    [string]$Password
)
$ErrorActionPreference = 'Stop'
$secrets = 'F:\Pill\tmp\opencode\secrets'
if (-not $Login -or -not $Password) { Write-Output 'NO_CREDENTIALS'; exit 1 }

$proxy = 'socks5h://127.0.0.1:10808'
# VK official Android app client (public well-known constants).
$clientId     = '2274003'
$clientSecret = 'hHbZxrkaUuLM2mNq5iWEbGPy8tT5koSW0'

$url = ('https://oauth.vk.com/token?grant_type=password' +
    '&client_id=' + $clientId +
    '&client_secret=' + $clientSecret +
    '&scope=wall,photos,groups,offline&v=5.199' +
    '&username=' + [System.Uri]::EscapeDataString($Login) +
    '&password=' + [System.Uri]::EscapeDataString($Password))

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

$resp = (Invoke-Curl ("--max-time 30 -s -x `"$proxy`" `"$url`""))
$o = $null
try { $o = $resp | ConvertFrom-Json } catch { }

if (-not $o) { Write-Output ("VK_TOKEN_FAIL no_response: " + $resp); exit 1 }

if ($o.access_token) {
    [System.IO.File]::WriteAllText((Join-Path $secrets 'vk_token.txt'), $o.access_token, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output ("VK_TOKEN_OK user_id=" + $o.user_id + " expires=" + $o.expires_in)
    exit 0
}

$err = $o.error
if ($err -eq 'need_captcha') {
    Write-Output ("VK_TOKEN_NEED_CAPTCHA sid=" + $o.captcha_sid + " img=" + $o.captcha_img)
} else {
    Write-Output ("VK_TOKEN_FAIL error=" + $err + " desc=" + $o.error_description)
}
exit 1