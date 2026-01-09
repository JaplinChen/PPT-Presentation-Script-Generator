from .ppt_parser import PPTParser
from .script import ScriptGenerator
from .tts import TTSService
from .avatar_service import AvatarService
from .instances import (
    ppt_parser, tts_service, script_generator, avatar_service,
    init_script_generator, init_avatar_service
)

__all__ = [
    'PPTParser', 'ScriptGenerator', 'TTSService', 'AvatarService',
    'ppt_parser', 'tts_service', 'script_generator', 'avatar_service',
    'init_script_generator', 'init_avatar_service'
]
