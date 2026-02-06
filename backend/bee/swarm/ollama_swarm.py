import httpx
from typing import Any


class OllamaSwarm:
    def __init__(self, endpoint: str, model: str) -> None:
        self.endpoint = endpoint
        self.model = model

    async def generate(self, prompt: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.endpoint}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()
