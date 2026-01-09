from app.tasks.common import *
import logging

logger = logging.getLogger(__name__)

@async_task_handler("Avatar Generation")
async def run_avatar_generation_task(
    job_id: str,
    photo_path: str,
    audio_path: str,
    output_path: str,
    options: Dict
):
    """Background worker for single avatar generation"""
    try:
        def prog(p, m, image=None):
            data = {"progress": p, "message": m}
            if image:
                data["current_frame"] = image
            state.update_ppt_job(f"avatar_{job_id}", data)
            
        result = await instances.avatar_service.generate_talking_head(
            audio_path=audio_path,
            image_path=photo_path,
            output_path=output_path,
            progress_callback=prog,
            options=options
        )
        
        if result["success"]:
            # Use relative URL for frontend
            video_filename = Path(output_path).name
            state.update_ppt_job(f"avatar_{job_id}", {
                "status": "completed",
                "progress": 100,
                "message": "Avatar generation completed",
                "video_url": f"/outputs/{video_filename}"
            })
    except Exception as e:
         logger.error(f"Avatar task failed: {e}")
         state.update_ppt_job(f"avatar_{job_id}", {"status": "failed", "error": str(e)})
    finally:
        # Use photo_id if available to match acquisition, else fallback to job_id
        lock_id = options.get("photo_id", job_id) if isinstance(options, dict) else job_id
        instances.avatar_service.release_lock(user_id=lock_id)

