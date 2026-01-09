"""
Ditto TalkingHead 環境設置與診斷工具

功能:
1. 檢查 GPU 和 CUDA 環境
2. 下載 Ditto 模型檔案
3. 驗證模型完整性
4. 提供診斷報告
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import hashlib
import json


class Colors:
    """終端機顏色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def check_gpu():
    """檢查 GPU 可用性"""
    print("\n" + "="*50)
    print("GPU 環境檢查")
    print("="*50)
    
    try:
        import torch
        
        # 檢查 CUDA
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            cuda_version = torch.version.cuda
            
            print_success(f"GPU: {gpu_name}")
            print_success(f"VRAM: {gpu_memory:.1f} GB")
            print_success(f"CUDA: {cuda_version}")
            
            # 檢查 VRAM 是否足夠
            if gpu_memory < 12:
                print_warning(f"VRAM 可能不足 (建議 24GB+)")
            elif gpu_memory < 24:
                print_warning(f"VRAM 勉強可用 (建議 24GB+)")
            else:
                print_success(f"VRAM 充足")
            
            return True
        else:
            print_error("CUDA 不可用")
            print_info("請確認:")
            print_info("1. 已安裝 NVIDIA 驅動")
            print_info("2. 已安裝 CUDA Toolkit 12.1+")
            print_info("3. PyTorch 是 CUDA 版本")
            return False
            
    except ImportError:
        print_error("PyTorch 未安裝")
        print_info("請先安裝: pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121")
        return False


def check_dependencies():
    """檢查相依套件"""
    print("\n" + "="*50)
    print("相依套件檢查")
    print("="*50)
    
    required_packages = [
        'torch',
        'librosa',
        'opencv-python-headless',
        'scikit-image',
        'numpy',
        'scipy'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"{package}")
        except ImportError:
            print_error(f"{package} 未安裝")
            all_installed = False
    
    if not all_installed:
        print_info("\n請安裝缺少的套件:")
        print_info("pip install -r ditto_requirements.txt")
    
    return all_installed


def download_models():
    """下載 Ditto 模型"""
    print("\n" + "="*50)
    print("下載 Ditto 模型")
    print("="*50)
    
    checkpoint_dir = Path("checkpoints")
    
    # 檢查是否已存在
    if checkpoint_dir.exists() and (checkpoint_dir / "ditto_pytorch").exists():
        print_warning("模型目錄已存在")
        response = input("是否重新下載? (y/N): ")
        if response.lower() != 'y':
            print_info("跳過下載")
            return True
    
    print_info("開始從 HuggingFace 下載模型 (~10GB)...")
    print_info("這可能需要 10-30 分鐘,取決於您的網路速度")
    
    # 檢查 git-lfs
    try:
        subprocess.run(['git', 'lfs', 'version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("git-lfs 未安裝")
        print_info("請安裝 git-lfs:")
        print_info("Windows: https://git-lfs.github.com/")
        print_info("Linux: sudo apt-get install git-lfs")
        return False
    
    # 下載模型
    try:
        cmd = [
            'git', 'clone',
            'https://huggingface.co/digital-avatar/ditto-talkinghead',
            str(checkpoint_dir)
        ]
        
        subprocess.run(cmd, check=True)
        print_success("模型下載完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"下載失敗: {e}")
        return False


def verify_models():
    """驗證模型檔案"""
    print("\n" + "="*50)
    print("驗證模型檔案")
    print("="*50)
    
    checkpoint_dir = Path("checkpoints")
    
    required_files = [
        "ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
        "ditto_pytorch/models/appearance_extractor.pth",
        "ditto_pytorch/models/decoder.pth",
        "ditto_pytorch/models/lmdm_v0.4_hubert.pth",
        "ditto_pytorch/models/motion_extractor.pth",
        "ditto_pytorch/models/stitch_network.pth",
        "ditto_pytorch/models/warp_network.pth",
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = checkpoint_dir / file_path
        if full_path.exists():
            size_mb = full_path.stat().st_size / 1024**2
            print_success(f"{file_path} ({size_mb:.1f} MB)")
        else:
            print_error(f"{file_path} 不存在")
            all_exist = False
    
    return all_exist


def run_test_inference():
    """執行測試推理"""
    print("\n" + "="*50)
    print("測試推理")
    print("="*50)
    
    print_info("此步驟會載入模型並執行簡單測試")
    print_info("這可能需要 1-2 分鐘...")
    
    try:
        import torch
        from pathlib import Path
        
        # 檢查模型路徑
        model_path = Path("checkpoints/ditto_pytorch")
        config_path = Path("checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl")
        
        if not model_path.exists() or not config_path.exists():
            print_error("模型檔案不存在,請先下載")
            return False
        
        print_info("載入模型...")
        # 這裡簡化測試,只檢查檔案是否可讀取
        import pickle
        with open(config_path, 'rb') as f:
            config = pickle.load(f)
        
        print_success("配置檔案載入成功")
        
        # 檢查 PyTorch 模型
        model_file = model_path / "models/decoder.pth"
        state_dict = torch.load(model_file, map_location='cpu')
        print_success("模型檔案載入成功")
        
        print_success("測試通過!")
        return True
        
    except Exception as e:
        print_error(f"測試失敗: {e}")
        return False


def generate_report():
    """生成診斷報告"""
    print("\n" + "="*50)
    print("系統診斷報告")
    print("="*50)
    
    report = {
        "gpu_available": False,
        "dependencies_ok": False,
        "models_ok": False,
        "ready": False
    }
    
    try:
        import torch
        if torch.cuda.is_available():
            report["gpu_available"] = True
            report["gpu_name"] = torch.cuda.get_device_name(0)
            report["gpu_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / 1024**3
            report["cuda_version"] = torch.version.cuda
    except:
        pass
    
    # 檢查相依套件
    try:
        import librosa
        import cv2
        import skimage
        report["dependencies_ok"] = True
    except:
        pass
    
    # 檢查模型
    checkpoint_dir = Path("checkpoints")
    if (checkpoint_dir / "ditto_pytorch").exists():
        report["models_ok"] = True
    
    report["ready"] = all([
        report["gpu_available"],
        report["dependencies_ok"],
        report["models_ok"]
    ])
    
    # 輸出報告
    print(json.dumps(report, indent=2))
    
    if report["ready"]:
        print_success("\n✨ 系統已就緒,可以開始使用 Ditto!")
    else:
        print_warning("\n⚠️  系統尚未就緒,請完成上述步驟")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Ditto TalkingHead 環境設置工具')
    parser.add_argument('--check-gpu', action='store_true', help='檢查 GPU 環境')
    parser.add_argument('--check-deps', action='store_true', help='檢查相依套件')
    parser.add_argument('--download-models', action='store_true', help='下載模型')
    parser.add_argument('--verify', action='store_true', help='驗證模型檔案')
    parser.add_argument('--test', action='store_true', help='執行測試推理')
    parser.add_argument('--diagnose', action='store_true', help='完整診斷')
    parser.add_argument('--all', action='store_true', help='執行所有步驟')
    
    args = parser.parse_args()
    
    # 如果沒有指定任何參數,顯示幫助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # 執行指定的步驟
    if args.check_gpu or args.all or args.diagnose:
        check_gpu()
    
    if args.check_deps or args.all or args.diagnose:
        check_dependencies()
    
    if args.download_models or args.all:
        download_models()
    
    if args.verify or args.all or args.diagnose:
        verify_models()
    
    if args.test or args.all:
        run_test_inference()
    
    if args.diagnose or args.all:
        generate_report()


if __name__ == "__main__":
    main()
