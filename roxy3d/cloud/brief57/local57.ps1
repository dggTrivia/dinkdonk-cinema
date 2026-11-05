param([ValidateSet('preflight','smoke')][string]$Mode='preflight')
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$taskBundle=Join-Path $PSScriptRoot 'verify/bundle'
foreach($taskName in @('temp','cuda','optix','config')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot ('local-cache/'+$taskName)) | Out-Null
}
$env:TEMP=Join-Path $PSScriptRoot 'local-cache/temp'
$env:TMP=$env:TEMP
$env:CUDA_CACHE_PATH=Join-Path $PSScriptRoot 'local-cache/cuda'
$env:OPTIX_CACHE_PATH=Join-Path $PSScriptRoot 'local-cache/optix'
$env:XDG_CACHE_HOME=Join-Path $PSScriptRoot 'local-cache'
$env:BLENDER_USER_RESOURCES=Join-Path $PSScriptRoot 'local-cache/config'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONWARNINGS='ignore::DeprecationWarning'
$taskBlender=Join-Path (Split-Path -Parent $taskRoot) 'tools/blender-5.2.3-windows-x64/blender.exe'
$taskStamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$taskLog=Join-Path $PSScriptRoot ($Mode+'-'+$taskStamp+'.log')
$ErrorActionPreference='Continue'
& $taskBlender -b --factory-startup --python-exit-code 1 -t 8 -P (Join-Path $taskBundle 'pipeline.py') -- $Mode *> $taskLog
$taskCode=$LASTEXITCODE
Write-Output ('LOG '+$taskLog)
Get-Content -LiteralPath $taskLog -Tail 16
exit $taskCode
