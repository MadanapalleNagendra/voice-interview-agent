"""
app/database/seed.py
Seeds the database with initial data if needed.
Run once: python -m app.database.seed
"""

import asyncio

from app.database.connection import init_db
from app.core.logger import get_logger

logger = get_logger(__name__)


async def seed():
    await init_db()
    logger.info("Seed complete — tables are ready.")


if __name__ == "__main__":
    asyncio.run(seed())
