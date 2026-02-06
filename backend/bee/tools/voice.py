import httpx


class VoiceClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key

    async def synthesize(self, text: str) -> bytes:
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not set")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.elevenlabs.io/v1/text-to-speech/default",
                json={"text": text},
                headers={"xi-api-key": self.api_key},
            )
            resp.raise_for_status()
            return resp.content
