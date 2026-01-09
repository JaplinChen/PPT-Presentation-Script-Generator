from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Body
from app.models import (
    GenerateScriptRequest,
    GenerateScriptResponse,
    TranslateRequest,
    ModelInfo,
    ModelListResponse,
)
from app.config import settings
from app.utils.state_manager import state
from app.services import instances
from app.utils.genai_compat import get_genai, is_genai_available, is_client_mode
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["script"])

def get_script_generator():
    """Helper to get or initialize a shared ScriptGenerator."""
    if instances.script_generator:
        return instances.script_generator
    
    # Initialize with server default key if available, but it can be overridden per request
    key = settings.GEMINI_API_KEY
    if not key:
        # Warning: If no server key and no user key is passed later, it might fail.
        # But we initialize it anyway to allow methods to run with passed keys.
        pass
        
    return instances.init_script_generator(key)

@router.post("/generate/{file_id}", response_model=GenerateScriptResponse)
async def generate_script(file_id: str, request: GenerateScriptRequest):
    """Generate presentation script for a previously uploaded PPT."""
    file_data = state.get_uploaded_file(file_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="找不到檔案資料，可能因伺服器重啟而遺失，請嘗試重新整理頁面或重新上傳 PPT 檔案。")

    generator = get_script_generator()

    # Dynamically update Ollama base URL if provided
    if request.ollama_base_url and hasattr(generator, 'ollama'):
        generator.ollama.base_url = request.ollama_base_url.rstrip("/")

    # Cache logic
    cache_key = "|".join([
        file_id, request.provider.lower(), request.model or "",
        request.audience, request.purpose, request.context, request.tone,
        str(request.duration_sec), str(request.include_transitions), request.language,
    ])

    result = state.get_generation_cache(cache_key)
    
    if not result:
        try:
            result = generator.generate_full_script(
                slides=file_data["slides"],
                audience=request.audience,
                purpose=request.purpose,
                context=request.context,
                tone=request.tone,
                duration_sec=request.duration_sec,
                include_transitions=request.include_transitions,
                language=request.language,
                provider=request.provider,
                model=request.model,
                api_key=request.api_key,
                avatar_name=request.avatar_name,
                custom_system_prompt=request.system_prompt,
            )

            # Save to cache
            state.set_generation_cache(cache_key, result)
        except instances.ScriptGenerator.QuotaExceededError:
            raise HTTPException(
                status_code=429, 
                detail="系統繁忙，Google AI 免費額度已達上限。請稍候 1-2 分鐘再試，或使用已快取的文稿。"
            )
        except Exception as exc:
            error_msg = str(exc)
            if "connect" in error_msg.lower() and "ollama" in error_msg.lower():
                detail = "無法連接到 Ollama。請確保 Ollama 已啟動，且已設定 OLLAMA_HOST=0.0.0.0 以供連接。"
            else:
                detail = f"Failed to generate script: {error_msg}"
            raise HTTPException(status_code=500, detail=detail)

    # Save scripts to individual files (post-processing)
    try:
        scripts_dir = settings.OUTPUT_DIR / file_id / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Save full script
        if "full_script" in result:
             (scripts_dir / "full_script.md").write_text(str(result["full_script"]), encoding="utf-8")

        # Save individual slides as slide_X.md
        if "slide_scripts" in result:
            for slide in result["slide_scripts"]:
                slide_no = slide.get("slide_no")
                content = slide.get("script", "")
                if slide_no is not None:
                    file_path = scripts_dir / f"slide_{slide_no}.md"
                    file_path.write_text(str(content), encoding="utf-8")
        
        logger.info(f"Saved scripts to {scripts_dir}")
        
    except Exception as e:
        logger.error(f"Failed to save script files to disk: {e}")
        # We process this error silently as it shouldn't block the API response
        
    return GenerateScriptResponse(**result)

