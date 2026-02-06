param(
    [string]$EvermemEndpoint,
    [string]$EvermemApiKey,
    [string]$EvermemGroupId,
    [string]$EvermemGroupName,
    [string]$EvermemSender = "bee",
    [string]$EvermemSenderName = "B.E.E.",
    [string]$EvermemRole = "assistant",
    [string]$EvermemScene,
    [string]$EvermemRoot,
    [int]$EvermemPort = 8001,
    [string]$EvermemLlmApiKey,
    [string]$EvermemVectorizeApiKey,
    [switch]$NoEvermem,
    [string]$OpenAiApiKey,
    [string]$OpenAiTranscribeModel = "gpt-4o-mini-transcribe",
    [string]$BraveSearchApiKey,
    [string]$BraveSearchEndpoint,
    [string]$BrowserUseApiKey,
    [string]$BrowserUseLlm,
    [switch]$NonInteractive,
    [switch]$BuildWebUi,
    [switch]$NoRun
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$envPath = Join-Path $repoRoot '.env'
$envExample = Join-Path $repoRoot '.env.example'

function Get-EnvValue {
    param([string]$Path, [string]$Key)
    if (-not (Test-Path $Path)) { return $null }
    $content = Get-Content -Raw -Path $Path
    $regex = '(?m)^' + [regex]::Escape($Key) + '=(.*)$'
    if ($content -match $regex) { return $Matches[1] }
    return $null
}

function Set-EnvValue {
    param([string]$Path, [string]$Key, [string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return }
    $content = Get-Content -Raw -Path $Path
    $regex = '(?m)^' + [regex]::Escape($Key) + '=.*$'
    if ($content -match $regex) {
        $content = [regex]::Replace($content, $regex, "$Key=$Value")
    } else {
        $content = $content.TrimEnd() + "`r`n$Key=$Value`r`n"
    }
    Set-Content -Path $Path -Value $content
}

function Ensure-EvermemOS {
    param(
        [string]$Root,
        [int]$Port,
        [string]$LlmApiKey,
        [string]$VectorizeApiKey
    )
    if (-not $Root) { return $false }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warning "[B.E.E] git not found. Skipping EvermemOS install."
        return $false
    }

    if (-not (Test-Path $Root)) {
        Write-Host "[B.E.E] Cloning EvermemOS..."
        git clone https://github.com/EverMind-AI/EverMemOS.git $Root
    } elseif (Test-Path (Join-Path $Root ".git")) {
        Write-Host "[B.E.E] Updating EvermemOS..."
        git -C $Root pull --ff-only
    } else {
        Write-Warning "[B.E.E] EvermemOS path exists but is not a git repo: $Root"
        return $false
    }

    $evermemEnvTemplate = Join-Path $Root "env.template"
    $evermemEnv = Join-Path $Root ".env"
    if ((Test-Path $evermemEnvTemplate) -and -not (Test-Path $evermemEnv)) {
        Copy-Item -Path $evermemEnvTemplate -Destination $evermemEnv
    }
    if (Test-Path $evermemEnv) {
        Set-EnvValue -Path $evermemEnv -Key "LLM_API_KEY" -Value $LlmApiKey
        Set-EnvValue -Path $evermemEnv -Key "VECTORIZE_API_KEY" -Value $VectorizeApiKey
    }

    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Push-Location $Root
        $dockerComposeOk = $false
        try {
            docker compose version *> $null
            $dockerComposeOk = $true
        } catch { }
        if ($dockerComposeOk) {
            docker compose up -d
        } elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
            docker-compose up -d
        } else {
            Write-Warning "[B.E.E] Docker Compose not available. EvermemOS dependencies may not be running."
        }
        Pop-Location
    } else {
        Write-Warning "[B.E.E] Docker not found. EvermemOS dependencies may not be running."
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
        Write-Host "[B.E.E] uv not found. Attempting install with pip..."
        try {
            python -m pip install --user uv
        } catch {
            Write-Warning "[B.E.E] Failed to install uv. Install uv and run EvermemOS manually."
            return $false
        }
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            $uvExe = 'uv'
            $uvArgs = @()
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            $uvExe = 'python'
            $uvArgs = @('-m', 'uv')
        }
    }

    Push-Location $Root
    if ($uvExe) {
        & $uvExe @uvArgs sync
    } else {
        Write-Warning "[B.E.E] uv still not available. Skipping EvermemOS dependency install."
    }
    Pop-Location

    return $true
}

if (-not (Test-Path $envPath)) {
    Copy-Item -Path $envExample -Destination $envPath
    Write-Host "[B.E.E] Created .env from .env.example"
}

