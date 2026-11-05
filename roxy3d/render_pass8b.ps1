param([ValidateSet('preview','all','package')][string]$Mode='all')
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$workspaceRoot=Split-Path -Parent $taskRoot
$blender=Join-Path $workspaceRoot 'tools/blender-5.2.3-windows-x64/blender.exe'
$python=Join-Path $workspaceRoot 'tools/blender-5.2.3-windows-x64/5.2/python/bin/python.exe'
$savedEnvironment=@{}
foreach ($key in @('TEMP','TMP','OPTIX_CACHE_PATH','CUDA_CACHE_PATH')) {
    $savedEnvironment[$key]=[Environment]::GetEnvironmentVariable($key,'Process')
    $folder=switch ($key) {'OPTIX_CACHE_PATH' {'optix'} 'CUDA_CACHE_PATH' {'cuda'} default {'temp'}}
    $path=Join-Path $taskRoot "cache/$folder";New-Item -ItemType Directory -Force $path | Out-Null
    [Environment]::SetEnvironmentVariable($key,$path,'Process')
}
function Run-Blender([string]$script,[string[]]$ExtraArgs=@()) {
    & $blender -b --python-exit-code 1 -P (Join-Path $taskRoot $script) -- @ExtraArgs
    if ($LASTEXITCODE -ne 0) {throw "$script failed"}
}
function Run-Python([string]$script) {
    & $python (Join-Path $taskRoot $script)
    if ($LASTEXITCODE -ne 0) {throw "$script failed"}
}
try {
    if ($Mode -eq 'preview') {Run-Blender 'build_pass8b.py' @('--preview');return}
    if ($Mode -eq 'all') {
        Run-Python 'pass8b_common.py'
        Run-Blender 'build_pass8b.py'
        Run-Blender 'calibrate_pass8b.py'
        Run-Python 'weather_pass8b.py'
        Run-Python 'glass_pass8b.py'
        Run-Blender 'encode_pass8b.py'
    }
    Run-Python 'finalize_pass8b.py'
    Run-Python 'write_notes_pass8b.py'
    Write-Output 'Pass 8b complete in out8b. All eight live packs verified unchanged.'
} finally {
    foreach ($key in $savedEnvironment.Keys) {[Environment]::SetEnvironmentVariable($key,$savedEnvironment[$key],'Process')}
}
