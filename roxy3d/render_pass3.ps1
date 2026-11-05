param(
    [ValidateSet('preview','all','package')][string]$Mode = 'all',
    [int]$Samples = 96
)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$workspaceRoot = Split-Path -Parent $taskRoot
$blender = Join-Path $workspaceRoot 'tools/blender-5.2.3-windows-x64/blender.exe'
$python = Join-Path $workspaceRoot 'tools/blender-5.2.3-windows-x64/5.2/python/bin/python.exe'
$savedEnvironment = @{}
foreach ($key in @('TEMP','TMP','OPTIX_CACHE_PATH','CUDA_CACHE_PATH')) {
    $savedEnvironment[$key] = [Environment]::GetEnvironmentVariable($key,'Process')
    $folder = switch ($key) { 'OPTIX_CACHE_PATH' {'optix'} 'CUDA_CACHE_PATH' {'cuda'} default {'temp'} }
    $path = Join-Path $taskRoot "cache/$folder"
    New-Item -ItemType Directory -Force -Path $path | Out-Null
    [Environment]::SetEnvironmentVariable($key,$path,'Process')
}
try {
    if ($Mode -eq 'preview') {
        & $blender -b -P (Join-Path $taskRoot 'build_vehicles.py') -- --preview --samples 32
        if ($LASTEXITCODE -ne 0) { throw 'Vehicle preview render failed' }
        & $python (Join-Path $taskRoot 'package_vehicles.py') --preview
        if ($LASTEXITCODE -ne 0) { throw 'Vehicle preview packaging failed' }
        return
    }
    & $blender -b -P (Join-Path $taskRoot 'calibrate_pass3.py')
    if ($LASTEXITCODE -ne 0) { throw 'Vehicle calibration failed' }
    if ($Mode -eq 'all') {
        & $blender -b -P (Join-Path $taskRoot 'build_vehicles.py') -- --samples $Samples
        if ($LASTEXITCODE -ne 0) { throw 'Vehicle render failed' }
    }
    & $python (Join-Path $taskRoot 'package_vehicles.py')
    if ($LASTEXITCODE -ne 0) { throw 'Vehicle packaging failed' }
    & $python (Join-Path $taskRoot 'verify_vehicles.py')
    if ($LASTEXITCODE -ne 0) { throw 'Vehicle validation failed' }
    Write-Output 'Pass 3 complete in out3. Both live output folders verified unchanged.'
} finally {
    foreach ($key in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key,$savedEnvironment[$key],'Process')
    }
}
