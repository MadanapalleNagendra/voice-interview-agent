"""
app/services/followup_service.py
Generates targeted follow-up questions when a candidate's answer is weak.
"""

from app.core.logger import get_logger
from app.core.prompts import FOLLOWUP_PROMPT, LANGUAGE_LABELS
from app.services.llm_service import chat_complete

logger = get_logger(__name__)


async def generate_followup(
    question: str,
    candidate_answer: str,
    score: dict,
    language: str = "en",
) -> str:
    """
    Produce a single follow-up question targeting the lowest-scoring dimension.
    """
    # Identify the weakest dimensions
    dims = {
        "relevance": score.get("relevance", 5),
        "technical_depth": score.get("technical_depth", 5),
        "completeness": score.get("completeness", 5),
        "communication": score.get("communication", 5),
    }
    low_dims = [k for k, v in dims.items() if v < 6]
    gaps = ", ".join(low_dims) if low_dims else "general depth"

    prompt = FOLLOWUP_PROMPT.substitute(
        question=question,
        candidate_answer=candidate_answer,
        gaps=gaps,
        language_label=LANGUAGE_LABELS.get(language, "English"),
    )

    followup = await chat_complete(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=128,
    )
    logger.info(f"Follow-up generated: '{followup}'")
    return followup