@async_task_handler("Batch Avatar Generation")
async def run_batch_avatar_task(
    job_id: str,
    image_path: str,
    audio_paths: List[str],
    options: Dict,
    log_ip: str = None  # New argument for IP logging
):
    """Background worker for batch avatar generation"""
    from app.utils.power_manager import PowerManager
    try:
        PowerManager.prevent_sleep()
        total = len(audio_paths)
        results = [None] * total
        
        # Define log function for IP-specific logging
        def log_to_ip(message):
            if log_ip:
                try:
                    log_file = Path("logs") / f"{log_ip}.log"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] {message}\n")
                        f.flush()
                except: pass

        from datetime import datetime
        now = datetime.now()
        today_str = now.strftime("%Y%m%d")
        
        # Use Time ID (HHMMSS) instead of UUID for human readability
        short_id = now.strftime("%H%M%S")
        folder_name = f"avatar_batch_slide_1_{today_str}_{short_id}"
        
        job_dir = settings.OUTPUT_DIR / folder_name
        job_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[Batch Avatar {short_id}] Created folder: {folder_name}")
        log_to_ip(f"🎬 Batch Generation Started. Folder: {folder_name}")

        def progress_callback(current_idx: int):
            # Use a mutable dictionary to track state across closure calls for this specific slide
            state_tracker = {"last_logged": -1}
            
            def inner(progress: int, message: str, image: str = None):
                overall_progress = int(((current_idx + (progress / 100)) / total) * 100)
                update_data = {
                    "progress": overall_progress,
                    "message": f"Processing slide {current_idx + 1}/{total}: {message}"
                }
                if image:
                    update_data["current_frame"] = image
                    
                state.update_ppt_job(f"avatar_batch_{job_id}", update_data)
                
                # Log detailed progress for the monitor window
                # Debounce: Only log if we hit a new 20% milestone that hasn't been logged yet
                if (progress % 20 == 0 or progress == 100) and progress != state_tracker["last_logged"]:
                    log_to_ip(f"Slide {current_idx + 1}/{total}: {message} ({progress}%)")
                    state_tracker["last_logged"] = progress
                    
            return inner

        # Resolve image path to absolute
        img_path_obj = Path(image_path)
        if not img_path_obj.is_absolute():
            img_path_obj = (settings.UPLOAD_DIR / img_path_obj.name).absolute()
        image_path = str(img_path_obj)
        
        logger.info(f"[Batch Avatar {short_id}] Using image: {image_path}")
        logger.info(f"[Batch Avatar {short_id}] Received {len(audio_paths)} audio paths for processing")
        for i, audio_path in enumerate(audio_paths):
            if not audio_path:
                logger.warning(f"[Batch Avatar {short_id}] Skipping empty audio path at index {i}")
                continue
                
            # Resolve audio path correctly - Use absolute paths to avoid CWD issues
            audio_path_str = str(audio_path)
            
            # 1. Try resolving relative to settings.OUTPUT_DIR
            # Handle cases where path includes subfolders like "audio_batch_xyz/slide_1.mp3"
            clean_rel_path = audio_path_str.replace("/outputs/", "").replace("\\outputs\\", "").lstrip("/\\")
            p = (settings.OUTPUT_DIR / clean_rel_path).absolute()
            
            if not p.exists():
                # 2. Try raw path if absolute
                p_raw = Path(audio_path_str).absolute()
                if p_raw.exists():
                    p = p_raw
                else:
                    # 3. Fallback: try filename only (legacy flat structure)
                    p_legacy = settings.OUTPUT_DIR / Path(audio_path_str).name
                    if p_legacy.exists():
                        p = p_legacy
                    else:
                        logger.error(f"[Batch Avatar {short_id}] Audio path error: {audio_path} (Resolved to: {p})")
                        continue
            
            logger.info(f"[Batch Avatar {short_id}] Processing slide {i+1} with audio: {p.name}")

            output_name = f"slide_{i+1}.mp4"
            output_path = str(job_dir / output_name)
            
            if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                logger.info(f"[Batch Avatar {short_id}] ⏭️ Slide {i+1} exists, skipping generation")
                # Update progress for skipped item
                progress_callback(i)(100, f"Slide {i+1} already exists, skipping")
                result = {"success": True, "message": "Skipped"}
            else:
                # Generate video for ALL slides (not just slide 1)
                result = await instances.avatar_service.generate_talking_head(
                    audio_path=str(p),
                    image_path=image_path,
                    output_path=output_path,
                    progress_callback=progress_callback(i),
                    options={
                        "emotion": options.get("emotion", 4),
                        "crop_scale": options.get("crop_scale", 2.3),
                        "sampling_steps": options.get("sampling_steps", 50),
                        "max_size": options.get("max_size", 480),  # 解析度：480/720/1080
                        "preview_duration": options.get("preview_duration"),
                        "pbar_desc": f"Slide {i+1}/{len(audio_paths)}" # Show readable slide progress
                    }
                )

            
            if result["success"]:
                # Correctly point to the custom folder name we created
                results[i] = f"/outputs/{folder_name}/{output_name}"
                # Keep original job_id for state updates as frontend uses it
                state.update_ppt_job(f"avatar_batch_{job_id}", {"results": results})
                logger.info(f"[Batch Avatar {short_id}] ✅ Slide {i+1} completed: {output_name}")
            else:
                # Log failure reason
                error_msg = result.get("message", "Unknown error")
                logger.error(f"[Batch Avatar {short_id}] ❌ Slide {i+1} failed: {error_msg}")
                log_to_ip(f"❌ Slide {i+1} Failed: {error_msg}")
        
        # Final status
        success_count = sum(1 for r in results if r is not None)
        if success_count == total and total > 0:
            status_msg = "All avatar videos generated successfully"
            overall_status = "completed"
        elif success_count > 0:
            status_msg = f"Generated {success_count}/{total} videos, some failed"
            overall_status = "completed"
        else:
            status_msg = "No videos were generated (audio paths empty or all failed)"
            overall_status = "failed"
            
        logger.info(f"[Batch Avatar {short_id}] {status_msg}")
        log_to_ip(f"🏁 Batch Finished. {status_msg}")
        
        state.update_ppt_job(f"avatar_batch_{job_id}", {
            "status": overall_status,
            "progress": 100,
            "message": status_msg
        })
    except Exception as e:
         logger.error(f"Batch avatar task failed: {e}")
         log_to_ip(f"🔥 Batch Crashed: {str(e)}")
         state.update_ppt_job(f"avatar_batch_{job_id}", {"status": "failed", "error": str(e)})
    finally:
        PowerManager.allow_sleep()
        # Use photo_id if available to match acquisition, else fallback to job_id
        lock_id = options.get("photo_id", job_id) if isinstance(options, dict) else job_id
        instances.avatar_service.release_lock(user_id=lock_id)
