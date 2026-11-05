param([Parameter(Mandatory=$true)][string]$Spec)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$job = Get-Content -Raw -LiteralPath $Spec | ConvertFrom-Json
$allowed = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'qa10')) + [IO.Path]::DirectorySeparatorChar
$target = [IO.Path]::GetFullPath($job.output)
if (-not $target.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw 'Draft annotation must stay inside qa10' }
$bitmap = New-Object Drawing.Bitmap($job.input)
$g = [Drawing.Graphics]::FromImage($bitmap)
$g.SmoothingMode = 'AntiAlias'
$g.TextRenderingHint = 'AntiAliasGridFit'
foreach ($item in $job.items) {
    $color = [Drawing.ColorTranslator]::FromHtml($item.color)
    $pen = New-Object Drawing.Pen($color,[single]$item.width)
    if ($item.dashed) { $pen.DashStyle = 'Dash' }
    if ($item.type -eq 'polygon' -or $item.type -eq 'path') {
        [Drawing.PointF[]]$points = @($item.points | ForEach-Object { New-Object Drawing.PointF([single]$_[0],[single]$_[1]) })
        if ($item.type -eq 'polygon') {
            $brush = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb([int]$item.fill,$color))
            $g.FillPolygon($brush,$points)
            $g.DrawPolygon($pen,$points)
            $brush.Dispose()
        } else { $g.DrawLines($pen,$points) }
    } elseif ($item.type -eq 'point') {
        $back = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(235,10,18,26))
        $g.FillEllipse($back,[single]($item.x-5),[single]($item.y-5),10,10)
        $g.DrawEllipse($pen,[single]($item.x-5),[single]($item.y-5),10,10)
        $back.Dispose()
    } elseif ($item.type -eq 'panel') {
        $back = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(235,10,18,26))
        $g.FillRectangle($back,[single]$item.x,[single]$item.y,[single]$item.w,[single]$item.h)
        $g.DrawRectangle($pen,[single]$item.x,[single]$item.y,[single]$item.w,[single]$item.h)
        $back.Dispose()
    } else {
        $font = New-Object Drawing.Font('Arial',[single]$item.size,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel)
        $extent = $g.MeasureString([string]$item.text,$font)
        $back = New-Object Drawing.SolidBrush([Drawing.Color]::FromArgb(225,10,18,26))
        $brush = New-Object Drawing.SolidBrush($color)
        $g.FillRectangle($back,[single]($item.x-4),[single]($item.y-2),[single]($extent.Width+8),[single]($extent.Height+4))
        $g.DrawString([string]$item.text,$font,$brush,[single]$item.x,[single]$item.y)
        $font.Dispose();$back.Dispose();$brush.Dispose()
    }
    $pen.Dispose()
}
$g.Dispose()
$bitmap.Save($target,[Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
