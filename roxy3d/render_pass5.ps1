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
function Run-Blender([string]$script,[string[]]$ExtraArgs=@()) {
    & $blender -b -P (Join-Path $taskRoot $script) -- @ExtraArgs
    if ($LASTEXITCODE -ne 0) { throw "$script failed" }
}
function Run-Python([string]$script) {
    & $python (Join-Path $taskRoot $script)
    if ($LASTEXITCODE -ne 0) { throw "$script failed" }
}
try {
    $qaFolder = Join-Path $taskRoot 'qa5'
    New-Item -ItemType Directory -Force -Path $qaFolder | Out-Null
    $baselinePath = Join-Path $qaFolder 'live_before.json'
    if (-not (Test-Path -LiteralPath $baselinePath)) {
        $baseline = foreach ($folder in @('out','out2','out3','out4')) {
            Get-ChildItem -LiteralPath (Join-Path $taskRoot $folder) -File -Recurse | ForEach-Object {
                @{path=$_.FullName;bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
            }
        }
        $baseline | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $baselinePath -Encoding UTF8
    }
    if ($Mode -eq 'preview') {
        Run-Blender 'render_cat_pass5.py' @('--preview')
        return
    }
    Run-Blender 'calibrate_pass5.py'
    if ($Mode -eq 'all') {
        Run-Blender 'render_vehicle_pass5.py' @('--samples',[string]$Samples)
        Run-Blender 'render_cat_pass5.py'
    }
    Run-Python 'package_vehicle_pass5.py'
    Run-Python 'package_cat_pass5.py'
    Run-Python 'qa_pass5.py'
    Run-Blender 'encode_preview_pass5.py'
    Run-Python 'verify_pass5.py'
    Write-Output 'Pass 5 is ready in out5. All four live folders verified unchanged.'
} finally {
    foreach ($key in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key,$savedEnvironment[$key],'Process')
    }
}
