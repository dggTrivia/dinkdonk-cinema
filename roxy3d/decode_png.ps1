param([Parameter(Mandatory=$true)][string]$List)
$ErrorActionPreference = 'Stop'
$env:TEMP = Join-Path $PSScriptRoot 'cache/temp'
$env:TMP = $env:TEMP
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.IO;
public static class RoxyPngDecoder {
    public static void Decode(string src, string dst) {
        using (var image = new Bitmap(src)) {
            int w = image.Width, h = image.Height;
            var bits = image.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            byte[] rgba = new byte[w*h*4];
            byte[] row = new byte[Math.Abs(bits.Stride)];
            for (int y=0;y<h;y++) {
                Marshal.Copy(IntPtr.Add(bits.Scan0,y*bits.Stride),row,0,row.Length);
                for (int x=0;x<w;x++) {
                    int i=x*4, o=(y*w+x)*4;
                    rgba[o]=row[i+2]; rgba[o+1]=row[i+1]; rgba[o+2]=row[i]; rgba[o+3]=row[i+3];
                }
            }
            image.UnlockBits(bits);
            File.WriteAllBytes(dst,rgba);
        }
    }
}
'@
foreach ($line in Get-Content -LiteralPath $List) {
    $parts = $line.Split("`t")
    [RoxyPngDecoder]::Decode($parts[0], $parts[1])
}
