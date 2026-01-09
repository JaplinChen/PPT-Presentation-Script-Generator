import logging
import threading
from typing import Dict, Optional, Any
from app.models.db_models import SessionLocal, FileRecord, ParseStatusRecord, JobRecord, CacheRecord, init_db

logger = logging.getLogger(__name__)

class StateManager:
    """Manages application state using SQLite/SQLAlchemy for persistence"""
    
    def __init__(self):
        # Initialize database tables
        init_db()
        self._job_memory_cache: Dict[str, Dict] = {} # For transient data like previews
        logger.info("[StateManager] Database initialized and connected.")
    
    # These are legacy placeholders, actual operations go to DB
    def _load_from_disk(self): pass
    def _save_to_disk(self): pass

    # Uploaded Files
    def add_uploaded_file(self, file_id: str, data: Dict):
        """Add or update uploaded file metadata"""
        db = SessionLocal()
        try:
            record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
            if not record:
                record = FileRecord(file_id=file_id)
                db.add(record)
            
            record.filename = data.get("filename")
            record.path = data.get("path")
            record.status = data.get("status")
            record.slides = data.get("slides", [])
            record.summary = data.get("summary", {})
            db.commit()
        except Exception as e:
            logger.error(f"Failed to add uploaded file {file_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_uploaded_file(self, file_id: str) -> Optional[Dict]:
        """Get uploaded file metadata"""
        db = SessionLocal()
        try:
            record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
            if record:
                return {
                    "filename": record.filename,
                    "path": record.path,
                    "status": record.status,
                    "slides": record.slides,
                    "summary": record.summary
                }
            return None
        finally:
            db.close()
    
    def delete_uploaded_file(self, file_id: str):
        """Delete uploaded file metadata"""
        db = SessionLocal()
        try:
            db.query(FileRecord).filter(FileRecord.file_id == file_id).delete()
            db.query(ParseStatusRecord).filter(ParseStatusRecord.file_id == file_id).delete()
            db.commit()
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    # Parse Status
    def set_parse_status(self, file_id: str, status: Dict):
        """Set parsing status"""
        db = SessionLocal()
        try:
            record = db.query(ParseStatusRecord).filter(ParseStatusRecord.file_id == file_id).first()
            if not record:
                record = ParseStatusRecord(file_id=file_id)
                db.add(record)
            
            record.status = status.get("status")
            record.progress = status.get("progress", 0)
            record.message = status.get("message")
            db.commit()
        except Exception as e:
            logger.error(f"Failed to set parse status {file_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_parse_status(self, file_id: str) -> Optional[Dict]:
        """Get parsing status"""
        db = SessionLocal()
        try:
            record = db.query(ParseStatusRecord).filter(ParseStatusRecord.file_id == file_id).first()
            if record:
                return {
                    "status": record.status,
                    "progress": record.progress,
                    "message": record.message
                }
            return None
        finally:
            db.close()
    
    # Generation Cache
    def set_generation_cache(self, cache_key: str, data: Dict):
        """Cache generated script"""
        db = SessionLocal()
        try:
            record = db.query(CacheRecord).filter(CacheRecord.cache_key == cache_key).first()
            if not record:
                record = CacheRecord(cache_key=cache_key)
                db.add(record)
            
            record.data = data
            db.commit()
        except Exception as e:
            logger.error(f"Failed to set cache {cache_key}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_generation_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached script"""
        db = SessionLocal()
        try:
            record = db.query(CacheRecord).filter(CacheRecord.cache_key == cache_key).first()
            if record:
                return record.data
            return None
        finally:
            db.close()
    
    def clear_generation_cache_for_file(self, file_id: str):
        """Clear all cached generations for a specific file"""
        db = SessionLocal()
        try:
            db.query(CacheRecord).filter(CacheRecord.cache_key.like(f"{file_id}%")).delete(synchronize_session='fetch')
            db.commit()
        except Exception as e:
            logger.error(f"Failed to clear cache for {file_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    # PPT Jobs
    def add_ppt_job(self, job_id: str, data: Dict):
        """Add narrated PPT job"""
        db = SessionLocal()
        try:
            record = JobRecord(
                job_id=job_id,
                file_id=data.get("file_id"),
                job_type=data.get("type", "narrated"),
                status=data.get("status"),
                progress=data.get("progress", 0),
                message=data.get("message"),
                result=data.get("result")
            )
            db.add(record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_ppt_job(self, job_id: str) -> Optional[Dict]:
        """Get PPT job status"""
        db = SessionLocal()
        try:
            record = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if record:
                result = {
                    "job_id": record.job_id,
                    "file_id": record.file_id,
                    "status": record.status,
                    "progress": record.progress,
                    "message": record.message,
                    "result": record.result
                }
                # Merge transient memory cache (current_frame 等暫態資料)
                if job_id in self._job_memory_cache:
                    result.update(self._job_memory_cache[job_id])
                
                return result
            return None
        finally:
            db.close()
    
    def update_ppt_job(self, job_id: str, updates: Dict):
        """Update PPT job status"""
        db = SessionLocal()
        try:
            record = db.query(JobRecord).filter(JobRecord.job_id == job_id).first()
            if record:
                if "status" in updates: record.status = updates["status"]
                if "progress" in updates: record.progress = updates["progress"]
                if "message" in updates: record.message = updates["message"]
                if "result" in updates: record.result = updates["result"]
                if "result" in updates: record.result = updates["result"]
                db.commit()
            
            # Update memory cache for transient data
            if "current_frame" in updates:
                if job_id not in self._job_memory_cache:
                    self._job_memory_cache[job_id] = {}
                self._job_memory_cache[job_id]["current_frame"] = updates["current_frame"]
            
            # Cleanup memory cache on completion
            if updates.get("status") in ["completed", "failed"] and job_id in self._job_memory_cache:
                self._job_memory_cache[job_id].pop("current_frame", None)
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_jobs_by_file_id(self, file_id: str) -> list[Dict]:
        """Get all jobs associated with a file_id"""
        db = SessionLocal()
        try:
            records = db.query(JobRecord).filter(JobRecord.file_id == file_id).all()
            results = []
            for record in records:
                job_data = {
                    "job_id": record.job_id,
                    "file_id": record.file_id,
                    "type": record.job_type,
                    "status": record.status,
                    "progress": record.progress,
                    "message": record.message,
                    "result": record.result
                }
                # Merge memory cache if exists
                if record.job_id in self._job_memory_cache:
                    job_data.update(self._job_memory_cache[record.job_id])
                results.append(job_data)
            return results
        finally:
            db.close()

    def delete_jobs_by_file_id(self, file_id: str):
        """Delete all jobs associated with a file_id"""
        db = SessionLocal()
        try:
            # Clean up memory keys first
            records = db.query(JobRecord).filter(JobRecord.file_id == file_id).all()
            for record in records:
                self._job_memory_cache.pop(record.job_id, None)
            
            # Delete from DB
            db.query(JobRecord).filter(JobRecord.file_id == file_id).delete()
            db.commit()
        except Exception as e:
            logger.error(f"Failed to delete jobs for file {file_id}: {e}")
            db.rollback()
        finally:
            db.close()

# Global state manager instance
state = StateManager()
