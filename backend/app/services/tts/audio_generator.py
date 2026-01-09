"""
Audio generation using Edge TTS with Content Hashing Cache.
"""
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import shutil
import logging
import edge_tts
from app.middleware.session import get_current_session_id
from app.core.config import settings

logger = logging.getLogger(__name__)

class AudioGenerator:
    """Handles TTS audio generation using Edge TTS with caching"""
    
    _voices_cache = []

    def __init__(self, output_dir: Path):
        self.base_output_dir = output_dir
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.base_output_dir / ".cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_session_output_dir(self) -> Path:
        """Get session-specific output directory."""
        session_id = get_current_session_id()
        return settings.get_session_output_dir(session_id)
    
    async def list_voices(self, language: str = None) -> List[Dict[str, Any]]:
        """
        List available voices, optionally filtered by language.
        
        Args:
            language: Language prefix filter (e.g., 'zh', 'en')
            
        Returns:
            List of voice dictionaries
        """
        if not AudioGenerator._voices_cache:
            logger.debug("Fetching voice list from edge-tts...")
            import asyncio
            try:
                # Use a larger timeout for network requests
                AudioGenerator._voices_cache = await asyncio.wait_for(edge_tts.list_voices(), timeout=20.0)
                logger.debug(f"Loaded {len(AudioGenerator._voices_cache)} voices.")
            except Exception as e:
                logger.error(f"Error fetching voices: {e}")
                return []
            
        voices = AudioGenerator._voices_cache
        
        result = []
        for v in voices:
            # Match by language prefix (e.g. 'zh' matches 'zh-CN', 'zh-TW')
            if language and not v['Locale'].lower().startswith(language.lower()):
                continue
                
            result.append({
                "short_name": v['ShortName'],
                "friendly_name": v['FriendlyName'],
                "gender": v['Gender'],
                "locale": v['Locale']
            })
            
        return result
    
    def _compute_hash(self, text: str, voice: str, rate: str, pitch: str) -> str:
        """Compute MD5 hash for cache key"""
        content = f"{text}|{voice}|{rate}|{pitch}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    async def generate_audio(
        self, 
        text: str, 
        voice: str, 
        rate: str = "+0%", 
        pitch: str = "+0Hz",
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate audio file from text with caching support.
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        # 0. Clean markers (ensure consistent cleaning across all entry points)
        import re
        # Remove markers and special brackets used for counting
        text = re.sub(r'===.*?===|---.*?---|[*()\[\]/]', ' ', text)
        # Remove standalone dash lines or sequences like ---
        text = re.sub(r'\s*-{2,}\s*', ' ', text)
        # Remove estimated time patterns
        text = re.sub(r'\([約大概]*\s*\d+\s*[秒分鐘seconds]+\)', '', text)
        # Final cleanup of extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
             return {"filename": "", "path": "", "url_path": ""}

        # 1. Compute Hash
        content_hash = self._compute_hash(text, voice, rate, pitch)
        cache_path = self.cache_dir / f"{content_hash}.mp3"
        
        # 2. Check Cache
        # 2. Check Cache
        if cache_path.exists():
            logger.debug(f"Cache hit for {content_hash}")
        else:
            logger.debug(f"Generating new audio for {content_hash}")
            import asyncio
            
            # Retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                    # Set a hard timeout to prevent infinite hang on network issues
                    # Increased from 30s to 45s
                    await asyncio.wait_for(communicate.save(str(cache_path)), timeout=45.0)
                    break # Success, exit loop
                except asyncio.TimeoutError:
                    logger.warning(f"TTS generation timed out (Attempt {attempt+1}/{max_retries})")
                    if attempt == max_retries - 1:
                        raise Exception("語音生成超時 (微軟伺服器無回應)，請檢查網路或稍後再試。")
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e} (Attempt {attempt+1}/{max_retries})")
                    if attempt == max_retries - 1:
                        raise Exception(f"語音生成失敗: {str(e)}")
                
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
        
        # 3. Determine Output
        if not filename:
            filename = f"{uuid.uuid4()}.mp3"
        elif not filename.endswith(".mp3"):
            filename = f"{filename}.mp3"
        
        # Use session-specific output directory
        session_output_dir = self._get_session_output_dir()
        session_id = get_current_session_id()
        output_path = session_output_dir / filename
        
        # Ensure subdirectory exists if filename contains paths
        if filename and ("/" in filename or "\\" in filename):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
        # 4. Copy from Cache to Output
        # (Using copy significantly reduces I/O and generation time compared to calling API again)
        shutil.copy2(cache_path, output_path)

        # URL path includes session_id for proper routing
        url_path = f"/outputs/{session_id}/{filename}" if session_id != 'default' else f"/outputs/{filename}"

        return {
            "filename": filename,
            "path": str(output_path),
            "url_path": url_path
        }
