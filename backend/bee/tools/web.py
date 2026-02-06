from __future__ import annotations

import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


class WebTools:
    def __init__(self, api_key: str | None, endpoint: str) -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    async def search(
        self,
        query: str,
        *,
        count: int = 5,
        country: str = "US",
        search_lang: str = "en",
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": query,
            "count": count,
            "country": country,
            "search_lang": search_lang,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(self.endpoint, params=params, headers=headers)
        except httpx.HTTPError:
            logger.warning("Brave search request failed", exc_info=True)
            return []

        if resp.status_code != 200:
            logger.warning("Brave search error status=%s body=%s", resp.status_code, resp.text[:200])
            return []

        data = resp.json()
        web = data.get("web", {})
        results: list[dict[str, Any]] = []
        for item in web.get("results", []) or []:
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "description": item.get("description"),
                    "age": item.get("age"),
                    "extra_snippets": item.get("extra_snippets"),
                }
            )
        return results

    async def scrape(self, url: str, *, max_chars: int = 20000) -> dict[str, Any]:
        headers = {"User-Agent": "B.E.E. WebTools/1.0"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(url, headers=headers, follow_redirects=True)
        except httpx.HTTPError:
            logger.warning("Scrape failed url=%s", url, exc_info=True)
            return {"url": url, "content": "", "status_code": None}

        content_type = resp.headers.get("content-type")
        text = resp.text
        if max_chars and len(text) > max_chars:
            text = text[:max_chars]

        return {
            "url": url,
            "status_code": resp.status_code,
            "content_type": content_type,
            "content": text,
        }
