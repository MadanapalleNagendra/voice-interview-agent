"""
app/api/health.py
Simple liveness / readiness probes.
"""

from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health():
    return {"status": "ok", "model": settings.openai_chat_model}


@router.get("/ready")
async def ready():
    """Check critical dependencies."""
    from app.services.memory_service import get_redis
    from app.vectorstore.faiss_store import _index

    checks = {}

    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    checks["faiss"] = "ok" if _index is not None else "not loaded"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ready" if all_ok else "degraded", "checks": checks}
