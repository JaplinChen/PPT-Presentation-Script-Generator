# PPT 演講文稿生成器 (PPT Presentation Script Generator) - 技術規格書

## 1. 專案概述
本專案是一個基於 AI 的 Web 應用程式，旨在幫助使用者將 PowerPoint 簡報自動轉換為專業、口語化的演講文稿。系統利用 Google Gemini AI 模型解析投影片內容，並根據設定的聽眾、口吻與時長生成合適的講稿。此外，系統支援語音合成 (TTS) 與有聲 PPT 生成，並具備動畫同步功能。

## 2. 技術棧 (Tech Stack)

### 後端 (Backend)
- **語言**: Python 3.8+
- **框架**: FastAPI
- **AI 模型**: Google Gemini 2.5 Flash (google-generativeai)
- **文件解析**: python-pptx
- **語音合成**: edge-tts
- **音訊處理**: pydub, mutagen
- **自動化控制**: win32com (僅限 Windows，用於 PPT 動畫同步)
- **環境管理**: python-dotenv

### 前端 (Frontend)
- **框架**: React 18 (使用 Vite 構建)
- **樣式**: Vanilla CSS (現代化暗色主題, 漸層與玻璃擬態效果)
- **API 通訊**: Axios

## 3. 核心功能模組

### A. PPT 解析服務 (`PPTParser`)
- 使用 `python-pptx` 提取每頁投影片的：
  - 標題 (具備位置與字體大小的 fallback 識別機制)
  - 項目符號 (Bullets)
  - 備註 (Notes)
  - 表格內容
  - 圖片數量
- 排除隱藏投影片。
- 提供摘要統計 (總頁數、要點總數等)。

### B. 講稿生成服務 (`ScriptGenerator`)
- **單次 API 優化**: 使用單一 API Call 生成整份簡報的講稿，以節省 Token 並保持上下文連貫。
- **結構化 Prompt**: 內嵌精密設計的轉場、開場白與逐頁講稿模板。
- **解析邏輯**: 透過特定的標記 (如 `=== 開場白 ===`, `[要點 1]`, `[轉場]`) 將 AI 輸出的文字解析回結構化資料。
- **自動分段**: 若 AI 輸出未包含標記，具備基於「首先、其次、最後」等連接詞的自動切分機制。

### C. 語音與動畫服務 (`TTSService`)
- **分段合成**: 為每個講稿片段具體生成音訊，並記錄精確的時間戳 (Duration)。
- **PPT 嵌入**: 將生成的 MP3 檔案嵌入 PPTX，並注入 XML 以達成「投影片切換時自動播放」。
- **動畫同步**: 在 Windows 環境下，透過 COM 介面自動為 PPT 元素添加「淡入」與「重點高亮」動畫，並與語音時間精確對齊。

## 4. API 介面摘要
- `POST /api/upload`: 上傳並解析 PPT。
- `POST /api/generate/{file_id}`: 生成演講講稿。
- `POST /api/translate`: 翻譯現有講稿。
- `POST /api/tts/generate`: 生成單段或分段語音。
- `POST /api/ppt/generate-narrated`: 生成包含語音與動畫的有聲 PPT。

## 5. 目錄結構
- `backend/app/main.py`: API 入口與路由。
- `backend/app/services/`: 核心邏輯 (Parser, Generator, TTS, PromptLoader)。
- `backend/prompts/`: Markdown 格式的 Prompt 模板。
- `frontend/src/`: React 組件與 UI 邏輯。
- `uploads/` / `outputs/`: 檔案儲存目錄。

## 6. Prompt 系統設計
系統採用模組化設計，包含：
- `system.md`: 定義 AI 作為資深演講專家的角色。
- `opening.md`: 規範開場白的三段式結構。
- `slide.md`: 規範每頁講稿的敘事邏輯。
- `transition.md`: 串聯上下文。
