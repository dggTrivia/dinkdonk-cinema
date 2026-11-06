param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$cinemaRoot = $PSScriptRoot
$logRoot = Join-Path $env:LOCALAPPDATA 'DinkDonkCinema'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Get-Listener($port) {
    @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
}
function Assert-ServicePort($port, $script) {
    foreach ($listener in (Get-Listener $port)) {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        if (!$process.CommandLine -or !$process.CommandLine.Contains($script)) {
            throw "Port $port is used by another application (PID $($listener.OwningProcess)). Nothing was stopped."
        }
    }
}
function Wait-Endpoint($url) {
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        try { return Invoke-RestMethod -Uri $url -TimeoutSec 2 } catch { Start-Sleep -Milliseconds 250 }
    }
    throw "Service did not start: $url. See logs in $logRoot."
}

try {
    $serverScript = Join-Path $cinemaRoot 'standby-server.js'
    $relayScript = Join-Path $cinemaRoot 'cinema-chat-relay.py'
    $bridgeScript = Join-Path $cinemaRoot 'obs-bridge.js'
    # Check all ports before starting anything. Never terminate an unrelated app.
    Assert-ServicePort 18770 $serverScript
    Assert-ServicePort 18765 $relayScript
    foreach ($listener in (Get-Listener 18790)) {
        $bridgeProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        $bridgeCommand = $bridgeProcess.CommandLine
        $relativeBridge = $bridgeCommand -match 'node.exe"?\s+obs-bridge\.js\s*$'
        if (!$bridgeCommand -or (!$bridgeCommand.Contains($bridgeScript) -and !$relativeBridge)) {
            throw "Port 18790 is used by another application. Nothing was stopped."
        }
        $bridgeHealth = Invoke-WebRequest 'http://127.0.0.1:18790/' -UseBasicParsing -TimeoutSec 2
        if ($bridgeHealth.Content -notlike 'obs-bridge:*') { throw 'Unexpected service on bridge port 18790.' }
    }
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $node = if ($nodeCommand) { $nodeCommand.Source } else {
        @(
            (Join-Path $env:ProgramFiles 'nodejs\node.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\nodejs\node.exe'),
            (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
        ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }
    if (!$node) { throw 'Node.js could not be found. Install Node 22 or newer from https://nodejs.org/' }
    $python = (& py -c 'import sys, aiohttp; print(sys.executable)' | Select-Object -Last 1)
    if ($LASTEXITCODE -ne 0 -or !$python -or !(Test-Path -LiteralPath $python)) {
        throw 'Python with aiohttp is required. Install with: py -m pip install aiohttp'
    }
    if (!(Get-Listener 18765)) {
        Start-Process -FilePath $python -ArgumentList @('-u', ('"' + $relayScript + '"')) -WorkingDirectory $cinemaRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'relay.log') -RedirectStandardError (Join-Path $logRoot 'relay-error.log') | Out-Null
    }
    $relay = Wait-Endpoint 'http://127.0.0.1:18765/healthz'
    if ($relay.service -ne 'cinema-chat-relay') { throw 'Unexpected service on chat relay port.' }
    if (!(Get-Listener 18770)) {
        $env:STANDBY_PORT = '18770'
        Start-Process -FilePath $node -ArgumentList ('"' + $serverScript + '"') -WorkingDirectory $cinemaRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'server.log') -RedirectStandardError (Join-Path $logRoot 'server-error.log') | Out-Null
    }
    $state = Wait-Endpoint 'http://127.0.0.1:18770/ctl/state'
    if ($state.controlVersion -ne 2) { throw 'Unexpected cinema server response.' }
    if (!(Get-Listener 18790)) {
        $env:OBS_BRIDGE_PORT = '18790'
        $env:CINEMA_CONTROL_URL = 'http://127.0.0.1:18770/ctl/state'
        Start-Process -FilePath $node -ArgumentList ('"' + $bridgeScript + '"') -WorkingDirectory $cinemaRoot -WindowStyle Normal | Out-Null
    }
    $bridgeHealth = Wait-Endpoint 'http://127.0.0.1:18790/'
    if ([string]$bridgeHealth -notlike 'obs-bridge:*') { throw 'Unexpected service on bridge port 18790.' }
    # Windows opens an HTTP URL in the default browser, normally in a new tab.
    if (!$NoBrowser) { Start-Process 'http://127.0.0.1:18770/control.html' }
    "Cinema ready. Control: http://127.0.0.1:18770/control.html"
} catch {
    $_.Exception.Message | Set-Content -LiteralPath (Join-Path $logRoot 'launch-error.txt')
    if (!$NoBrowser) {
        $shell = New-Object -ComObject WScript.Shell
        $shell.Popup($_.Exception.Message, 0, 'Cinema could not start', 16) | Out-Null
    }
    Write-Error $_
    exit 1
}
