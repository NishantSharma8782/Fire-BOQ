@echo off
echo ============================================
echo   Fire BOQ Platform - Backend Startup
echo ============================================
echo.
cd /d "%~dp0backend"
echo Starting FastAPI backend on http://localhost:8000
echo Press Ctrl+C to stop
echo.
call venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload
