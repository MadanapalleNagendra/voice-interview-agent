"""
app/main.py
FastAPI application — entrypoint.
"""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import feedback, health, interview
from app.core.config import get_settings
from app.core.logger import get_logger
from app.database.connection import init_db
from app.vectorstore import faiss_store

logger = get_logger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, build/load FAISS index."""
    logger.info("Starting up …")

    # Init Postgres tables
    await init_db()

    # Load QA dataset
    with open(settings.qa_dataset_path, "r") as f:
        qa_records = json.load(f)
    logger.info(f"Loaded {len(qa_records)} Q&A records")

    # Build or load FAISS index
    if not faiss_store.load_index():
        logger.info("No cached FAISS index found — building …")
        await faiss_store.build_index(qa_records)
    else:
        logger.info("FAISS index loaded from disk")

    logger.info("Startup complete ✓")
    yield
    logger.info("Shutting down …")


app = FastAPI(
    title="Grounded Voice Interview Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(interview.router)
app.include_router(feedback.router)
