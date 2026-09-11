# lead-intent.ps1 - Lead Intent Engine: classify scan items -> intent tier ->
# enrich contacts (email/domain) -> outreach drafts -> notify manager (TG).
# ASCII-only source. Templates (RU text): tools/intent-templates.json (UTF-8).
# Usage:
#   powershell -File lead-intent.ps1 [-Scan <scan json>] [-Enrich] [-Notify [-Chat 58308448]]
param(
    [string]$Scan,
    [switch]$Enrich,
    [switch]$Notify,
    [string]$Chat = '58308448'
)
$ErrorActionPreference = 'Continue'

$repo = 'F:\Pill\tmp\opencode\sonic-repo'
$tgDir = 'F:\Pill\tmp\opencode\tg'
$toolsDir = Join-Path $repo 'tools'
$todayMark = Get-Date -Format 'yyyy-MM-dd'
$intelDir = Join-Path $repo 'reports\intel'
$outreachDir = Join-Path $repo 'reports\outreach'
$leadsDir = Join-Path $tgDir 'leads'
foreach ($d in @($intelDir, $outreachDir, $leadsDir)) { if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }

if (-not $Scan) {
    $scanJson = Get-ChildItem (Join-Path $tgDir 'scan') -Filter '*.json' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $scanJson) { Write-Output 'NO_SCAN'; exit 1 }
    $Scan = $scanJson.FullName
}
$scanData = Get-Content $Scan -Raw -Encoding UTF8 | ConvertFrom-Json
$tt = Get-Content (Join-Path $toolsDir 'intent-templates.json') -Raw -Encoding UTF8 | ConvertFrom-Json

function Count-Hits([string]$text, [object]$kws) {
    if (-not $text) { return 0 }
    $t = $text.ToLowerInvariant()
    $n = 0
    foreach ($k in $kws) {
        $kk = ([string]$k).ToLowerInvariant()
        if ($kk -and $t.Contains($kk)) { $n++ }
    }
    return $n
}

function Get-Domain([string]$url) {
    if (-not $url) { return '' }
    if ($url -match 'duckduckgo\.com/y\.js|bing\.com/aclick|ad_domain=') { return '' }
    $m = [regex]::Match($url, 'https?://([^/]+)')
    if (-not $m.Success) { return '' }
    $hostName = $m.Groups[1].Value
    if ($hostName -match '(duckduckgo\.com|news\.ycombinator\.com|ycombinator\.com|github\.com|reddit\.com|twitter\.com|x\.com|youtube\.com|facebook\.com|instagram\.com)$') { return '' }
    $hostName = $hostName -replace '^www\.|^www2\.', ''
    $parts = $hostName.Split('.')
    if ($parts.Count -ge 2) { return $parts[$parts.Count - 2] + '.' + $parts[$parts.Count - 1] }
    return $hostName
}

function Get-TierText([int]$score) {
    if ($score -ge $tt.thresholds.t3) { return 't3' }
    if ($score -ge $tt.thresholds.t2) { return 't2' }
    if ($score -ge $tt.thresholds.t1) { return 't1' }
    return 't0'
}

function Get-DaysAgo([string]$ts) {
    if (-not $ts) { return -1 }
    $p = [DateTime]::MinValue
    if ([DateTime]::TryParse($ts, [ref]$p)) { return [int]((Get-Date) - $p).TotalDays }
    return -1
}

