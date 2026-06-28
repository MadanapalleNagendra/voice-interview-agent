"""
app/workflows/interview_graph.py
LangGraph state machine for the interview pipeline.

Node order:
  START → retrieve_context → evaluate_answer → decide_followup
        → next_question → generate_tts → END

The graph is compiled once and reused across requests (it's stateless internally;
all mutable state lives in InterviewState which is passed per-invocation).
"""

from __future__ import annotations

import json
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.logger import get_logger
from app.core.prompts import (
    FINAL_FEEDBACK_PROMPT,
    INTERVIEWER_SYSTEM_PROMPT,
    LANGUAGE_LABELS,
    NEXT_QUESTION_PROMPT,
)
from app.services import (
    followup_service,
    llm_service,
    retrieval_service,
    scoring_service,
    tts_service,
)

logger = get_logger(__name__)


# ── State schema ──────────────────────────────────────────────────────────────

class InterviewState(TypedDict, total=False):
    # Inputs per turn
    session_id: str
    language: str
    candidate_answer: str          # current turn's transcript
    current_question_id: int       # which question we just asked
    current_question_text: str
    conversation_history: list[dict]  # full chat messages list

    # Retrieved context
    reference_context: list[dict]  # top-k FAISS results

    # Evaluation output
    score: dict
    is_weak: bool
    is_complete: bool              # all questions done?

    # Outputs
    interviewer_message: str       # text response from agent
    audio_bytes: Optional[bytes]   # TTS output

    # Accumulated state (carried forward across turns)
    asked_ids: list[int]
    scores: list[dict]             # one per question answered
    followup_count: int            # follow-ups for current question
    feedback: Optional[dict]       # populated when is_complete=True


# ── Node implementations ──────────────────────────────────────────────────────

async def node_retrieve_context(state: InterviewState) -> InterviewState:
    """Semantic search: find the most relevant Q&A references for this answer."""
    query = state.get("candidate_answer", "") or state.get("current_question_text", "")
    refs = await retrieval_service.retrieve_context(query, top_k=3)
    return {**state, "reference_context": refs}


async def node_evaluate_answer(state: InterviewState) -> InterviewState:
    """Score the candidate's answer against the reference ideal answer."""
    candidate_answer = state.get("candidate_answer", "")
    if not candidate_answer:
        # No answer yet (first turn — just asking a question)
        return {**state, "score": {}, "is_weak": False}

    # Find the reference for the current question
    current_id = state.get("current_question_id")
    ref = await retrieval_service.get_question_by_id(current_id) if current_id else None

    if ref is None:
        # Fall back to top FAISS result
        refs = state.get("reference_context", [])
        ref = refs[0] if refs else {}

    score = await scoring_service.score_answer(
        question=ref.get("question", state.get("current_question_text", "")),
        ideal_answer=ref.get("ideal_answer", ""),
        candidate_answer=candidate_answer,
    )

    # Attach metadata for final feedback
    score["question_id"] = ref.get("id")
    score["question_text"] = ref.get("question", state.get("current_question_text", ""))

    scores = list(state.get("scores", []))
    scores.append(score)

    return {**state, "score": score, "is_weak": score.get("is_weak", False), "scores": scores}


async def node_decide_followup(state: InterviewState) -> InterviewState:
    """
    Decision node: should we ask a follow-up or move on?
    Follow-up if: answer is weak AND we haven't already asked 2 follow-ups for this Q.
    """
    is_weak = state.get("is_weak", False)
    followup_count = state.get("followup_count", 0)
    candidate_answer = state.get("candidate_answer", "")

    if is_weak and followup_count < 2 and candidate_answer:
        followup = await followup_service.generate_followup(
            question=state.get("current_question_text", ""),
            candidate_answer=candidate_answer,
            score=state.get("score", {}),
            language=state.get("language", "en"),
        )
        # Build full interviewer message acknowledging then asking follow-up
        msg = followup
        history = list(state.get("conversation_history", []))
        history.append({"role": "assistant", "content": msg})
        return {
            **state,
            "interviewer_message": msg,
            "conversation_history": history,
            "followup_count": followup_count + 1,
            # Stay on same question — don't advance
        }
    else:
        # Reset follow-up counter and advance
        return {**state, "followup_count": 0}


