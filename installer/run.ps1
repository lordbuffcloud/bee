param(
    [switch]$NoBackend,
    [switch]$NoUi
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$backend = Join-Path $repoRoot 'backend'
$venvPython = Join-Path $backend '.venv\Scripts\python.exe'
$envPath = Join-Path $repoRoot '.env'

function Get-EnvValue {
    param([string]$Path, [string]$Key)
    if (-not (Test-Path $Path)) { return $null }
    $content = Get-Content -Raw -Path $Path
    $regex = '(?m)^' + [regex]::Escape($Key) + '=(.*)$'
    if ($content -match $regex) { return $Matches[1] }
    return $null
}

function Start-EvermemOS {
    param([string]$Root, [int]$Port)
    if (-not (Test-Path $Root)) {
        Write-Warning "[B.E.E] EvermemOS root not found at $Root"
        return
    }
    $portOpen = $false
    try {
        $portOpen = (Test-NetConnection -ComputerName 'localhost' -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
    } catch { }
    if ($portOpen) {
        return
    }
    $uvExe = $null
    $uvArgs = @()
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        $uvExe = 'uv'
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $uvExe = 'python'
        $uvArgs = @('-m', 'uv')
    }
    if (-not $uvExe) {
        Write-Warning "[B.E.E] uv not found. EvermemOS server not started."
        return
    }
    Write-Host "[B.E.E] Starting EvermemOS..."
    $uvArgString = ($uvArgs + @('run', 'python', 'src/run.py', '--port', $Port)) -join ' '
    Start-Process powershell -WorkingDirectory $Root -ArgumentList '-NoExit', '-Command', "$uvExe $uvArgString"
}

if (-not (Test-Path $venvPython)) {
    throw "[B.E.E] Virtual environment not found. Run .\installer\install.ps1 first."
}

$evermemLocal = Get-EnvValue -Path $envPath -Key 'EVERMEM_LOCAL'
if ($evermemLocal -eq '1') {
    $evermemRoot = Get-EnvValue -Path $envPath -Key 'EVERMEM_ROOT'
    if (-not $evermemRoot) { $evermemRoot = Join-Path $repoRoot '.evermemos' }
    $evermemPortRaw = Get-EnvValue -Path $envPath -Key 'EVERMEM_PORT'
    $evermemPort = 8001
    if ($evermemPortRaw) { $evermemPort = [int]$evermemPortRaw }
    Start-EvermemOS -Root $evermemRoot -Port $evermemPort
}

if (-not $NoBackend) {
    Write-Host "[B.E.E] Starting backend..."
    Start-Process powershell -WorkingDirectory $backend -ArgumentList '-NoExit', '-Command', "& `"$venvPython`" main.py"
    Write-Host "[B.E.E] Backend started on http://localhost:8080"
}

if (-not $NoUi) {
    Write-Host "[B.E.E] Starting Python UI..."
    Start-Process powershell -WorkingDirectory $backend -ArgumentList '-NoExit', '-Command', "& `"$venvPython`" -m bee.ui"
    Write-Host "[B.E.E] Python UI started."
}
