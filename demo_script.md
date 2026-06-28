# Demo Script — Voice Interview Agent

## Before you record
- Have the app running: `docker-compose up --build`
- Open `http://localhost:8501` in Chrome (mic permissions granted)
- Open a second tab with `http://localhost:8000/docs` to show the API

---

## Scene 1 — Setup (0:00–0:20)
"I'm going to demo the Voice Interview Agent — a voice-based mock interview system
for software engineers. Let me show you the architecture briefly."

*(Show `architecture.md` or the folder tree for 5 seconds)*

---

## Scene 2 — Start the Interview (0:20–0:40)
"I'll select English, type my name, and start the interview."

*(Click **Start Interview**)*

The agent responds with the first question (e.g. "Let's begin! Can you walk me through
how you'd design a URL shortener like bit.ly?") and plays the TTS audio.

---

## Scene 3 — Strong Answer (0:40–1:20)
Switch to the **Record Voice** tab. Record:

*"I'd use Base62 encoding on an auto-incrementing ID to generate short codes,
store the mapping in Postgres, and put Redis in front for caching hot URLs since
reads massively outnumber writes. I'd also use a CDN for the redirect layer."*

Submit. The agent acknowledges it positively and moves to the next question.

Show the score card that appears: Relevance 9, Technical Depth 8, Overall 8.5.

---

## Scene 4 — Weak Answer triggering follow-up (1:20–2:10)
The next question is about the CAP theorem. Record a weak answer:

*"CAP theorem is about consistency and availability in databases… I think?"*

Submit. The agent asks a targeted follow-up:
*"What does partition tolerance mean, and why can't distributed systems avoid it?"*

Record a better answer:
*"Partition tolerance means the system keeps working even if nodes can't communicate.
Network splits always happen eventually so you have to choose between C and A."*

Show that the score improves and the agent moves on.

---

## Scene 5 — Final Feedback (2:10–3:30)
Speed through a few more answers, then show the final feedback screen:
- Overall Score: 7.2 / 10
- Grade: Good
- Hiring Recommendation: Hire
- Strengths / Weaknesses / Recommended Topics

*(Highlight the per-question breakdown table)*

---

## Scene 6 — API Explorer (3:30–4:00)
*(Switch to FastAPI docs tab)*

"The backend is a fully documented REST API — here's the `/interview/start` endpoint,
and here's `/feedback/{session_id}` returning structured JSON."

*(Show a live response in the Swagger UI)*

"The dataset is a plain JSON file — adding a question is a one-line edit,
no code changes needed."
