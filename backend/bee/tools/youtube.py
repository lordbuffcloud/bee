from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import Any

from openai import OpenAI
from yt_dlp import YoutubeDL


logger = logging.getLogger(__name__)


class YouTubeTranscriber:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = model

    @staticmethod
    def _to_url(video: str) -> str:
        if video.startswith("http://") or video.startswith("https://"):
            return video
        return f"https://www.youtube.com/watch?v={video}"

    @staticmethod
    def _download_audio(url: str, workdir: str) -> tuple[str, dict[str, Any]]:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(workdir, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
        return path, info

    def _transcribe_file(self, path: str) -> str:
        if not self.client:
            return ""
        with open(path, "rb") as handle:
            result = self.client.audio.transcriptions.create(
                model=self.model,
                file=handle,
            )
        return result.text

    async def transcribe(self, video: str) -> dict[str, Any]:
        if not self.client:
            return {"ok": False, "error": "OPENAI_API_KEY not set", "text": ""}

        url = self._to_url(video)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                path, info = await asyncio.to_thread(self._download_audio, url, tmpdir)
                text = await asyncio.to_thread(self._transcribe_file, path)
        except Exception as exc:
            logger.warning("YouTube transcription failed", exc_info=True)
            return {"ok": False, "error": str(exc), "text": ""}

        return {
            "ok": True,
            "video_id": info.get("id"),
            "title": info.get("title"),
            "url": url,
            "text": text,
        }
