import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from bee.models import GoalState


@dataclass
class BEEState:
    memory_goals: GoalState = field(default_factory=GoalState)
    last_tick: datetime | None = None
    heartbeat_running: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def set_goals(self, goals: list[str]) -> None:
        async with self.lock:
            self.memory_goals.goals = goals

    async def record_tick(self, before_tick: str | None, tick_state: str | None, after_tick: str | None) -> None:
        async with self.lock:
            self.memory_goals.before_tick = before_tick
            self.memory_goals.tick_state = tick_state
            self.memory_goals.after_tick = after_tick
            self.last_tick = datetime.utcnow()
