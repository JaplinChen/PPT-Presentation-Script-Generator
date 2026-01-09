# 專案背景與規則 (PROJECT CONTEXT & RULES)

## 1. 技術堆疊 (STRICT)

- **Frontend:** HTML/JS (除非特別指定，否則不使用 React/Vue)
- **Backend:** Python (Flask/FastAPI - 請檢查 check requirements.txt)
- **Database:** SQLite/PostgreSQL

## 2. 檔案結構錨點 (FILE STRUCTURE ANCHORS)

- 設定檔位於：`.env.example` (唯讀)
- 相依套件位於：`requirements.txt`
- 程式進入點：`app.py` 或 `main.py`

## 3. 行為覆寫 (BEHAVIORAL OVERRIDES)

- 絕不憑空臆造 (hallucinate) imports。先執行 `pip install` 檢查。
- 始終使用相對路徑。
- 若編輯 Python：使用嚴格的型別提示 (Type Hints)。
- 若編輯 Frontend：先檢查後端 API 回應格式。
