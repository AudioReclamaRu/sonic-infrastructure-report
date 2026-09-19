# url-shortener.ps1 — shorten a URL for VK posts (vk.cc via API, fallback clck.ru)
param([Parameter(Mandatory)][string]$Url)
$ErrorActionPreference='Stop'
$secrets='F:\Pill\tmp\opencode\secrets'
$proxy='socks5h://127.0.0.1:10808'
$ver='5.199'
$api='https://api.vk.com/method'

$token=''
$tokenFile=Join-Path $secrets 'vk_token.txt'
if(Test-Path $tokenFile){ $token=[System.IO.File]::ReadAllText($tokenFile).Trim() }

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

# 1) try VK API utils.getShortLink (produces vk.cc)
if($token){
    try{
        $r=Invoke-Curl ("--max-time 15 -s -x `"$proxy`" -G --data-urlencode `"url=$Url`" --data-urlencode `"access_token=$token`" --data-urlencode `"v=$ver`" `"$api/utils.getShortLink`"") | ConvertFrom-Json
        if($r.response.short_url){ Write-Output $r.response.short_url; exit 0 }
    }catch{}
}

# 2) fallback clck.ru
try{
    $enc=[uri]::EscapeDataString($Url)
    $r=Invoke-Curl ("--max-time 12 -s `"https://clck.ru/--?url=$enc`"")
    if($r -match '^https?://'){ Write-Output $r; exit 0 }
}catch{}

# 3) return original
Write-Output $Url