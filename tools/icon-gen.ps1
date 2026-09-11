# icon-gen.ps1 - square app icon PNG (1024x1024) from feed/cover-brand.json
Add-Type -AssemblyName System.Drawing
$cfg = [System.IO.File]::ReadAllText((Join-Path (Split-Path -Parent $PSScriptRoot) 'feed\cover-brand.json')) | ConvertFrom-Json
$brand = [string]$cfg.brand
$tag = [string]$cfg.tag

$S = 1024
$bmp = New-Object System.Drawing.Bitmap($S, $S)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$rect = New-Object System.Drawing.Rectangle(0, 0, $S, $S)
$bg = New-Object System.Drawing.Drawing2D.LinearGradientBrush($rect, [System.Drawing.Color]::FromArgb(24, 34, 54), [System.Drawing.Color]::FromArgb(44, 62, 96), 90)
$g.FillRectangle($bg, $rect)

$accent = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 176, 92, 44))
$white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 245, 246, 248))
$grey = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 176, 186, 202))

$g.FillRectangle($accent, 0, 0, $S, 16)
$ring = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(60, 176, 92, 44)), 4
$g.DrawEllipse($ring, 200, 180, 624, 624)
$ring2 = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(40, 176, 92, 44)), 3
$g.DrawEllipse($ring2, 140, 120, 744, 744)

$brandFont = New-Object System.Drawing.Font('Georgia', 54, [System.Drawing.FontStyle]::Bold)
$tagFont = New-Object System.Drawing.Font('Verdana', 30, [System.Drawing.FontStyle]::Regular)

$tfC = New-Object System.Drawing.StringFormat
$tfC.Alignment = [System.Drawing.StringAlignment]::Center
$tfC.LineAlignment = [System.Drawing.StringAlignment]::Center

$g.DrawString($brand, $brandFont, $white, (New-Object System.Drawing.RectangleF(60, 380, 904, 120)), $tfC)
$g.DrawString($tag, $tagFont, $grey, (New-Object System.Drawing.RectangleF(60, 520, 904, 80)), $tfC)

$out = Join-Path $PSScriptRoot 'app-icon.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output ("ICON " + $out)