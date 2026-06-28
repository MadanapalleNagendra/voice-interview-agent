"""
app/services/tts_service.py
Text-to-Speech via ElevenLabs streaming API.
Returns audio bytes (MP3) for a given text string.
"""

import asyncio
from typing import AsyncGenerator, Optional

import httpx

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


async def synthesise(text: str, voice_id: Optional[str] = None) -> bytes:
    """
    Convert text to speech and return MP3 bytes.
    Uses ElevenLabs streaming endpoint; buffers all chunks.
    """
    vid = voice_id or settings.elevenlabs_voice_id
    url = f"{_ELEVENLABS_BASE}/text-to-speech/{vid}"

    payload = {
        "text": text,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.2,
            "use_speaker_boost": True,
        },
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            audio = response.content
            logger.info(f"TTS: {len(audio)} bytes synthesised for {len(text)} chars")
            return audio
        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise


async def synthesise_stream(text: str, voice_id: Optional[str] = None) -> AsyncGenerator[bytes, None]:
    """
    Stream TTS audio chunks as they arrive from ElevenLabs.
    Yields MP3 chunk bytes.
    """
    vid = voice_id or settings.elevenlabs_voice_id
    url = f"{_ELEVENLABS_BASE}/text-to-speech/{vid}/stream"

    payload = {
        "text": text,
        "model_id": settings.elevenlabs_model_id,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=4096):
                if chunk:
                    yield chunk
