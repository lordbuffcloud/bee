import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from bee.config import Settings
from bee.state import BEEState
from bee.heartbeat import Heartbeat
from bee.security import RiskMonitor
from bee.models import (
    GoalState,
    StatusResponse,
    EvermemAddRequest,
    EvermemSearchRequest,
    WebSearchRequest,
    WebScrapeRequest,
    YouTubeTranscribeRequest,
    BrowserUseExtractRequest,
)
from bee.personality.engine import Personality
from bee.memory.evermemos import EvermemOS
from bee.telegram.bot import TelegramBot
from bee.tools.web import WebTools
from bee.tools.youtube import YouTubeTranscriber
from bee.tools.browser_use import BrowserUseClient


def create_app() -> FastAPI:
    settings = Settings()
    state = BEEState()
    personality = Personality()
    heartbeat = Heartbeat(settings.heartbeat_interval_sec)
    risk_monitor = RiskMonitor(tolerance=settings.risk_tolerance, events=[])
    evermem = EvermemOS(
        settings.evermem_endpoint,
        settings.evermem_api_key,
        group_id=settings.evermem_group_id,
        group_name=settings.evermem_group_name,
        sender=settings.evermem_sender,
        sender_name=settings.evermem_sender_name,
        role=settings.evermem_role,
        scene=settings.evermem_scene,
    )
    web_tools = WebTools(settings.brave_search_api_key, settings.brave_search_endpoint)
    youtube = YouTubeTranscriber(settings.openai_api_key, settings.openai_transcribe_model)
    browser_use = BrowserUseClient(settings.browser_use_api_key, settings.browser_use_llm)

    app = FastAPI(title="B.E.E.")
    app.state.settings = settings
    app.state.state = state
    app.state.personality = personality
    app.state.heartbeat = heartbeat
    app.state.risk_monitor = risk_monitor
    app.state.evermemos = evermem

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

    if (static_dir := "../frontend/dist"):
        try:
            app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")
        except RuntimeError:
            pass

    @app.on_event("startup")
    async def on_startup() -> None:
        if settings.telegram_bot_token:
            bot = TelegramBot(settings.telegram_bot_token, state)
            app.state.telegram_task = bot.run_in_background()

        if evermem.enabled:
            goals = await evermem.fetch_goals()
            if goals:
                await state.set_goals(goals)

        async def memory_thump() -> None:
            before = state.memory_goals.before_tick
            tick = state.memory_goals.tick_state
            after = state.memory_goals.after_tick
            state.last_tick = datetime.utcnow()
            await evermem.record_state(before, tick, after, state.memory_goals.goals)

        heartbeat.register_thump(memory_thump)
        await heartbeat.start()
        state.heartbeat_running = True

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/status", response_model=StatusResponse)
    async def status() -> StatusResponse:
        return StatusResponse(
            heartbeat_running=state.heartbeat_running,
            heartbeat_interval_sec=heartbeat.interval_sec,
            risk_tolerance=risk_monitor.tolerance,
            memory_goals=state.memory_goals,
            personality_summary=personality.summary(),
            evermem_enabled=evermem.enabled,
            evermem_endpoint=evermem.endpoint,
            evermem_group_id=evermem.group_id,
            last_tick=state.last_tick.isoformat() if state.last_tick else None,
        )

    @app.post("/api/config")
    async def update_config(payload: dict) -> dict:
        # Placeholder config update from UI
        risk = int(payload.get("risk_tolerance", risk_monitor.tolerance))
        risk_monitor.tolerance = risk
        return {"ok": True, "risk_tolerance": risk}

    @app.post("/api/heartbeat/start")
    async def start_heartbeat() -> dict:
        await heartbeat.start()
        state.heartbeat_running = True
        return {"ok": True}

    @app.post("/api/heartbeat/stop")
    async def stop_heartbeat() -> dict:
        await heartbeat.stop()
        state.heartbeat_running = False
        return {"ok": True}

    @app.post("/api/memory/goals")
    async def set_goals(payload: dict) -> dict:
        goals = payload.get("goals", [])
        if len(goals) != 3:
            return {"ok": False, "error": "Provide exactly 3 goals"}
        await state.set_goals(goals)
        await evermem.record_goals(goals)
        return {"ok": True}

    @app.post("/api/evermem/memories")
    async def add_memory(payload: EvermemAddRequest) -> dict:
        result = await evermem.add_memory(
            content=payload.content,
            message_id=payload.message_id,
            create_time_ms=payload.create_time,
            sender=payload.sender,
            sender_name=payload.sender_name,
            role=payload.role,
            scene=payload.scene,
            group_id=payload.group_id,
            group_name=payload.group_name,
            refer_list=payload.refer_list,
            flush=payload.flush,
        )
        return {"ok": bool(result), "result": result}

    @app.post("/api/evermem/search")
    async def search_memories(payload: EvermemSearchRequest) -> dict:
        result = await evermem.search_memories(
            payload.search_query,
            result_limit=payload.result_limit,
            group_id=payload.group_id,
            group_name=payload.group_name,
            timeout=payload.timeout,
        )
        return {"ok": bool(result), "result": result}

    @app.post("/api/web/search")
    async def web_search(payload: WebSearchRequest) -> dict:
        results = await web_tools.search(
            payload.query,
            count=payload.count or 5,
            country=payload.country or "US",
            search_lang=payload.search_lang or "en",
        )
        return {"ok": True, "results": results}

    @app.post("/api/web/scrape")
    async def web_scrape(payload: WebScrapeRequest) -> dict:
        result = await web_tools.scrape(payload.url, max_chars=payload.max_chars or 20000)
        return {"ok": True, "result": result}

    @app.post("/api/youtube/transcribe")
    async def youtube_transcribe(payload: YouTubeTranscribeRequest) -> dict:
        result = await youtube.transcribe(payload.video)
        if payload.store_memory and result.get("ok") and evermem.enabled:
            title = result.get("title") or payload.video
            content = f"YouTube transcription: {title}\n\n{result.get('text', '')}"
            await evermem.add_memory(content=content)
        return result

    @app.post("/api/browser-use/extract")
    async def browser_use_extract(payload: BrowserUseExtractRequest) -> dict:
        result = await browser_use.extract_text(payload.url)
        if payload.store_memory and result.get("ok") and evermem.enabled:
            output = result.get("output") or {}
            title = output.get("title") if isinstance(output, dict) else None
            summary = output.get("summary") if isinstance(output, dict) else None
            text = output.get("text") if isinstance(output, dict) else None
            sections = [f"Browser-use extract: {payload.url}"]
            if title:
                sections.append(f"Title: {title}")
            if summary:
                sections.append(f"Summary: {summary}")
            if text:
                sections.append(text)
            await evermem.add_memory(content="\n\n".join(sections))
        return result

    @app.post("/api/tick")
    async def manual_tick(payload: dict) -> dict:
        before = payload.get("before_tick")
        tick = payload.get("tick_state")
        after = payload.get("after_tick")
        await state.record_tick(before, tick, after)
        personality.evolve({"discipline": 0.01})
        return {"ok": True}

    @app.post("/api/risk/log")
    async def log_risk(payload: dict) -> dict:
        action = payload.get("action", "unknown")
        score = int(payload.get("risk_score", 0))
        risk_monitor.log(action, score)
        return {"ok": True, "halted": risk_monitor.halted}

    return app
