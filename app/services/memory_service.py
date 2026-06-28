"""
app/services/memory_service.py
Redis-backed session memory.  Stores interview state (which questions were asked,
conversation history, accumulated scores) so the API remains stateless.
"""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


# ── Session state helpers ───────────────────────────────────────────────────

SESSION_TTL = 7200  # 2 hours


async def create_session(session_id: str, initial_state: dict) -> None:
    redis = await get_redis()
    key = f"session:{session_id}"
    await redis.set(key, json.dumps(initial_state), ex=SESSION_TTL)
    logger.info(f"Session created: {session_id}")


async def get_session(session_id: str) -> Optional[dict]:
    redis = await get_redis()
    raw = await redis.get(f"session:{session_id}")
    if raw is None:
        return None
    return json.loads(raw)


async def update_session(session_id: str, state: dict) -> None:
    redis = await get_redis()
    await redis.set(f"session:{session_id}", json.dumps(state), ex=SESSION_TTL)


async def delete_session(session_id: str) -> None:
    redis = await get_redis()
    await redis.delete(f"session:{session_id}")


# ── Conversation history helpers ────────────────────────────────────────────

async def append_message(session_id: str, role: str, content: str) -> None:
    """Append a chat message to the session's conversation history."""
    state = await get_session(session_id)
    if state is None:
        return
    state.setdefault("history", []).append({"role": role, "content": content})
    await update_session(session_id, state)


async def get_history(session_id: str) -> list[dict]:
    state = await get_session(session_id)
    if state is None:
        return []
    return state.get("history", [])


# ── Cache helpers ────────────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    redis = await get_redis()
    await redis.set(key, json.dumps(value), ex=ttl)


async def cache_get(key: str) -> Optional[Any]:
    redis = await get_redis()
    raw = await redis.get(key)
    return json.loads(raw) if raw else None