if (-not $EvermemEndpoint) { $EvermemEndpoint = $env:EVERMEM_ENDPOINT }
if (-not $EvermemApiKey) { $EvermemApiKey = $env:EVERMEM_API_KEY }
if (-not $EvermemGroupId) { $EvermemGroupId = $env:EVERMEM_GROUP_ID }
if (-not $EvermemGroupName) { $EvermemGroupName = $env:EVERMEM_GROUP_NAME }
if (-not $EvermemScene) { $EvermemScene = $env:EVERMEM_SCENE }
if (-not $EvermemRoot) { $EvermemRoot = $env:EVERMEM_ROOT }
if ($env:EVERMEM_PORT) { $EvermemPort = [int]$env:EVERMEM_PORT }
if (-not $EvermemLlmApiKey) { $EvermemLlmApiKey = $env:EVERMEM_LLM_API_KEY }
if (-not $EvermemVectorizeApiKey) { $EvermemVectorizeApiKey = $env:EVERMEM_VECTORIZE_API_KEY }
if (-not $OpenAiApiKey) { $OpenAiApiKey = $env:OPENAI_API_KEY }
if (-not $OpenAiTranscribeModel) { $OpenAiTranscribeModel = $env:OPENAI_TRANSCRIBE_MODEL }
if (-not $BraveSearchApiKey) { $BraveSearchApiKey = $env:BRAVE_SEARCH_API_KEY }
if (-not $BraveSearchEndpoint) { $BraveSearchEndpoint = $env:BRAVE_SEARCH_ENDPOINT }
if (-not $BrowserUseApiKey) { $BrowserUseApiKey = $env:BROWSER_USE_API_KEY }
if (-not $BrowserUseLlm) { $BrowserUseLlm = $env:BROWSER_USE_LLM }

$existingEndpoint = Get-EnvValue -Path $envPath -Key 'EVERMEM_ENDPOINT'
$existingApiKey = Get-EnvValue -Path $envPath -Key 'EVERMEM_API_KEY'
$existingEvermemLocal = Get-EnvValue -Path $envPath -Key 'EVERMEM_LOCAL'
$existingEvermemRoot = Get-EnvValue -Path $envPath -Key 'EVERMEM_ROOT'
$existingEvermemPort = Get-EnvValue -Path $envPath -Key 'EVERMEM_PORT'
$existingEvermemScene = Get-EnvValue -Path $envPath -Key 'EVERMEM_SCENE'
$existingEvermemLlmApiKey = Get-EnvValue -Path $envPath -Key 'EVERMEM_LLM_API_KEY'
$existingEvermemVectorizeApiKey = Get-EnvValue -Path $envPath -Key 'EVERMEM_VECTORIZE_API_KEY'
$existingOpenAi = Get-EnvValue -Path $envPath -Key 'OPENAI_API_KEY'
$existingBrave = Get-EnvValue -Path $envPath -Key 'BRAVE_SEARCH_API_KEY'
$existingBrowserUse = Get-EnvValue -Path $envPath -Key 'BROWSER_USE_API_KEY'

if (-not $PSBoundParameters.ContainsKey('EvermemRoot') -and $existingEvermemRoot) { $EvermemRoot = $existingEvermemRoot }
if (-not $PSBoundParameters.ContainsKey('EvermemPort') -and $existingEvermemPort) { $EvermemPort = [int]$existingEvermemPort }
if (-not $PSBoundParameters.ContainsKey('EvermemScene') -and $existingEvermemScene) { $EvermemScene = $existingEvermemScene }
if (-not $PSBoundParameters.ContainsKey('EvermemLlmApiKey') -and $existingEvermemLlmApiKey) { $EvermemLlmApiKey = $existingEvermemLlmApiKey }
if (-not $PSBoundParameters.ContainsKey('EvermemVectorizeApiKey') -and $existingEvermemVectorizeApiKey) { $EvermemVectorizeApiKey = $existingEvermemVectorizeApiKey }

$useLocalEvermem = $false
if (-not $NoEvermem) {
    if (-not $EvermemEndpoint -and -not $existingEndpoint) {
        $EvermemEndpoint = "http://localhost:$EvermemPort"
        $useLocalEvermem = $true
    } elseif ($EvermemEndpoint -and $EvermemEndpoint -match 'localhost|127\.0\.0\.1') {
        $useLocalEvermem = $true
    } elseif ($existingEndpoint -and $existingEndpoint -match 'localhost|127\.0\.0\.1' -and $existingEvermemLocal -eq '1') {
        $useLocalEvermem = $true
    }
}

if (-not $EvermemRoot) { $EvermemRoot = Join-Path $repoRoot '.evermemos' }
if ($useLocalEvermem -and $EvermemEndpoint -and $EvermemEndpoint -match ':(\d{2,5})\b') {
    $EvermemPort = [int]$Matches[1]
}

