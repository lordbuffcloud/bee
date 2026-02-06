from pydantic import BaseModel, Field
from typing import List, Optional


class GoalState(BaseModel):
    goals: List[str] = Field(default_factory=list)
    before_tick: Optional[str] = None
    tick_state: Optional[str] = None
    after_tick: Optional[str] = None


class StatusResponse(BaseModel):
    heartbeat_running: bool
    heartbeat_interval_sec: int
    risk_tolerance: int
    memory_goals: GoalState
    personality_summary: str
    evermem_enabled: bool
    evermem_endpoint: Optional[str] = None
    evermem_group_id: Optional[str] = None
    last_tick: Optional[str] = None


class EvermemAddRequest(BaseModel):
    content: str
    message_id: Optional[str] = None
    create_time: Optional[int] = None
    sender: Optional[str] = None
    sender_name: Optional[str] = None
    role: Optional[str] = None
    scene: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    refer_list: Optional[List[str]] = None
    flush: Optional[bool] = None


class EvermemSearchRequest(BaseModel):
    search_query: str
    result_limit: Optional[int] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    timeout: Optional[int] = None


class WebSearchRequest(BaseModel):
    query: str
    count: Optional[int] = 5
    country: Optional[str] = "US"
    search_lang: Optional[str] = "en"


class WebScrapeRequest(BaseModel):
    url: str
    max_chars: Optional[int] = 20000


class YouTubeTranscribeRequest(BaseModel):
    video: str
    store_memory: Optional[bool] = True


class BrowserUseExtractRequest(BaseModel):
    url: str
    store_memory: Optional[bool] = True
