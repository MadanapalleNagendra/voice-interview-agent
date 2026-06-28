"""
app/schemas/interview_schema.py
Request/response schemas for the interview API.
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    language: str = Field(default="en", pattern="^(en|hi|de)$")
    candidate_name: Optional[str] = None


class StartInterviewResponse(BaseModel):
    session_id: str
    message: str
    audio_url: Optional[str] = None
    question_number: int = 1
    total_questions: int


class AnswerRequest(BaseModel):
    session_id: str
    transcript: Optional[str] = None  # pre-transcribed text (used by Streamlit)


class AnswerResponse(BaseModel):
    session_id: str
    interviewer_message: str
    audio_url: Optional[str] = None
    question_number: int
    total_questions: int
    is_complete: bool = False
    score: Optional[dict] = None


class AudioUploadResponse(BaseModel):
    transcript: str
    duration_seconds: Optional[float] = None


class SessionStatusResponse(BaseModel):
    session_id: str
    language: str
    questions_asked: int
    total_questions: int
    is_complete: bool
    current_score_avg: Optional[float] = None
