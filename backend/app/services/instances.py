from typing import Optional
from app.config import settings
from app.services.ppt_parser import PPTParser
from app.services.script import ScriptGenerator
from app.services.tts import TTSService
from app.services.avatar_service import AvatarService

# Initialize services (stateless ones or those with default config)
ppt_parser = PPTParser()
tts_service = TTSService(output_dir=settings.OUTPUT_DIR)

# Global script generator instance
script_generator = ScriptGenerator(prompts_dir=str(settings.PROMPTS_DIR))
avatar_service: Optional[AvatarService] = None

def init_script_generator(api_key: Optional[str] = None):
    global script_generator
    script_generator = ScriptGenerator(api_key=api_key, prompts_dir=str(settings.PROMPTS_DIR))
    return script_generator

def init_avatar_service():
    global avatar_service
    avatar_service = AvatarService()
    return avatar_service
