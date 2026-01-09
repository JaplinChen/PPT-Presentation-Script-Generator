"""
Avatar 相關的 Pydantic 資料模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class PhotoUploadResponse(BaseModel):
    """照片上傳回應"""
    photo_id: str = Field(..., description="照片 ID")
    photo_url: str = Field(..., description="照片 URL")
    validation: Dict = Field(..., description="驗證結果")


class AvatarGenerateRequest(BaseModel):
    """生成數位播報員請求"""
    photo_id: str = Field(..., description="照片 ID")
    audio_path: str = Field(..., description="音訊檔案路徑")
    output_path: Optional[str] = Field(None, description="輸出路徑 (選填)")
    
    # 生成參數
    emotion: int = Field(4, ge=0, le=7, description="情緒強度 (0-7)")
    crop_scale: float = Field(2.3, description="裁切比例")
    sampling_steps: int = Field(50, ge=10, le=100, description="Diffusion 步數")
    fade_in: int = Field(5, ge=0, description="淡入幀數")
    fade_in: int = Field(5, ge=0, description="淡入幀數")
    fade_out: int = Field(5, ge=0, description="淡出幀數")
    preview_duration: Optional[float] = Field(None, description="預覽時長 (秒), 若設定則只生成片段")


class AvatarJobStatus(BaseModel):
    """任務狀態"""
    job_id: str = Field(..., description="任務 ID")
    status: str = Field(..., description="狀態: pending, processing, completed, failed")
    progress: int = Field(0, ge=0, le=100, description="進度 (0-100)")
    message: str = Field("", description="狀態訊息")
    video_url: Optional[str] = Field(None, description="影片 URL (完成時)")
    error: Optional[str] = Field(None, description="錯誤訊息 (失敗時)")
    duration: Optional[float] = Field(None, description="生成耗時 (秒)")
    current_frame: Optional[str] = Field(None, description="目前畫面預覽 (base64)")


class AvatarSystemInfo(BaseModel):
    """系統資訊"""
    cuda_available: bool = Field(..., description="CUDA 是否可用")
    gpu_name: Optional[str] = Field(None, description="GPU 名稱")
    gpu_memory_total: Optional[float] = Field(None, description="GPU 總記憶體 (GB)")
    gpu_memory_available: Optional[float] = Field(None, description="GPU 可用記憶體 (GB)")
    model_loaded: bool = Field(False, description="模型是否已載入")
    avatar_enabled: bool = Field(False, description="Avatar 功能是否啟用")
    is_generating: bool = Field(False, description="是否正在生成中")
    busy_message: Optional[str] = Field(None, description="忙碌時的提示訊息")
    current_frame: Optional[str] = Field(None, description="當前預覽幀 (base64)")


class NarratedPPTWithAvatarRequest(BaseModel):
    """生成有聲 PPT (含 Avatar) 請求"""
    file_id: str = Field(..., description="PPT 檔案 ID")
    slide_scripts: List[Dict] = Field(..., description="投影片文稿")
    voice: str = Field(..., description="TTS 語音")
    rate: str = Field("+0%", description="語速")
    pitch: str = Field("+0Hz", description="音調")
    
    # Avatar 相關
    enable_avatar: bool = Field(False, description="是否啟用 Avatar")
    photo_id: Optional[str] = Field(None, description="播報員照片 ID")
    avatar_mode: str = Field("corner", description="嵌入模式: corner, fullscreen, split")
    avatar_emotion: int = Field(4, ge=0, le=7, description="情緒強度")


class BatchAvatarRequest(BaseModel):
    """批量生成數位播報員請求"""
    model_config = {"extra": "ignore"}  # 忽略額外欄位
    
    photo_id: str = Field(..., description="照片 ID")
    audio_paths: List[str] = Field(..., description="音訊路徑清單")
    
    # 生成參數 - 放寬驗證以避免 422 錯誤
    emotion: Optional[int] = Field(4, ge=0, le=10, description="情緒強度")
    crop_scale: Optional[float] = Field(2.3, description="裁切比例")
    sampling_steps: Optional[int] = Field(50, ge=1, le=200, description="生成步數")
    preview_duration: Optional[float] = Field(None, description="預覽時長 (秒)")


class PPTVideoEmbedRequest(BaseModel):
    """PPT 影片嵌入請求"""
    pptx_path: str = Field(..., description="PPT 檔案路徑")
    video_paths: List[Optional[str]] = Field(..., description="影片路徑清單 (按投影片順序)")
