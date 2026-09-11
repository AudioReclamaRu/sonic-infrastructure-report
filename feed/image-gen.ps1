# image-gen.ps1 - generate branded cover PNGs for VK feed items (1200x630)
# Reads feed/items.csv (UTF-8): col0 pubDate, col1 title, col6 image file.
# Brand texts come from feed/cover-brand.json (UTF-8) - script source stays ASCII.
param([string]$ItemsCsv)
Add-Type -AssemblyName System.Drawing
$W = 1200; $H = 630

function New-FontHelv([string]$name, [single]$size, [System.Drawing.FontStyle]$style) {
    return [System.Drawing.Font]::new($name, $size, $style)
}

function Wrap-Text([string]$text, [int]$maxWidth, [System.Drawing.Font]$font, [System.Drawing.Graphics]$g) {
    $words = ($text -split ' ')
    $lines = @()
    $cur = ''
    foreach ($w in $words) {
        $try = if ($cur) { $cur + ' ' + $w } else { $w }
        $sz = $g.MeasureString($try, $font)
        if ($sz.Width -le $maxWidth) { $cur = $try } else { if ($cur) { $lines += $cur }; $cur = $w }
    }
    if ($cur) { $lines += $cur }
    return , $lines
}

$rows = [System.IO.File]::ReadAllLines($ItemsCsv)
$feedDir = Split-Path -Parent $ItemsCsv
$imgDir = Join-Path $feedDir 'images'
if (-not (Test-Path $imgDir)) { New-Item -ItemType Directory -Path $imgDir -Force | Out-Null }

$cfg = ([System.IO.File]::ReadAllText((Join-Path $feedDir 'cover-brand.json'))) | ConvertFrom-Json
$brandText = [string]$cfg.brand
$tagText = [string]$cfg.tag
$footerText = [string]$cfg.footer

foreach ($row in $rows) {
    if (-not $row) { continue }
    if ($row.StartsWith('TITLE~~~') -or $row.StartsWith('DESC~~~')) { continue }
    $p = $row -split '~~~'
    if ($p.Count -lt 6) { continue }
    if (-not $p[5]) { continue }
    $title = $p[1]
    $imgName = $p[5] + '.png'
    $outPath = Join-Path $imgDir $imgName

    $bmp = New-Object System.Drawing.Bitmap($W, $H)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
    $bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, [System.Drawing.Color]::FromArgb(24, 34, 54), [System.Drawing.Color]::FromArgb(44, 62, 96), 90)
    $g.FillRectangle($bg, $rect)

    $accent = [System.Drawing.Color]::FromArgb(255, 176, 92, 44)
    $g.FillRectangle((New-Object System.Drawing.SolidBrush $accent), 0, 0, $W, 10)

    $white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 246, 248))
    $grey = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 176, 186, 202))

    $brandFont = New-FontHelv 'Verdana' 24 ([System.Drawing.FontStyle]::Bold)
    $subFont = New-FontHelv 'Verdana' 18 ([System.Drawing.FontStyle]::Regular)
    $g.DrawString($brandText, $brandFont, $grey, 48, 44)
    $g.DrawString($tagText, $subFont, $grey, 48, 82)

    $size = if ($title.Length -lt 46) { 46 } elseif ($title.Length -lt 80) { 40 } else { 34 }
    $titleFont = New-FontHelv 'Georgia' $size ([System.Drawing.FontStyle]::Bold)
    $lines = Wrap-Text $title ($W - 120) $titleFont $g
    $lineHeight = [int]($size * 1.32)
    $startY = 220
    if ($lines.Count -gt 3) { $startY = 200; $lineHeight = [int]($size * 1.22) }
    $y = $startY
    foreach ($ln in $lines) {
        $tf = New-Object System.Drawing.StringFormat
        $tf.Alignment = [System.Drawing.StringAlignment]::Center
        $lr = New-Object System.Drawing.RectangleF(60, $y, ($W - 120), $lineHeight)
        $g.DrawString($ln, $titleFont, $white, $lr, $tf)
        $y += $lineHeight
    }

    $datePart = ''
    if ($p[0] -match '\w{3}, (\d{1,2} \w{3} \d{4})') { $datePart = $Matches[1] }
    $g.DrawString(($datePart + '  |  ' + $footerText), $subFont, $grey, 48, ($H - 74))

    $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
    Write-Output ("IMG " + $outPath + "  title_len=" + $title.Length + " lines=" + $lines.Count)
}
Write-Output ('DONE images in ' + $imgDir)