from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
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

    @staticmethod
    def _isoformat_time(value: str | int | float | datetime | None) -> str:
        if value is None:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat()
        if isinstance(value, (int, float)):
            seconds = value / 1000 if value > 10**12 else value
            return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()
        if isinstance(value, str):
            return value
        return datetime.now(timezone.utc).isoformat()

    def _default_user_details(self) -> dict[str, Any]:
        if not self.sender:
            return {}
        details: dict[str, Any] = {
            self.sender: {
                "full_name": self.sender_name or self.sender,
                "role": self.role,
            }
        }
        return details

    def _conversation_meta_payload(
        self,
        *,
        scene: str | None = None,
        scene_desc: dict[str, Any] | None = None,
        name: str | None = None,
        description: str | None = None,
        group_id: str | None = None,
        created_at: str | int | float | datetime | None = None,
        default_timezone: str | None = None,
        user_details: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_scene = scene or self.scene or "assistant"
        resolved_name = (
            name
            or self.group_name
            or self.sender_name
            or self.sender
            or "B.E.E. Conversation"
        )
        resolved_desc = scene_desc or {
            "description": f"B.E.E. {resolved_name} context"
        }
        payload: dict[str, Any] = {
            "scene": resolved_scene,
            "scene_desc": resolved_desc,
            "name": resolved_name,
            "created_at": self._isoformat_time(created_at),
        }
        resolved_group_id = group_id or self.group_id
        if resolved_group_id is not None:
            payload["group_id"] = resolved_group_id
        if description:
            payload["description"] = description
        if default_timezone:
            payload["default_timezone"] = default_timezone
        payload["user_details"] = user_details or self._default_user_details()
        if tags is not None:
            payload["tags"] = tags
        return payload

    async def add_memory(
        self,
        content: str,
        *,
        message_id: str | None = None,
        create_time: str | int | float | datetime | None = None,
        sender: str | None = None,
        sender_name: str | None = None,
        role: str | None = None,
        group_id: str | None = None,
        group_name: str | None = None,
        refer_list: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {
            "message_id": message_id or str(uuid.uuid4()),
            "create_time": self._isoformat_time(create_time),
            "sender": sender or self.sender,
            "content": content,
            "role": role or self.role,
        }
        if sender_name or self.sender_name:
            payload["sender_name"] = sender_name or self.sender_name
        if group_id or self.group_id:
            payload["group_id"] = group_id or self.group_id
        if group_name or self.group_name:
            payload["group_name"] = group_name or self.group_name
        if refer_list is not None:
            payload["refer_list"] = refer_list

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
        user_id: str | None = None,
        group_id: str | None = None,
        memory_type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        version_range: list[str | None] | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {}
        resolved_group_id = group_id or self.group_id
        resolved_user_id = user_id
        if not resolved_group_id and not resolved_user_id:
            resolved_user_id = self.sender
        if resolved_user_id:
            payload["user_id"] = resolved_user_id
        if resolved_group_id:
            payload["group_id"] = resolved_group_id
        if memory_type:
            payload["memory_type"] = memory_type
        if limit is not None:
            payload["limit"] = limit
        if offset is not None:
            payload["offset"] = offset
        if start_time:
            payload["start_time"] = start_time
        if end_time:
            payload["end_time"] = end_time
        if version_range:
            payload["version_range"] = version_range

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
        query: str | None,
        *,
        user_id: str | None = None,
        group_id: str | None = None,
        memory_types: list[str] | None = None,
        top_k: int | None = None,
        retrieve_method: str | None = None,
        include_metadata: bool | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        radius: float | None = None,
        current_time: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {}
        if query:
            payload["query"] = query
        resolved_group_id = group_id or self.group_id
        resolved_user_id = user_id
        if not resolved_group_id and not resolved_user_id:
            resolved_user_id = self.sender
        if resolved_user_id:
            payload["user_id"] = resolved_user_id
        if resolved_group_id:
            payload["group_id"] = resolved_group_id
        if memory_types is not None:
            payload["memory_types"] = memory_types
        if top_k is not None:
            payload["top_k"] = top_k
        if retrieve_method:
            payload["retrieve_method"] = retrieve_method
        if include_metadata is not None:
            payload["include_metadata"] = include_metadata
        if start_time:
            payload["start_time"] = start_time
        if end_time:
            payload["end_time"] = end_time
        if radius is not None:
            payload["radius"] = radius
        if current_time:
            payload["current_time"] = current_time

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
                    self._url("/api/v1/stats/request"),
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

    async def get_conversation_meta(
        self,
        *,
        group_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        params: dict[str, Any] = {}
        if group_id or self.group_id:
            params["group_id"] = group_id or self.group_id

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    self._url("/api/v1/memories/conversation-meta"),
                    params=params,
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS get_conversation_meta failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS get_conversation_meta error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def save_conversation_meta(
        self,
        *,
        scene: str | None = None,
        scene_desc: dict[str, Any] | None = None,
        name: str | None = None,
        description: str | None = None,
        group_id: str | None = None,
        created_at: str | int | float | datetime | None = None,
        default_timezone: str | None = None,
        user_details: dict[str, Any] | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload = self._conversation_meta_payload(
            scene=scene,
            scene_desc=scene_desc,
            name=name,
            description=description,
            group_id=group_id,
            created_at=created_at,
            default_timezone=default_timezone,
            user_details=user_details,
            tags=tags,
        )

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    self._url("/api/v1/memories/conversation-meta"),
                    json=payload,
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS save_conversation_meta failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS save_conversation_meta error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def patch_conversation_meta(
        self,
        *,
        group_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        scene_desc: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        user_details: dict[str, Any] | None = None,
        default_timezone: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.endpoint:
            return None

        payload: dict[str, Any] = {}
        if group_id is not None or self.group_id is not None:
            payload["group_id"] = group_id if group_id is not None else self.group_id
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if scene_desc is not None:
            payload["scene_desc"] = scene_desc
        if tags is not None:
            payload["tags"] = tags
        if user_details is not None:
            payload["user_details"] = user_details
        if default_timezone is not None:
            payload["default_timezone"] = default_timezone

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.patch(
                    self._url("/api/v1/memories/conversation-meta"),
                    json=payload,
                    headers=self._headers(),
                )
        except httpx.HTTPError:
            logger.warning("EvermemOS patch_conversation_meta failed", exc_info=True)
            return None

        if resp.status_code >= 400:
            logger.warning(
                "EvermemOS patch_conversation_meta error status=%s body=%s",
                resp.status_code,
                resp.text[:200],
            )
            return None

        try:
            return resp.json()
        except ValueError:
            return {"status_code": resp.status_code, "text": resp.text}

    async def ensure_conversation_meta(self) -> dict[str, Any] | None:
        if not self.endpoint:
            return None
        return await self.save_conversation_meta()

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

        response = await self.search_memories("BEE Goals:", top_k=5)
        if not response:
            return []

        result = response.get("result", {}) if isinstance(response, dict) else {}
        memories = result.get("memories", []) if isinstance(result, dict) else []
        pending = result.get("pending_messages", []) if isinstance(result, dict) else []

        candidates: list[tuple[str, str]] = []
        if isinstance(pending, list):
            for item in pending:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, str) and "BEE Goals:" in content:
                    stamp = item.get("message_create_time") or ""
                    candidates.append((stamp, content))

        if isinstance(memories, list):
            for group in memories:
                if not isinstance(group, dict):
                    continue
                for mem_list in group.values():
                    if not isinstance(mem_list, list):
                        continue
                    for memory in mem_list:
                        if not isinstance(memory, dict):
                            continue
                        content = memory.get("content") or memory.get("summary")
                        if not isinstance(content, str):
                            continue
                        if "BEE Goals:" not in content:
                            continue
                        stamp = memory.get("timestamp") or ""
                        candidates.append((stamp, content))

        for _, content in sorted(candidates, key=lambda item: item[0], reverse=True):
            goals = self._parse_goals(content)
            if goals:
                return goals

        return []
