"""
app/api/feedback.py
GET /feedback/{session_id} — retrieve final structured feedback.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.feedback_schema import FeedbackResponse, QuestionScore
from app.services import memory_service

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("/{session_id}", response_model=FeedbackResponse)
async def get_feedback(session_id: str):
    """Return the final structured feedback for a completed interview."""
    state = await memory_service.get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if not state.get("is_complete"):
        raise HTTPException(status_code=400, detail="Interview not yet complete")

    feedback = state.get("feedback", {})
    scores = state.get("scores", [])

    question_scores = [
        QuestionScore(
            question_id=s.get("question_id", i),
            question_text=s.get("question_text", ""),
            relevance=s.get("relevance", 0),
            technical_depth=s.get("technical_depth", 0),
            completeness=s.get("completeness", 0),
            communication=s.get("communication", 0),
            confidence=s.get("confidence", 0),
            overall=s.get("overall", 0),
        )
        for i, s in enumerate(scores)
    ]

    return FeedbackResponse(
        session_id=session_id,
        overall_score=feedback.get("overall_score", 0),
        grade=feedback.get("grade", ""),
        strengths=feedback.get("strengths", []),
        weaknesses=feedback.get("weaknesses", []),
        improvements=feedback.get("improvements", []),
        recommended_topics=feedback.get("recommended_topics", []),
        hiring_recommendation=feedback.get("hiring_recommendation", ""),
        summary=feedback.get("summary", ""),
        question_scores=question_scores,
    )
