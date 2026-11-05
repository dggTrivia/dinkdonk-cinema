param(
    [ValidateSet('preview','final','calibrate','package')][string]$Mode = 'final',
    [int]$Samples = 96
)
$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$standbyDir = Split-Path -Parent $projectDir
$blenderPath = Join-Path $standbyDir 'tools/blender-5.2.3-windows-x64/blender.exe'
$pythonPath = Join-Path $standbyDir 'tools/blender-5.2.3-windows-x64/5.2/python/bin/python.exe'
$previousEnvironment = @{}
foreach ($envName in @('OPTIX_CACHE_PATH','CUDA_CACHE_PATH','TEMP','TMP','PYTHONDONTWRITEBYTECODE')) {
    $previousEnvironment[$envName] = [Environment]::GetEnvironmentVariable($envName, 'Process')
}
foreach ($cacheName in @('optix','cuda','temp')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $projectDir "cache/$cacheName") | Out-Null
}
$env:OPTIX_CACHE_PATH = Join-Path $projectDir 'cache/optix'
$env:CUDA_CACHE_PATH = Join-Path $projectDir 'cache/cuda'
$env:TEMP = Join-Path $projectDir 'cache/temp'
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
Push-Location $standbyDir
try {
    if ($Mode -eq 'calibrate' -or $Mode -eq 'final') {
        & $blenderPath -b -P (Join-Path $projectDir 'calibrate.py')
        if ($LASTEXITCODE -ne 0) { throw "Calibration process failed: $LASTEXITCODE" }
    }
    if ($Mode -eq 'preview' -or $Mode -eq 'final') {
        & $blenderPath -b -P (Join-Path $projectDir 'build_scene.py') -- --mode $Mode --samples $Samples
        if ($LASTEXITCODE -ne 0) { throw "Render process failed: $LASTEXITCODE" }
    }
    if ($Mode -eq 'package' -or $Mode -eq 'final') {
        & $pythonPath (Join-Path $projectDir 'package_layers.py')
        if ($LASTEXITCODE -ne 0) { throw "Layer packaging failed: $LASTEXITCODE" }
        & $pythonPath (Join-Path $projectDir 'qa/check_registration.py')
        if ($LASTEXITCODE -ne 0) { throw "Registration / slice check failed: $LASTEXITCODE" }
        & $pythonPath (Join-Path $projectDir 'qa/verify_delivery.py')
        if ($LASTEXITCODE -ne 0) { throw "Delivery inventory check failed: $LASTEXITCODE" }
    }
} finally {
    Pop-Location
    foreach ($envName in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($envName, $previousEnvironment[$envName], 'Process')
    }
}
