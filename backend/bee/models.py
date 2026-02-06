from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union


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
    create_time: Optional[Union[int, float, str]] = None
    sender: Optional[str] = None
    sender_name: Optional[str] = None
    role: Optional[str] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    refer_list: Optional[List[str]] = None


class EvermemSearchRequest(BaseModel):
    query: Optional[str] = None
    search_query: Optional[str] = None
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    memory_types: Optional[List[str]] = None
    top_k: Optional[int] = None
    result_limit: Optional[int] = None
    retrieve_method: Optional[str] = None
    include_metadata: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    radius: Optional[float] = None
    current_time: Optional[str] = None


class EvermemConversationMetaRequest(BaseModel):
    group_id: Optional[str] = None
    scene: Optional[str] = None
    scene_desc: Optional[Dict[str, Any]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[Union[int, float, str]] = None
    default_timezone: Optional[str] = None
    user_details: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class EvermemConversationMetaPatchRequest(BaseModel):
    group_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    scene_desc: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    user_details: Optional[Dict[str, Any]] = None
    default_timezone: Optional[str] = None


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
