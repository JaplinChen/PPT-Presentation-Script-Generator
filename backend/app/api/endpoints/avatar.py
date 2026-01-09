import uuid
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks, Request
from app.models.avatar import (
    PhotoUploadResponse, AvatarGenerateRequest, AvatarJobStatus, 
    AvatarSystemInfo, BatchAvatarRequest
)
from app.config import settings
from app.utils.state_manager import state
import app.services.instances as instances
from app.tasks import run_avatar_generation_task, run_batch_avatar_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/avatar", tags=["avatar"])

@router.get("/system-info", response_model=AvatarSystemInfo)
async def get_avatar_system_info():
    """Get Avatar system information."""
    if not instances.avatar_service:
        return AvatarSystemInfo(cuda_available=False, avatar_enabled=False, model_loaded=False)
    try:
        info = await instances.avatar_service.get_system_info()
        return AvatarSystemInfo(**info)
    except Exception as exc:
        return AvatarSystemInfo(cuda_available=False, model_loaded=False, avatar_enabled=False, message=str(exc))

@router.post("/force-unlock")
async def force_unlock_avatar():
    """Force release the avatar generation lock."""
    if not instances.avatar_service:
        raise HTTPException(status_code=503, detail="Avatar service not available")
    
    instances.avatar_service.release_lock(user_id="admin_force")
    logger.warning("Avatar generation lock has been forcibly released by user.")
    return {"status": "unlocked", "message": "System lock forced released"}

@router.post("/upload-photo", response_model=PhotoUploadResponse)
async def upload_avatar_photo(file: UploadFile = File(...)):
    """Upload and validate avatar photo."""
    if not instances.avatar_service:
        raise HTTPException(status_code=503, detail="Avatar service not available")
    
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Only JPG and PNG images are supported")
    
    # User Request: Use original filename
    path_obj = Path(file.filename)
    # Basic sanitization but keep original name recognizable
    safe_stem = re.sub(r'[^\w\-\.]', '_', path_obj.stem)
    file_extension = path_obj.suffix
    
    # photo_id is now the filename (sanitized) to keep it human readable and persistent
    # e.g. "MyPhoto.jpg" -> photo_id="MyPhoto.jpg"
    # Or just use the safe_stem + ext?
    # User said "Use uploaded file name".
    save_filename = f"{safe_stem}{file_extension}"
    photo_id = save_filename # ID is the filename itself
    
    upload_dir = settings.UPLOAD_DIR
    logger.debug(f"Uploading photo: {file.filename}, dir: {upload_dir}")
    
    logger.debug(f"Save filename: {save_filename}")
    save_path = upload_dir / save_filename
    
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        validation = await instances.avatar_service.validate_image(str(save_path))
        if not validation["valid"]:
            save_path.unlink()
            raise HTTPException(status_code=400, detail=validation["message"])
        
        state.add_uploaded_file(f"avatar_{photo_id}", {
            "filename": save_filename,
            "path": str(save_path),
            "type": "avatar_photo",
            "validation": validation
        })
        
        return PhotoUploadResponse(
            photo_id=photo_id,
            photo_url=f"/uploads/{save_filename}",
            validation=validation
        )
    except HTTPException: raise
    except Exception as exc:
        if save_path.exists(): save_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {exc}")

@router.post("/generate")
async def generate_avatar_video(request: AvatarGenerateRequest, background_tasks: BackgroundTasks):
    """Generate single avatar video."""
    if not instances.avatar_service:
        raise HTTPException(status_code=503, detail="Avatar service not available")
    
    photo_data = state.get_uploaded_file(f"avatar_{request.photo_id}")
    if not photo_data:
        # Fallback disk check
        # Check for direct filename match first (New logic)
        direct_path = settings.UPLOAD_DIR / request.photo_id
        if direct_path.exists():
             photo_data = {"path": str(direct_path)}
             state.add_uploaded_file(f"avatar_{request.photo_id}", photo_data)
        else:
            # Check for legacy UUID naming (Old logic)
            matches = list(settings.UPLOAD_DIR.glob(f"avatar_{request.photo_id}.*"))
            if matches:
                photo_data = {"path": str(matches[0])}
                state.add_uploaded_file(f"avatar_{request.photo_id}", photo_data)
            else:
                raise HTTPException(status_code=404, detail=f"Photo {request.photo_id} not found")
    
    # Check for concurrency lock
    if not instances.avatar_service.acquire_lock(user_id=request.photo_id, message="Generating Single Video"):
        busy_msg = instances.avatar_service._busy_message or "System Busy"
        raise HTTPException(status_code=409, detail=f"System is busy: {busy_msg}")
    else: # Indentation fix for the 'else' block of 'if not photo_data' is NOT needed? 
          # Wait, the original code had 'else: raise'. 
          # My new block handles the raise inside the 'else' of 'if matches'.
          pass
    
    raw_audio_path = request.audio_path.lstrip("/\\")
    audio_path = Path(raw_audio_path)
    if not audio_path.is_absolute():
        audio_path = Path.cwd() / raw_audio_path
        if not audio_path.exists():
            audio_path = settings.OUTPUT_DIR.parent / raw_audio_path
            
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail=f"Audio not found at {audio_path}")
    
    job_id = str(uuid.uuid4())
    output_path = request.output_path or str(settings.OUTPUT_DIR / f"avatar_{job_id}.mp4")
    
    state.add_ppt_job(f"avatar_{job_id}", {
        "job_id": job_id, "type": "avatar", "status": "processing",
        "progress": 0, "message": "Starting avatar generation...", "video_url": None
    })
    
    background_tasks.add_task(
        run_avatar_generation_task, job_id, photo_data["path"], str(audio_path), output_path, request.dict()
    )
    
    return {"job_id": job_id, "status": "processing"}

