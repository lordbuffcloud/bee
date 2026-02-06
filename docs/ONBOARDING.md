# Onboarding

1. Create a Telegram bot with BotFather and set `TELEGRAM_BOT_TOKEN`.
2. Set `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` in `.env`.
3. Optional: set `OPENAI_TRANSCRIBE_MODEL` for Whisper-based YouTube transcription.
4. EvermemOS is auto-provisioned by the installer (local on `http://localhost:8001`). Set `EVERMEM_ENDPOINT` + `EVERMEM_API_KEY` (and group/sender fields) if you want a remote instance, and use `EVERMEM_LLM_API_KEY` / `EVERMEM_VECTORIZE_API_KEY` to override local credentials.
5. Optional: set `BRAVE_SEARCH_API_KEY` for web search and `BROWSER_USE_API_KEY` for browser automation.
6. Start backend and run the Python UI with `python -m bee.ui`.
