# 📦 Final Deliverables — Grounded Voice Interview Agent

**Candidate:** Nagendra Madanapalle
**GitHub:** https://github.com/MadanapalleNagendra/voice-interview-agent
**Date:** June 2026

---

## Deliverable 1 — Working Code (GitHub Repository)

### Repository URL
```
https://github.com/MadanapalleNagendra/voice-interview-agent
```

### How to run it (3 commands)

```bash
# 1. Clone
git clone https://github.com/MadanapalleNagendra/voice-interview-agent.git
cd voice-interview-agent

# 2. Add API keys
cp .env.example .env
# Edit .env: set OPENAI_API_KEY and ELEVENLABS_API_KEY

# 3. Run
docker-compose up --build
# → Open http://localhost:8501
```

### Complete file inventory (51 files)

```
voice-interview-agent/
│
├── app/                          # FastAPI backend
│   ├── __init__.py
│   ├── main.py                   # App startup + FAISS index loading
│   ├── worker.py                 # Celery async task worker
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── interview.py          # /interview/start, /answer, /transcribe, /status
│   │   ├── feedback.py           # /feedback/{session_id}
│   │   └── health.py             # /health, /ready
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic settings (reads .env)
│   │   ├── prompts.py            # All 5 prompt templates
│   │   └── logger.py             # Structured logging
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stt_service.py        # Whisper API — audio → transcript
│   │   ├── tts_service.py        # ElevenLabs — text → MP3 (streaming)
│   │   ├── llm_service.py        # GPT-4o — chat_complete, JSON mode, stream
│   │   ├── retrieval_service.py  # FAISS search facade
│   │   ├── scoring_service.py    # 5-dimension evaluator
│   │   ├── followup_service.py   # Follow-up question generator
│   │   └── memory_service.py     # Redis session state + cache
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py             # InterviewSession + InterviewTurn ORM models
│   │   ├── connection.py         # Async SQLAlchemy engine
│   │   └── seed.py               # Table creation
│   │
│   ├── vectorstore/
│   │   ├── __init__.py
│   │   ├── faiss_store.py        # Build/load/search FAISS index
│   │   └── embedder.py           # text-embedding-3-large + Redis cache
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── interview_schema.py   # Request/response Pydantic models
│   │   └── feedback_schema.py    # Feedback response schema
│   │
│   ├── workflows/
│   │   ├── __init__.py
│   │   └── interview_graph.py    # LangGraph state machine (the core)
│   │
│   └── utils/
│       ├── __init__.py
│       ├── audio.py              # WAV conversion, silence detection
│       ├── language.py           # Language validation
│       └── metrics.py            # Async latency timer
│
├── frontend/
│   └── streamlit_app.py          # Voice UI (record + type + feedback dashboard)
│
├── data/
│   └── qa_dataset.json           # 10 software-engineer Q&A pairs
│
├── tests/
│   ├── __init__.py
│   ├── test_stt.py               # STT service unit tests
│   ├── test_tts.py               # TTS service unit tests
│   ├── test_retrieval.py         # FAISS retrieval tests
│   └── test_scoring.py           # Scoring + aggregate tests
│
├── Dockerfile                    # Backend image (Python 3.11 + ffmpeg)
├── Dockerfile.frontend           # Streamlit image
├── docker-compose.yml            # 5 services: backend, frontend, db, redis, worker
├── requirements.txt              # All Python dependencies
├── pyproject.toml                # pytest asyncio config
├── .gitignore                    # Excludes .env, FAISS cache, __pycache__
├── .env.example                  # Copy → .env, add API keys
├── LICENSE                       # MIT
│
├── README.md                     # ← This file
├── architecture.md               # Engineering decisions (1-2 pages)
├── demo_script.md                # Scene-by-scene recording guide
├── DELIVERABLES.md               # This document
├── github_push.sh                # Linux/Mac push script
└── github_push.bat               # Windows push script
```

---

## Deliverable 2 — Demo Recording

**Instructions:** Follow `demo_script.md` to record a 2–4 minute Loom video.

**Loom URL:** _(paste here after recording)_

**What the demo shows:**
1. App running at http://localhost:8501
2. Language selection → Start interview
3. Candidate records a strong answer → interviewer acknowledges + moves on
4. Candidate gives a weak answer → follow-up question triggered
5. Candidate improves answer → score shown
6. Final feedback dashboard (overall score, strengths, weaknesses, recommendations)
7. Swagger API docs at http://localhost:8000/docs

---

## Deliverable 3 — Architecture Note

See [`architecture.md`](architecture.md)

**Summary of key decisions:**

### Retrieval Design
Each Q&A pair is embedded as a **single chunk** (`question + ideal_answer` concatenated). This means every FAISS hit is a complete grounding context — not just a question fragment. The system uses **two retrieval modes**:
- **Semantic search** (embed candidate answer → FAISS top-k): gives the LLM related context
- **Exact lookup** (`get_by_id(question_id)`): guarantees scoring against the exact right reference

