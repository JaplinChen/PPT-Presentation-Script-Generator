@echo off
chcp 65001 > nul
echo.
echo ============================================
echo   AI PPT Generator - Quick Start
echo ============================================
echo.

:: Check if backend venv exists
if not exist "backend\.venv\Scripts\activate" (
    echo [ERROR] Backend virtual environment not found!
    echo Please run: cd backend ^&^& python -m venv .venv ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

:: Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not found!
    echo Please run: cd frontend ^&^& npm install
    pause
    exit /b 1
)

echo [1/2] Starting Backend (FastAPI)...
echo       URL: http://localhost:8080
echo.
cd backend
start "PPT_Backend" cmd /k "call .venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080"

echo [2/2] Starting Frontend (Vite)...
echo       URL: http://localhost:5173
echo.
cd ..\frontend
start "PPT_Frontend" cmd /k "npm run dev -- --host"

echo.
echo ============================================
echo   Both servers are starting...
echo.
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8080
echo.
echo   For LAN access, use your machine IP
echo   Example: http://192.168.x.x:5173
echo ============================================
echo.
pause
