#!/bin/bash

echo "==========================================="
echo "  PPT Presentation Generator - Mac/Linux"
echo "  Starting services..."
echo "==========================================="

# Function to open a new terminal tab/window with command
# This is Mac specific (osascript)
open_terminal() {
    local cmd="$1"
    local title="$2"
    osascript -e "tell application \"Terminal\" to do script \"$cmd; exit\""
}

echo "[1/2] Starting Backend (Port 8080)..."
# Check if backend directory exists
if [ -d "backend" ]; then
    open_terminal "cd \"$(pwd)/backend\" && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080" "PPT_Backend"
else
    echo "Error: backend directory not found!"
fi

echo "[2/2] Starting Frontend (Port 5173)..."
if [ -d "frontend" ]; then
    open_terminal "cd \"$(pwd)/frontend\" && npm run dev" "PPT_Frontend"
else
    echo "Error: frontend directory not found!"
fi

echo "==========================================="
echo "  ✅ Services starting in new windows."
echo ""
echo "  👉 Local:   http://localhost:5173"
echo "==========================================="
