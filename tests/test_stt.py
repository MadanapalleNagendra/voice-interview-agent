"""
tests/test_stt.py
Unit tests for the STT service.
Uses pytest-asyncio + mocking so no real API calls are made.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_transcribe_returns_text():
    """transcribe() should return {'text': ..., 'language': ...}."""
    fake_response = MagicMock()
    fake_response.text = "I would design a URL shortener using Base62 encoding."
    fake_response.language = "en"

    with patch("openai.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.audio.transcriptions.create = AsyncMock(return_value=fake_response)

        from app.services.stt_service import transcribe
        result = await transcribe(b"fake_audio_bytes", language="en")

    assert result["text"] == "I would design a URL shortener using Base62 encoding."
    assert result["language"] == "en"


@pytest.mark.asyncio
async def test_transcribe_with_no_language_hint():
    """Should still work without an explicit language param."""
    fake_response = MagicMock()
    fake_response.text = "Hallo, ich bin bereit."
    fake_response.language = "de"

    with patch("openai.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.audio.transcriptions.create = AsyncMock(return_value=fake_response)

        from app.services.stt_service import transcribe
        result = await transcribe(b"fake_audio")

    assert "text" in result
    assert "language" in result


@pytest.mark.asyncio
async def test_transcribe_error_propagates():
    """OpenAI errors should propagate, not be silently swallowed."""
    import openai

    with patch("openai.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.audio.transcriptions.create = AsyncMock(
            side_effect=openai.APIConnectionError(request=MagicMock())
        )

        from app.services.stt_service import transcribe
        with pytest.raises(openai.OpenAIError):
            await transcribe(b"bad_audio")
