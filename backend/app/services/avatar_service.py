import asyncio
import logging
import shutil
import subprocess
import time
import os
from pathlib import Path
from typing import Dict, Optional, Callable, Any

from app.core.device import device_manager
from app.utils.validators import ImageValidator

logger = logging.getLogger(__name__)

class AvatarService:
    """數位播報員生成服務"""
    
    def __init__(
        self,
        model_path: str = "./checkpoints/ditto_pytorch",
        config_path: str = "./checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl",
        device: str = "cuda" # Hint only, will use DeviceManager
    ):
        """
        初始化 Avatar 服務
        """
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.sdk = None
        self._is_loaded = False
        
        # Concurrency Control
        self._is_generating = False
        self._current_user = None
        self._busy_message = None
        self._current_frame = None
        
        logger.debug(f"AvatarService initialized.")
    
    async def load_models(self) -> bool:
        """
        載入 Ditto 模型到記憶體 (Async Wrapper)
        """
        detected_device = await device_manager.get_device()
        if detected_device == "mps":
            logger.info("Mac MPS detected. Forcing CPU for AvatarService.")
            device = "cpu"
        else:
            device = detected_device
            
        if self._is_loaded:
            return True
            
        # Run heavy loading in thread pool
        return await asyncio.to_thread(self._load_models_sync, device)

    def _load_models_sync(self, device: str) -> bool:
        """Synchronous heavy loading logic"""
        try:
            logger.info(f"開始載入 Ditto 模型 (Device: {device})...")
            
            if not self.model_path.exists():
                logger.error(f"模型路徑不存在: {self.model_path}")
                return False
            
            try:
                from app.services.ditto.stream_pipeline import StreamSDK, run, USE_MOCK
                
                if USE_MOCK:
                    logger.info("Ditto 使用 Mock 模式")
                    self._is_loaded = True
                    return True
                
                from app.services.ditto.config import DittoConfig
            except ImportError as e:
                logger.warning(f"Ditto modules not found: {e}, running in mock mode")
                self._is_loaded = True 
                return True
            
            # 驗證配置
            config = DittoConfig(
                model_path=str(self.model_path),
                config_path=str(self.config_path),
                device=device
            )
            
            if not config.validate_paths():
                logger.error("模型檔案驗證失敗")
                return False
            
            # 初始化 SDK
            self.sdk = StreamSDK(
                str(self.config_path),
                str(self.model_path),
                device=device
            )
            
            self._is_loaded = True
            logger.info(f"✅ Ditto 模型載入成功 ({device})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型載入失敗: {e}", exc_info=True)
            return False

    def acquire_lock(self, user_id: str = "unknown", message: str = "Processing") -> bool:
        """嘗試獲取生成鎖"""
        if self._is_generating:
            return False
        self._is_generating = True
        self._current_user = user_id
        self._busy_message = message
        return True

    def release_lock(self, user_id: str = "unknown"):
        """釋放生成鎖"""
        # Simple release for now, strict ownership check can be added if needed
        self._is_generating = False
        self._current_user = None
        self._busy_message = None

    async def get_system_info(self) -> Dict[str, Any]:
        """Get system info including lock status"""
        try:
            # Optimization: Skip heavy hardware checks during generation to satisfy high CPU load
            if self._is_generating:
                return {
                    "cuda_available": False, # Just a placeholder
                    "gpu_name": "Generating...",
                    "gpu_memory_total": 0,
                    "gpu_memory_available": 0,
                    "model_loaded": self._is_loaded,
                    "avatar_enabled": True,
                    "is_generating": self._is_generating,
                    "busy_message": self._busy_message,
                    "current_frame": self._current_frame
                }

            detected_device = await device_manager.get_device()
            info = await device_manager.get_gpu_info()
            
            return {
                "cuda_available": (detected_device == "cuda"),
                "gpu_name": info.get("name"),
                "gpu_memory_total": info.get("total_memory"),
                "gpu_memory_available": info.get("free_memory"),
                "model_loaded": self._is_loaded,
                "avatar_enabled": True,
                "is_generating": self._is_generating,
                "busy_message": self._busy_message,
                "current_frame": self._current_frame
            }
        except Exception as e:
            logger.error(f"get_system_info failed: {e}")
            # Fallback to avoid 500 error on frontend
            return {
                "cuda_available": False,
                "model_loaded": self._is_loaded,
                "avatar_enabled": True,
                "is_generating": self._is_generating,
                "busy_message": self._busy_message or "System error (recovering)",
                "current_frame": self._current_frame
            }

    async def validate_image(self, image_path: str) -> Dict[str, Any]:
        """
        驗證照片是否適合用於生成
        """
        return await asyncio.to_thread(ImageValidator.validate, image_path)

    async def generate_talking_head(
        self,
        audio_path: str,
        image_path: str,
        output_path: str,
        progress_callback: Optional[Callable] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成數位播報員影片
        """
        start_time = time.time()
        
        try:
            # 1. 確保模型已準備好
            if not self._is_loaded:
                self._busy_message = "載入核心模型中..."
                if progress_callback:
                    progress_callback(0, self._busy_message)
                await self.load_models()
                
            # Internal wrapper to update busy message
            original_callback = progress_callback
            def internal_progress(p, m, img=None):
                self._busy_message = m
                if img:
                    self._current_frame = img
                if original_callback:
                    original_callback(p, m, img)
            
            progress_callback = internal_progress
            
            # 2. 驗證與預處理 (Offload heavy audio processing)
            options = options or {}
            preview_duration = options.get("preview_duration", 0)
            is_preview = (preview_duration and preview_duration > 0)
            
            # 使用 Thread 處理音訊裁切 (pydub is sync and slow)
            if preview_duration and preview_duration > 0:
                audio_path = await asyncio.to_thread(
                    self._process_preview_audio, 
                    audio_path, 
                    output_path, 
                    preview_duration
                )
                if not audio_path:
                     raise Exception("音訊處理失敗")

            # 3. 準備參數與路徑
            # ... (caching logic can remain here as os.stat is fast enough, md5 is fast for small files)
            # But MD5 for large files might block. Let's wrap caching too?
            # For now, let's stick to wrapping the heaviest parts.
            
            # ... (rest of logic)
            
            # ======== CACHING LOGIC START ========
            import hashlib
            
            # Calculate fingerprint
            # Added "v3_final_h264" to salt to invalidate old caches and ensure H264
            cache_key_str = f"{image_path}-{os.path.getsize(image_path)}-{audio_path}-{os.path.getsize(audio_path)}-{str(options)}-v3_final_h264"
            params_hash = hashlib.md5(cache_key_str.encode()).hexdigest()
            
            # Define cache path
            cache_dir = Path(output_path).parent.parent / "video_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cached_filename = f"cached_{params_hash}.mp4"
            cached_file = cache_dir / cached_filename
            
            # Check cache
            if cached_file.exists():
                short_hash = cached_filename[:15] + "..." + cached_filename[-8:]
                logger.info(f"✨ Found cached video: {short_hash}. Skipping generation.")
                if progress_callback:
                    progress_callback(50, "發現已生成的快取影片...")
                    time.sleep(0.5)
                    progress_callback(90, "應用快取...")
                
                # Copy cached file to output path
                shutil.copy2(cached_file, output_path)
                
                if progress_callback:
                    progress_callback(100, "生成完成 (Used Cache)!")
                    
                return {
                    "success": True,
                    "video_path": str(output_path),
                    "duration": 0,
                    "message": "Avatar generation successful (Cached)"
                }
            # ======== CACHING LOGIC END ========
            
            setup_kwargs = {
                "crop_scale": options.get("crop_scale", 2.0),
                "smo_k_s": 5,
                # For preview: 10 steps (Fast). For full: 30 steps (Balanced).
                "sampling_timesteps": 10 if is_preview else options.get("sampling_steps", 30),
                # Disable face restoration for preview to save massive CPU time
                "enable_face_restoration": not is_preview,
                # Force SD resolution for preview (480p)
                # For full generation: Use user option (default 1920)
                "max_size": 480 if is_preview else options.get("max_size", 1920),
                "pbar_desc": options.get("pbar_desc", "Video Gen")
            }
            run_kwargs = {
                "fade_in": options.get("fade_in", 5),
                "fade_out": options.get("fade_out", 5),
                "emo": options.get("emotion", 4),
            }
            
            backend_dir = Path(__file__).parent.parent.parent.absolute()
            cfg_pkl = backend_dir / "checkpoints/ditto_cfg/v0.4_hubert_cfg_pytorch.pkl"
            data_root = backend_dir / "checkpoints/ditto_pytorch"
            
            # 4. 執行實體生成
            # 從 stream_pipeline 導入正確的 SDK (mock 或 full)
            from app.services.ditto.stream_pipeline import StreamSDK, run
            
            if not self.sdk:
                # 初始化 SDK (mock 模式下每次都會創建新實例)
                self.sdk = StreamSDK(
                    cfg_pkl=str(cfg_pkl),
                    data_root=str(data_root),
                )
            
            video_output = await asyncio.to_thread(
                run,
                self.sdk,
                audio_path=audio_path,
                source_path=image_path,
                output_path=output_path,
                more_kwargs={"setup_kwargs": setup_kwargs, "run_kwargs": run_kwargs},
                progress_callback=progress_callback
            )
            
            if not Path(video_output).exists():
                raise Exception("影片生成失敗，輸出檔案未產生")

            # Apply circular mask using FFmpeg
            # DISABLED: VP9/WebM causes "Codec Unavailable" in PPT.
            # We rely on PPT's native Oval shape cropping initiated in ppt_embedder.
            # try:
            #     circular_output = await self._apply_circular_mask(video_output)
            #     if circular_output:
            #         video_output = circular_output
            #         logger.debug(f"Applied circular mask: {video_output}")
            # except Exception as e:
            #     logger.warning(f"Circular mask failed (using square video): {e}")

            # Enforce H.264 Compatibility (Fix for "Codec Unavailable")
            compatible_output = self._ensure_compatibility(video_output)
            if compatible_output:
                video_output = compatible_output

            # Save to cache
            try:
                shutil.copy2(video_output, cached_file)
                logger.info(f"✅ Video cached to: {cached_file}")
            except Exception as e:
                logger.warning(f"Failed to cache video: {e}")

            duration = time.time() - start_time
            # if progress_callback:
            #    progress_callback(100, "生成完成!")

            return {
                "success": True,
                "video_path": video_output,
                "duration": duration,
                "message": "Avatar generation successful"
            }
            
        except Exception as e:
            logger.error(f"Avatar generation failed: {e}", exc_info=True)
            return {
                "success": False, 
                "message": f"生成失敗: {str(e)}", 
                "duration": time.time() - start_time
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """
        取得系統資訊
        """
        info = await device_manager.get_system_info()
        info.update({
             "model_loaded": self._is_loaded,
             "avatar_enabled": True
        })
        return info
    
    def unload_models(self):
        """卸載模型釋放記憶體"""
        if self._is_loaded:
            del self.sdk
            self.sdk = None
            self._is_loaded = False
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            logger.info("模型已卸載")

    async def _apply_circular_mask(self, video_path: str) -> Optional[str]:
        """
        Apply circular mask to video using FFmpeg.
        Returns the path to the circular video (overwrites original).
        """
        # FFmpeg filter: Create circular mask with TRANSPARENCY
        # Use webm (VP9) which supports alpha channel
        input_path = Path(video_path)
        temp_output = input_path.with_suffix('.webm') # Change ext to webm
        
        # Use system FFmpeg
        # import imageio_ffmpeg
        # ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_path = "ffmpeg"
        
        cmd = [
            ffmpeg_path, '-y',
            '-i', str(input_path),
            '-f', 'lavfi', '-i', 'color=c=black@0.0:s=1920x1920,format=rgba', # Transparent BG
            '-filter_complex', 
            "[0:v]format=rgba,geq="
            "r='r(X,Y)':"
            "g='g(X,Y)':"
            "b='b(X,Y)':"
            "a='if(lte(pow(X-W/2,2)+pow(Y-H/2,2),pow(min(W,H)/2,2)),255,0)'"
            "[fg];"
            "[1:v][fg]overlay=shortest=1", # Overlay on transparent BG
            '-c:v', 'libvpx-vp9', # VP9 supports alpha
            '-b:v', '1M', # Bitrate
            '-c:a', 'libvorbis', # WebM compatible audio
            str(temp_output)
        ]

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=180 # Increased timeout for encoding
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg circular mask failed: {result.stderr}")
                return None
            
            # Remove original MP4 if successful to save space? 
            # Or keep it as caching might rely on it.
            # But the caller expects the final video.
            
            logger.info(f"✅ Circular video created: {temp_output}")
            return str(temp_output)
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg circular mask timed out")
            return None
        except Exception as e:
            logger.error(f"FFmpeg circular mask error: {e}")
            return None

    def _process_preview_audio(self, audio_path: str, output_path: str, preview_duration: float) -> Optional[str]:
        """
        Process audio for preview mode: slice duration. (Run in thread)
        """
        try:
            # import imageio_ffmpeg
            from pydub import AudioSegment
            # Configure pydub to use system ffmpeg (default behavior)
            # AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
            
            logger.info(f"Processing preview audio: {preview_duration}s")
            audio = AudioSegment.from_file(audio_path)
            total_dur = len(audio)
            req_dur = preview_duration * 1000
            
            if total_dur > req_dur:
                # Slice from middle to capture speech
                start_t = (total_dur - req_dur) // 2
                audio = audio[start_t : start_t + req_dur]
                
                # Save temp audio
                p_audio_path = str(Path(output_path).parent / f"preview_{Path(audio_path).name}")
                audio.export(p_audio_path, format="mp3")
                logger.info(f"Sliced audio saved to: {p_audio_path}")
                return p_audio_path
            
            return audio_path # Return original if short enough
            
        except Exception as e:
            logger.error(f"Failed to slice preview audio: {e}", exc_info=True)
            return None

    def _ensure_compatibility(self, video_path: str) -> Optional[str]:
        """
        Transcode video to strict H.264 (libx264) + yuv420p for PowerPoint compatibility.
        """
        try:
            input_path = Path(video_path)
            temp_output = input_path.with_name(f"compatible_{input_path.name}")
            
            ffmpeg_path = shutil.which("ffmpeg") or "ffmpeg"
            logger.info(f"Using FFmpeg at: {ffmpeg_path}")
            
            cmd = [
                ffmpeg_path, '-y',
                '-i', str(input_path),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-movflags', '+faststart',
                str(temp_output)
            ]
            
            logger.info(f"Transcoding for compatibility: {video_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg transcoding failed: {result.stderr}")
                return None
                
            # Replace original with compatible version
            shutil.move(str(temp_output), str(input_path))
            logger.info(f"✅ Compatibility enforced: {input_path}")
            return str(input_path)
            
        except Exception as e:
            logger.error(f"Compatibility transcoding error: {e}")
            return None
