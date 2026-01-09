from app.tasks.common import *
import logging

logger = logging.getLogger(__name__)

@async_task_handler("PPT Analysis")
async def background_parse_ppt(file_id: str, save_path: str):
    """CPU-bound parsing in a background thread."""
    state.set_parse_status(file_id, {"status": "processing", "progress": 10, "message": "Analyzing PPT structure..."})
    
    slides = instances.ppt_parser.parse(save_path)
    summary = instances.ppt_parser.get_summary(slides)
    
    file_data = state.get_uploaded_file(file_id)
    file_data.update({
        "slides": slides,
        "summary": summary,
        "status": "completed",
        "warnings": []
    })
    state.add_uploaded_file(file_id, file_data)
    state.set_parse_status(file_id, {"status": "completed", "progress": 100, "message": "Analysis complete"})


@async_task_handler("Final PPT Assembly")
async def run_assemble_task(full_job_id: str, file_id: str, slide_scripts: List[Dict], audio_paths: List[str], video_paths: List[str], photo_id: str = None):
    """Background task for final PPT assembly"""
    def prog(p, m):
        state.update_ppt_job(full_job_id, {"progress": p, "message": m})
    
    # Resolve original PPT path
    logger.info(f"[PPT Task] Looking up file_id: {file_id}")
    original_file = state.get_uploaded_file(file_id)
    if not original_file:
        logger.error(f"[PPT Task] File not found in database: {file_id}")
        raise Exception(f"Original file not found (file_id: {file_id}). The file may have been deleted or the session expired.")
    
    # Verify the file actually exists on disk
    file_path = original_file.get("path")
    if not file_path or not Path(file_path).exists():
        logger.error(f"[PPT Task] File path invalid or missing: {file_path}")
        raise Exception(f"Original file missing from disk: {file_path}")
    
    logger.info(f"[PPT Task] Found file: {file_path}")

    
    # Resolve Photo Path (if provided)
    photo_path = None
    if photo_id:
        p_data = state.get_uploaded_file(f"avatar_{photo_id}")
        if p_data:
            photo_path = p_data.get("path")
        else:
            # Fallback search: Check for direct filename match FIRST
            direct_path = settings.UPLOAD_DIR / photo_id
            if direct_path.exists():
                photo_path = str(direct_path)
            else:
                # Legacy check: Check for avatar_ prefix
                try:
                    matches = list(settings.UPLOAD_DIR.glob(f"avatar_{photo_id}.*"))
                    if matches:
                        photo_path = str(matches[0])
                except: pass
            
    # Standardize audio and video paths to absolute
    abs_audio_paths = []
    for ap in audio_paths:
        if not ap:
            abs_audio_paths.append(None)
            continue
        ap_abs = (settings.OUTPUT_DIR / Path(str(ap)).name).absolute()
        abs_audio_paths.append(str(ap_abs) if ap_abs.exists() else ap)

    abs_video_paths = []
    logger.debug(f"[PPT Task] Resolving {len(video_paths)} video paths...")
    
    # First, scan outputs folder for all existing video files (mp4/webm)
    existing_videos = {}
    
    # Get all video files, sorted by modification time (newest first)
    all_video_files = []
    for ext in ["**/*.mp4", "**/*.webm"]:
        all_video_files.extend(list(settings.OUTPUT_DIR.glob(ext)))
    
    # Sort by mtime descending
    all_video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for video_file in all_video_files:
        # Skip temporary files
        if ".tmp" in video_file.name:
            continue
            
        name = video_file.stem  # e.g., "slide_1"
        if name.startswith("slide_"):
            try:
                slide_num = int(name.split("_")[1])
                # If we haven't found a video for this slide yet, or if this is a webm (transparent)
                # and we previously found an mp4, update it.
                if slide_num not in existing_videos:
                    existing_videos[slide_num] = str(video_file.absolute())
                elif video_file.suffix == '.webm' and existing_videos[slide_num].endswith('.mp4'):
                    existing_videos[slide_num] = str(video_file.absolute())
            except (ValueError, IndexError):
                pass
    
    logger.debug(f"[PPT Task] Found existing videos: {list(existing_videos.keys())}")
    
    for idx, vp in enumerate(video_paths):
        slide_num = idx + 1  # 1-indexed
        
        # Check if this slide has an existing video
        if slide_num in existing_videos:
            abs_video_paths.append(existing_videos[slide_num])
            logger.debug(f"  - Slide {slide_num}: Found existing video")
        elif vp:
            # Try the provided path
            vp_str = str(vp)
            if vp_str.startswith('/outputs/'):
                vp_abs = (settings.OUTPUT_DIR / vp_str.replace('/outputs/', '', 1)).absolute()
            else:
                vp_abs = (settings.OUTPUT_DIR / Path(vp_str).name).absolute()
                
            if vp_abs.exists():
                abs_video_paths.append(str(vp_abs))
            else:
                abs_video_paths.append(None)
        else:
            abs_video_paths.append(None)

    result = await instances.tts_service.assemble_final_pptx(
        original_file["path"],
        slide_scripts,
        abs_audio_paths,
        abs_video_paths,
        photo_path=photo_path,
        progress_callback=prog
    )
    
    state.update_ppt_job(full_job_id, {
        "status": "completed",
        "progress": 100,
        "message": "Final PPT assembled.",
        "result": result
    })
