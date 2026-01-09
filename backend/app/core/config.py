import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "PPT Presentation Script API"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent # backend root
    
    @computed_field
    def UPLOAD_DIR(self) -> Path:
        return self.BASE_DIR / "uploads"

    @computed_field
    def OUTPUT_DIR(self) -> Path:
        return self.BASE_DIR / "outputs"
        
    @computed_field
    def PROMPTS_DIR(self) -> Path:
        return self.BASE_DIR / "prompts"
    
    # API Keys
    GEMINI_API_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # Ditto / Model Settings
    DITTO_MODE: str = "full" # mock or full
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore"
    )

    def init_dirs(self):
        """Ensure critical directories exist."""
        self.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        # Prompts dir is usually static source, not created at runtime, but we can ensure it exists
        if not self.PROMPTS_DIR.exists():
            # Fallback for relative path safe-guard if running from different CWD
            (Path.cwd() / "prompts").mkdir(exist_ok=True)
    
    def get_session_output_dir(self, session_id: str) -> Path:
        """Get session-specific output directory, creating it if needed."""
        if not session_id:
            return self.OUTPUT_DIR
        session_dir = self.OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True, parents=True)
        return session_dir

settings = Settings()
