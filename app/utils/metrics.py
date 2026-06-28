"""
app/utils/metrics.py
Simple in-process latency tracking helpers.
"""

import time
from contextlib import asynccontextmanager
from typing import Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def timer(label: str):
    """Async context manager that logs elapsed time."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"⏱  {label}: {elapsed:.1f}ms")
