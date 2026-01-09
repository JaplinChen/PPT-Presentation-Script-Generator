"""
TTS services - modularized from the original tts_service.py
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

from .audio_generator import AudioGenerator
from .ppt_embedder import PPTEmbedder
from .notes_sync import NotesSync

class TTSService:
    """
    Unified TTS service facade.
    Coordinates audio generation, PPT embedding, and notes synchronization.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.audio_gen = AudioGenerator(output_dir)
        self.ppt_embedder = PPTEmbedder(output_dir)
        self.notes_sync = NotesSync()
    
    async def list_voices(self, language: str = None) -> List[Dict]:
        """List available TTS voices"""
        return await self.audio_gen.list_voices(language)
    
    async def generate_audio(
        self, 
        text: str, 
        voice: str, 
        rate: str = "+0%", 
        pitch: str = "+0Hz"
    ) -> Dict:
        """Generate audio from text"""
        return await self.audio_gen.generate_audio(text, voice, rate, pitch)
    
    async def generate_narrated_pptx(
        self,
        original_pptx_path: str,
        slide_scripts: List[Dict],
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        progress_callback: Optional[callable] = None,
    ) -> Dict:
        """
        Generate narrated PPT with audio and notes.
        
        Args:
            original_pptx_path: Path to original PPT
            slide_scripts: List of slide script data
            voice: TTS voice
            rate: Speech rate
            pitch: Speech pitch
            progress_callback: Progress callback function
            
        Returns:
            Dict with filename, path, url_path, and audio_files
        """
        # Embed audio
        output_path, all_slide_scripts, audio_files = await self.ppt_embedder.embed_audio(
            original_pptx_path,
            slide_scripts,
            self.audio_gen,
            voice,
            rate,
            pitch,
            progress_callback
        )
        
        # Sync notes
        if progress_callback:
            progress_callback(90, "Synchronizing slide notes...")
        
        try:
            self.notes_sync.sync_notes(output_path, all_slide_scripts)
        except Exception as e:
            logger.warning(f"Notes sync failed: {e}")
        
        # Return result
        output_filename = Path(output_path).name
        return {
            "filename": output_filename,
            "path": output_path,
            "url_path": f"/outputs/{output_filename}",
            "audio_files": audio_files  # 添加音訊檔案列表
        }

    async def embed_videos_to_pptx(
        self,
        pptx_path: str,
        video_paths: List[Optional[str]],
        progress_callback: Optional[callable] = None,
    ) -> Dict:
        """
        Embed videos into an existing narrated PPT.
        """
        final_path = await self.ppt_embedder.embed_videos(
            pptx_path,
            video_paths,
            progress_callback
        )
        
        output_filename = Path(final_path).name
        return {
            "filename": output_filename,
            "path": final_path,
            "url_path": f"/outputs/{output_filename}"
        }

    async def generate_batch_audio(
        self,
        slide_scripts: List[Dict],
        voice: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
        progress_callback: Optional[callable] = None,
        job_id: str = None
    ) -> List[str]:
        """批量生成音訊檔"""
        audio_urls = []
        total = len(slide_scripts)
        
        for i, item in enumerate(slide_scripts):
            if progress_callback:
                progress_callback(int(((i+1)/total)*100), f"Generating audio {i+1}/{total}...")
            
            script = item.get('script', '')
            # Simple clean
            clean_text = re.sub(r'===.*?===|---.*?---|[*()\[\]/]', ' ', script)
            clean_text = re.sub(r'\([約大概]*\s*\d+\s*[秒分鐘seconds]+\)', '', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # Custom Pronunciation Fixes
            clean_text = clean_text.replace("VPIC1", "VPIC one")
            
            if not clean_text:
                audio_urls.append(None)
                continue
                
            # Use job_id subfolder if available, else root
            filename = f"slide_{item.get('slide_no')}.mp3"
            if job_id:
                filename = f"audio_batch_{job_id}/{filename}"
                
            info = await self.audio_gen.generate_audio(clean_text, voice, rate, pitch, filename=filename)
            audio_urls.append(info['url_path'])
            
        return audio_urls

    async def assemble_final_pptx(
        self,
        original_pptx_path: str,
        slide_scripts: List[Dict],
        audio_paths: List[Optional[str]],
        video_paths: List[Optional[str]],
        photo_path: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict:
        """最終封裝"""
        final_path = await self.ppt_embedder.embed_both(
            original_pptx_path,
            slide_scripts,
            audio_paths,
            video_paths,
            photo_path,
            progress_callback
        )
        
        # Sync notes (using slide_scripts)
        try:
            notes_dict = {int(s['slide_no']): s['script'] for s in slide_scripts}
            logger.info(f"Notes sync: {len(notes_dict)} entries, {sum(1 for v in notes_dict.values() if v)} non-empty")
            self.notes_sync.sync_notes(final_path, notes_dict)
        except Exception as e:
            logger.error(f"Final notes sync failed: {e}")
            
        output_filename = Path(final_path).name
        return {
            "filename": output_filename,
            "path": final_path,
            "url_path": f"/outputs/{output_filename}"
        }

__all__ = ['TTSService', 'AudioGenerator', 'PPTEmbedder', 'NotesSync']
