from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from app.models import TTSGenerateRequest, TTSGenerateResponse, BatchTTSRequest, PPTVideoEmbedRequest
from app.config import settings
from app.utils.state_manager import state
from app.services import tts_service
from app.tasks import run_tts_batch_task
from pathlib import Path
import uuid

router = APIRouter(prefix="/api/tts", tags=["tts"])


def get_session_id(request: Request) -> str:
    """Extract session_id from request state, with fallback."""
    return getattr(request.state, 'session_id', None) or 'default'


@router.get("/voices")
async def get_tts_voices(language: Optional[str] = None):
    """List available TTS voices."""
    try:
        return await tts_service.list_voices(language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {exc}")

@router.post("/generate", response_model=TTSGenerateResponse)
async def generate_tts(request_body: TTSGenerateRequest):
    """Generate TTS audio for provided text."""
    try:
        # Session ID is obtained via context variable inside the service
        result = await tts_service.generate_audio(
            text=request_body.text, 
            voice=request_body.voice, 
            rate=request_body.rate, 
            pitch=request_body.pitch
        )
        return TTSGenerateResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {exc}")

@router.post("/generate-batch")
async def generate_tts_batch(request_body: BatchTTSRequest, request: Request, background_tasks: BackgroundTasks):
    """Start background batch TTS generation"""
    session_id = get_session_id(request)
    job_id = str(uuid.uuid4())
    state.add_ppt_job(f"tts_batch_{job_id}", {
        "job_id": job_id,
        "type": "tts_batch",
        "status": "processing",
        "progress": 0,
        "message": "Starting batch audio generation...",
        "result": None,
        "session_id": session_id
    })
    
    # Note: Background tasks run outside request context, so we pass session_id explicitly
    background_tasks.add_task(
        run_tts_batch_task,
        job_id,
        request_body.slide_scripts,
        request_body.voice,
        request_body.rate,
        request_body.pitch,
        session_id
    )
    return {"job_id": f"tts_batch_{job_id}", "status": "processing"}

@router.post("/embed-videos")
async def embed_videos_to_pptx(request: PPTVideoEmbedRequest):
    """Embed video files into an existing PPTX"""
    try:
        pptx_path = request.pptx_path.lstrip('/')
        abs_pptx_path = Path(pptx_path)
        if not abs_pptx_path.is_absolute():
            abs_pptx_path = settings.OUTPUT_DIR.parent / pptx_path
            
        if not abs_pptx_path.exists():
            raise HTTPException(status_code=404, detail=f"PPTX not found at {abs_pptx_path}")

        abs_video_paths = []
        for v_path in request.video_paths:
            if not v_path:
                abs_video_paths.append(None)
                continue
            
            vp = v_path.lstrip('/')
            if vp.startswith('outputs/'):
                abs_vp = settings.OUTPUT_DIR / vp[len('outputs/'):]
            else:
                abs_vp = Path(vp)
                if not abs_vp.is_absolute():
                    abs_vp = settings.OUTPUT_DIR.parent / vp
            
            abs_video_paths.append(str(abs_vp) if abs_vp.exists() else None)
            
        result = await tts_service.embed_videos_to_pptx(str(abs_pptx_path), abs_video_paths)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
