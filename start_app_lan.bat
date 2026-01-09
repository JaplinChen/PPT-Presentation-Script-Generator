@echo off
chcp 65001 > nul
echo ===========================================
echo   PPT 演講文稿生成器 - 啟動腳本
echo   正在啟動區域網路分享模式...
echo ===========================================

echo.
echo [1/2] 啟動後端伺服器 (Backend)...
echo 正在監聽: 0.0.0.0:8080
echo.
echo [2/2] 啟動前端伺服器 (Frontend)...
echo 正在監聽: 0.0.0.0:5173
cd frontend
start "PPT_Frontend" cmd /k "npm run dev"

echo.
echo ===========================================
echo   ✅ 伺服器正在啟動...
echo.
echo   [1] Backend  (此視窗)
echo   [2] Frontend (新視窗)
echo   [3] Monitor  (自動彈出)
echo.
echo   👉 本機使用: http://localhost:5173
echo   👉 分享網址: http://192.168.90.186:5173
echo ===========================================
echo.
echo 正在啟動後端 (此視窗將保留)...
echo 正在啟動後端 (此視窗將保留)...
cd ..\backend
call .venv\Scripts\activate

:server_loop
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
echo.
echo ⚠️ 後端伺服器已停止。
echo 按任意鍵重新啟動伺服器 (或關閉視窗退出)...
pause
goto server_loop
