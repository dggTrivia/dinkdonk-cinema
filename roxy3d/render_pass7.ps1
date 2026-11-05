param([ValidateSet('preview','all','package')][string]$Mode='all',[int]$Samples=96)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$workspaceRoot=Split-Path -Parent $taskRoot
$blender=Join-Path $workspaceRoot 'tools/blender-5.2.3-windows-x64/blender.exe'
$python=Join-Path $workspaceRoot 'tools/blender-5.2.3-windows-x64/5.2/python/bin/python.exe'
$savedEnvironment=@{}
foreach ($key in @('TEMP','TMP','OPTIX_CACHE_PATH','CUDA_CACHE_PATH')) {
    $savedEnvironment[$key]=[Environment]::GetEnvironmentVariable($key,'Process')
    $folder=switch ($key) {'OPTIX_CACHE_PATH' {'optix'} 'CUDA_CACHE_PATH' {'cuda'} default {'temp'}}
    $path=Join-Path $taskRoot "cache/$folder"
    New-Item -ItemType Directory -Force $path | Out-Null
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
    $qaFolder=Join-Path $taskRoot 'qa7';New-Item -ItemType Directory -Force $qaFolder | Out-Null
    $baselinePath=Join-Path $qaFolder 'live_before.json'
    if (-not (Test-Path -LiteralPath $baselinePath)) {
        $baseline=@(foreach ($folder in @('out','out2','out3','out4','out5','out6')) {
            Get-ChildItem -LiteralPath (Join-Path $taskRoot $folder) -File -Recurse | ForEach-Object {
                @{path=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()}
            }
        })
        ConvertTo-Json -Depth 5 -InputObject $baseline | Set-Content -LiteralPath $baselinePath -Encoding UTF8
    }
    if ($Mode -eq 'preview') {Run-Blender 'render_items_pass7.py' @('--preview');return}
    if ($Mode -eq 'all') {Run-Blender 'render_items_pass7.py' @('--samples',[string]$Samples)}
    Run-Blender 'calibrate_pass7.py'
    Run-Python 'package_pass7.py'
    Run-Python 'qa_pass7.py'
    Run-Blender 'encode_preview_pass7.py'
    Run-Python 'verify_pass7.py'
    Write-Output 'Pass 7 complete in out7. All six live packs verified unchanged.'
} finally {
    foreach ($key in $savedEnvironment.Keys) {[Environment]::SetEnvironmentVariable($key,$savedEnvironment[$key],'Process')}
}
