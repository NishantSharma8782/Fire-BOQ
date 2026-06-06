@echo off
echo ============================================
echo   Fire BOQ Platform - Frontend Startup
echo ============================================
echo.
cd /d "%~dp0frontend"
echo Starting Next.js frontend on http://localhost:3000
echo Press Ctrl+C to stop
echo.
call npm run dev
