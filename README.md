# B.E.E. (Binary Executive Engine)

B.E.E. is an OpenClaw-style agent platform with a hive manager UI, Telegram interface, and an opinionated memory + heartbeat system.

## Highlights
- Telegram control surface (aiogram)
- Memory system interface (EvermemOS)
- Heartbeat with configurable "thumps"
- Risk tolerance monitor with halt threshold
- Agent swarm stub for local Ollama workers
- React "Hive Manager" UI for onboarding and control

## Stack
- Backend: Python + FastAPI
- Frontend: React + Vite (TypeScript)

## Quickstart (Dev)
1. Backend
```
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
python main.py
```
2. Python UI
```
python -m bee.ui
```

Backend runs on `http://localhost:8080`.
Python UI runs as a desktop window (no browser required).

## Installer
Use the PowerShell installer to set up venv and launch the backend + Python UI:
```
.\installer\install.ps1
```
If you want to launch later:
```
.\installer\run.ps1
```
Skip auto-launch:
```
.\installer\install.ps1 -NoRun
```
Build the optional web UI:
```
.\installer\install.ps1 -BuildWebUi
```
By default, the installer provisions a local EvermemOS instance (clones to `.evermemos`, boots dependencies, and prepares the Python env) and sets `EVERMEM_ENDPOINT` to `http://localhost:8001`.
To skip local EvermemOS or target a remote endpoint:
```
.\installer\install.ps1 -NoEvermem
.\installer\install.ps1 -EvermemEndpoint "http://localhost:8000"
```
Local EvermemOS provisioning expects Docker (Compose) and `uv` to be available.
Installer EvermemOS options (also reads from env vars or prompts):
```
.\installer\install.ps1 -EvermemEndpoint "http://localhost:8000" -EvermemApiKey "YOUR_KEY"
```
Additional EvermemOS options:
```
.\installer\install.ps1 -EvermemRoot "C:\path\to\EverMemOS" -EvermemPort 8001
.\installer\install.ps1 -EvermemLlmApiKey "LLM_KEY" -EvermemVectorizeApiKey "VECTOR_KEY"
```
Optional provider keys:
```
.\installer\install.ps1 -OpenAiApiKey "OPENAI_KEY" -BraveSearchApiKey "BRAVE_KEY" -BrowserUseApiKey "BROWSER_USE_KEY"
```

## Configuration
Copy `.env.example` to `.env` and set keys:
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `OPENAI_TRANSCRIBE_MODEL` (optional)
- `ELEVENLABS_API_KEY`
- `EVERMEM_ENDPOINT`
- `EVERMEM_API_KEY`
- `EVERMEM_GROUP_ID` (optional)
- `EVERMEM_GROUP_NAME` (optional)
- `EVERMEM_SENDER` (optional)
- `EVERMEM_SENDER_NAME` (optional)
- `EVERMEM_ROLE` (optional)
- `EVERMEM_SCENE` (optional)
- `EVERMEM_LOCAL` (optional)
- `EVERMEM_ROOT` (optional)
- `EVERMEM_PORT` (optional)
- `EVERMEM_LLM_API_KEY` (optional)
- `EVERMEM_VECTORIZE_API_KEY` (optional)
- `BRAVE_SEARCH_API_KEY` (optional)
- `BRAVE_SEARCH_ENDPOINT` (optional)
- `BROWSER_USE_API_KEY` (optional)
- `BROWSER_USE_LLM` (optional)

## Smoke Tests
With the backend running:
```
python backend/smoke_tests.py
```
Optional env vars:
- `BEE_YOUTUBE_TEST` (YouTube URL or ID)
- `BEE_BROWSER_USE_URL` (URL to extract)

## Notes
The web UI is still available at `/ui` if you build `frontend/`, but the primary UI is now the Python desktop app in `backend/bee/ui.py`.
This repo is scaffolded with stubs for voice; web search, YouTube transcription, and browser-use are now wired.

EvermemOS reference: https://github.com/EverMind-AI/EverMemOS/
