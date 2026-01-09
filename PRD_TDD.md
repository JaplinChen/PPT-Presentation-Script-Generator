# AI 簡報影音整合應用程式 (AI Presentation Multi-Media Generator)
## 技術需求規格書 (PRD/TDD)

本文件旨在提供系統完整架構、功能邏輯與實作細節，以便於在其他平台（如雲端環境）進行移植與重新實作。

---

### 1. 核心架構 (Architecture)

#### 技術棧 (Tech Stack)
*   **前端 (Frontend)**: React v19, Vite (Build Tool), i18next (Multi-language), Vanilla CSS (UI Styling).
*   **後端 (Backend)**: FastAPI (Python), Uvicorn (ASGI Server).
*   **AI 引擎 (AI Engines)**:
    *   **LLM**: Google Gemini / OpenAI (用於文稿生成與分析)。
    *   **TTS**: Microsoft Edge TTS (語音合成)。
    *   **CV/Avatar**: Ditto Talking Head (臉部動畫), GFPGAN (臉部畫質增強), MediaPipe (定位)。
*   **處理庫**: 
    *   **文件**: `python-pptx` (PPT 解析與嵌入)。
    *   **影像**: `FFmpeg` (影片轉碼與去背濾鏡處理)。

#### 系統設計模式
*   **前端**: 基於 Hooks 的狀態管理與元件化開發。
*   **後端**: 微服務導向 (Service-Oriented Architecture)，核心邏輯封裝於 `services/` 目錄。
*   **非同步處理**: 使用 FastAPI `BackgroundTasks` 與 GPU Lock 鎖定機制處理高耗能任務。
*   **狀態持久化**: 目前使用 `state.json` 進行進度追蹤，具備恢復 (Resume) 能力。

---

### 2. 功能矩陣 (Functional Requirements)

| 功能點 | 業務邏輯細節 |
| :--- | :--- |
| **PPT 解析 (Phase 1)** | 解析 `.pptx` 結構，提取文字、頁碼、備忘錄與圖片統計。 |
| **AI 文稿生成 (Phase 3)** | 根據 PPT 內容與用戶設定（受眾、語調、時長）調用 LLM 生成逐頁導覽文稿。 |
| **語音合成 (Phase 4)** | 調用 TTS 引擎生成每頁導覽語音，支援 MD5 內容雜湊快取以避免重複計費。 |
| **數位人生成 (Phase 6)** | 將照片與語音結合成說話影片，並套用 GFPGAN 增強畫質，最終轉為 WebM 透明背景或 MP4 格式。 |
| **PPT 封裝 (Phase 7)** | 將音訊、影片、備忘錄同步嵌入回原始 PPT，並實施動態版面配置（首頁大圖，內頁小圖）。 |

---

### 3. 資料模型 (Data Schema)

由於移植至雲端可能使用 Firestore，以下為建議的資料結構映射：

#### Collection: `uploaded_files`
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `file_id` | String (PK) | 唯一識別碼 |
| `filename` | String | 原始檔案名稱 |
| `path` | String | 儲存路徑 |
| `slides` | Array<Object> | 每頁內容 (題、列點、備忘錄) |
| `summary` | Map | 整體概述 |

#### Collection: `ppt_jobs` (任務追蹤)
| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `job_id` | String (PK) | 任務 ID |
| `type` | Enum | `avatar_batch`, `narrated_ppt`, `assemble` |
| `status` | String | `processing`, `completed`, `failed` |
| `progress` | Integer | 0 - 100 |
| `message` | String | 當前步驟說明 (例: Slide 24/42) |
| `result` | Map | 產出的檔案路徑或 URL |

---

### 4. UI/UX 規範 (Design Tokens)

*   **色彩系統**:
    *   **Primary**: `#6366f1` (Indigo).
    *   **Background**: `#0f172a` (Dark Navy).
    *   **Card Background**: `rgba(30, 41, 59, 0.7)` (Glassmorphism effect).
*   **字體**: 無襯線體 (Sans-serif)，優先級: `Inter`, `system-ui`.
*   **響應式策略**: 斷點配置依據 1280px (Desktop) 與 768px (Mobile)，主要採用 Flexbox 與 Grid 佈局。

---

### 5. 關鍵算法與邏輯 (Technical Logic)

#### 影片去背與圓形裁切 (FFmpeg Logic)
```bash
# 虛擬碼邏輯：套用色鍵去背並裁切為圓形
ffmpeg -i input.mp4 -vf "colorkey=0x00FF00:0.1:0.1,format=rgba,geq=lum='p(X,Y)':a='if(st(0,pow(X-W/2,2)+pow(Y-H/2,2));lt(ld(0),pow(min(W,H)/2,2)),255,0)'" output.webm
```

#### GPU 任務鎖定機制 (Python Pseudocode)
```python
def acquire_gpu_lock():
    if gpu_busy:
        return False, "System Busy"
    set_busy(True)
    return True, "Lock Granted"
```

#### 進度恢復邏輯 (Resume Logic)
1. 啟動批次任務前，掃描 `outputs/` 資料夾。
2. 根據檔案指紋 (MD5 of Image + Script) 比對。
3. 若匹配，跳過生成階段，直接從快取讀取路徑。

---

### 6. 開發環境與依賴 (Environment & Dependencies)

*   **Python**: 3.10+ (需支援 asyncio)。
*   **GPU 環境**: NVIDIA CUDA 11.8+ (Ditto 運算需求)。
*   **環境變數 (`.env`)**:
    *   `GEMINI_API_KEY`: Google AI 密鑰。
    *   `OUTPUT_DIR`: 產出儲存路徑。
    *   `TEMP_DIR`: 暫存緩衝路徑。
*   **外部命令要求**: 系統環境變數需包含 `ffmpeg`。