async def node_next_question(state: InterviewState) -> InterviewState:
    """
    Select and pose the next interview question.
    If all questions are asked, trigger final feedback generation.
    """
    asked_ids = list(state.get("asked_ids", []))
    all_questions = retrieval_service.get_all_questions()
    remaining = [q for q in all_questions if q["id"] not in asked_ids]

    if not remaining:
        # All done — generate feedback
        return await _finalize_interview(state)

    # Pick the next question (LLM-guided selection for natural flow)
    next_q = await _pick_next_question(remaining, asked_ids, state)

    asked_ids.append(next_q["id"])
    question_text = next_q["question"]

    # Build interviewer message via LLM for natural phrasing
    lang = state.get("language", "en")
    lang_label = LANGUAGE_LABELS.get(lang, "English")

    # If there was a previous answer, acknowledge it first
    prev_score = state.get("score", {})
    prev_answer = state.get("candidate_answer", "")

    system = INTERVIEWER_SYSTEM_PROMPT.substitute(language_label=lang_label)
    history = list(state.get("conversation_history", []))

    # Compose turn context
    context_note = ""
    if prev_answer and prev_score:
        overall = prev_score.get("overall", 0)
        if overall >= 7:
            context_note = "The candidate gave a good answer. Acknowledge briefly and move on."
        else:
            context_note = "Transition naturally to the next question."

    user_content = (
        f"{context_note}\n\n"
        f"Now ask this question naturally (do NOT say 'Question X:'): {question_text}"
    )
    history.append({"role": "user", "content": user_content})

    messages = [{"role": "system", "content": system}] + history
    interviewer_msg = await llm_service.chat_complete(messages, temperature=0.7, max_tokens=200)

    history[-1] = {"role": "user", "content": f"[System: ask next question]"}
    history.append({"role": "assistant", "content": interviewer_msg})

    return {
        **state,
        "current_question_id": next_q["id"],
        "current_question_text": question_text,
        "asked_ids": asked_ids,
        "candidate_answer": "",  # reset for next turn
        "interviewer_message": interviewer_msg,
        "conversation_history": history,
        "is_complete": False,
    }


async def node_generate_tts(state: InterviewState) -> InterviewState:
    """Convert the interviewer's text response to audio."""
    msg = state.get("interviewer_message", "")
    if not msg:
        return state
    try:
        audio = await tts_service.synthesise(msg)
        return {**state, "audio_bytes": audio}
    except Exception as e:
        logger.warning(f"TTS failed (non-fatal): {e}")
        return {**state, "audio_bytes": None}


# ── Helper functions ───────────────────────────────────────────────────────────

async def _pick_next_question(
    remaining: list[dict], asked_ids: list[int], state: InterviewState
) -> dict:
    """Use LLM to pick the most natural next question, or fall back to first."""
    if len(remaining) == 1:
        return remaining[0]
    try:
        prompt = NEXT_QUESTION_PROMPT.substitute(
            available_questions=json.dumps([{"id": q["id"], "question": q["question"], "category": q["category"]} for q in remaining]),
            asked_ids=json.dumps(asked_ids),
            conversation_summary=f"Last question: {state.get('current_question_text', 'N/A')}",
        )
        raw = await llm_service.chat_complete(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=16,
        )
        chosen_id = int(raw.strip())
        match = next((q for q in remaining if q["id"] == chosen_id), None)
        return match or remaining[0]
    except Exception:
        return remaining[0]


async def _finalize_interview(state: InterviewState) -> InterviewState:
    """Generate structured final feedback once all questions are answered."""
    scores = state.get("scores", [])

    perf_summary = json.dumps(
        [
            {
                "question": s.get("question_text"),
                "overall": s.get("overall"),
                "relevance": s.get("relevance"),
                "technical_depth": s.get("technical_depth"),
                "completeness": s.get("completeness"),
                "communication": s.get("communication"),
                "confidence": s.get("confidence"),
            }
            for s in scores
        ],
        indent=2,
    )

    prompt = FINAL_FEEDBACK_PROMPT.substitute(performance_summary=perf_summary)
    try:
        feedback = await llm_service.chat_complete_json(
            [{"role": "user", "content": prompt}], temperature=0.3
        )
    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        feedback = {"error": str(e)}

    # Closing message from interviewer
    lang = state.get("language", "en")
    lang_label = LANGUAGE_LABELS.get(lang, "English")
    closing = await llm_service.chat_complete(
        [
            {
                "role": "user",
                "content": (
                    f"Respond in {lang_label}. The interview is now complete. "
                    "Give a warm 2-sentence closing, thank the candidate, "
                    "and say you'll share feedback shortly."
                ),
            }
        ],
        temperature=0.7,
        max_tokens=100,
    )

    history = list(state.get("conversation_history", []))
    history.append({"role": "assistant", "content": closing})

    return {
        **state,
        "interviewer_message": closing,
        "conversation_history": history,
        "is_complete": True,
        "feedback": feedback,
        "candidate_answer": "",
    }


# ── Conditional edge: after decide_followup ───────────────────────────────────

def should_ask_followup(state: InterviewState) -> str:
    """Route to TTS if we have a follow-up, else go to next_question."""
    if state.get("interviewer_message") and state.get("followup_count", 0) > 0:
        # We just set a follow-up message — go straight to TTS
        return "generate_tts"
    return "next_question"


# ── Graph compilation ──────────────────────────────────────────────────────────

def build_interview_graph():
    graph = StateGraph(InterviewState)

    graph.add_node("retrieve_context", node_retrieve_context)
    graph.add_node("evaluate_answer", node_evaluate_answer)
    graph.add_node("decide_followup", node_decide_followup)
    graph.add_node("next_question", node_next_question)
    graph.add_node("generate_tts", node_generate_tts)

    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "evaluate_answer")
    graph.add_edge("evaluate_answer", "decide_followup")
    graph.add_conditional_edges("decide_followup", should_ask_followup)
    graph.add_edge("next_question", "generate_tts")
    graph.add_edge("generate_tts", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_interview_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_interview_graph()
    return _compiled_graph
