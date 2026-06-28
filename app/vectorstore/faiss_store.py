"""
app/vectorstore/faiss_store.py
Builds, persists, and queries a FAISS index over the Q&A dataset.

Design decisions:
- Each entry is a (question + ideal_answer) chunk so retrieval returns
  the full reference context, not just a fragment.
- Inner-product (cosine) search after L2-normalising vectors.
- Index is loaded once at startup and held in memory.
"""

import json
import os
import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from app.core.config import get_settings
from app.core.logger import get_logger
from app.vectorstore.embedder import embed_batch

logger = get_logger(__name__)
settings = get_settings()

# ── In-memory singletons ────────────────────────────────────────────────────
_index: Optional[faiss.IndexFlatIP] = None
_metadata: list[dict] = []  # parallel list of QA records


def _index_path() -> tuple[str, str]:
    base = settings.faiss_index_path
    return f"{base}.index", f"{base}.meta"


async def build_index(qa_records: list[dict]) -> None:
    """Embed all Q&A pairs and build FAISS index.  Saves to disk."""
    global _index, _metadata

    logger.info(f"Building FAISS index for {len(qa_records)} records …")

    texts = [
        f"Question: {r['question']}\nIdeal answer: {r['ideal_answer']}"
        for r in qa_records
    ]
    vectors = await embed_batch(texts)

    dim = vectors[0].shape[0]
    index = faiss.IndexFlatIP(dim)  # inner-product = cosine after normalisation

    matrix = np.vstack(vectors).astype(np.float32)
    faiss.normalize_L2(matrix)
    index.add(matrix)

    _index = index
    _metadata = qa_records

    # Persist
    idx_path, meta_path = _index_path()
    os.makedirs(os.path.dirname(idx_path), exist_ok=True)
    faiss.write_index(index, idx_path)
    with open(meta_path, "wb") as f:
        pickle.dump(qa_records, f)

    logger.info(f"FAISS index saved → {idx_path}")


def load_index() -> bool:
    """Load persisted index from disk.  Returns True if successful."""
    global _index, _metadata
    idx_path, meta_path = _index_path()
    if not (Path(idx_path).exists() and Path(meta_path).exists()):
        return False
    _index = faiss.read_index(idx_path)
    with open(meta_path, "rb") as f:
        _metadata = pickle.load(f)
    logger.info(f"FAISS index loaded ({_index.ntotal} vectors)")
    return True


async def search(query: str, top_k: Optional[int] = None) -> list[dict]:
    """Return top-k QA records most similar to query."""
    global _index, _metadata

    if _index is None:
        raise RuntimeError("FAISS index not loaded. Call build_index() or load_index() first.")

    from app.vectorstore.embedder import embed_text
    vec = await embed_text(query)
    vec = vec.reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(vec)

    k = top_k or settings.retrieval_top_k
    scores, indices = _index.search(vec, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        record = dict(_metadata[idx])
        record["_similarity"] = float(score)
        results.append(record)

    return results


async def get_by_id(question_id: int) -> Optional[dict]:
    """Exact lookup by question ID (no embedding needed)."""
    for record in _metadata:
        if record["id"] == question_id:
            return record
    return None


def get_all_questions() -> list[dict]:
    """Return all QA records (metadata only)."""
    return _metadata
