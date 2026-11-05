param([switch]$ArtOnly)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$qa=Join-Path $PSScriptRoot 'qa10';$dir=Join-Path $qa 'draft5'
function C($s){[Drawing.ColorTranslator]::FromHtml($s)}
function Label($s,$x,$y,$size=20,$color='#eee8cf',$width=1450){$f=[Drawing.Font]::new('Arial',$size,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel);$b=[Drawing.SolidBrush]::new((C $color));$g.DrawString($s,$f,$b,[Drawing.RectangleF]::new($x,$y,$width,150));$f.Dispose();$b.Dispose()}
function Photo($file,$x,$y,$w,$h){$im=[Drawing.Image]::FromFile($file);$g.DrawImage($im,[Drawing.Rectangle]::new($x,$y,$w,$h));$im.Dispose()}
function Badge($n,$x,$y){$b=[Drawing.SolidBrush]::new((C '#ffe5a3'));$g.FillEllipse($b,$x-14,$y-14,28,28);$b.Dispose();Label "$n" ($x-8) ($y-12) 20 '#202c31' 36}
if(-not $ArtOnly){
$bm=[Drawing.Bitmap]::new(1600,1510);$g=[Drawing.Graphics]::FromImage($bm);$g.Clear((C '#17242c'));$g.SmoothingMode='AntiAlias';$g.TextRenderingHint='AntiAliasGridFit';$g.InterpolationMode='HighQualityBicubic'
Label 'DRAFT 5 / SURFACE WATER COVERAGE' 28 18 32
Label 'Numbered locations are physical scene surfaces. Interior and sheltered faces are excluded by sky visibility.' 30 63 18 '#c7d4d4'
Photo (Join-Path $qa 'draft_5.png') 0 100 1280 720
Badge 1 300 145;Badge 2 490 183;Badge 3 334 303;Badge 4 265 514;Badge 5 211 641;Badge 6 485 672;Badge 7 965 739;Badge 8 30 352;Badge 9 1158 309;Badge 10 176 553
Label '1  ROOF FELT' 1295 110 20 '#ffe5a3' 290;Label 'Wet grain, variable film; retained ripple rings in low spots.' 1295 138 17 '#d7dfdf' 286
Label '2  SKYLIGHTS' 1295 214 20 '#ffe5a3' 290;Label 'Glass beads + runnels; wet metal kerbs.' 1295 242 17 '#d7dfdf' 286
Label '3  AC / VENTS' 1295 305 20 '#ffe5a3' 290;Label 'Beaded tops, tiny crowns, edge drops and runoff.' 1295 333 17 '#d7dfdf' 286
Label '4  SHELTER' 1295 399 20 '#ffe5a3' 290;Label 'Steel roof beads + crowns + drips. Glass beads / runnels.' 1295 427 17 '#d7dfdf' 286
Label '5  ROAD / PUDDLES' 1295 505 20 '#ffe5a3' 290;Label 'Rough grain + varying water film, directional rain normals, rings and transient glints.' 1295 533 17 '#d7dfdf' 286
Label '6  PAVING / CAPS' 1295 634 20 '#ffe5a3' 290;Label 'Wet sheen + micro-impacts, drips and vertical runoff staining.' 1295 662 17 '#d7dfdf' 286
Label '7  ALLEY METAL' 30 847 20 '#ffe5a3' 370;Label 'Dumpster lids, fire escapes and rails: beads, splashes, edge drops.' 30 877 17 '#d7dfdf' 360
Label '8  FABRIC' 425 847 20 '#ffe5a3' 370;Label 'Soaked awnings and folded parasol, wet folds and hem drips.' 425 877 17 '#d7dfdf' 360
Label '9  SIGNS / LEDGES' 825 847 20 '#ffe5a3' 370;Label 'Wet sign boxes, parapet caps and sills; rain runoff down walls.' 825 877 17 '#d7dfdf' 360
Label '10  PARKED BUS' 1220 847 20 '#ffe5a3' 350;Label 'Wet roof, window beads, edge drops; original period advertisements.' 1220 877 17 '#d7dfdf' 350
Photo (Join-Path $dir 'rooftop_ac.png') 25 972 500 375
Photo (Join-Path $dir 'shelter_bus.png') 550 972 500 375
Photo (Join-Path $dir 'alley.png') 1075 972 500 375
Label 'AC / skylights / felt' 28 1359 22;Label 'Shelter roof / glass / bus' 553 1359 22;Label 'Alley: lids / railings / walls' 1078 1359 22
$scene=Get-Content -Raw (Join-Path $dir 'scene.json') | ConvertFrom-Json
$s=$scene.water_summary
Label ("Audited: {0} objects / {1} exposed upward polygons.  {2} bead sites / {3} crowns / {4} drips + runnels." -f $s.audited_objects,$s.exposed_upward_polygons,($s.static_beads_by_material.psobject.Properties.Value | Measure-Object -Sum).Sum,$s.splash_crowns,$s.edge_drips_and_runnels) 28 1410 19 '#c4d6d6'
Label ("Micro-impacts: {0} wet-surface sites, deterministic 2-second cycle.  Full object-level audit: draft5/scene.json" -f $s.micro_impact_sites) 28 1450 19 '#c4d6d6'
$g.Dispose();$bm.Save((Join-Path $qa 'water_coverage.png'),[Drawing.Imaging.ImageFormat]::Png);$bm.Dispose()
}
# Original artwork sheet: full sources, with no claim that fine text reads at 720p.
$keys=@('turf','cinema','whiplash','glorp','wcat','travel','buttons','boxing','courier','lookalike','conductor','cabge')
$names=@('01  YEE / PEPE turf war','02  ABSOLUTE CINEMA','03  WHIPLASH - IN 5 MIN','04  GLORP!','05  WCAT & ASSOCIATES','06  Nothing ever happens','07  PICK ONE call box','08  FROGS vs DINOS','09  CLIPPED & SHIPPED','10  LOOKALIKE CONTEST','11  RE-ELECT THE CONDUCTOR','12  CABGE - fresh daily')
$bm=[Drawing.Bitmap]::new(1600,1760);$g=[Drawing.Graphics]::FromImage($bm);$g.Clear((C '#243035'));$g.SmoothingMode='AntiAlias';$g.InterpolationMode='HighQualityBicubic'
Label 'THE APPROVED TWELVE / ORIGINAL PROCEDURAL ART' 30 20 30
Label 'Source artwork for close review. The draft and detail renders show its actual scale, perspective, lighting and weathering.' 30 65 18 '#b8cacc'
for($i=0;$i -lt 12;$i++){$x=25+($i%3)*530;$y=115+[int][Math]::Floor($i/3)*410;Label $names[$i] $x $y 21 '#f1dfaa' 500;$im=[Drawing.Image]::FromFile((Join-Path $dir ('art/'+$keys[$i]+'.png')));$scale=[Math]::Min([double](500.0/$im.Width),[double](350.0/$im.Height));$iw=[int]($im.Width*$scale);$ih=[int]($im.Height*$scale);$g.DrawImage($im,[Drawing.Rectangle]::new(($x+[int]((500-$iw)/2)),($y+42),$iw,$ih));$im.Dispose()}
$g.Dispose();$bm.Save((Join-Path $qa 'draft5_approved_art.png'),[Drawing.Imaging.ImageFormat]::Png);$bm.Dispose()

