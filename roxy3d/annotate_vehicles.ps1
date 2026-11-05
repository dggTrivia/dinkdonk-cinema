param([Parameter(Mandatory=$true)][string]$Spec)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$job = Get-Content -Raw -LiteralPath $Spec | ConvertFrom-Json
$allowed = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'qa3')) + [IO.Path]::DirectorySeparatorChar
$target = [IO.Path]::GetFullPath($job.output)
if (-not $target.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw 'Annotation output must stay inside qa3' }
$bitmap = New-Object Drawing.Bitmap($job.input)
$graphics = [Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = 'AntiAlias'
$graphics.TextRenderingHint = 'AntiAliasGridFit'
foreach ($item in $job.items) {
    $color = if ($item.color) { [Drawing.ColorTranslator]::FromHtml($item.color) } else { [Drawing.Color]::White }
    $pen = New-Object Drawing.Pen($color,1.0)
    if ($item.type -eq 'line') {
        $pen.DashStyle = 'Dash'
        $graphics.DrawLine($pen,[single]$item.x,[single]$item.y,[single]$item.x2,[single]$item.y2)
    } elseif ($item.type -eq 'cross') {
        $graphics.DrawEllipse($pen,[single]($item.x-5),[single]($item.y-5),10,10)
        $graphics.DrawLine($pen,[single]($item.x-8),[single]$item.y,[single]($item.x+8),[single]$item.y)
        $graphics.DrawLine($pen,[single]$item.x,[single]($item.y-8),[single]$item.x,[single]($item.y+8))
    } else {
        $font = New-Object Drawing.Font('Arial',[single]$item.size,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
        $extent = $graphics.MeasureString([string]$item.text,$font)
        $back = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(220,12,13,23))
        $brush = New-Object Drawing.SolidBrush($color)
        $graphics.FillRectangle($back,[single]($item.x-4),[single]($item.y-2),[single]($extent.Width+8),[single]($extent.Height+4))
        $graphics.DrawString([string]$item.text,$font,$brush,[single]$item.x,[single]$item.y)
        $font.Dispose();$back.Dispose();$brush.Dispose()
    }
    $pen.Dispose()
}
$graphics.Dispose()
$bitmap.Save($target,[Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
