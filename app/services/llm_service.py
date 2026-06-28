"""
app/services/llm_service.py
Async wrapper around OpenAI Chat Completions (GPT-4o).
Provides both standard and streaming variants.
"""

import json
from typing import Any, AsyncGenerator, Optional

import openai

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: Optional[openai.AsyncOpenAI] = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def chat_complete(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 512,
    response_format: Optional[str] = None,  # "json_object"
) -> str:
    """Non-streaming chat completion.  Returns the assistant message string."""
    client = _get_client()
    kwargs: dict[str, Any] = {
        "model": settings.openai_chat_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json_object":
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    return content.strip()


async def chat_complete_json(messages: list[dict], temperature: float = 0.1) -> dict:
    """Convenience: get a JSON response from the LLM."""
    raw = await chat_complete(
        messages,
        temperature=temperature,
        max_tokens=1024,
        response_format="json_object",
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip markdown fences if model ignored response_format
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(clean)


async def chat_stream(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> AsyncGenerator[str, None]:
    """Streaming chat — yields text delta chunks."""
    client = _get_client()
    stream = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
