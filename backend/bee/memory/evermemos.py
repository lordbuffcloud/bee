from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class EvermemOS:
    def __init__(
        self,
        endpoint: str | None,
        api_key: str | None,
        group_id: str | None = None,
        group_name: str | None = None,
        sender: str | None = None,
        sender_name: str | None = None,
        role: str | None = None,
        scene: str | None = None,
    ) -> None:
        self.endpoint = endpoint.rstrip("/") if endpoint else None
        self.api_key = api_key
        self.group_id = group_id
        self.group_name = group_name
        self.sender = sender or "bee"
        self.sender_name = sender_name or "B.E.E."
        self.role = role or "assistant"
        self.scene = scene or "assistant"

    @property
    def enabled(self) -> bool:
        return bool(self.endpoint)

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def _url(self, path: str) -> str:
        if not self.endpoint:
            return path
        return f"{self.endpoint}{path}"

    @staticmethod
    def _format_goals(goals: list[str]) -> str:
        lines = ["BEE Goals:"]
        for idx, goal in enumerate(goals, start=1):
            lines.append(f"{idx}. {goal}")
        return "\n".join(lines)

    @staticmethod
    def _parse_goals(content: str) -> list[str]:
        marker = "BEE Goals:"
        if marker not in content:
            return []
        _, tail = content.split(marker, 1)
        goals: list[str] = []
        for line in tail.splitlines():
            cleaned = re.sub(r"^[-\\d\\.)\\s]+", "", line).strip()
            if cleaned:
                goals.append(cleaned)
        return goals[:3]

    async def add_memory(
        self,
        content: str,
        *,
        message_id: str | None = None,
        create_time_ms: int | None = None,
        sender: str | None = None,
        sender_name: str | None = None,
        role: str | None = None,
        scene: str | None = None,
        group_id: str | None = None,
        group_name: str | None = None,
        refer_list: list[str] | None = None,
        flush: bool | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {
            "message_id": message_id or str(uuid.uuid4()),
            "create_time": create_time_ms or int(time.time() * 1000),
            "sender": sender or self.sender,
            "content": content,
            "role": role or self.role,
        }
        if scene or self.scene:
            payload["scene"] = scene or self.scene
        if sender_name or self.sender_name:
            payload["sender_name"] = sender_name or self.sender_name
        if group_id or self.group_id:
            payload["group_id"] = group_id or self.group_id
        if group_name or self.group_name:
            payload["group_name"] = group_name or self.group_name
        if refer_list is not None:
            payload["refer_list"] = refer_list
        if flush is not None:
            payload["flush"] = flush

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._url("/api/v1/memories"),
                    json=payload,
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS add_memory failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS add_memory error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def get_memories(
        self,
        *,
        message_id: str | None = None,
        group_id: str | None = None,
        group_name: str | None = None,
        time_range: str | None = None,
        time_range_type: str | None = None,
        requester: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {}
        if message_id:
            payload["message_id"] = message_id
        if group_id or self.group_id:
            payload["group_id"] = group_id or self.group_id
        if group_name or self.group_name:
            payload["group_name"] = group_name or self.group_name
        if time_range:
            payload["time_range"] = time_range
        if time_range_type:
            payload["time_range_type"] = time_range_type
        if requester:
            payload["requester"] = requester
        if timeout is not None:
            payload["timeout"] = timeout

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.request(
                    "GET",
                    self._url("/api/v1/memories"),
                    json=payload,
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS get_memories failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS get_memories error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def search_memories(
        self,
        search_query: str,
        *,
        result_limit: int | None = None,
        group_id: str | None = None,
        group_name: str | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {"search_query": search_query}
        if result_limit is not None:
            payload["result_limit"] = result_limit
        if group_id or self.group_id:
            payload["group_id"] = group_id or self.group_id
        if group_name or self.group_name:
            payload["group_name"] = group_name or self.group_name
        if timeout is not None:
            payload["timeout"] = timeout

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.request(
                    "GET",
                    self._url("/api/v1/memories/search"),
                    json=payload,
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS search_memories failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS search_memories error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def request_status(self, request_id: str) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    self._url("/api/v1/status/request"),
                    params={"request_id": request_id},
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS request_status failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS request_status error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def record_state(
        self,
        before_tick: str | None,
        tick_state: str | None,
        after_tick: str | None,
        goals: list[str] | None,
    ) -> None:
        if not self.endpoint:
            return

        sections: list[str] = ["BEE Heartbeat Tick"]
        if goals:
            sections.append(self._format_goals(goals))
        if before_tick:
            sections.append(f"Before tick: {before_tick}")
        if tick_state:
            sections.append(f"Tick state: {tick_state}")
        if after_tick:
            sections.append(f"After tick: {after_tick}")
        content = "\n\n".join(sections)

        await self.add_memory(content=content)

    async def record_goals(self, goals: list[str]) -> None:
        if not goals:
            return
        content = self._format_goals(goals)
        await self.add_memory(content=content)

    async def fetch_goals(self) -> list[str]:
        if not self.endpoint:
            return []

        response = await self.search_memories("BEE Goals:", result_limit=5)
        if not response:
            return []

        memories = response.get("memory_list", [])
        if not isinstance(memories, list):
            return []

        def sort_key(item: dict[str, Any]) -> int:
            create_time = item.get("create_time")
            return int(create_time) if isinstance(create_time, int) else 0

        for memory in sorted(memories, key=sort_key, reverse=True):
            content = memory.get("content", "")
            if not isinstance(content, str):
                continue
            goals = self._parse_goals(content)
            if goals:
                return goals

        return []
