# 🎙️ Grounded Voice Interview Agent

> **A production-grade, voice-based mock interview system for software engineers.**
> The candidate speaks naturally. The AI interviews them using a grounded Q&A dataset,
> asks adaptive follow-up questions, evaluates every answer, and produces structured feedback.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-purple)](https://langchain-ai.github.io/langgraph/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)

---

## 📺 Demo

> Record a 2–4 minute Loom screen recording using [demo_script.md](demo_script.md)
> and paste the Loom link here.

---

## 🗺️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    CANDIDATE (Browser)                           │
│           Streamlit UI  :8501                                    │
│     [🎤 Record Voice] [⌨️ Type] [📊 Feedback Dashboard]          │
└───────────────────────┬──────────────────────────────────────────┘
                        │  HTTP / base64 audio
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│              FastAPI Backend  :8000                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              LangGraph State Machine                       │  │
│  │                                                            │  │
│  │  START → retrieve_context → evaluate_answer                │  │
│  │        → decide_followup  → next_question                  │  │
│  │        → generate_tts     → END                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Whisper API    GPT-4o API    ElevenLabs TTS    Embeddings API   │
│  FAISS (local)  Redis (sessions+cache)  PostgreSQL (audit log)   │
└──────────────────────────────────────────────────────────────────┘
```

### Warm path latency budget

| Step | ~Time |
|---|---|
| STT (Whisper API, 10–20s audio) | 800–1200 ms |
| Embed answer + FAISS search | 200–400 ms |
| LLM evaluation (JSON mode) | 600–1200 ms |
| LLM interviewer response | 400–800 ms |
| TTS first chunk (ElevenLabs) | 300–600 ms |
| **Total end-to-end** | **~2.3–4.2 s** |

---

## 📁 Project Structure

```
voice-interview-agent/
├── app/
│   ├── api/
│   │   ├── interview.py        # POST /interview/start|answer|transcribe
│   │   ├── feedback.py         # GET  /feedback/{session_id}
│   │   └── health.py           # GET  /health  /ready
│   ├── core/
│   │   ├── config.py           # Pydantic settings — reads .env
│   │   ├── prompts.py          # ALL prompt templates (edit here)
│   │   └── logger.py           # Structured logging
│   ├── services/
│   │   ├── stt_service.py      # Whisper API wrapper
│   │   ├── tts_service.py      # ElevenLabs streaming TTS
│   │   ├── llm_service.py      # GPT-4o async (stream + JSON mode)
│   │   ├── retrieval_service.py# FAISS semantic search facade
│   │   ├── scoring_service.py  # 5-dimension answer evaluator
│   │   ├── followup_service.py # Follow-up question generator
│   │   └── memory_service.py   # Redis session state + cache
│   ├── database/
│   │   ├── models.py           # SQLAlchemy: InterviewSession, Turn
│   │   ├── connection.py       # Async engine + session factory
│   │   └── seed.py             # Table creation helper
│   ├── vectorstore/
│   │   ├── faiss_store.py      # Build / load / search FAISS index
│   │   └── embedder.py         # text-embedding-3-large + Redis cache
│   ├── schemas/
│   │   ├── interview_schema.py # Pydantic I/O models
│   │   └── feedback_schema.py  # Feedback response schema
│   ├── workflows/
│   │   └── interview_graph.py  # LangGraph state machine (core)
│   ├── utils/
│   │   ├── audio.py            # WAV conversion, silence detection
│   │   ├── language.py         # Language validation
│   │   └── metrics.py          # Async latency timer
│   ├── main.py                 # FastAPI app + startup events
│   └── worker.py               # Celery app definition
├── frontend/
│   └── streamlit_app.py        # Voice UI
├── data/
│   └── qa_dataset.json         # 10 Q&A pairs  ← edit here
├── tests/
│   ├── test_stt.py
│   ├── test_tts.py
│   ├── test_retrieval.py
│   └── test_scoring.py
├── Dockerfile                  # Backend image
├── Dockerfile.frontend         # Streamlit image
├── docker-compose.yml          # 5-service stack
├── requirements.txt
├── pyproject.toml
├── architecture.md             # Engineering decisions
├── demo_script.md
├── github_push.sh              # One-command GitHub upload
└── .env.example
```

---

## ⚡ Quick Start (Docker — recommended)

### 1. Clone

```bash
git clone https://github.com/MadanapalleNagendra/voice-interview-agent.git
cd voice-interview-agent
```

### 2. Configure

```bash
cp .env.example .env
# Open .env and fill in:
#   OPENAI_API_KEY=sk-...
#   ELEVENLABS_API_KEY=...
```

### 3. Run

```bash
docker-compose up --build
```

First boot: ~2 min (builds images + creates FAISS embeddings via OpenAI API once).
Restarts: fast (index cached to disk).

### 4. Open

| Service | URL |
|---|---|
| 🎙️ **Interview UI** | **http://localhost:8501** |
| 📖 API Docs (Swagger) | http://localhost:8000/docs |
| ❤️ Health | http://localhost:8000/health |

---

## 🔧 Local Dev (no Docker)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start just the infrastructure
docker-compose up db redis -d

# Set env vars
export OPENAI_API_KEY=sk-...
export ELEVENLABS_API_KEY=...
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/interview_db
export REDIS_URL=redis://localhost:6379/0

# Backend
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
streamlit run frontend/streamlit_app.py --server.port 8501
```

---

## 🌐 Supported Languages

| Code | Language |
|---|---|
| `en` | English (default) |
| `hi` | Hindi |
| `de` | German |

Uses `eleven_multilingual_v2` — one voice model handles all three.

---

## 📊 Scoring Dimensions (1–10 each)

| Dimension | What it measures |
|---|---|
| **Relevance** | Does the answer address the question? |
| **Technical Depth** | Are the right technical concepts present? |
| **Completeness** | Are all key points covered? |
| **Communication** | Clear, structured explanation? |
| **Confidence** | Assertive delivery? |

Follow-up is triggered when `overall < 6.0` AND `follow-up count < 2`.

---

## 🗃️ Updating the Q&A Dataset

Edit `data/qa_dataset.json` — **zero code changes needed**:

```json
{
  "id": 11,
  "question": "Explain the difference between SQL and NoSQL databases.",
  "ideal_answer": "SQL databases are relational with fixed schemas...",
  "category": "databases",
  "difficulty": "medium",
  "keywords": ["relational", "NoSQL", "ACID", "schema"]
}
```

Then restart:

```bash
rm -f data/faiss_index.index data/faiss_index.meta
docker-compose restart backend
```

---

## 🔌 API Reference

### `POST /interview/start`
```json
// Request
{ "language": "en", "candidate_name": "Ada Lovelace" }

// Response
{
  "session_id": "uuid-...",
  "message": "Welcome Ada! Let's begin — can you walk me through how you'd design a URL shortener?",
  "audio_url": "<base64 MP3>",
  "question_number": 1,
  "total_questions": 10
}
```

### `POST /interview/answer`
```json
// Request
{ "session_id": "uuid-...", "transcript": "I'd use Base62 encoding..." }

// Response
{
  "interviewer_message": "Good point on Base62! How would you handle caching?",
  "audio_url": "<base64 MP3>",
  "question_number": 2,
  "is_complete": false,
  "score": { "relevance": 8, "technical_depth": 6, "overall": 7.6, "is_weak": false }
}
```

### `POST /interview/transcribe`
Upload audio file → returns transcript. Stateless (no session required).

### `GET /feedback/{session_id}`
```json
{
  "overall_score": 7.4,
  "grade": "Good",
  "strengths": ["Strong systems thinking", "Clear communication"],
  "weaknesses": ["Missed caching strategies"],
  "improvements": ["Study Redis patterns", "Practice CAP theorem trade-offs"],
  "recommended_topics": ["distributed systems", "database indexing"],
  "hiring_recommendation": "Hire",
  "summary": "The candidate demonstrated solid fundamentals..."
}
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

All tests use mocking — **no real API calls, no API key needed**.

```
tests/test_stt.py::test_transcribe_returns_text          PASSED
tests/test_stt.py::test_transcribe_error_propagates      PASSED
tests/test_tts.py::test_synthesise_returns_bytes         PASSED
tests/test_retrieval.py::test_build_and_search           PASSED
tests/test_retrieval.py::test_get_by_id                  PASSED
tests/test_scoring.py::test_score_answer_structure       PASSED
tests/test_scoring.py::test_score_answer_fallback        PASSED
tests/test_scoring.py::test_compute_aggregate_score      PASSED
8 passed
```

---

## ⚙️ Full Configuration

```env
# Required
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# Auto-set by Docker Compose
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/interview_db
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Optional overrides
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
MAX_QUESTIONS=10
DEFAULT_LANGUAGE=en
LOG_LEVEL=INFO
DEBUG=false
```

---

## 🚀 Production Notes

- The backend is **stateless** — scale horizontally (`docker-compose up --scale backend=4`)
- All session state lives in Redis (auto-expires after 2h)
- FAISS index must be on a **shared volume** (EFS/NFS) for multi-instance deployments
- Replace Docker Redis/Postgres with managed services (ElastiCache / RDS) in production

---

## 🛠️ Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend | FastAPI + asyncio | High-throughput async, auto Swagger |
| Workflow | LangGraph | Typed state machine, testable nodes |
| LLM | GPT-4o | Best reasoning + JSON mode reliability |
| STT | OpenAI Whisper | Multilingual, high accuracy |
| TTS | ElevenLabs multilingual v2 | Natural prosody, EN/HI/DE in one model |
| Embeddings | text-embedding-3-large | Best semantic retrieval accuracy |
| Vector DB | FAISS (local) | No managed service needed for ≤100 Q&A |
| Session store | Redis | Stateless API, auto-expiring TTL |
| Durable store | PostgreSQL | Audit trail + score analytics |
| Async tasks | Celery + Redis | Non-blocking background jobs |
| Frontend | Streamlit | Fast iteration, voice recorder built-in |
| Infrastructure | Docker Compose | One-command reproducible deploy |

---

## 📋 Deliverables

- [x] Working code — `docker-compose up --build` runs immediately
- [x] README — this file
- [x] Architecture note — [`architecture.md`](architecture.md)
- [x] Q&A dataset — [`data/qa_dataset.json`](data/qa_dataset.json)
- [x] Demo script — [`demo_script.md`](demo_script.md)
- [x] Test suite — 4 files, fully mocked
- [x] Multilingual — English / Hindi / German

---

## 👤 Author

**Nagendra Madanapalle**
GitHub: [@MadanapalleNagendra](https://github.com/MadanapalleNagendra)
