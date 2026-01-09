"""
Ditto 配置管理

管理 Ditto 模型路徑、參數和運行時配置
"""

from pathlib import Path
from typing import Optional, Dict
import pickle


class DittoConfig:
    """Ditto 配置類別"""
    
    def __init__(
        self,
        model_path: str = "./checkpoints/ditto_pytorch",
        config_path: str = "./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
        device: str = "cuda"
    ):
        """
        初始化配置
        
        Args:
            model_path: 模型檔案路徑
            config_path: 配置檔案路徑
            device: 運算裝置 ('cuda' 或 'cpu')
        """
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.device = device
        
        # 預設參數
        self.default_params = {
            # Avatar Registrar
            "max_size": 1920,
            "crop_scale": 2.3,
            "crop_vx_ratio": 0,
            "crop_vy_ratio": -0.125,
            "crop_flag_do_rot": True,
            
            # Condition Handler
            "emo": 4,  # 情緒強度 0-7
            "eye_f0_mode": False,
            
            # Audio2Motion
            "sampling_timesteps": 50,  # Diffusion 步數
            "overlap_v2": 10,
            "smo_k_d": 3,
            
            # Motion Stitch
            "fade_in": 5,  # 淡入幀數
            "fade_out": 5,  # 淡出幀數
            "flag_stitching": True,
        }
    
    def load_config(self) -> Dict:
        """
        載入配置檔案
        
        Returns:
            配置字典
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置檔案不存在: {self.config_path}")
        
        with open(self.config_path, 'rb') as f:
            config = pickle.load(f)
        
        return config
    
    def get_setup_kwargs(self, **overrides) -> Dict:
        """
        取得 setup 參數
        
        Args:
            **overrides: 覆寫的參數
            
        Returns:
            參數字典
        """
        kwargs = self.default_params.copy()
        kwargs.update(overrides)
        
        return {
            "max_size": kwargs["max_size"],
            "crop_scale": kwargs["crop_scale"],
            "crop_vx_ratio": kwargs["crop_vx_ratio"],
            "crop_vy_ratio": kwargs["crop_vy_ratio"],
            "crop_flag_do_rot": kwargs["crop_flag_do_rot"],
            "emo": kwargs["emo"],
            "eye_f0_mode": kwargs["eye_f0_mode"],
            "sampling_timesteps": kwargs["sampling_timesteps"],
            "overlap_v2": kwargs["overlap_v2"],
            "smo_k_d": kwargs["smo_k_d"],
            "flag_stitching": kwargs["flag_stitching"],
        }
    
    def get_run_kwargs(self, **overrides) -> Dict:
        """
        取得 run 參數
        
        Args:
            **overrides: 覆寫的參數
            
        Returns:
            參數字典
        """
        kwargs = self.default_params.copy()
        kwargs.update(overrides)
        
        return {
            "fade_in": kwargs["fade_in"],
            "fade_out": kwargs["fade_out"],
        }
    
    def validate_paths(self) -> bool:
        """
        驗證路徑是否存在
        
        Returns:
            是否有效
        """
        if not self.model_path.exists():
            print(f"❌ 模型路徑不存在: {self.model_path}")
            return False
        
        if not self.config_path.exists():
            print(f"❌ 配置路徑不存在: {self.config_path}")
            return False
        
        # 檢查必要的模型檔案
        required_models = [
            "models/appearance_extractor.pth",
            "models/decoder.pth",
            "models/lmdm_v0.4_hubert.pth",
            "models/motion_extractor.pth",
            "models/stitch_network.pth",
            "models/warp_network.pth",
        ]
        
        for model_file in required_models:
            model_path = self.model_path / model_file
            if not model_path.exists():
                print(f"❌ 模型檔案不存在: {model_path}")
                return False
        
        return True
