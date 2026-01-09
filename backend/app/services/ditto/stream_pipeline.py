"""
簡化的 Ditto 推理管線

此檔案提供兩種模式:
1. Mock 模式: 用於開發和測試,不需要 GPU
2. Full 模式: 使用完整的 Ditto 核心組件

使用環境變數 DITTO_MODE 控制:
- DITTO_MODE=mock: 使用模擬實作
- DITTO_MODE=full (預設): 使用完整實作
"""

import os
import sys
import logging
import warnings
# 抑制 librosa/soundfile 相關警告
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
from pathlib import Path
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)

# 將當前目錄加入 sys.path 以解法 'core' 的 import 問題
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 檢查模式 (預設 full: 使用完整 Ditto AI 動畫)
# 若 onnxruntime 無法安裝（Python 3.14），會自動降級到 mock 模式
DITTO_MODE = os.getenv("DITTO_MODE", "full").lower()

def get_device():
    """判斷可用設備"""
    import torch
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

try:
    if DITTO_MODE == "full":
        # 嘗試導入完整組件
        from .stream_pipeline_full import StreamSDK
        
        # 定義推理函數 (基於 inference_ref.py)
        def run(
            SDK: StreamSDK, 
            audio_path: str, 
            source_path: str, 
            output_path: str, 
            more_kwargs: Optional[Dict] = None,
            progress_callback: Optional[Callable] = None
        ):
            import librosa
            import math
            import numpy as np
            
            if more_kwargs is None:
                more_kwargs = {}
                
            setup_kwargs = more_kwargs.get("setup_kwargs", {})
            run_kwargs = more_kwargs.get("run_kwargs", {})

            if progress_callback: progress_callback(10, "初始化 SDK...")
            
            if hasattr(SDK, "set_progress_callback"):
                SDK.set_progress_callback(progress_callback)
            
            SDK.setup(source_path, output_path, **setup_kwargs)

            if progress_callback: progress_callback(30, "處理音訊...")
            
            # 抑制 PySoundFile 警告
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, message=".*PySoundFile failed.*")
                audio, sr = librosa.core.load(audio_path, sr=16000)
            num_f = math.ceil(len(audio) / 16000 * 25)

            fade_in = run_kwargs.get("fade_in", -1)
            fade_out = run_kwargs.get("fade_out", -1)
            ctrl_info = run_kwargs.get("ctrl_info", {})
            SDK.setup_Nd(N_d=num_f, fade_in=fade_in, fade_out=fade_out, ctrl_info=ctrl_info)

            if progress_callback: progress_callback(50, f"開始推理 ({num_f} 幀)...")
            
            # 使用非同步安全的模式（如果有 tqdm 就關閉它或重導向）
            aud_feat = SDK.wav2feat.wav2feat(audio)
            SDK.audio2motion_queue.put(aud_feat)
            
            # 關閉並等待完成
            SDK.close()

            if progress_callback: progress_callback(90, "合併音訊影片...")
            # 合併音訊 (ffmpeg)
            cmd = f'ffmpeg -loglevel error -y -i "{SDK.tmp_output_path}" -i "{audio_path}" -map 0:v -map 1:a -c:v copy -c:a aac "{output_path}"'
            os.system(cmd)
            
            if progress_callback: progress_callback(100, "生成完成")
            return output_path

        USE_MOCK = False
        logger.info("✓ 使用完整 Ditto 實作")
    else:
        raise ImportError("DITTO_MODE is set to mock")

except Exception as e:
    logger.warning(f"⚠️  無法初始化完整 Ditto 實作: {e}")
    logger.info("ℹ️  降級到模擬模式")
    from .mock_implementation import MockStreamSDK as StreamSDK
    from .mock_implementation import mock_run as run
    USE_MOCK = True

# 導出
__all__ = ['StreamSDK', 'run', 'USE_MOCK', 'get_device']
