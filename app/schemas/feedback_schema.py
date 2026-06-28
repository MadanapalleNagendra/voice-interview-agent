"""
app/schemas/feedback_schema.py
"""

from typing import Optional
from pydantic import BaseModel


class QuestionScore(BaseModel):
    question_id: int
    question_text: str
    relevance: float
    technical_depth: float
    completeness: float
    communication: float
    confidence: float
    overall: float


class FeedbackResponse(BaseModel):
    session_id: str
    overall_score: float
    grade: str
    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    recommended_topics: list[str]
    hiring_recommendation: str
    summary: str
    question_scores: list[QuestionScore]
