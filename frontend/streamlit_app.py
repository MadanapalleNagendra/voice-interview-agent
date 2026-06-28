"""
frontend/streamlit_app.py
Streamlit UI for the Voice Interview Agent.

Features:
- Language selector
- Start interview button
- Audio recorder (st-audiorec)
- Text fallback input
- Live transcript display
- Score display per question
- Final feedback dashboard
"""

import base64
import io
import time

import httpx
import streamlit as st

# ── Configuration ─────────────────────────────────────────────────────────────
API_BASE = "http://backend:8000"
LANG_OPTIONS = {"English": "en", "Hindi": "hi", "German": "de"}

st.set_page_config(
    page_title="Voice Interview Agent",
    page_icon="🎙️",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .interviewer-msg {
        background: #1e3a5f;
        color: white;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        font-size: 1.05rem;
    }
    .candidate-msg {
        background: #f0f4f8;
        color: #222;
        padding: 0.8rem 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.5rem;
        font-size: 1rem;
    }
    .score-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-top: 0.3rem;
        background: #fafafa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state helpers ─────────────────────────────────────────────────────
def init_state():
    defaults = {
        "session_id": None,
        "language": "en",
        "messages": [],          # list of {role, content}
        "is_complete": False,
        "scores": [],
        "feedback": None,
        "question_number": 0,
        "total_questions": 10,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ── API helpers ───────────────────────────────────────────────────────────────
def api_start(language: str, name: str | None) -> dict:
    r = httpx.post(
        f"{API_BASE}/interview/start",
        json={"language": language, "candidate_name": name or None},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def api_answer(session_id: str, transcript: str) -> dict:
    r = httpx.post(
        f"{API_BASE}/interview/answer",
        json={"session_id": session_id, "transcript": transcript},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def api_transcribe(audio_bytes: bytes, language: str) -> str:
    r = httpx.post(
        f"{API_BASE}/interview/transcribe",
        files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
        data={"language": language},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["transcript"]


def api_feedback(session_id: str) -> dict:
    r = httpx.get(f"{API_BASE}/feedback/{session_id}", timeout=30)
    r.raise_for_status()
    return r.json()


def play_audio(audio_b64: str | None):
    if not audio_b64:
        return
    audio_bytes = base64.b64decode(audio_b64)
    st.audio(audio_bytes, format="audio/mp3", autoplay=True)


# ── UI ────────────────────────────────────────────────────────────────────────

st.title("🎙️ Voice Interview Agent")
st.caption("A realistic mock software-engineer interview powered by GPT-4o + Whisper + ElevenLabs")

# ── Sidebar: setup ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    lang_label = st.selectbox("Interview Language", list(LANG_OPTIONS.keys()))
    lang_code = LANG_OPTIONS[lang_label]
    candidate_name = st.text_input("Your Name (optional)", placeholder="Ada Lovelace")

    st.markdown("---")
    st.markdown("**How to use:**")
    st.markdown("1. Click **Start Interview**")
    st.markdown("2. Listen to the question")
    st.markdown("3. Record your answer or type it")
    st.markdown("4. Submit and await follow-up")
    st.markdown("5. Receive final feedback at the end")

    if st.session_state.session_id:
        st.markdown("---")
        st.markdown(f"**Session:** `{st.session_state.session_id[:8]}…`")
        st.markdown(f"**Progress:** {st.session_state.question_number}/{st.session_state.total_questions}")
        if st.button("🔄 Restart Interview"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ── Start screen ──────────────────────────────────────────────────────────────
if not st.session_state.session_id:
    st.markdown("### Ready to practise?")
    st.markdown(
        "This agent will ask you **software-engineer interview questions**, "
        "evaluate your answers in real-time, ask follow-ups when you're vague, "
        "and give you structured feedback at the end."
    )

    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        with st.spinner("Setting up your interview…"):
            try:
                result = api_start(lang_code, candidate_name)
                st.session_state.session_id = result["session_id"]
                st.session_state.language = lang_code
                st.session_state.total_questions = result["total_questions"]
                st.session_state.question_number = result["question_number"]
                st.session_state.messages.append(
                    {"role": "assistant", "content": result["message"]}
                )
                st.session_state._last_audio = result.get("audio_url")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to start: {e}")

    st.stop()


# ── Active interview ──────────────────────────────────────────────────────────

# Play latest TTS audio
if hasattr(st.session_state, "_last_audio") and st.session_state._last_audio:
    play_audio(st.session_state._last_audio)
    st.session_state._last_audio = None

# Display conversation history
st.markdown("### 💬 Conversation")
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.markdown(
            f'<div class="interviewer-msg">🤖 <b>Interviewer:</b> {msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="candidate-msg">🧑 <b>You:</b> {msg["content"]}</div>',
            unsafe_allow_html=True,
        )

# Progress
if not st.session_state.is_complete:
    st.progress(
        st.session_state.question_number / st.session_state.total_questions,
        text=f"Question {st.session_state.question_number} of {st.session_state.total_questions}",
    )

    st.markdown("---")
    st.markdown("### 🎤 Your Answer")

    # Audio recorder tab vs text tab
    tab_audio, tab_text = st.tabs(["🎙️ Record Voice", "⌨️ Type Answer"])

    with tab_audio:
        try:
            from st_audiorec import st_audiorec
            wav_audio_data = st_audiorec()

            if wav_audio_data is not None:
                with st.spinner("Transcribing your answer…"):
                    transcript = api_transcribe(wav_audio_data, lang_code)
                st.success(f"**Transcript:** {transcript}")

                if st.button("✅ Submit Voice Answer", type="primary"):
                    with st.spinner("Thinking…"):
                        resp = api_answer(st.session_state.session_id, transcript)
                    st.session_state.messages.append({"role": "user", "content": transcript})
                    st.session_state.messages.append({"role": "assistant", "content": resp["interviewer_message"]})
                    st.session_state.question_number = resp["question_number"]
                    st.session_state.is_complete = resp["is_complete"]
                    st.session_state._last_audio = resp.get("audio_url")
                    if resp.get("score"):
                        st.session_state.scores.append(resp["score"])
                    st.rerun()

        except ImportError:
            st.info("Install `st-audiorec` for voice recording: `pip install st-audiorec`")

    with tab_text:
        answer_text = st.text_area(
            "Type your answer here:",
            placeholder="Explain your approach…",
            height=150,
            key="text_answer",
        )
        if st.button("✅ Submit Text Answer", type="primary", disabled=not answer_text.strip()):
            with st.spinner("Evaluating…"):
                resp = api_answer(st.session_state.session_id, answer_text.strip())
            st.session_state.messages.append({"role": "user", "content": answer_text.strip()})
            st.session_state.messages.append({"role": "assistant", "content": resp["interviewer_message"]})
            st.session_state.question_number = resp["question_number"]
            st.session_state.is_complete = resp["is_complete"]
            st.session_state._last_audio = resp.get("audio_url")
            if resp.get("score"):
                st.session_state.scores.append(resp["score"])
            st.rerun()

    # Show last score inline
    if st.session_state.scores:
        last = st.session_state.scores[-1]
        with st.expander("📊 Last answer score"):
            cols = st.columns(5)
            dims = ["relevance", "technical_depth", "completeness", "communication", "confidence"]
            for col, dim in zip(cols, dims):
                col.metric(dim.replace("_", " ").title(), f"{last.get(dim, 0)}/10")
            st.metric("Overall", f"{last.get('overall', 0)}/10")


# ── Completed interview — show feedback ───────────────────────────────────────
else:
    st.success("🎉 Interview Complete!")

    with st.spinner("Generating your feedback…"):
        try:
            feedback = api_feedback(st.session_state.session_id)
        except Exception as e:
            st.error(f"Could not load feedback: {e}")
            st.stop()

    st.markdown("---")
    st.markdown("## 📋 Your Interview Feedback")

    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Score", f"{feedback['overall_score']}/10")
    col2.metric("Grade", feedback["grade"])
    col3.metric("Recommendation", feedback["hiring_recommendation"])

    st.markdown(f"> {feedback['summary']}")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### ✅ Strengths")
        for s in feedback["strengths"]:
            st.markdown(f"- {s}")

    with col_right:
        st.markdown("### ⚠️ Weaknesses")
        for w in feedback["weaknesses"]:
            st.markdown(f"- {w}")

    st.markdown("### 📈 How to Improve")
    for imp in feedback["improvements"]:
        st.markdown(f"- {imp}")

    st.markdown("### 📚 Recommended Study Topics")
    for topic in feedback["recommended_topics"]:
        st.markdown(f"- `{topic}`")

    if feedback.get("question_scores"):
        st.markdown("---")
        st.markdown("### 📊 Per-Question Breakdown")
        for qs in feedback["question_scores"]:
            with st.expander(f"Q: {qs['question_text'][:80]}…"):
                cols = st.columns(5)
                for col, dim in zip(cols, ["relevance", "technical_depth", "completeness", "communication", "confidence"]):
                    col.metric(dim.replace("_", " ").title(), f"{qs[dim]}/10")
                st.metric("Overall", f"{qs['overall']}/10")

    if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
