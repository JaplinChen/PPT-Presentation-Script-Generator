import os
import collections 
import collections.abc

# Monkey patch for python-pptx on Python 3.10+
if not hasattr(collections, 'Container'):
    collections.Container = collections.abc.Container
import threading
import asyncio
from contextlib import asynccontextmanager
import warnings

# Suppress TensorFlow/MediaPipe logs ASAP
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["GLOG_minloglevel"] = "2"

# Filter warnings
warnings.filterwarnings("ignore", category=FutureWarning, message=".*google.generativeai.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*on_event.*")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Core Modules
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import global_exception_handler

# Middleware
from app.middleware.audit import AuditMiddleware
from app.middleware.session import SessionMiddleware

# Services & API
from app.services import init_script_generator, init_avatar_service, tts_service, instances
from app.api.endpoints import ppt, script, tts, avatar

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: Startup and Shutdown"""
    # 1. Initialize Gemini
    try:
        init_script_generator(settings.GEMINI_API_KEY)
        logger.info("Script generator initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize script generator: {e}")
    
    # 2. Initialize Avatar Service (Background)
    def background_init():
        try:
            init_avatar_service()
            logger.info("Avatar service initialized.")
        except Exception as e:
            logger.error(f"Avatar service init failed: {e}")

    threading.Thread(target=background_init, daemon=True).start()
    
    # 3. Pre-fetch TTS voices
    try:
        asyncio.create_task(tts_service.list_voices())
    except Exception as e:
        logger.warning(f"TTS voice pre-fetch warning: {e}")

    # 4. Start Log Monitor
    try:
        from app.monitor import LogMonitor
        monitor = LogMonitor()
        monitor.start()
        app.state.monitor = monitor
    except Exception as e:
        logger.error(f"Failed to start LogMonitor: {e}")

    yield

    # Shutdown Logic
    logger.info("Application shutting down...")

# App Definition
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Upload PPT, generate presentation scripts, translate, and synthesize narration.",
    lifespan=lifespan
)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)

# Global Middleware
app.add_middleware(AuditMiddleware)
app.add_middleware(SessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Static Files
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(ppt.router)
app.include_router(script.router)
app.include_router(tts.router)
app.include_router(avatar.router)

@app.get("/")
async def root():
    return {
        "message": settings.APP_NAME, 
        "version": settings.APP_VERSION, 
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_configured": instances.script_generator is not None,
        "avatar_configured": instances.avatar_service is not None,
    }

@app.get("/api/ping")
async def ping():
    return {"message": "pong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
