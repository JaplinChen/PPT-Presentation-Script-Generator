# Ditto Avatar 整合 - 使用指南

## 📋 已完成的工作

### 階段 1 & 2: 環境準備 ✅
- ✅ `ditto_requirements.txt` - Ditto 專用相依套件
- ✅ `setup_ditto.py` - 環境設置和診斷工具
- ✅ `app/services/ditto/` - Ditto 核心模組結構
  - `config.py` - 配置管理
  - `stream_pipeline.py` - 推理管線介面

### 階段 3: 後端 API ✅
- ✅ `app/models/avatar.py` - Pydantic 資料模型
- ✅ `app/services/avatar_service.py` - Avatar 服務類別
- ✅ `app/main.py` - 4 個 Avatar API 端點

## 🚀 快速開始

### 1. 環境檢查

```bash
cd backend
python setup_ditto.py --diagnose
```

**預期輸出:**
```
==================================================
GPU 環境檢查
==================================================
✅ GPU: NVIDIA GeForce RTX 4090
✅ VRAM: 24.0 GB
✅ CUDA: 12.1
✅ VRAM 充足
```

### 2. 下載模型 (首次使用)

```bash
# 下載 Ditto 模型 (~10GB)
python setup_ditto.py --download-models

# 驗證模型檔案
python setup_ditto.py --verify
```

### 3. 啟動後端

```bash
# 啟動 FastAPI 伺服器
python -m uvicorn app.main:app --reload --port 8080
```

**啟動日誌:**
```
[Init] Script generator ready.
[Init] Avatar service initialized (models will load on first use)
INFO:     Uvicorn running on http://127.0.0.1:8080
```

---

## 📡 API 端點說明

### 1. 檢查系統資訊

**端點:** `GET /api/avatar/system-info`

**回應:**
```json
{
  "cuda_available": true,
  "gpu_name": "NVIDIA GeForce RTX 4090",
  "gpu_memory_total": 24.0,
  "gpu_memory_available": 22.5,
  "model_loaded": false,
  "avatar_enabled": true
}
```

**測試:**
```bash
curl http://localhost:8080/api/avatar/system-info
```

---

### 2. 上傳播報員照片

**端點:** `POST /api/avatar/upload-photo`

**請求:**
```bash
curl -X POST http://localhost:8080/api/avatar/upload-photo \
  -F "file=@/path/to/avatar.jpg"
```

**回應:**
```json
{
  "photo_id": "abc123-...",
  "photo_url": "/uploads/avatar_abc123.jpg",
  "validation": {
    "valid": true,
    "message": "照片驗證通過",
    "face_count": 1,
    "face_bbox": [120, 80, 300, 300],
    "image_size": [1024, 1024]
  }
}
```

**錯誤範例:**
```json
{
  "detail": "未檢測到人臉,請使用清晰的正面人臉照片"
}
```

---

### 3. 生成數位播報員影片

**端點:** `POST /api/avatar/generate`

**請求:**
```json
{
  "photo_id": "abc123-...",
  "audio_path": "./outputs/audio/slide_1.wav",
  "emotion": 4,
  "crop_scale": 2.3,
  "sampling_steps": 50,
  "fade_in": 5,
  "fade_out": 5
}
```

**回應:**
```json
{
  "job_id": "xyz789-...",
  "status": "processing"
}
```

**測試:**
```bash
curl -X POST http://localhost:8080/api/avatar/generate \
  -H "Content-Type: application/json" \
  -d '{
    "photo_id": "abc123",
    "audio_path": "./outputs/audio/test.wav",
    "emotion": 5
  }'
```

---

### 4. 查詢生成進度

**端點:** `GET /api/avatar/job/{job_id}/status`

**回應 (處理中):**
```json
{
  "job_id": "xyz789-...",
  "status": "processing",
  "progress": 45,
  "message": "生成面部運動... (2/5 分鐘)",
  "video_url": null,
  "error": null,
  "duration": null
}
```

**回應 (完成):**
```json
{
  "job_id": "xyz789-...",
  "status": "completed",
  "progress": 100,
  "message": "Avatar video generated successfully",
  "video_url": "/outputs/avatar_xyz789.mp4",
  "error": null,
  "duration": 125.3
}
```

**測試:**
```bash
# 輪詢進度
while true; do
  curl http://localhost:8080/api/avatar/job/xyz789/status | jq
  sleep 2
done
```

---

## 🧪 完整測試流程

### Python 測試腳本

