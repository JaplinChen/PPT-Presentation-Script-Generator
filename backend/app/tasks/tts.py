from app.tasks.common import *
from app.middleware.session import current_session_id
import logging

logger = logging.getLogger(__name__)

@async_task_handler("Narrated PPT Generation")
async def run_narrated_pptx_task(
    job_id: str,
    file_id: str,
    original_pptx_path: str,
    slide_scripts: List[Dict],
    voice: str,
    rate: str,
    pitch: str,
):
    """Background worker for narrated PPT generation with progress reporting."""

    def progress_callback(progress: int, message: str):
        if state.get_ppt_job(job_id):
            state.update_ppt_job(job_id, {
                "progress": progress,
                "message": message
            })
            logger.info(f"[Job {job_id[:8]}] {progress}% - {message}")

    result = await instances.tts_service.generate_narrated_pptx(
        original_pptx_path, slide_scripts, voice, rate, pitch, progress_callback=progress_callback
    )
    if state.get_ppt_job(job_id):
        state.update_ppt_job(job_id, {
            "status": "completed",
            "progress": 100,
            "message": "Narrated PPT generated successfully",
            "result": result
        })

@async_task_handler("Batch TTS Generation")
async def run_tts_batch_task(job_id: str, slide_scripts: List[Dict], voice: str, rate: str, pitch: str, session_id: str = 'default'):
    """Background task for batch TTS generation"""
    # Set session context for this background task
    token = current_session_id.set(session_id)
    
    try:
        def prog(p, m):
            state.update_ppt_job(f"tts_batch_{job_id}", {"progress": p, "message": m})
        
        urls = await instances.tts_service.generate_batch_audio(
            slide_scripts,
            voice,
            rate,
            pitch,
            progress_callback=prog,
            job_id=job_id
        )
        state.update_ppt_job(f"tts_batch_{job_id}", {
            "status": "completed",
            "progress": 100,
            "message": "Batch audio generated.",
            "result": {"audio_files": urls}
        })
    finally:
        current_session_id.reset(token)
