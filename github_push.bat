@echo off
:: =============================================================================
:: github_push.bat
:: Windows version of the GitHub push script
:: Run from the folder that CONTAINS voice-interview-agent\
::
:: Prerequisites:
::   git          https://git-scm.com/downloads
::   GitHub CLI   https://cli.github.com/
::   gh auth login  (run once before this script)
:: =============================================================================

set REPO_NAME=voice-interview-agent
set GITHUB_USER=MadanapalleNagendra
set DESCRIPTION=Production-grade Voice Interview Agent -- GPT-4o + Whisper + ElevenLabs + FAISS + LangGraph

echo.
echo ============================================================
echo   Voice Interview Agent -- GitHub Push
echo   Target: github.com/%GITHUB_USER%/%REPO_NAME%
echo ============================================================
echo.

if not exist "%REPO_NAME%" (
    echo ERROR: Run this from the parent folder containing %REPO_NAME%\
    pause
    exit /b 1
)

cd %REPO_NAME%

:: Init git
if not exist ".git" (
    git init
    echo [OK] Git initialised
)

:: Create GitHub repo
gh repo create "%GITHUB_USER%/%REPO_NAME%" --public --description "%DESCRIPTION%" --source=. --remote=origin --push=false 2>nul
echo [OK] GitHub repo ready

:: Set remote
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/%REPO_NAME%.git
echo [OK] Remote set

:: Stage all files
git add -A
echo [OK] Files staged

:: Commit
git commit -m "feat: initial release — Grounded Voice Interview Agent" 2>nul || echo [OK] Already committed

:: Push
git branch -M main
git push -u origin main --force

echo.
echo ============================================================
echo   SUCCESS!
echo   https://github.com/%GITHUB_USER%/%REPO_NAME%
echo ============================================================
pause
