from __future__ import annotations

import logging
from typing import Any

from browser_use_sdk import AsyncBrowserUse
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class PageExtraction(BaseModel):
    url: str | None = Field(default=None, description="Original URL")
    title: str | None = Field(default=None, description="Page title")
    summary: str | None = Field(default=None, description="Short summary")
    text: str | None = Field(default=None, description="Main readable text")


class BrowserUseClient:
    def __init__(self, api_key: str | None, llm: str | None = None) -> None:
        self.api_key = api_key
        self.llm = llm

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def extract_text(self, url: str) -> dict[str, Any]:
        if not self.api_key:
            return {"ok": False, "error": "BROWSER_USE_API_KEY not set"}

        try:
            async with AsyncBrowserUse(api_key=self.api_key, llm=self.llm) as client:
                task = await client.tasks.create_task(
                    task=(
                        f"Open {url} and extract the page title, a short summary, "
                        "and the main readable text. Only respond with the schema."
                    ),
                    schema=PageExtraction,
                )
                result = await task.complete()
        except Exception as exc:
            logger.warning("Browser-use extraction failed", exc_info=True)
            return {"ok": False, "error": str(exc)}

        output = None
        if result is not None:
            if hasattr(result, "output"):
                output = result.output
            elif hasattr(result, "result") and hasattr(result.result, "output"):
                output = result.result.output
        if output is not None and hasattr(output, "model_dump"):
            output = output.model_dump()
        if isinstance(output, dict) and not output.get("url"):
            output["url"] = url

        return {
            "ok": True,
            "status": getattr(result, "status", None),
            "output": output,
            "task_id": getattr(result, "id", None) or getattr(result, "task_id", None),
        }
