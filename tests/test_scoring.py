"""
tests/test_scoring.py
"""

import pytest
from unittest.mock import AsyncMock, patch


MOCK_SCORE = {
    "relevance": 8,
    "technical_depth": 7,
    "completeness": 6,
    "communication": 9,
    "confidence": 7,
    "overall": 7.4,
    "reasoning": {
        "relevance": "Answer directly addresses the question.",
        "technical_depth": "Mentions core concepts but misses edge cases.",
        "completeness": "Covers main points but omits caching.",
        "communication": "Clear and well-structured.",
        "confidence": "Speaks with conviction.",
    },
    "is_weak": False,
}


@pytest.mark.asyncio
async def test_score_answer_structure():
    """score_answer should return a dict with the 5 required dimensions."""
    with patch("app.services.scoring_service.chat_complete_json", AsyncMock(return_value=MOCK_SCORE)):
        from app.services.scoring_service import score_answer
        result = await score_answer(
            question="Design a URL shortener",
            ideal_answer="Use Base62 encoding with a Redis cache.",
            candidate_answer="I would hash the URL and store in a database.",
        )

    required_keys = {"relevance", "technical_depth", "completeness", "communication", "confidence", "overall"}
    assert required_keys.issubset(result.keys())
    assert 1 <= result["overall"] <= 10


@pytest.mark.asyncio
async def test_score_answer_fallback_on_error():
    """If LLM call fails, should return neutral score instead of crashing."""
    with patch("app.services.scoring_service.chat_complete_json", AsyncMock(side_effect=Exception("API down"))):
        from app.services.scoring_service import score_answer
        result = await score_answer("Q", "A", "B")

    assert result["overall"] == 5.0  # neutral fallback


def test_compute_aggregate_score():
    from app.services.scoring_service import compute_aggregate_score

    scores = [{"overall": 7.0}, {"overall": 9.0}, {"overall": 5.0}]
    avg = compute_aggregate_score(scores)
    assert avg == pytest.approx(7.0, 0.1)

    assert compute_aggregate_score([]) == 0.0
