from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import datetime
import asyncio
from app.core.config import settings
from app.core.logger import logger

class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.log_dir = settings.BASE_DIR / "logs"
        self.log_dir.mkdir(exist_ok=True)

    async def dispatch(self, request: Request, call_next):
        # 1. Processing Request
        client_ip = request.client.host if request.client else "unknown"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0]
            
        safe_ip = client_ip.replace(":", "_")
        path = request.url.path
        method = request.method
        
        # 2. Identify Interesting Actions
        interesting_actions = [
            "/api/upload", 
            "/api/generate", 
            "/api/translate", 
            "/api/tts/generate", 
            "/api/avatar/generate",
            "/api/ppt/generate-narrated",
            "/api/ppt/assemble-final"
        ]
        
        is_interesting = method == "POST" and any(path.startswith(action) for action in interesting_actions)
        
        if is_interesting:
            msg = f"{method} {path}"
            logger.info(f"👉 [AUDIT] {client_ip} initiated {msg}")
            
            # Non-blocking log write
            self._log_background(safe_ip, msg)
            
        response = await call_next(request)
        return response

    def _log_background(self, safe_ip: str, msg: str):
        """Schedule log writing in background thread"""
        try:
            log_file = self.log_dir / f"{safe_ip}.log"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            def write_op():
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] {msg}\n")
                except Exception as e:
                    logger.error(f"File write failed: {e}")

            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, write_op)
        except Exception as e:
            logger.error(f"Audit scheduling failed: {e}")