function Get-Contact([string]$domain) {
    $c = @{ email = ''; base = '' }
    if (-not $domain) { return $c }
    $mediaDomains = @('latimes.com','foxnews.com','business20channel.tv','prnewswire.com','variety.com','unite.ai','digitalmusicnews.com','ecency.com','businessinsider.com','reuters.com','bloomberg.com','cnn.com','bbc.com','theguardian.com','nytimes.com','washingtonpost.com','theverge.com','techcrunch.com','venturebeat.com','thebusinessresearchcompany.com','statista.com','grandviewresearch.com','marketsandmarkets.com')
    foreach ($md in $mediaDomains) {
        if ($domain -eq $md -or $domain.EndsWith('.' + $md)) { $c.skip = 'media-domain'; return $c }
    }
    $urls = @("https://$domain/", "https://$domain/contact", "https://$domain/contacts", "https://$domain/about")
    $found = $false
    foreach ($u in $urls) {
        $html = & curl.exe --max-time 12 -s -L -A 'Mozilla/5.0 (compatible; LeadIntent/1.0)' $u 2>$null
        if (-not $html -or $html.Length -lt 100) { continue }
        $em = [regex]::Match($html, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
        if ($em.Success) { $c.email = $em.Value; $found = $true }
        $c.res = $u
        break
    }
    return $c
}

# ---- classify ----
$rows = @()
foreach ($it in $scanData.items) {
    $text = ($it.title + ' ' + $it.snippet + ' ' + $it.url)
    $svcHits = Count-Hits ($it.title + ' ' + $it.snippet) $tt.kw_svc
    $mktHits = Count-Hits ($it.title + ' ' + $it.snippet) $tt.kw_market
    $prcHits = Count-Hits ($it.title + ' ' + $it.snippet) $tt.kw_proc
    $entHits = Count-Hits ($it.title + ' ' + $it.snippet) $tt.kw_entity
    $domain = Get-Domain $it.url

    $score = 0
    $score += [math]::Min($svcHits, $tt.weights.cap) * $tt.weights.svc
    $score += [math]::Min($mktHits, $tt.weights.cap) * $tt.weights.market
    $score += [math]::Min($prcHits, $tt.weights.cap) * $tt.weights.proc
    if ($entHits -gt 0) { $score += $tt.weights.entity }
    if ($domain) { $score += $tt.weights.entity }
    $days = Get-DaysAgo $it.ts
    if ($days -ge 0 -and $days -le 7) { $score += $tt.weights.recency }
    if ([long]$it.points -ge 50) { $score += $tt.weights.heat }

    $tier = Get-TierText $score
    $r = @{
        tier = $tier
        score = $score
        title = $it.title
        url = $it.url
        src = $it.src
        pts = $it.points
        snippet = $it.snippet
        svc = $svcHits
        mkt = $mktHits
        prc = $prcHits
        ent = $entHits
        domain = $domain
    }
    $rows += $r
}

$hot = @($rows | Where-Object { $_.tier -eq 't3' -or $_.tier -eq 't2' })
if ($Enrich) {
    $n = 0
    foreach ($r in $hot) {
        if ($n -ge 5) { break }
        if (-not $r.domain) { continue }
        $ct = Get-Contact $r.domain
        $r.contact_email = $ct.email
        $r.contact_page = $ct.res
        if ($ct.email) { $r.contact_ready = $true } else { $r.contact_ready = $false }
        $n++
    }
}

# ---- write intel md ----
$md = Join-Path $intelDir ("intel-" + $todayMark + '.md')
$lines = @()
$lines += "# Lead Intent Intel - " + $todayMark
$lines += ("Generated: " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " | source scan: " + (Split-Path $Scan -Leaf))
$lines += ''
$lines += "Classification: EVENT (t0) / NEED (t1) / DECISION_MAKER (t2) / READY_TO_CONTACT (t3)"
$lines += ''
foreach ($t in @('t3','t2','t1','t0')) {
    $ti = $tt.tiers | Where-Object { $_.id -eq $t }
    $sel = @($rows | Where-Object { $_.tier -eq $t })
    $lines += ("## " + $ti.label_en + " - " + $ti.label_ru + " (" + $sel.Count + ")")
    $lines += ''
    foreach ($r in ($sel | Sort-Object score -Descending)) {
        $ce = if ($r.contact_email) { ' | CONTACT: ' + $r.contact_email } elseif ($r.tier -eq 't3') { ' | CONTACT: RESOLVE' } else { '' }
        $lines += ("- [" + $r.score + " pts] " + $r.title + $ce)
        $lines += ("  src=" + $r.src + " url=" + $r.url + " (svc=" + $r.svc + " mkt=" + $r.mkt + " prc=" + $r.prc + " ent=" + $r.ent + ")")
        if ($r.snippet) { $lines += ("  " + $r.snippet) }
    }
    $lines += ''
}
[System.IO.File]::WriteAllText($md, ($lines -join "`n"), (New-Object System.Text.UTF8Encoding($false)))

# ---- write intel json ----
$jsonPath = Join-Path $intelDir ("intel-" + $todayMark + '.json')
[System.IO.File]::WriteAllText($jsonPath, (@{ date = $todayMark; rows = $rows } | ConvertTo-Json -Depth 5), (New-Object System.Text.UTF8Encoding($false)))

# ---- leads log (machine queue for manager) ----
$leadsFile = Join-Path $leadsDir 'intent-leads.jsonl'
foreach ($r in ($rows | Where-Object { $_.tier -eq 't3' })) {
    $rec = @{ ts = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'); tier = $r.tier; score = $r.score; title = $r.title; url = $r.url; domain = $r.domain; email = $r.contact_email }
    Add-Content -Path $leadsFile -Value ($rec | ConvertTo-Json -Compress) -Encoding UTF8
}

# ---- outreach drafts for READY_TO_CONTACT ----
$draftN = 0
foreach ($r in ($rows | Where-Object { $_.tier -eq 't3' })) {
    $draftN++
    $co = $r.domain
    if (-not $co) { $dm = [regex]::Match($r.url, 'https?://([^/]+)'); if ($dm.Success) { $co = ($dm.Groups[1].Value -replace '^www\.','') } }
    $ctx = $r.title
    $contactRef = if ($r.contact_email) { $r.contact_email } else { ('RESOLVE CONTACT FOR: ' + $co) }
    $subj = ($tt.outreach_email.subject -replace '\{company\}', $co)
    $body = ($tt.outreach_email.body -replace '\{company\}', $co -replace '\{context\}', $ctx -replace '\{contact_ref\}', $contactRef)
    $script = ($tt.call_script -replace '\{company\}', $co -replace '\{context\}', $ctx -replace '\{url\}', $r.url)
    $df = Join-Path $outreachDir ("draft-" + $todayMark + "-" + $draftN + ".md")
    $content = "# Outreach draft " + $draftN + " - " + $co + "`n`n## Source`n" + $r.title + "`n" + $r.url + "`n`n## Email`nTo: " + $contactRef + "`nSubject: " + $subj + "`n`n" + $body + "`n`n## Call script`n" + $script + "`n"
    [System.IO.File]::WriteAllText($df, $content, (New-Object System.Text.UTF8Encoding($false)))
}

# ---- summary ----
$t3 = @($rows | Where-Object { $_.tier -eq 't3' }).Count
$t2 = @($rows | Where-Object { $_.tier -eq 't2' }).Count
$t1 = @($rows | Where-Object { $_.tier -eq 't1' }).Count
$t0 = @($rows | Where-Object { $_.tier -eq 't0' }).Count
Write-Output ("INTENT scan=" + $scanData.date + " rows=" + $rows.Count + " t3=" + $t3 + " t2=" + $t2 + " t1=" + $t1 + " t0=" + $t0 + " drafts=" + $draftN)
Write-Output ("intel md -> " + $md)
Write-Output "top t3:"
$top = @($rows | Where-Object { $_.tier -eq 't3' } | Sort-Object score -Descending) + @($rows | Where-Object { $_.tier -eq 't2' } | Sort-Object score -Descending | Select-Object -First 3)
$top | Sort-Object score -Descending | Select-Object -First 6 | ForEach-Object { Write-Output ("  [" + $_.score + " " + $_.tier + "] " + $_.title + " | " + $_.url) }

if ($Notify) {
    $envTxt = Get-Content (Join-Path $tgDir 'env.txt')
    $envMap = @{}
    foreach ($ln in $envTxt) { $k,$v = $ln -split '=',2; if ($v) { $envMap[$k] = $v } }
    $token = (Get-Content $envMap['BOT_TOKEN_FILE'] -Raw).Trim()
    $api = $envMap['API']
    $proxy = $envMap['PROXY']
    $t = "Lead Intent Engine: scan " + $scanData.date + "`n"
    $t += "READY_TO_CONTACT: " + $t3 + " | DECISION_MAKER: " + $t2 + " | NEED: " + $t1 + " | EVENT: " + $t0 + "`n`n"
    $t += "Top ready-to-contact:"
    foreach ($r in ($top | Sort-Object score -Descending | Select-Object -First 5)) {
        $ce = if ($r.contact_email) { ' | ' + $r.contact_email } else { '' }
        $t += ("`n- [" + $r.tier + "] " + $r.title + $ce + "`n  " + $r.url)
    }
    $payload = @{ chat_id = $Chat; text = $t } | ConvertTo-Json -Compress
    $pf = Join-Path $env:TEMP ("intent_" + [guid]::NewGuid().ToString('N') + '.json')
    [System.IO.File]::WriteAllText($pf, $payload, (New-Object System.Text.UTF8Encoding($false)))
    & curl.exe --max-time 25 -s -x $proxy -H 'Content-Type: application/json' --data-binary "@$pf" ("$api/bot$token/sendMessage") 2>$null | Out-Null
    Remove-Item $pf -Force -ErrorAction SilentlyContinue
    Write-Output 'NOTIFIED_TG'
}