@router.post("/translate", response_model=GenerateScriptResponse)
async def translate_script(request: TranslateRequest):
    """Translate an existing script and parse it back into sections."""
    generator = get_script_generator()
    try:
        # For translation, we use the default provider logic from generator
        result = generator.translate_and_parse(
            full_script=request.full_script,
            target_language=request.target_language,
            api_key=request.api_key,
        )
        return GenerateScriptResponse(**result)
    except ScriptGenerator.QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=f"Gemini quota exceeded or rate limited: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to translate script: {exc}")

@router.get("/gemini/models", response_model=ModelListResponse)
async def get_gemini_models(api_key: Optional[str] = None):
    """Get available Gemini models. Supports both google-generativeai and google-genai SDKs."""
    try:
        target_key = api_key if api_key and api_key.strip() else settings.GEMINI_API_KEY
        if not target_key:
            return ModelListResponse(models=[], success=False, error="No API key provided")
            
        if not is_genai_available():
             return ModelListResponse(models=[], success=False, error="Google GenAI library not found in backend environment.")

        genai = get_genai()
        models = []
        
        # Modern SDK (google-genai) uses Client
        if is_client_mode():
            try:
                client = genai.Client(api_key=target_key)
                for m in client.models.list():
                    is_supported = False
                    if hasattr(m, 'supported_generation_methods'):
                        is_supported = 'generateContent' in m.supported_generation_methods
                    else:
                        # Fallback: assume 'gemini' models are supported
                        is_supported = 'gemini' in m.name.lower()
                        
                    if is_supported:
                        display_id = m.name.replace("models/", "")
                        display_name = getattr(m, 'display_name', display_id)
                        models.append(ModelInfo(value=display_id, label=f"{display_id} ({display_name})"))
            except Exception as e:
                logger.warning(f"Failed using GenAI Client: {e}")
                return ModelListResponse(models=[], success=False, error=str(e))

        # Standard SDK (google-generativeai) uses configure/list_models
        else:
            try:
                genai.configure(api_key=target_key)
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        display_id = m.name.replace("models/", "")
                        models.append(ModelInfo(value=display_id, label=f"{display_id} ({m.display_name})"))
            except Exception as e:
                logger.error(f"Failed using GenAI list_models: {e}")
                return ModelListResponse(models=[], success=False, error=str(e))
        
        models.sort(key=lambda x: x.value, reverse=True)
        return ModelListResponse(models=models)
    except Exception as e:
        logger.error(f"Unexpected error in get_gemini_models: {e}")
        return ModelListResponse(models=[], success=False, error=str(e))

@router.get("/ollama/models", response_model=ModelListResponse)
async def get_ollama_models(base_url: Optional[str] = None):
    """Get available Ollama models."""
    import httpx
    try:
        target_url = base_url.rstrip("/") if base_url and base_url.strip() else "http://localhost:11434"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{target_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                
                models = []
                if "models" in data:
                    for m in data["models"]:
                        name = m.get("name")
                        if name:
                            models.append(ModelInfo(value=name, label=name))
                
                models.sort(key=lambda x: x.value)
                return ModelListResponse(models=models)
            except httpx.ConnectError:
                 return ModelListResponse(models=[], success=False, error="無法連接到 Ollama。請確認服務已啟動。")
            
    except Exception as e:
        logger.error(f"Failed to get Ollama models: {e}")
        return ModelListResponse(models=[], success=False, error=str(e))

@router.get("/script/default-prompt")
async def get_default_prompt():
    """Get the default system prompt template."""
    from app.services.script.generator import ScriptGenerator
    return {"prompt": ScriptGenerator.get_default_system_prompt()}

@router.get("/prompts", response_model=List[str])
async def list_prompts():
    """List all available prompt templates."""
    generator = get_script_generator()
    return generator.list_prompts()

@router.get("/prompts/{name}")
async def get_prompt(name: str):
    """Get specific prompt content."""
    generator = get_script_generator()
    content = generator.get_prompt(name)
    if not content:
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    return {"name": name, "content": content}

@router.post("/prompts/{name}")
async def save_prompt(name: str, content: str = Body(..., embed=True)):
    """Update specific prompt content."""
    generator = get_script_generator()
    success = generator.save_prompt(name, content)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save prompt")
    return {"success": True, "name": name}

