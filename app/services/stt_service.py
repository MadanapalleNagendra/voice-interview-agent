"""
app/services/stt_service.py
Speech-to-Text via OpenAI Whisper API.
Accepts raw audio bytes (WAV/MP3/WebM) and returns a transcript.
"""

import io
from typing import Optional

import openai

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def transcribe(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
) -> dict:
    """
    Transcribe audio bytes using Whisper.

    Args:
        audio_bytes: Raw audio file content.
        filename: Hint for the file extension so Whisper knows the codec.
        language: BCP-47 code ('en', 'hi', 'de').  None = auto-detect.
        prompt: Optional context prompt to improve accuracy.

    Returns:
        {"text": str, "language": str}
    """
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename  # Whisper SDK reads .name for Content-Type

    kwargs: dict = {
        "model": settings.openai_whisper_model,
        "file": audio_file,
        "response_format": "verbose_json",
    }
    if language:
        kwargs["language"] = language
    if prompt:
        kwargs["prompt"] = prompt

    try:
        response = await client.audio.transcriptions.create(**kwargs)
        transcript = response.text.strip()
        detected_lang = getattr(response, "language", language or "en")
        logger.info(f"STT: '{transcript[:80]}…' (lang={detected_lang})")
        return {"text": transcript, "language": detected_lang}
    except openai.OpenAIError as e:
        logger.error(f"Whisper API error: {e}")
        raise
