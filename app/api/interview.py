"""
app/api/interview.py
FastAPI routes for interview sessions.

POST /interview/start        — start a new session, get first question
POST /interview/answer       — submit a text answer, get next response
POST /interview/transcribe   — upload audio, get transcript (STT only)
GET  /interview/{session_id}/status
"""

import base64
import uuid
from datetime import datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.prompts import INTERVIEWER_SYSTEM_PROMPT, LANGUAGE_LABELS
from app.database.connection import get_db
from app.database.models import InterviewSession, InterviewTurn
from app.schemas.interview_schema import (
    AnswerRequest,
    AnswerResponse,
    AudioUploadResponse,
    SessionStatusResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from app.services import memory_service, stt_service, tts_service
from app.services.retrieval_service import get_all_questions
from app.utils.audio import convert_to_wav
from app.utils.language import validate_language
from app.utils.metrics import timer
from app.workflows.interview_graph import get_interview_graph, InterviewState

router = APIRouter(prefix="/interview", tags=["Interview"])
settings = get_settings()
logger = get_logger(__name__)


@router.post("/start", response_model=StartInterviewResponse)
async def start_interview(req: StartInterviewRequest):
    """Create a new interview session and return the opening question."""
    lang = validate_language(req.language)
    session_id = str(uuid.uuid4())

    # Build initial LangGraph state
    all_questions = get_all_questions()

    initial_state: InterviewState = {
        "session_id": session_id,
        "language": lang,
        "candidate_answer": "",
        "current_question_id": None,
        "current_question_text": "",
        "conversation_history": [
            {
                "role": "system",
                "content": INTERVIEWER_SYSTEM_PROMPT.substitute(
                    language_label=LANGUAGE_LABELS.get(lang, "English")
                ),
            }
        ],
        "reference_context": [],
        "score": {},
        "is_weak": False,
        "is_complete": False,
        "interviewer_message": "",
        "audio_bytes": None,
        "asked_ids": [],
        "scores": [],
        "followup_count": 0,
        "feedback": None,
    }

    # Add opening greeting + first question via graph
    async with timer("interview_start"):
        graph = get_interview_graph()
        result: InterviewState = await graph.ainvoke(initial_state)

    # Persist session to Redis
    redis_state = {k: v for k, v in result.items() if k != "audio_bytes"}
    await memory_service.create_session(session_id, redis_state)

    # Persist to Postgres
    async with get_db() as db:
        session = InterviewSession(
            id=session_id,
            candidate_name=req.candidate_name,
            language=lang,
        )
        db.add(session)

    audio_b64 = None
    if result.get("audio_bytes"):
        audio_b64 = base64.b64encode(result["audio_bytes"]).decode()

    return StartInterviewResponse(
        session_id=session_id,
        message=result.get("interviewer_message", ""),
        audio_url=audio_b64,  # base64 in response; frontend decodes
        question_number=1,
        total_questions=len(all_questions),
    )


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(req: AnswerRequest):
    """Process a candidate's text answer and return the next interviewer message."""
    state = await memory_service.get_session(req.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if state.get("is_complete"):
        raise HTTPException(status_code=400, detail="Interview already complete")

    state["candidate_answer"] = req.transcript or ""
    state["audio_bytes"] = None  # can't serialise bytes in Redis

    async with timer("graph_invocation"):
        graph = get_interview_graph()
        result: InterviewState = await graph.ainvoke(state)

    # Save updated state (without audio bytes)
    redis_state = {k: v for k, v in result.items() if k != "audio_bytes"}
    await memory_service.update_session(req.session_id, redis_state)

    # Persist turn to Postgres
    async with get_db() as db:
        turn = InterviewTurn(
            session_id=req.session_id,
            turn_number=len(result.get("asked_ids", [])),
            question_id=result.get("current_question_id"),
            question_text=result.get("current_question_text", ""),
            candidate_answer=req.transcript,
            interviewer_response=result.get("interviewer_message"),
            is_followup=result.get("followup_count", 0) > 0,
            score_json=result.get("score") or None,
        )
        db.add(turn)

        if result.get("is_complete"):
            await db.execute(
                __import__("sqlalchemy").update(InterviewSession)
                .where(InterviewSession.id == req.session_id)
                .values(
                    is_complete=True,
                    ended_at=datetime.utcnow(),
                    overall_score=result.get("feedback", {}).get("overall_score"),
                    feedback_json=result.get("feedback"),
                )
            )

    audio_b64 = None
    if result.get("audio_bytes"):
        audio_b64 = base64.b64encode(result["audio_bytes"]).decode()

    all_questions = get_all_questions()
    return AnswerResponse(
        session_id=req.session_id,
        interviewer_message=result.get("interviewer_message", ""),
        audio_url=audio_b64,
        question_number=len(result.get("asked_ids", [])),
        total_questions=len(all_questions),
        is_complete=result.get("is_complete", False),
        score=result.get("score") or None,
    )


@router.post("/transcribe", response_model=AudioUploadResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = Form(default="en"),
):
    """Accept an audio file upload and return its Whisper transcript."""
    raw = await audio.read()
    wav = convert_to_wav(raw, source_format=audio.filename.split(".")[-1] if audio.filename else "webm")

    async with timer("stt"):
        result = await stt_service.transcribe(wav, filename=audio.filename or "audio.wav", language=language)

    return AudioUploadResponse(transcript=result["text"])


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_status(session_id: str):
    state = await memory_service.get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    scores = state.get("scores", [])
    avg = sum(s.get("overall", 5) for s in scores) / len(scores) if scores else None

    return SessionStatusResponse(
        session_id=session_id,
        language=state.get("language", "en"),
        questions_asked=len(state.get("asked_ids", [])),
        total_questions=len(get_all_questions()),
        is_complete=state.get("is_complete", False),
        current_score_avg=round(avg, 1) if avg else None,
    )
