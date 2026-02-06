import asyncio
from collections.abc import Awaitable, Callable


Thump = Callable[[], Awaitable[None]]


class Heartbeat:
    def __init__(self, interval_sec: int) -> None:
        self.interval_sec = interval_sec
        self._task: asyncio.Task | None = None
        self._thumps: list[Thump] = []
        self._stop_event = asyncio.Event()

    def register_thump(self, thump: Thump) -> None:
        self._thumps.append(thump)

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        await self._task

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            for thump in list(self._thumps):
                await thump()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_sec)
            except asyncio.TimeoutError:
                continue
