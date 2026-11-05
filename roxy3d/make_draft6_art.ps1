$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$dir=Join-Path $PSScriptRoot 'qa10/draft6/art'; New-Item -ItemType Directory -Force -Path $dir | Out-Null
$rng=[Random]::new(171006)
function Col($hex){[Drawing.ColorTranslator]::FromHtml($hex)}
function Rect($x,$y,$w,$h,$c){$br=[Drawing.SolidBrush]::new((Col $c));$script:g.FillRectangle($br,[single]$x,[single]$y,[single]$w,[single]$h);$br.Dispose()}
function Line($xy,$c,$w=4){$pts=[Drawing.PointF[]]@();for($i=0;$i -lt $xy.Count;$i+=2){$pts += [Drawing.PointF]::new($xy[$i],$xy[$i+1])};$p=[Drawing.Pen]::new((Col $c),$w);$g.DrawLines($p,$pts);$p.Dispose()}
function Txt($s,$x,$y,$sz,$c,$font='Arial',$width=800){$f=[Drawing.Font]::new($font,[single]$sz,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel);$br=[Drawing.SolidBrush]::new((Col $c));$sf=[Drawing.StringFormat]::new();$sf.Alignment='Center';$g.DrawString($s,$f,$br,[Drawing.RectangleF]::new($x,$y,$width,900),$sf);$f.Dispose();$br.Dispose();$sf.Dispose()}
function Begin($name,$w,$h,$bg){$script:name=$name;$script:w=$w;$script:h=$h;$script:bm=[Drawing.Bitmap]::new($w,$h,[Drawing.Imaging.PixelFormat]::Format32bppArgb);$script:g=[Drawing.Graphics]::FromImage($bm);$g.SmoothingMode='AntiAlias';$g.TextRenderingHint='AntiAliasGridFit';$g.Clear((Col $bg))}
function Save($grain=1500){for($i=0;$i -lt $grain;$i++){$br=[Drawing.SolidBrush]::new([Drawing.Color]::FromArgb($rng.Next(5,24),30,20,35));$g.FillRectangle($br,$rng.Next($w),$rng.Next($h),$rng.Next(1,4),$rng.Next(1,5));$br.Dispose()};$g.Dispose();$bm.Save((Join-Path $dir "$name.png"),[Drawing.Imaging.ImageFormat]::Png);$bm.Dispose()}
Begin 'eatfresh' 1000 1400 '#eee1c5'
Rect 22 22 956 1356 '#302c49';Rect 42 42 916 1316 '#eadbc0'
Txt 'EAT OUR FRESH' 50 62 81 '#a94744' 'Arial Black' 900
Txt 'NOTHING' 48 158 142 '#302c49' 'Impact' 904
Txt 'BURGERS' 50 314 141 '#302c49' 'Impact' 900
Rect 92 498 816 690 '#272832'
$im=[Drawing.Image]::FromFile((Join-Path $PSScriptRoot 'ref/eatfresh-emote/EatFresh.png'))
$g.InterpolationMode='NearestNeighbor';$g.PixelOffsetMode='Half';$g.DrawImage($im,[Drawing.Rectangle]::new(158,511,684,684));$im.Dispose();$g.InterpolationMode='HighQualityBicubic'
Txt 'ALL THE HYPE. ZERO SUBSTANCE.' 80 1212 38 '#a94744' 'Arial Black' 840
Txt 'A CHAT-SIZED MEAL  /  SATISFACTION: UNCONFIRMED' 70 1295 23 '#302c49' 'Arial' 860
Save 5000
Begin 'timetable' 700 1000 '#d1cbb6'
Rect 20 20 660 960 '#e5e0cc';Rect 20 20 660 165 '#283e50';Txt 'd.gg transit' 45 40 61 '#e9dfbb' 'Arial' 610;Txt 'Route 05' 45 115 43 '#e9dfbb' 'Arial' 610
Txt 'every' 116 222 60 '#293e4c' 'Arial' 200;Txt '15' 325 222 60 '#293e4c' 'Arial' 90;Txt 'min' 430 222 60 '#293e4c' 'Arial' 160
$t=$g.Save();$g.TranslateTransform(370,252);$g.RotateTransform(-6);Rect -57 -47 114 87 '#eee1b4';Txt '5' -52 -47 75 '#253a4b' 'Arial' 104;$g.Restore($t)
Txt 'TO DINK DONK CINEMA' 25 333 33 '#293e4c' 'Arial' 650
Line @(125,430,125,790,530,790) '#427b84' 18
foreach($y in @(452,554,656,790)){$br=[Drawing.SolidBrush]::new((Col '#f1e9ce'));$g.FillEllipse($br,112,($y-13),26,26);$br.Dispose()}
Txt 'MARKET STREET' 180 438 26 '#263c4d' 'Arial' 420;Txt 'CENTRAL ARCADE' 180 541 26 '#263c4d' 'Arial' 420;Txt 'CAFE LUNA' 180 645 26 '#263c4d' 'Arial' 420;Txt 'DINK DONK' 200 738 28 '#263c4d' 'Arial' 350
Txt 'FIRST 06:05  /  LAST 00:05' 30 876 29 '#263c4d' 'Arial' 640;Txt 'FARES  |  PAY THE DRIVER' 30 933 23 '#59666b' 'Arial' 640;Save 2700
Begin 'newspaper' 900 650 '#b6b19f'
Txt 'THE EVENING NOTHING' 30 20 59 '#303738' 'Georgia' 840;Line @(30,98,870,98) '#52574f' 4;Txt 'STILL NOTHING TO REPORT' 25 115 35 '#303738' 'Arial' 850
Rect 38 199 274 209 '#737971';for($col=0;$col -lt 5;$col++){for($j=0;$j -lt 28;$j++){if($col -lt 2 -and $j -lt 14){continue};Rect (40+$col*170) (198+$j*14) ($rng.Next(95,153)) 3 '#646960'}};Save 6000
Begin 'flyer' 500 700 '#c4b487';Txt 'ONE NIGHT' 20 30 57 '#423845' 'Impact' 460;Txt 'ONLY' 20 109 80 '#423845' 'Impact' 460;Rect 40 231 420 250 '#62585d';Txt 'LATE SHOW' 20 530 50 '#423845' 'Arial' 460;Txt 'FRIDAY / 23:05' 20 615 27 '#423845' 'Arial' 460;Save 2200
