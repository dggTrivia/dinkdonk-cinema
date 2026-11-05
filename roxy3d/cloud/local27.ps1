param([string]$Script='pipeline.py',[string]$Mode='smoke',[string]$Log='smoke-fast27.log')
$ErrorActionPreference='Stop'
$taskRoot=Join-Path $PSScriptRoot 'bundle'
foreach ($item in @('temp','cuda','optix','user')) { New-Item -ItemType Directory -Force "$taskRoot/work/cache/$item" | Out-Null }
$env:TEMP="$taskRoot/work/cache/temp"; $env:TMP=$env:TEMP
$env:CUDA_CACHE_PATH="$taskRoot/work/cache/cuda"; $env:OPTIX_CACHE_PATH="$taskRoot/work/cache/optix"
$env:BLENDER_USER_RESOURCES="$taskRoot/work/cache/user"; $env:PYTHONDONTWRITEBYTECODE='1'
$taskBlender=Join-Path $PSScriptRoot '../../tools/blender-5.2.3-windows-x64/blender.exe'
$ErrorActionPreference='Continue'
& $taskBlender -b --python-exit-code 1 --python "$taskRoot/$Script" -- $Mode *> "$PSScriptRoot/$Log"
if ($LASTEXITCODE -ne 0) { throw "Blender failed ($LASTEXITCODE): $Log" }
