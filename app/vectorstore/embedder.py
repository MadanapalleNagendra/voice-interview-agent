"""
app/vectorstore/embedder.py
Thin async wrapper around OpenAI text-embedding-3-large.
Caches embeddings in Redis to avoid re-calling the API for identical text.
"""

import hashlib
import json
from typing import Optional

import numpy as np
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


async def embed_text(text: str, use_cache: bool = True) -> np.ndarray:
    """Return a 3072-dim embedding vector for the given text."""
    # Try Redis cache first
    if use_cache:
        cached = await _cache_get(text)
        if cached is not None:
            return cached

    client = _get_client()
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text.strip(),
    )
    vector = np.array(response.data[0].embedding, dtype=np.float32)

    if use_cache:
        await _cache_set(text, vector)

    return vector


async def embed_batch(texts: list[str]) -> list[np.ndarray]:
    """Embed multiple texts in one API call (more efficient)."""
    client = _get_client()
    response = await client.embeddings.create(
        model=settings.openai_embedding_model,
        input=[t.strip() for t in texts],
    )
    return [np.array(d.embedding, dtype=np.float32) for d in response.data]


# ── Redis helpers ──────────────────────────────────────────────────────────

async def _cache_get(text: str) -> Optional[np.ndarray]:
    try:
        from app.services.memory_service import get_redis
        redis = await get_redis()
        key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        raw = await redis.get(key)
        if raw:
            return np.array(json.loads(raw), dtype=np.float32)
    except Exception:
        pass
    return None


async def _cache_set(text: str, vector: np.ndarray) -> None:
    try:
        from app.services.memory_service import get_redis
        redis = await get_redis()
        key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
        await redis.set(key, json.dumps(vector.tolist()), ex=settings.redis_cache_ttl)
    except Exception:
        pass
