from fastapi import Request
from fastapi.responses import JSONResponse
import datetime
import traceback
from app.core.logger import logger
from app.core.config import settings

async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent server crashes and log errors.
    """
    error_msg = f"Global error: {request.method} {request.url} - {exc}"
    logger.error(error_msg, exc_info=True)
    
    # Write to error.log for persistence
    try:
        error_log = settings.BASE_DIR / "error.log"
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.datetime.now()}] {error_msg}\n")
            f.write(traceback.format_exc())
            f.write("-" * 50 + "\n")
    except Exception as ie:
        logger.error(f"Failed to write to error.log: {ie}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "error": str(exc), 
            "detail": "Internal Server Error"
        }
    )