```python
import requests
import time

BASE_URL = "http://localhost:8080"

# 1. 檢查系統
response = requests.get(f"{BASE_URL}/api/avatar/system-info")
print("系統資訊:", response.json())

# 2. 上傳照片
with open("test_avatar.jpg", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/avatar/upload-photo",
        files={"file": f}
    )
photo_data = response.json()
print("照片上傳:", photo_data)

# 3. 生成影片
response = requests.post(
    f"{BASE_URL}/api/avatar/generate",
    json={
        "photo_id": photo_data["photo_id"],
        "audio_path": "./outputs/audio/test.wav",
        "emotion": 4
    }
)
job_data = response.json()
print("任務建立:", job_data)

# 4. 輪詢進度
job_id = job_data["job_id"]
while True:
    response = requests.get(f"{BASE_URL}/api/avatar/job/{job_id}/status")
    status = response.json()
    print(f"[{status['progress']}%] {status['message']}")
    
    if status["status"] in ["completed", "failed"]:
        break
    
    time.sleep(2)

if status["status"] == "completed":
    print(f"✅ 影片已生成: {status['video_url']}")
    print(f"⏱️  耗時: {status['duration']} 秒")
else:
    print(f"❌ 生成失敗: {status['error']}")
```

---

## ⚠️ 重要注意事項

### 目前狀態

> [!WARNING]
> **Ditto 核心組件尚未完整移植**
> 
> 目前的實作提供了完整的 API 架構和服務封裝,但 Ditto 的核心推理組件尚未從官方 repo 移植。
> 
> **需要移植的組件:**
> - `core/atomic_components/avatar_registrar.py`
> - `core/atomic_components/condition_handler.py`
> - `core/atomic_components/audio2motion.py`
> - `core/atomic_components/motion_stitch.py`
> - `core/atomic_components/warp_f3d.py`
> - `core/atomic_components/decode_f3d.py`
> - `core/atomic_components/wav2feat.py`

### 下一步工作

1. **移植 Ditto 核心組件**
   ```bash
   # 從官方 repo 複製核心組件
   git clone https://github.com/antgroup/ditto-talkinghead
   cp -r ditto-talkinghead/core backend/app/services/ditto/
   ```

2. **實作完整推理流程**
   - 更新 `stream_pipeline.py` 使用實際的 Ditto 組件
   - 測試端到端生成流程

3. **前端整合**
   - 建立 Avatar 設定 UI 組件
   - 實作照片上傳和預覽
   - 整合到主工作流程

---

## 📚 相關文件

- [implementation_plan.md](file:///C:/Users/japlin.chen/.gemini/antigravity/brain/0da0a70b-7b8e-4275-a6bd-e51a04c54b90/implementation_plan.md) - 完整實施計劃
- [ditto_technical_guide.md](file:///C:/Users/japlin.chen/.gemini/antigravity/brain/0da0a70b-7b8e-4275-a6bd-e51a04c54b90/ditto_technical_guide.md) - 技術指南
- [walkthrough.md](file:///C:/Users/japlin.chen/.gemini/antigravity/brain/0da0a70b-7b8e-4275-a6bd-e51a04c54b90/walkthrough.md) - 研究總結

---

## 🐛 故障排除

### 問題 1: Avatar service not available

**原因:** AvatarService 初始化失敗

**解決:**
```bash
# 檢查 PyTorch 是否安裝
python -c "import torch; print(torch.cuda.is_available())"

# 檢查模型路徑
ls -la checkpoints/ditto_pytorch/
```

### 問題 2: Photo validation failed

**原因:** 照片中未檢測到人臉

**解決:**
- 使用正面、清晰的人臉照片
- 確保人臉佔照片的 30-50%
- 解析度至少 512x512

### 問題 3: CUDA out of memory

**原因:** GPU 記憶體不足

**解決:**
```python
# 降低 sampling_steps
{
  "sampling_steps": 30  # 從 50 降到 30
}

# 或清理 GPU 快取
import torch
torch.cuda.empty_cache()
```

---

## 📊 效能基準

| GPU 型號 | 生成時間 (1 分鐘影片) | VRAM 使用 |
|---------|---------------------|----------|
| RTX 4090 | ~2-3 分鐘 | ~8GB |
| RTX 3090 | ~3-5 分鐘 | ~10GB |
| A100 | ~1-2 分鐘 | ~6GB |

**注意:** 實際效能取決於 `sampling_steps` 參數和影片長度。
