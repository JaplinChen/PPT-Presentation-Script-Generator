"""
Application configuration management.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Directories
    # Use the actual backend directory instead of a hardcoded path
    BASE_DIR: Path = Path(__file__).resolve().parent.parent  # Points to /backend
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "outputs"
    PROMPTS_DIR: Path = Path("prompts")
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    def __init__(self):
        """Ensure directories exist"""
        self.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        self.PROMPTS_DIR.mkdir(exist_ok=True, parents=True)

# Global settings instance
settings = Settings()
