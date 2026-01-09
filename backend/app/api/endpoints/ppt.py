import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from app.models import PPTUploadResponse, ParseStatusResponse, NarratedPPTRequest, NarratedPPTStatusResponse, FinalAssembleRequest
from app.config import settings
from app.utils.state_manager import state
from app.tasks import background_parse_ppt, run_narrated_pptx_task, run_assemble_task
import shutil
import re
from datetime import datetime

router = APIRouter(prefix="/api", tags=["ppt"])

@router.post("/upload", response_model=PPTUploadResponse)
async def upload_ppt(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Phase 1: Upload file and return file_id immediately."""
    if not file.filename.lower().endswith((".ppt", ".pptx")):
        raise HTTPException(status_code=400, detail="Only .ppt and .pptx files are supported.")

    file_id = str(uuid.uuid4())
    path_obj = Path(file.filename)
    
    # Sanitize filename
    safe_stem = re.sub(r'[^\w\-\.]', '_', path_obj.stem)
    if not safe_stem: safe_stem = "presentation"
    
    file_extension = path_obj.suffix
    date_str = datetime.now().strftime("%Y%m%d")
    base_name = f"{safe_stem}_{date_str}"
    
    # Find next sequence number
    upload_dir = settings.UPLOAD_DIR
    existing_files = list(upload_dir.glob(f"{base_name}_*{file_extension}"))
    max_seq = 0
    for f in existing_files:
        try:
            parts = f.stem.split('_')
            if parts:
                seq_part = parts[-1]
                if seq_part.isdigit():
                    max_seq = max(max_seq, int(seq_part))
        except ValueError:
            continue
            
    next_seq = max_seq + 1
    save_filename = f"{base_name}_{next_seq:03d}{file_extension}"
    save_path = upload_dir / save_filename

    try:
        # Save file
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        state.add_uploaded_file(file_id, {
            "filename": file.filename,
            "path": str(save_path),
            "status": "pending",
            "slides": [],
            "summary": {}
        })
        state.set_parse_status(file_id, {"status": "pending", "progress": 0, "message": "Queued for parsing"})
        
        # Start background parsing
        background_tasks.add_task(background_parse_ppt, file_id, str(save_path))

        return PPTUploadResponse(
            success=True,
            message="File uploaded, parsing started in background",
            file_id=file_id,
            slides=[],
            summary={}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(exc)}")

@router.get("/parse/{file_id}/status", response_model=ParseStatusResponse)
async def get_parse_status(file_id: str):
    """Phase 2: Poll for parsing progress."""
    status_data = state.get_parse_status(file_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="File not found or parsing not started")
    
    response = {
        "file_id": file_id,
        "status": status_data["status"],
        "progress": status_data["progress"],
        "message": status_data["message"]
    }
    
    if status_data["status"] == "completed":
        file_data = state.get_uploaded_file(file_id)
        response["slides"] = file_data["slides"]
        response["summary"] = file_data["summary"]
        
    return response

@router.get("/files/{file_id}")
async def get_file_info(file_id: str):
    """Return metadata for an uploaded file (used for session sharing)."""
    file_info = state.get_uploaded_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found.")
    return {
        "file_id": file_id,
        "filename": file_info.get("filename"),
        "path": file_info.get("path"),
        "status": file_info.get("status"),
        "slides": file_info.get("slides", []),
        "summary": file_info.get("summary", {})
    }


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete uploaded file and all generated assets (scripts, audio, video)."""
    file_data = state.get_uploaded_file(file_id)
    # Even if file_data is missing, we should try to clean up jobs/orphaned files if possible
    # But usually we return 404. Let's keep 404 for consistency if main file record is gone.
    if not file_data:
        # Check if there are jobs at least?
        # If no file record, we can't get path, but we might have jobs.
        # For now, stick to original logic: if no file record, 404.
        raise HTTPException(status_code=404, detail="File not found.")

    # 1. Advanced Cleanup: Find associated jobs and delete their outputs
    try:
        jobs = state.get_jobs_by_file_id(file_id)
        dirs_to_delete = set()
        files_to_delete = set()

        for job in jobs:
            result = job.get("result")
            if not result: continue
            
            # Check for 'results' list (common in avatar/batch jobs)
            if isinstance(result, dict):
                # Avatar batch results: ["/outputs/folder/file.mp4", ...]
                paths = result.get("results", [])
                if isinstance(paths, list):
                    for p in paths:
                        if isinstance(p, str) and "/outputs/" in p:
                            # Map /outputs/foo/bar.mp4 -> OUTPUT_DIR/foo/bar.mp4
                            rel_path = p.split("/outputs/")[-1] 
                            full_path = settings.OUTPUT_DIR / rel_path
                            if full_path.exists():
                                files_to_delete.add(full_path)
                                # If it's in a subfolder like avatar_batch_..., mark folder for deletion
                                # But be careful not to delete root OUTPUT_DIR
                                parent = full_path.parent
                                if parent != settings.OUTPUT_DIR and parent.name.startswith("avatar_batch"):
                                    dirs_to_delete.add(parent)
                
                # Single video result or similar
                video_url = result.get("video_url")
                if video_url and isinstance(video_url, str) and "/outputs/" in video_url:
                     rel_path = video_url.split("/outputs/")[-1]
                     full_path = settings.OUTPUT_DIR / rel_path
                     if full_path.exists():
                         files_to_delete.add(full_path)
        
        # Execute deletion
        for d in dirs_to_delete:
            try:
                if d.exists():
                    shutil.rmtree(d)
                    print(f"Deleted job directory: {d}")
            except Exception as e:
                print(f"Failed to delete directory {d}: {e}")
        
        for f in files_to_delete:
            try:
                if f.exists(): # Re-check in case parent dir was deleted
                    f.unlink()
                    print(f"Deleted job file: {f}")
            except Exception as e:
                print(f"Failed to delete file {f}: {e}")

        # Delete job records
        state.delete_jobs_by_file_id(file_id)

    except Exception as e:
        print(f"Error during deep cleanup for {file_id}: {e}")

    # 2. Delete the source uploaded file
    file_path = Path(file_data["path"])
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError as e:
            print(f"Error deleting source file {file_path}: {e}")
    
    # 3. Delete generated outputs in OUTPUT_DIR matching file_id or filename stem
    # (Legacy wildcard cleanup)
    for f in settings.OUTPUT_DIR.glob(f"*{file_id}*"):
        try:
            if f.is_file(): f.unlink()
            elif f.is_dir(): shutil.rmtree(f)
        except Exception: pass

    stem = file_path.stem
    if len(stem) > 5:
        for f in settings.OUTPUT_DIR.glob(f"*{stem}*"):
            try:
                if f.is_file(): f.unlink()
            except Exception: pass

    # 4. Clean up backend state
    state.delete_uploaded_file(file_id)
    state.clear_generation_cache_for_file(file_id)
    
    return {"success": True, "message": "File and associated assets deleted."}

@router.post("/ppt/generate-narrated")
async def generate_narrated_ppt(request: NarratedPPTRequest, background_tasks: BackgroundTasks):
    """Generate narrated PPTX (audio embedded) as a background task."""
    if not state.get_uploaded_file(request.file_id):
        raise HTTPException(status_code=404, detail="File info not found. Please re-upload.")

    job_id = f"narrated_{str(uuid.uuid4())}"
    state.add_ppt_job(job_id, {
        "job_id": job_id,
        "file_id": request.file_id,
        "status": "processing",
        "progress": 0,
        "message": "Starting narration generation...",
        "result": None,
    })

    file_data = state.get_uploaded_file(request.file_id)
    original_pptx_path = file_data["path"]

    background_tasks.add_task(
        run_narrated_pptx_task,
        job_id,
        request.file_id,
        original_pptx_path,
        request.slide_scripts,
        request.voice,
        request.rate,
        request.pitch,
    )

    return {"job_id": job_id, "status": "processing"}

@router.get("/ppt/job/{job_id}/status", response_model=NarratedPPTStatusResponse)
async def get_ppt_job_status(job_id: str):
    """Poll for the status of a narrated PPT generation job."""
    job_data = state.get_ppt_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found.")
    return NarratedPPTStatusResponse(**job_data)

@router.post("/ppt/assemble-final")
async def assemble_final_ppt(request: FinalAssembleRequest, background_tasks: BackgroundTasks):
    """Start background final PPT assembly"""
    job_id = str(uuid.uuid4())
    full_job_id = f"assemble_{job_id}"
    
    state.add_ppt_job(full_job_id, {
        "job_id": full_job_id,
        "type": "assemble",
        "status": "processing",
        "progress": 0,
        "message": "Starting final assembly...",
        "result": None
    })
    
    background_tasks.add_task(
        run_assemble_task,
        full_job_id,
        request.file_id,
        request.slide_scripts,
        request.audio_paths,
        request.video_paths,
        photo_id=request.photo_id
    )
    
    return {"job_id": full_job_id, "status": "processing"}
