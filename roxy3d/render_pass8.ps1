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
    $qaFolder=Join-Path $taskRoot 'qa8';New-Item -ItemType Directory -Force $qaFolder | Out-Null
    $baselinePath=Join-Path $qaFolder 'live_before.json'
    if (-not (Test-Path -LiteralPath $baselinePath)) {
        $baseline=@(foreach ($folder in @('out','out2','out3','out4','out5','out6','out7')) {
            Get-ChildItem -LiteralPath (Join-Path $taskRoot $folder) -File -Recurse | ForEach-Object {
                @{path=$_.FullName.Substring($taskRoot.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower()}
            }
        })
        ConvertTo-Json -Depth 5 -InputObject $baseline | Set-Content -LiteralPath $baselinePath -Encoding UTF8
    }
    if ($Mode -in @('preview','all')) {
        Run-Blender 'build_pass8.py' @('--lighting')
        # The preview and its zero-occlusion report are journalled before loops.
        if ($Mode -eq 'preview') {return}
        Run-Blender 'render_wet_scene_pass8.py'
        Run-Blender 'geometry_qa_pass8.py'
        Run-Blender 'calibrate_pass8.py'
        Run-Python 'weather_pass8.py'
        Run-Blender 'render_wet_print_pass8.py'
        Run-Python 'package_props_pass8.py'
        Run-Python 'roof_water_pass8.py'
        Run-Blender 'encode_pass8.py'
    }
    Run-Python 'finalize_pass8.py'
    Run-Python 'write_notes_pass8.py'
    Write-Output 'Pass 8 complete in out8; all seven live packs verified unchanged.'
} finally {
    foreach ($key in $savedEnvironment.Keys) {[Environment]::SetEnvironmentVariable($key,$savedEnvironment[$key],'Process')}
}