### LLM Grounding Without Leaking
Evaluation and interviewer response are **two separate LLM calls**. The interviewer prompt only receives gap labels (e.g. "low technical_depth") — it never sees the ideal answer text. This prevents the agent from quoting the answer back to the candidate.

### Follow-Up Logic
`decide_followup` node: trigger follow-up if `overall < 6.0 AND followup_count < 2`. The cap prevents stalling on hard questions. Follow-ups are targeted to the lowest-scoring dimension.

### Latency
Total warm-path: ~2.3–4.2s. Key optimisations:
- Redis embedding cache (repeated text → < 1ms)
- FAISS on disk (no rebuild after first boot)
- ElevenLabs streaming (playback starts on first audio chunk)
- Async throughout (no blocking calls)

---

## Deliverable 4 — Q&A Dataset

See [`data/qa_dataset.json`](data/qa_dataset.json)

**10 software-engineer interview questions with ideal answers:**

| # | Question | Category | Difficulty |
|---|---|---|---|
| 1 | Design a URL shortener like bit.ly | system_design | medium |
| 2 | Difference between process and thread | operating_systems | medium |
| 3 | What is the CAP theorem? | distributed_systems | hard |
| 4 | How does garbage collection work? | language_internals | medium |
| 5 | How would you design a rate limiter? | system_design | medium |
| 6 | Explain the SOLID principles | software_design | medium |
| 7 | What happens when you type a URL and hit Enter? | networking | medium |
| 8 | What are database indexes? | databases | medium |
| 9 | How does async/await work under the hood in Python? | concurrency | hard |
| 10 | Describe debugging a hard production issue | behavioral | medium |

**Dataset format (easy to extend):**
```json
{
  "id": 11,
  "question": "Your question here",
  "ideal_answer": "The reference answer used internally by the evaluator",
  "category": "system_design",
  "difficulty": "medium",
  "keywords": ["keyword1", "keyword2"]
}
```
Add entries, delete FAISS cache files, restart backend. Zero code changes.

---

## How to Push to GitHub

### Windows (recommended)

1. Open **Command Prompt** or **PowerShell** as Administrator
2. Install GitHub CLI if you haven't: https://cli.github.com/
3. Run `gh auth login` and follow the prompts
4. Navigate to the parent folder of `voice-interview-agent\`
5. Double-click `github_push.bat` OR run in terminal:
   ```cmd
   cd C:\qa\files
   github_push.bat
   ```

### Mac/Linux

```bash
cd /path/to/parent/of/voice-interview-agent
chmod +x voice-interview-agent/github_push.sh
./voice-interview-agent/github_push.sh
```

### Manual Git commands (if scripts don't work)

```bash
cd voice-interview-agent

git init
git add -A
git commit -m "feat: initial release — Grounded Voice Interview Agent"
git branch -M main
git remote add origin https://github.com/MadanapalleNagendra/voice-interview-agent.git
git push -u origin main --force
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | GPT-4o + Whisper + Embeddings |
| `ELEVENLABS_API_KEY` | ✅ Yes | TTS voice synthesis |
| `DATABASE_URL` | Auto | Set by Docker Compose |
| `REDIS_URL` | Auto | Set by Docker Compose |
| `OPENAI_CHAT_MODEL` | Optional | Default: `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | Optional | Default: `text-embedding-3-large` |
| `ELEVENLABS_VOICE_ID` | Optional | Default: `EXAVITQu4vr4xnSDxMaL` (Bella) |
| `ELEVENLABS_MODEL_ID` | Optional | Default: `eleven_multilingual_v2` |
| `MAX_QUESTIONS` | Optional | Default: `10` |
| `DEFAULT_LANGUAGE` | Optional | Default: `en` (en/hi/de) |

---

## Running Tests

```bash
# From the project root (with venv activated)
pytest tests/ -v

# Expected output:
# tests/test_stt.py::test_transcribe_returns_text          PASSED
# tests/test_stt.py::test_transcribe_with_no_language_hint PASSED
# tests/test_stt.py::test_transcribe_error_propagates      PASSED
# tests/test_tts.py::test_synthesise_returns_bytes         PASSED
# tests/test_tts.py::test_synthesise_raises_on_http_error  PASSED
# tests/test_retrieval.py::test_build_and_search           PASSED
# tests/test_retrieval.py::test_get_by_id                  PASSED
# tests/test_scoring.py::test_score_answer_structure       PASSED
# tests/test_scoring.py::test_score_answer_fallback        PASSED
# tests/test_scoring.py::test_compute_aggregate_score      PASSED
# 10 passed
```

All tests use mocking — **no API keys needed to run tests**.