@router.post("/generate-batch")
async def generate_avatar_batch(request: Request, background_tasks: BackgroundTasks):
    """Start batch avatar generation."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get raw JSON data for debugging
    try:
        raw_data = await request.json()
        if not instances.avatar_service:
             raise HTTPException(status_code=503, detail="Avatar service not available")

        if "audio_paths" in raw_data and isinstance(raw_data["audio_paths"], list):
            # Create a copy to not mutate original
            log_data = raw_data.copy()
            paths = log_data["audio_paths"]
            if len(paths) > 3:
                log_data["audio_paths"] = paths[:3] + [f"... ({len(paths)-3} more)"]
            logger.info(f"[Avatar Batch] Received data: {log_data}")
        else:
            logger.info(f"[Avatar Batch] Received data: {raw_data}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    
    # Extract required fields
    photo_id = raw_data.get("photo_id")
    audio_paths = raw_data.get("audio_paths", [])
    
    if not photo_id:
        raise HTTPException(status_code=400, detail="photo_id is required")
    if not audio_paths:
        raise HTTPException(status_code=400, detail="audio_paths is required")
    
    photo_data = state.get_uploaded_file(f"avatar_{photo_id}")
    if not photo_data:
        # Fallback disk check
        # Check for direct filename match first (New logic)
        direct_path = settings.UPLOAD_DIR / photo_id
        if direct_path.exists():
             photo_data = {"path": str(direct_path)}
             state.add_uploaded_file(f"avatar_{photo_id}", photo_data)
        else:
            # Check for legacy UUID naming (Old logic)
            matches = list(settings.UPLOAD_DIR.glob(f"avatar_{photo_id}.*"))
            if matches:
                 photo_data = {"path": str(matches[0])}
                 state.add_uploaded_file(f"avatar_{photo_id}", photo_data)
            else:
                # Fallback: 如果找不到指定 ID 的照片，使用 uploads 資料夾中最新的一張
                # print(f"[WARNING] Photo {photo_id} not found. Trying fallback to latest uploaded photo.")
                logger.warning(f"Photo {photo_id} not found. Trying fallback to latest uploaded photo.")
                try:
                    all_photos = list(settings.UPLOAD_DIR.glob("*.jpg")) + list(settings.UPLOAD_DIR.glob("*.png"))
                    if all_photos:
                        # Sort by modification time, newest first
                        latest_photo = sorted(all_photos, key=lambda f: f.stat().st_mtime, reverse=True)[0]
                        photo_data = {"path": str(latest_photo)}
                        # print(f"[INFO] Fallback successful. Using latest photo: {latest_photo.name}")
                        logger.info(f"Fallback successful. Using latest photo: {latest_photo.name}")
                        # Update state to avoid future lookups
                        state.add_uploaded_file(f"avatar_{photo_id}", photo_data)
                    else:
                        raise HTTPException(status_code=404, detail="Photo not found (and no fallback photos available)")
                except Exception as e:
                    # print(f"[ERROR] Fallback failed: {e}")
                    logger.error(f"Fallback failed: {e}")
                    raise HTTPException(status_code=404, detail="Photo not found")

    # Check for concurrency lock
    if not instances.avatar_service.acquire_lock(user_id=photo_id, message="Batch Generation"):
        busy_msg = instances.avatar_service._busy_message or "System Busy"
        raise HTTPException(status_code=409, detail=f"System is busy: {busy_msg}")

    job_id = str(uuid.uuid4())
    state.add_ppt_job(f"avatar_batch_{job_id}", {
        "job_id": job_id, "type": "avatar_batch", "status": "processing",
        "progress": 0, "message": "Starting batch generation...", "results": []
    })

    # Get Client IP for logging
    client_ip = request.client.host if request.client else "unknown"
    # Sanitize IP for filename
    safe_ip = client_ip.replace(":", "_")
    
    background_tasks.add_task(run_batch_avatar_task, job_id, photo_data["path"], audio_paths, raw_data, safe_ip)
    return {"job_id": job_id, "status": "processing"}

@router.get("/job/{job_id}/status", response_model=AvatarJobStatus)
async def get_avatar_job_status(job_id: str):
    """Get avatar job status."""
    job_data = state.get_ppt_job(f"avatar_{job_id}") or state.get_ppt_job(f"avatar_batch_{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return AvatarJobStatus(
        job_id=job_id,
        status=job_data["status"],
        progress=job_data["progress"],
        message=job_data["message"],
        video_url=job_data.get("video_url"),
        error=job_data.get("error"),
        duration=job_data.get("duration"),
        current_frame=job_data.get("current_frame")
    )
