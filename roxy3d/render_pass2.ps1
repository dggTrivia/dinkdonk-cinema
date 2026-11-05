param(
    [ValidateSet('preview','stills','all','loops')][string]$Mode = 'all',
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
        & $blender -b -P (Join-Path $taskRoot 'build_pass2.py') -- --mode preview --samples 32
        if ($LASTEXITCODE -ne 0) { throw 'Preview failed' }
        return
    }
    if ($Mode -in @('stills','all')) {
        & $blender -b -P (Join-Path $taskRoot 'calibrate_pass2.py')
        if ($LASTEXITCODE -ne 0) { throw 'Calibration failed' }
        & $blender -b -P (Join-Path $taskRoot 'build_pass2.py') -- --mode final --samples $Samples
        if ($LASTEXITCODE -ne 0) { throw 'Stills render failed' }
        & $python (Join-Path $taskRoot 'package_pass2.py')
        if ($LASTEXITCODE -ne 0) { throw 'Stills packaging failed' }
        & $python (Join-Path $taskRoot 'verify_pass2.py')
        if ($LASTEXITCODE -ne 0) { throw 'Stills QA failed' }
        Write-Output 'Layout 2 stills and manifest are ready in out2/.'
    }
    if ($Mode -in @('loops','all')) {
        & $blender -b -P (Join-Path $taskRoot 'render_loop_basis.py')
        if ($LASTEXITCODE -ne 0) { throw 'Light basis render failed' }
        & $python (Join-Path $taskRoot 'make_loop.py')
        if ($LASTEXITCODE -ne 0) { throw 'Loop composition failed' }
        & $blender -b -P (Join-Path $taskRoot 'encode_loop.py')
        if ($LASTEXITCODE -ne 0) { throw 'VP9 encoding failed' }
        & $python (Join-Path $taskRoot 'finalize_loop.py')
        if ($LASTEXITCODE -ne 0) { throw 'Decoded video QA failed' }
        & $python (Join-Path $taskRoot 'verify_pass2.py')
        if ($LASTEXITCODE -ne 0) { throw 'Final QA failed' }
    }
} finally {
    foreach ($key in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key,$savedEnvironment[$key],'Process')
    }
}
