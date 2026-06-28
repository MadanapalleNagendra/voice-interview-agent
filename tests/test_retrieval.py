"""
tests/test_retrieval.py
Tests for the FAISS vector store and retrieval pipeline.
Uses small synthetic data; no real OpenAI calls.
"""

import json
import numpy as np
import pytest
from unittest.mock import AsyncMock, patch


SYNTHETIC_QA = [
    {
        "id": 1,
        "question": "What is a hash table?",
        "ideal_answer": "A hash table maps keys to values using a hash function.",
        "category": "data_structures",
        "difficulty": "easy",
        "keywords": ["hash", "table"],
    },
    {
        "id": 2,
        "question": "Explain binary search.",
        "ideal_answer": "Binary search finds an element in a sorted array in O(log n) time.",
        "category": "algorithms",
        "difficulty": "easy",
        "keywords": ["binary", "search", "sorted"],
    },
]


@pytest.mark.asyncio
async def test_build_and_search():
    """Build a tiny FAISS index and verify search returns results."""
    DIM = 8
    fake_vectors = [np.random.rand(DIM).astype(np.float32) for _ in SYNTHETIC_QA]

    with patch("app.vectorstore.faiss_store.embed_batch", AsyncMock(return_value=fake_vectors)), \
         patch("app.vectorstore.faiss_store.embed_text", AsyncMock(return_value=np.random.rand(DIM).astype(np.float32))), \
         patch("app.vectorstore.faiss_store._index_path", return_value=("/tmp/test.index", "/tmp/test.meta")), \
         patch("faiss.write_index"), \
         patch("builtins.open", create=True):

        from app.vectorstore import faiss_store
        await faiss_store.build_index(SYNTHETIC_QA)
        results = await faiss_store.search("hash table", top_k=2)

    assert isinstance(results, list)
    assert len(results) <= 2
    for r in results:
        assert "_similarity" in r


@pytest.mark.asyncio
async def test_get_by_id():
    """get_by_id should return the right record."""
    DIM = 8
    fake_vectors = [np.random.rand(DIM).astype(np.float32) for _ in SYNTHETIC_QA]

    with patch("app.vectorstore.faiss_store.embed_batch", AsyncMock(return_value=fake_vectors)), \
         patch("app.vectorstore.faiss_store._index_path", return_value=("/tmp/t.index", "/tmp/t.meta")), \
         patch("faiss.write_index"), \
         patch("builtins.open", create=True):

        from app.vectorstore import faiss_store
        await faiss_store.build_index(SYNTHETIC_QA)
        rec = await faiss_store.get_by_id(1)

    assert rec is not None
    assert rec["id"] == 1
    assert "question" in rec
