#!/usr/bin/env bash
# =============================================================================
# github_push.sh
# Run this from the folder that CONTAINS voice-interview-agent/
# It initialises git and pushes everything to GitHub.
#
# Prerequisites:
#   git          → https://git-scm.com/downloads
#   GitHub CLI   → https://cli.github.com/
#   logged in    → gh auth login
#
# Usage (Linux/Mac/Git Bash on Windows):
#   chmod +x github_push.sh
#   ./github_push.sh
# =============================================================================

set -euo pipefail

REPO_NAME="voice-interview-agent"
GITHUB_USER="MadanapalleNagendra"
DESCRIPTION="Production-grade Voice Interview Agent — GPT-4o + Whisper + ElevenLabs + FAISS + LangGraph"

echo ""
echo "============================================================"
echo "  Voice Interview Agent — GitHub Push"
echo "  Target: github.com/${GITHUB_USER}/${REPO_NAME}"
echo "============================================================"
echo ""

# Check we're in the right place
if [ ! -d "$REPO_NAME" ]; then
  echo "ERROR: Run this script from the parent folder containing '$REPO_NAME/'"
  exit 1
fi

cd "$REPO_NAME"

# Init git if needed
if [ ! -d ".git" ]; then
  git init
  echo "✓ Git initialised"
fi

# Create GitHub repo (skip if already exists)
gh repo create "${GITHUB_USER}/${REPO_NAME}" \
  --public \
  --description "$DESCRIPTION" \
  --source=. \
  --remote=origin \
  --push=false 2>/dev/null \
  && echo "✓ GitHub repo created" \
  || echo "  (repo already exists — continuing)"

# Set remote
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
echo "✓ Remote: https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

# Stage + commit
git add -A
git commit -m "feat: initial release — Grounded Voice Interview Agent

Stack: FastAPI + LangGraph + GPT-4o + Whisper + ElevenLabs + FAISS + Redis + Postgres
- Complete LangGraph state machine (retrieve → evaluate → follow-up → next Q → TTS)
- Information firewall: LLM interviewer never sees ideal answers directly
- FAISS vector store on 10 software-engineer Q&A pairs (question+answer chunk)
- Two-mode retrieval: semantic for context, exact get_by_id() for scoring
- Redis embedding cache + TTS streaming for <3s warm path latency
- Streamlit voice UI with real-time scoring dashboard
- Docker Compose 5-service stack, runs with: docker-compose up --build
- Multilingual: English / Hindi / German (eleven_multilingual_v2)
- 4 test files, fully mocked — pytest tests/ -v" 2>/dev/null \
  || echo "  (already committed)"

# Push
git branch -M main
git push -u origin main --force

echo ""
echo "============================================================"
echo "  ✅  SUCCESS!"
echo ""
echo "  Your repo is live at:"
echo "  https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "  Next steps:"
echo "  1. Go to the repo → add a description in the About section"
echo "  2. Record your Loom demo using demo_script.md"
echo "  3. Add the Loom link to README.md line 11 and push again"
echo "============================================================"
