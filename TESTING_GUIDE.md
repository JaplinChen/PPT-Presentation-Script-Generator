# Ditto Avatar 整合 - 測試與部署指南

## 🎯 當前狀態

已完成 Ditto Avatar 的完整架構實作,包含:
- ✅ 後端 API (4 個端點)
- ✅ 前端 UI (2 個 React 組件)
- ✅ 模擬實作 (可立即測試)
- ⚠️  完整 Ditto 核心組件 (待移植)

---

## 🚀 快速測試 (使用模擬模式)

### 1. 啟動後端

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8080
```

### 2. 啟動前端

```bash
cd frontend
npm run dev
```

### 3. 測試流程

1. 開啟 http://localhost:3000
2. 上傳 PPT 檔案
3. 生成文稿
4. 點擊 "生成有聲 PPT"
5. 在 Step 4 中上傳播報員照片
6. 點擊 "生成數位播報員"
7. 觀察進度並預覽結果

**注意:** 目前使用模擬模式,生成的影片是簡單的測試影片,不是真實的 Talking Head。

---

## 📦 完整 Ditto 移植步驟

### 方案 A: 從官方 Repo 移植

```bash
# 1. 下載官方專案
cd backend
git clone https://github.com/antgroup/ditto-talkinghead.git temp_ditto

# 2. 複製核心組件
mkdir -p app/services/ditto/core
cp -r temp_ditto/core/* app/services/ditto/core/

# 3. 下載模型
python setup_ditto.py --download-models

# 4. 切換到完整模式
# 設置環境變數
export DITTO_MODE=full  # Linux/Mac
# 或
set DITTO_MODE=full  # Windows

# 5. 重啟後端
python -m uvicorn app.main:app --reload
```

### 方案 B: 使用 Web API

如果沒有 GPU,可以改用商業 API:

**修改 `avatar_service.py`:**
```python
async def generate_talking_head(self, ...):
    # 改為調用 D-ID API
    import requests
    
    response = requests.post(
        "https://api.d-id.com/talks",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "source_url": image_url,
            "script": {
                "type": "audio",
                "audio_url": audio_url
            }
        }
    )
    
    # 輪詢結果...
```

---

## 🧪 測試指南

### API 測試

```bash
# 1. 檢查系統資訊
curl http://localhost:8080/api/avatar/system-info

# 2. 上傳照片
curl -X POST http://localhost:8080/api/avatar/upload-photo \
  -F "file=@test_photo.jpg"

# 3. 生成影片
curl -X POST http://localhost:8080/api/avatar/generate \
  -H "Content-Type: application/json" \
  -d '{
    "photo_id": "abc123",
    "audio_path": "./outputs/audio/test.wav",
    "emotion": 4
  }'

# 4. 查詢進度
curl http://localhost:8080/api/avatar/job/{job_id}/status
```

### Python 測試腳本

建立 `test_avatar_manual.py`:
```python
import asyncio
from app.services.avatar_service import AvatarService

async def test():
    service = AvatarService()
    
    # 測試系統資訊
    info = await service.get_system_info()
    print(f"GPU: {info.get('gpu_name', 'N/A')}")
    
    # 測試照片驗證
    result = await service.validate_image("test.jpg")
    print(f"驗證: {result['valid']}")
    
    # 測試生成
    result = await service.generate_talking_head(
        audio_path="test.wav",
        image_path="test.jpg",
        output_path="output.mp4"
    )
    print(f"成功: {result['success']}")

asyncio.run(test())
```

---

## 📊 效能基準

### 模擬模式
- 生成時間: ~5-10 秒
- 輸出: 簡單測試影片
- GPU 需求: 無

### 完整模式 (預期)
- RTX 4090: ~2-3 分鐘/分鐘影片
- RTX 3090: ~3-5 分鐘/分鐘影片
- A100: ~1-2 分鐘/分鐘影片

---

## 🐛 常見問題

### Q1: 模擬模式生成的影片無法播放

**解決:** 確保已安裝 ffmpeg
```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# Linux
sudo apt-get install ffmpeg

# Mac
brew install ffmpeg
```

### Q2: 切換到完整模式後出現 ImportError

**原因:** Ditto 核心組件未正確移植

**解決:**
1. 檢查 `app/services/ditto/core/` 目錄是否存在
2. 確認所有必要的組件都已複製
3. 檢查 import 路徑是否正確

### Q3: GPU 記憶體不足

**解決:**
1. 降低 `sampling_steps` (50 → 30)
2. 關閉其他使用 GPU 的程式
3. 清理 GPU 快取:
```python
import torch
torch.cuda.empty_cache()
```

---

## 📁 專案結構

```
backend/
├── app/
│   ├── services/
│   │   ├── ditto/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── stream_pipeline.py  # 支援 mock/full 模式
│   │   │   ├── mock_implementation.py  # 模擬實作
│   │   │   └── core/  # (待移植) Ditto 核心組件
│   │   └── avatar_service.py
│   ├── models/
│   │   └── avatar.py
│   └── main.py  # 4 個 Avatar API 端點
├── setup_ditto.py
└── ditto_requirements.txt

frontend/
├── src/
│   ├── services/
│   │   └── avatarService.js
│   ├── components/
│   │   ├── AvatarSettings.jsx
│   │   ├── AvatarSettings.css
│   │   ├── AvatarProgress.jsx
│   │   └── AvatarProgress.css
│   └── App.jsx  # 整合 Step 5
```

---

## 🎓 下一步建議

### 短期 (1-2 天)
1. ✅ 測試模擬模式的完整流程
2. ✅ 驗證前後端整合
3. ⬜ 優化 UI/UX
4. ⬜ 撰寫使用者文件

### 中期 (1-2 週)
1. ⬜ 移植 Ditto 核心組件
2. ⬜ 下載並測試模型
3. ⬜ 端到端測試
4. ⬜ 效能優化

### 長期 (1 個月+)
1. ⬜ 生產環境部署
2. ⬜ 監控和日誌
3. ⬜ 使用者回饋收集
4. ⬜ 功能擴展

---

## 📞 支援資源

**官方文件:**
- [Ditto GitHub](https://github.com/antgroup/ditto-talkinghead)
- [HuggingFace 模型](https://huggingface.co/digital-avatar/ditto-talkinghead)

**專案文件:**
- [implementation_plan.md](file:///C:/Users/japlin.chen/.gemini/antigravity/brain/0da0a70b-7b8e-4275-a6bd-e51a04c54b90/implementation_plan.md)
- [ditto_technical_guide.md](file:///C:/Users/japlin.chen/.gemini/antigravity/brain/0da0a70b-7b8e-4275-a6bd-e51a04c54b90/ditto_technical_guide.md)
- [DITTO_INTEGRATION.md](file:///d:/Works/PPT_Dev/backend/DITTO_INTEGRATION.md)

---

**最後更新:** 2025-12-27  
**狀態:** ✅ 架構完成,模擬模式可用,完整模式待移植
