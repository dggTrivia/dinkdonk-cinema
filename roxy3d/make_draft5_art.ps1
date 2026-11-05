$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$dir=Join-Path $PSScriptRoot 'qa10/draft5/art'; New-Item -ItemType Directory -Force -Path $dir | Out-Null
$rng=[Random]::new(161005)
function Col($hex){[Drawing.ColorTranslator]::FromHtml($hex)}
function Brush($c){[Drawing.SolidBrush]::new((Col $c))}
function Rect($x,$y,$w,$h,$c){$br=Brush $c;$script:g.FillRectangle($br,[single]$x,[single]$y,[single]$w,[single]$h);$br.Dispose()}
function Oval($x,$y,$w,$h,$c){$br=Brush $c;$script:g.FillEllipse($br,[single]$x,[single]$y,[single]$w,[single]$h);$br.Dispose()}
function Poly($xy,$c){$p=[Drawing.PointF[]]@();for($i=0;$i -lt $xy.Count;$i+=2){$p += [Drawing.PointF]::new($xy[$i],$xy[$i+1])};$br=Brush $c;$script:g.FillPolygon($br,$p);$br.Dispose()}
function Line($xy,$c,$w=4){$p=[Drawing.PointF[]]@();for($i=0;$i -lt $xy.Count;$i+=2){$p += [Drawing.PointF]::new($xy[$i],$xy[$i+1])};$pen=[Drawing.Pen]::new((Col $c),$w);$pen.StartCap='Round';$pen.EndCap='Round';$script:g.DrawLines($pen,$p);$pen.Dispose()}
function Txt($s,$x,$y,$size,$c,$font='Arial',$width=950){$f=[Drawing.Font]::new($font,[single]$size,[Drawing.FontStyle]::Bold,[Drawing.GraphicsUnit]::Pixel);$br=Brush $c;$sf=[Drawing.StringFormat]::new();$sf.Alignment='Center';$sf.LineAlignment='Near';$script:g.DrawString($s,$f,$br,[Drawing.RectangleF]::new($x,$y,$width,350),$sf);$f.Dispose();$br.Dispose();$sf.Dispose()}
function Begin($name,$w,$h,$bg){$script:name=$name;$script:w=$w;$script:h=$h;$script:bm=[Drawing.Bitmap]::new($w,$h,[Drawing.Imaging.PixelFormat]::Format32bppArgb);$script:g=[Drawing.Graphics]::FromImage($bm);$g.SmoothingMode='AntiAlias';$g.TextRenderingHint='AntiAliasGridFit';$g.Clear((Col $bg))}
function Save($grain=1600){for($i=0;$i -lt $grain;$i++){$x=$rng.Next($w);$y=$rng.Next($h);$br=[Drawing.SolidBrush]::new([Drawing.Color]::FromArgb($rng.Next(6,30),20,27,22));$g.FillRectangle($br,$x,$y,$rng.Next(1,4),$rng.Next(1,5));$br.Dispose()};$g.Dispose();$bm.Save((Join-Path $dir "$name.png"),[Drawing.Imaging.ImageFormat]::Png);$bm.Dispose()}
function DrawCat($x,$y,$s,$fur,$suit=$false){
 if($suit){Poly @(($x-95*$s),($y+70*$s),($x+95*$s),($y+70*$s),($x+135*$s),($y+280*$s),($x-140*$s),($y+280*$s)) '#202e48';Poly @(($x-37*$s),($y+72*$s),($x+38*$s),($y+72*$s),($x),($y+175*$s)) '#eee3c7';Poly @(($x),($y+105*$s),($x+16*$s),($y+122*$s),($x),($y+200*$s),($x-14*$s),($y+122*$s)) '#b7934b';Line @(($x-97*$s),($y+160*$s),($x+90*$s),($y+220*$s)) '#3f5068' (31*$s);Line @(($x+95*$s),($y+150*$s),($x-85*$s),($y+220*$s)) '#32415b' (31*$s)}
 Poly @(($x-85*$s),($y),($x-90*$s),($y-105*$s),($x-25*$s),($y-55*$s),($x+24*$s),($y-55*$s),($x+90*$s),($y-105*$s),($x+83*$s),($y)) $fur
 Oval ($x-91*$s) ($y-62*$s) (182*$s) (145*$s) $fur;Oval ($x-61*$s) ($y-13*$s) (45*$s) (32*$s) '#fff1b6';Oval ($x+17*$s) ($y-13*$s) (45*$s) (32*$s) '#fff1b6';Oval ($x-42*$s) ($y-10*$s) (9*$s) (27*$s) '#162323';Oval ($x+35*$s) ($y-10*$s) (9*$s) (27*$s) '#162323';Poly @(($x-12*$s),($y+31*$s),($x+12*$s),($y+31*$s),($x),($y+43*$s)) '#485537';Line @(($x-31*$s),($y+52*$s),($x),($y+59*$s),($x+31*$s),($y+52*$s)) '#26352c' (4*$s)
}
Begin 'wcat' 1400 700 '#cfc3a0'
Rect 22 22 1356 656 '#e5dcc0';Rect 42 40 1316 620 '#d8ceb3';DrawCat 268 260 1.17 '#a19a84' $true
Txt 'WCAT' 510 110 150 '#28374e' 'Georgia' 810;Txt '& ASSOCIATES' 510 280 64 '#28374e' 'Georgia' 810;Line @((570),(379),(1260),(379)) '#947644' 5;Txt "let's do bidness." 520 422 60 '#554c3d' 'Georgia' 790;Txt 'COUNSEL  |  CONTRACTS  |  CONFIDENCE' 520 555 23 '#655b45' 'Arial' 790;Save 5000
Begin 'whiplash' 1400 700 '#161b1b'
for($y=45;$y -lt 680;$y+=16){Line @((25),($y),(1370),($y)) '#2e3431' 2}
Txt 'NEXT SHOWING:' 60 65 78 '#ede6ce' 'Arial' 1280;Txt 'WHIPLASH' 60 194 156 '#eee7d1' 'Arial' 1280;Txt 'IN          MIN' 80 440 99 '#e6e0ca' 'Arial' 1220
Poly @((630),(400),(790),(410),(774),(591),(619),(580)) '#d5bc7c';$state=$g.Save();$g.TranslateTransform(690,451);$g.RotateTransform(-8);Txt '5' -61 -42 150 '#292c22' 'Comic Sans MS' 145;$g.Restore($state)
Rect 605 391 72 26 '#a7a28b';Rect 741 574 73 23 '#ada78f';Rect 590 410 25 105 '#545445';Rect 799 481 22 88 '#545445';Save 2700
Begin 'glorp' 700 1050 '#d9ce81'
Poly @((0),(0),(700),(0),(700),(650),(0),(880)) '#173e34';for($i=0;$i -lt 8;$i++){Poly @((350),(460),(($i*150-250)),(0),(($i*150-155)),(0)) '#315d42'}
Txt 'GLORP!' 12 30 151 '#c6dd56' 'Impact' 676;Txt 'IT CAME FROM THE CHAT.' 20 217 32 '#eddfad' 'Arial' 660
DrawCat 350 475 1.65 '#88b84e';Line @((280),(370),(237),(305)) '#a9cb5e' 12;Line @((422),(372),(469),(300)) '#a9cb5e' 12;Oval 216 281 38 38 '#d8e98a';Oval 452 278 38 38 '#d8e98a'
for($i=0;$i -lt 12;$i++){$x=$i*62;$ht=$rng.Next(90,210);Rect $x (880-$ht) 49 $ht '#263b34';for($j=0;$j -lt 4;$j++){Rect ($x+8) (890-$ht+$j*33) 9 13 '#b0b768';Rect ($x+29) (890-$ht+$j*33) 9 13 '#b0b768'}}
for($i=0;$i -lt 16;$i++){Oval ($i*45+8) 858 17 24 '#20332e';Rect ($i*45+2) 881 29 45 '#20332e'};DrawCat 595 883 .15 '#ddb544'
Txt 'A COLOSSAL CHAT-O-SCOPE SPECTACLE' 15 937 24 '#24382a' 'Arial' 670;Txt 'ONE NIGHT ONLY  /  ALL SEATS 5.00' 15 987 21 '#24382a' 'Arial' 670
for($x=0;$x -lt 700;$x+=8){for($y=0;$y -lt 920;$y+=8){$br=[Drawing.SolidBrush]::new([Drawing.Color]::FromArgb(25,15,35,20));$g.FillEllipse($br,$x,$y,2,2);$br.Dispose()}};Save 3500
Begin 'travel' 700 1050 '#80b8bc';Rect 0 570 700 480 '#ded2a8';Oval 425 260 170 170 '#e8d0a1';Poly @((0),(550),(180),(480),(420),(550),(700),(510),(700),(660),(0),(660)) '#549997'
foreach($x in @((120),(570))){Line @(($x),(670),(($x+22)),(400)) '#6a6650' 18;foreach($dx in @((-120),(-65),(65),(120))){Line @((($x+22)),(400),(($x+$dx)),(360),(($x+$dx*1.2)),(410)) '#487b65' 18}}
Rect 265 613 220 200 '#ac714b';Line @((320),(612),(320),(573),(428),(573),(428),(612)) '#624f3e' 10;Rect 294 620 15 180 '#5b5d4b';Rect 439 620 15 180 '#5b5d4b';Txt 'GOING AWAY?' 20 48 76 '#244b50' 'Impact' 660;Txt 'Relax -' 30 169 65 '#f1ead6' 'Georgia' 640;Txt 'nothing ever' 20 252 49 '#f1ead6' 'Arial' 660;Txt 'happens.*' 20 313 58 '#f1ead6' 'Arial' 660;Txt '*something will happen' 20 937 26 '#485b55' 'Arial' 660;Save 2200
Begin 'buttons' 500 700 '#909f9b';Rect 25 25 450 650 '#7e8d88';Rect 59 60 380 146 '#dfd5b6';Rect 47 54 72 25 '#b8b495';Rect 390 182 63 25 '#b8b495';Txt 'PICK ONE' 65 89 59 '#303932' 'Comic Sans MS' 370;Oval 70 294 145 145 '#353d3e';Oval 284 294 145 145 '#353d3e';Oval 81 303 122 122 '#b8433c';Oval 296 303 122 122 '#3c6d9d';Oval 104 317 40 17 '#d37464';Oval 318 317 40 17 '#77a0b8';Oval 239 521 27 27 '#598e50';Line @((204),(562),(237),(548)) '#4d7947' 3;Save 2000
Begin 'boxing' 1500 500 '#8d302a';Rect 13 13 1474 474 '#c5a554';Rect 23 23 1454 454 '#7c2c28';Txt 'FROGS vs DINOS' 235 30 113 '#e4c676' 'Impact' 1020;Txt 'THE REMATCH' 300 173 79 '#ebddae' 'Impact' 900;Txt 'LIVE THIS WINTER' 350 339 57 '#ddbf73' 'Arial' 800
Oval 30 140 245 190 '#4b8e54';Rect 35 292 143 88 '#3b7046';Oval 182 215 103 116 '#58965b';Oval 1216 142 245 190 '#83618e';Rect 1325 294 142 88 '#634c76';Oval 1206 218 107 113 '#97749b';Line @((60),(310),(173),(310)) '#c4ba78' 8;Line @((1336),(312),(1444),(312)) '#c4ba78' 8;Save 3200
Begin 'courier' 1500 350 '#554330';Rect 0 15 1500 17 '#cbaa49';Rect 0 318 1500 17 '#cbaa49';Poly @((80),(116),(156),(77),(236),(116),(158),(156)) '#d7b54c';Poly @((80),(116),(158),(156),(158),(255),(80),(215)) '#ae8b39';Poly @((158),(156),(236),(116),(236),(215),(158),(255)) '#caa64b';Line @((158),(156),(158),(255)) '#5b482e' 5;Txt 'CLIPPED & SHIPPED' 270 61 96 '#e0be59' 'Impact' 1170;Txt 'same-day delivery, Mondays & Fridays' 260 207 43 '#dbca8b' 'Arial' 1190;Save 2600
Begin 'lookalike' 700 1000 '#d7d4bf';Txt 'LOOKALIKE' 20 32 94 '#2a302d' 'Impact' 660;Txt 'CONTEST' 20 134 104 '#2a302d' 'Impact' 660;Txt 'hear me out' 20 270 51 '#3a3e35' 'Comic Sans MS' 660
Oval 133 440 98 116 '#4d5147';Poly @((117),(561),(245),(561),(285),(770),(83),(770)) '#4d5147';Rect 490 474 18 281 '#454a42';Poly @((400),(478),(450),(374),(551),(374),(603),(478)) '#51564c';Oval 437 751 120 23 '#454a42';Txt 'VS' 280 565 65 '#626657' 'Arial' 145;Txt 'you gotta give me this one' 20 850 34 '#292f29' 'Arial' 660;Save 15000
Begin 'conductor' 700 1000 '#d0c594';Rect 18 18 664 964 '#263d3c';Rect 30 30 640 940 '#d0c594';Txt 'RE-ELECT' 20 45 107 '#263d3c' 'Impact' 660;Txt 'THE CONDUCTOR' 25 183 78 '#263d3c' 'Impact' 650;Poly @((120),(465),(173),(366),(527),(366),(580),(465),(530),(510),(166),(510)) '#263d3c';Oval 163 474 370 77 '#263d3c';Rect 162 456 372 33 '#d0c594';Oval 319 384 60 58 '#d0c594';Txt 'fewer buffering' 20 656 49 '#263d3c' 'Arial' 660;Txt 'more kino' 20 728 63 '#263d3c' 'Arial' 660;Txt 'KEEP THE REELS TURNING' 20 912 24 '#263d3c' 'Arial' 660;Save 6500
Begin 'cabge' 1400 450 '#395c44';for($i=0;$i -lt 14;$i++){Rect ($i*100) 0 48 450 '#456b4e'};Txt 'CABGE' 20 20 228 '#e1d5a4' 'Georgia' 1360;Txt 'fresh daily' 20 297 71 '#d6c99b' 'Comic Sans MS' 1360;Save 4500
Begin 'turf' 1400 700 'Transparent';Rect 110 240 1110 298 '#697164';Txt 'YEE NEVA LOSE' 25 55 133 '#927095' 'Comic Sans MS' 1350;Line @((100),(167),(1290),(242)) '#507b48' 18;Line @((140),(242),(1270),(171)) '#507b48' 12;Txt 'PEPE WINS' 60 289 156 '#73a45e' 'Comic Sans MS' 1280;Rect 110 416 330 90 '#697164';Line @((160),(527),(1010),(553)) '#577e4c' 7;Oval 1110 541 98 73 '#97769d';Oval 1179 497 100 60 '#97769d';Line @((1135),(593),(1117),(644),(1164),(643)) '#97769d' 13;Line @((1183),(592),(1205),(646),(1249),(643)) '#97769d' 13;Line @((1118),(568),(1063),(536)) '#97769d' 13;Oval 1234 512 9 9 '#2b3034';
for($i=0;$i -lt 1600;$i++){$x=$rng.Next(70,1320);$y=$rng.Next(65,545);$br=[Drawing.SolidBrush]::new([Drawing.Color]::FromArgb($rng.Next(5,40),84,135,77));$g.FillEllipse($br,$x,$y,2,2);$br.Dispose()};Save 0
Begin 'cinema' 1600 700 'Transparent'
foreach($row in @((@('ABSOLUTE',48)),(@('CINEMA',283)))){$s=$row[0];$y=[int]$row[1];for($dx=-8;$dx -le 8;$dx+=8){for($dy=-8;$dy -le 8;$dy+=8){Txt $s (165+$dx) ($y+$dy) 205 '#202729' 'Impact' 1270}};Txt $s 165 $y 205 '#bac3bc' 'Impact' 1270;Txt $s 165 ($y+4) 199 '#d1d6cb' 'Impact' 1270}
foreach($x in @((210),(480),(790),(1120),(1390))){Line @(($x),(484),($x),(($rng.Next(525,620)))) '#afbbb3' 7}
Line @((40),(570),(31),(349),(40),(278),(58),(280),(72),(370),(77),(242),(96),(240),(102),(368),(118),(248),(138),(254),(132),(381),(155),(281),(174),(287),(161),(441),(121),(503),(120),(570)) '#d1d6cb' 9
Line @((1552),(570),(1567),(350),(1557),(276),(1538),(280),(1524),(369),(1520),(243),(1501),(242),(1495),(369),(1477),(252),(1457),(257),(1464),(383),(1440),(283),(1421),(290),(1436),(439),(1479),(503),(1480),(570)) '#d1d6cb' 9;Save 0
Write-Output 'Twelve original procedural artwork PNGs complete.'

