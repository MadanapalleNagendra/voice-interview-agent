"""
tests/test_tts.py
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_synthesise_returns_bytes():
    fake_audio = b"\xff\xfb\x90\x00" * 100  # fake MP3 bytes

    with patch("httpx.AsyncClient") as MockClient:
        mock_resp = MagicMock()
        mock_resp.content = fake_audio
        mock_resp.raise_for_status = MagicMock()
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(return_value=mock_resp)

        from app.services.tts_service import synthesise
        result = await synthesise("Hello candidate, welcome to the interview.")

    assert isinstance(result, bytes)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_synthesise_raises_on_http_error():
    import httpx

    with patch("httpx.AsyncClient") as MockClient:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("401", request=MagicMock(), response=MagicMock())
        )
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(return_value=mock_resp)

        from app.services.tts_service import synthesise
        with pytest.raises(httpx.HTTPStatusError):
            await synthesise("test")