if (-not $EvermemEndpoint -and -not $existingEndpoint -and -not $NonInteractive -and -not $NoEvermem) {
    $EvermemEndpoint = Read-Host 'EvermemOS endpoint (e.g. http://localhost:8000)'
}
if (-not $EvermemApiKey -and -not $existingApiKey -and -not $NonInteractive -and -not $useLocalEvermem) {
    $EvermemApiKey = Read-Host 'EvermemOS API key (leave blank if none)'
}
if (-not $OpenAiApiKey -and -not $existingOpenAi -and -not $NonInteractive) {
    $OpenAiApiKey = Read-Host 'OpenAI API key (for Whisper transcription)'
}
if (-not $BraveSearchApiKey -and -not $existingBrave -and -not $NonInteractive) {
    $BraveSearchApiKey = Read-Host 'Brave Search API key (optional)'
}
if (-not $BrowserUseApiKey -and -not $existingBrowserUse -and -not $NonInteractive) {
    $BrowserUseApiKey = Read-Host 'Browser Use API key (optional)'
}

if (-not $EvermemLlmApiKey) { $EvermemLlmApiKey = $OpenAiApiKey }
if (-not $EvermemVectorizeApiKey) { $EvermemVectorizeApiKey = $OpenAiApiKey }
if (-not $EvermemScene) { $EvermemScene = 'assistant' }

if (-not $BraveSearchEndpoint) { $BraveSearchEndpoint = 'https://api.search.brave.com/res/v1/web/search' }

$evermemLocalValue = $null
$evermemRootValue = $null
$evermemPortValue = $null
if ($useLocalEvermem) {
    $evermemLocalValue = '1'
    $evermemRootValue = $EvermemRoot
    $evermemPortValue = "$EvermemPort"
} elseif ($NoEvermem) {
    $evermemLocalValue = '0'
}

Set-EnvValue -Path $envPath -Key 'EVERMEM_ENDPOINT' -Value $EvermemEndpoint
Set-EnvValue -Path $envPath -Key 'EVERMEM_API_KEY' -Value $EvermemApiKey
Set-EnvValue -Path $envPath -Key 'EVERMEM_GROUP_ID' -Value $EvermemGroupId
Set-EnvValue -Path $envPath -Key 'EVERMEM_GROUP_NAME' -Value $EvermemGroupName
Set-EnvValue -Path $envPath -Key 'EVERMEM_SENDER' -Value $EvermemSender
Set-EnvValue -Path $envPath -Key 'EVERMEM_SENDER_NAME' -Value $EvermemSenderName
Set-EnvValue -Path $envPath -Key 'EVERMEM_ROLE' -Value $EvermemRole
Set-EnvValue -Path $envPath -Key 'EVERMEM_SCENE' -Value $EvermemScene
Set-EnvValue -Path $envPath -Key 'EVERMEM_LOCAL' -Value $evermemLocalValue
Set-EnvValue -Path $envPath -Key 'EVERMEM_ROOT' -Value $evermemRootValue
Set-EnvValue -Path $envPath -Key 'EVERMEM_PORT' -Value $evermemPortValue
Set-EnvValue -Path $envPath -Key 'EVERMEM_LLM_API_KEY' -Value $EvermemLlmApiKey
Set-EnvValue -Path $envPath -Key 'EVERMEM_VECTORIZE_API_KEY' -Value $EvermemVectorizeApiKey
Set-EnvValue -Path $envPath -Key 'OPENAI_API_KEY' -Value $OpenAiApiKey
Set-EnvValue -Path $envPath -Key 'OPENAI_TRANSCRIBE_MODEL' -Value $OpenAiTranscribeModel
Set-EnvValue -Path $envPath -Key 'BRAVE_SEARCH_API_KEY' -Value $BraveSearchApiKey
Set-EnvValue -Path $envPath -Key 'BRAVE_SEARCH_ENDPOINT' -Value $BraveSearchEndpoint
Set-EnvValue -Path $envPath -Key 'BROWSER_USE_API_KEY' -Value $BrowserUseApiKey
Set-EnvValue -Path $envPath -Key 'BROWSER_USE_LLM' -Value $BrowserUseLlm

if ($useLocalEvermem) {
    Write-Host "[B.E.E] Setting up EvermemOS..."
    $evermemOk = Ensure-EvermemOS -Root $EvermemRoot -Port $EvermemPort -LlmApiKey $EvermemLlmApiKey -VectorizeApiKey $EvermemVectorizeApiKey
    if (-not $evermemOk) {
        Write-Warning "[B.E.E] EvermemOS setup incomplete. Memory sync may be unavailable."
    }
}

Write-Host "[B.E.E] Installing backend dependencies..."
Push-Location (Join-Path $repoRoot 'backend')
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
Pop-Location

if ($BuildWebUi) {
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "[B.E.E] npm not found. Install Node.js or re-run without -BuildWebUi."
    }
    Write-Host "[B.E.E] Installing frontend dependencies and building..."
    Push-Location (Join-Path $repoRoot 'frontend')
    npm install
    npm run build
    Pop-Location
} else {
    Write-Host "[B.E.E] Skipping web UI build (use -BuildWebUi to enable)."
}

Write-Host "[B.E.E] Install complete."

if (-not $NoRun) {
    Write-Host "[B.E.E] Launching backend + Python UI..."
    & (Join-Path $PSScriptRoot 'run.ps1')
}
