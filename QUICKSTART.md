# 快速啟動指南

## 1️⃣ 後端啟動（已完成 ✅）

後端服務已成功運行在 `http://127.0.0.1:8000`

如需重新啟動：
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## 2️⃣ 前端啟動

打開**新的終端機**，執行：
```bash
cd frontend
npm run dev
```

前端將運行在 `http://localhost:5173`

## 3️⃣ 設定 API Key

**重要！** 請確保已設定 Gemini API Key：

1. 編輯 `backend/.env` 檔案
2. 填入您的 API Key：
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## 4️⃣ 測試應用

1. 開啟瀏覽器訪問 `http://localhost:5173`
2. 上傳測試 PPT 檔案
3. 設定參數並生成文稿

## ⚙️ 已安裝套件

✅ FastAPI - Web 框架  
✅ Uvicorn - ASGI 伺服器  
✅ python-pptx - PPT 解析  
✅ google-generativeai - Gemini AI  
✅ python-dotenv - 環境變數  
✅ Pydantic - 資料驗證  

## 🔧 故障排除

**後端無法啟動？**
- 檢查 8000 port 是否被佔用
- 確認所有依賴已安裝：`pip list`

**前端無法連接？**
- 確認後端正在運行
- 檢查 API URL：`http://localhost:8000`

**API 錯誤？**
- 確認已設定 `GEMINI_API_KEY`
- 檢查 API key 是否有效
