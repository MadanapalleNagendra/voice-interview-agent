"""
app/services/scoring_service.py
Evaluates a candidate's answer against the ideal reference answer using the LLM.
Returns a structured score dict.
"""

from string import Template

from app.core.logger import get_logger
from app.core.prompts import EVALUATION_PROMPT
from app.services.llm_service import chat_complete_json

logger = get_logger(__name__)


async def score_answer(
    question: str,
    ideal_answer: str,
    candidate_answer: str,
) -> dict:
    """
    Score the candidate's answer on 5 dimensions (1–10 each).
    Returns a dict matching the EVALUATION_PROMPT schema.
    """
    prompt = EVALUATION_PROMPT.substitute(
        question=question,
        ideal_answer=ideal_answer,
        candidate_answer=candidate_answer,
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        result = await chat_complete_json(messages, temperature=0.1)
        # Validate required keys
        required = {"relevance", "technical_depth", "completeness", "communication", "confidence", "overall", "is_weak"}
        if not required.issubset(result.keys()):
            raise ValueError(f"Missing keys in score response: {required - result.keys()}")
        return result
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        # Return a neutral score on failure rather than crashing the interview
        return {
            "relevance": 5,
            "technical_depth": 5,
            "completeness": 5,
            "communication": 5,
            "confidence": 5,
            "overall": 5.0,
            "reasoning": {"error": str(e)},
            "is_weak": False,
        }


def compute_aggregate_score(scores: list[dict]) -> float:
    """Compute a weighted average across all question scores."""
    if not scores:
        return 0.0
    totals = [s.get("overall", 5.0) for s in scores]
    return round(sum(totals) / len(totals), 1)
