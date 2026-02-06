import os
from pydantic import BaseModel, Field


def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


class Settings(BaseModel):
    env: str = Field(default_factory=lambda: _env("BEE_ENV", "dev"))
    host: str = Field(default_factory=lambda: _env("BEE_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(_env("BEE_PORT", "8080")))

    telegram_bot_token: str | None = Field(default_factory=lambda: _env("TELEGRAM_BOT_TOKEN"))
    telegram_admin_chat_id: str | None = Field(default_factory=lambda: _env("TELEGRAM_ADMIN_CHAT_ID"))

    openai_api_key: str | None = Field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_transcribe_model: str = Field(default_factory=lambda: _env("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"))
    elevenlabs_api_key: str | None = Field(default_factory=lambda: _env("ELEVENLABS_API_KEY"))

    evermem_endpoint: str | None = Field(default_factory=lambda: _env("EVERMEM_ENDPOINT"))
    evermem_api_key: str | None = Field(default_factory=lambda: _env("EVERMEM_API_KEY"))
    evermem_group_id: str | None = Field(default_factory=lambda: _env("EVERMEM_GROUP_ID"))
    evermem_group_name: str | None = Field(default_factory=lambda: _env("EVERMEM_GROUP_NAME"))
    evermem_sender: str | None = Field(default_factory=lambda: _env("EVERMEM_SENDER", "bee"))
    evermem_sender_name: str | None = Field(default_factory=lambda: _env("EVERMEM_SENDER_NAME", "B.E.E."))
    evermem_role: str | None = Field(default_factory=lambda: _env("EVERMEM_ROLE", "assistant"))
    evermem_scene: str | None = Field(default_factory=lambda: _env("EVERMEM_SCENE", "assistant"))

    brave_search_api_key: str | None = Field(default_factory=lambda: _env("BRAVE_SEARCH_API_KEY"))
    brave_search_endpoint: str = Field(
        default_factory=lambda: _env("BRAVE_SEARCH_ENDPOINT", "https://api.search.brave.com/res/v1/web/search")
    )

    browser_use_api_key: str | None = Field(default_factory=lambda: _env("BROWSER_USE_API_KEY"))
    browser_use_llm: str | None = Field(default_factory=lambda: _env("BROWSER_USE_LLM"))

    ollama_endpoint: str = Field(default_factory=lambda: _env("OLLAMA_ENDPOINT", "http://localhost:11434"))
    ollama_model: str = Field(default_factory=lambda: _env("OLLAMA_MODEL", "llama3.1:8b"))

    heartbeat_interval_sec: int = Field(default_factory=lambda: int(_env("HEARTBEAT_INTERVAL_SEC", "30")))
    risk_tolerance: int = Field(default_factory=lambda: int(_env("RISK_TOLERANCE", "5")))
