"""
Main script generator that coordinates all script generation functionality.
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import os

from .gemini_provider import GeminiProvider, QuotaExceededError
from .ollama_provider import OllamaProvider
from .parser import ScriptParser

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """
    Generate and translate presentation scripts using AI.
    Coordinates Gemini provider and script parser.
    """
    
    # Re-export exception for backward compatibility
    QuotaExceededError = QuotaExceededError
    
    def __init__(self, api_key: Optional[str] = None, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.gemini = GeminiProvider(api_key)
        self.ollama = OllamaProvider()
        self.parser = ScriptParser()
    
    @staticmethod
    def get_default_system_prompt() -> str:
        """Returns the default system prompt template from prompts/system.md."""
        try:
            # Try to load from the prompts directory
            prompts_dir = Path("prompts")
            if not prompts_dir.exists():
                 # Fallback for different CWD
                 prompts_dir = Path("backend/prompts")
            
            system_prompt_path = prompts_dir / "system.md"
            if system_prompt_path.exists():
                return system_prompt_path.read_text(encoding="utf-8")
                
            # Fallback hardcoded if file missing (safety net)
            return """你是一位專業的高階簡報文稿撰寫專家，擅長製作廣播級、極具說服力的演說內容。

**核心任務：**
根據提供的投影片內容，生成一份完整的 {language} 演講稿。

**文稿質量要求 (極度重要)：**
1. **深度擴展 (Structural Mandate)：** 每一頁投影片的文稿「必須」包含以下三個部分：
   - **(a) 自然銜接：** 不要讀標題，用一句話順暢地從上一頁過渡到本頁主題。
   - **(b) 深度內容：** 針對重點進行「背景說明、技術細節、或邏輯推導」。這是文稿的核心，至少要佔 3-4 個長句子。
   - **(c) 價值總結：** 用一句話強調本頁內容對聽眾的價值或意義。
2. **長度與速度保持 (Quality Pacing)：** 
   - **警告：** 絕對不可以因為頁數多就「越寫越短」。第 16 頁以後的內容必須保持與前 15 頁同樣的深度與字數。
   - **繁體中文要求：** 每一頁內容必須達到至少 **{min_length} 個中文字**，以填滿預計的 {int_avg_time_per_slide} 秒。
3. **專業氣氛：** 使用指定語氣 ({tone})，聽起來要像是一位資深顧問或高階主管。
4. **拒絕贅字：** 不要包含任何元數據 (Metadata) 或時間標記。

**格式標籤：**
- 使用 `=== Opening ===` 作為開場白 (請先自我介紹為 Ai 數位人 {avatar_name_display})。
- 每頁投影片前必須加上 `--- Slide X ---` 標籤 (X 為頁碼)。

**完整性：**
你必須為**每一頁**投影片 (Slide 1 到 Slide {total_slides}) 生成文稿。絕對不可以中途停止、跳過頁面或簡略字數。"""
        except Exception as e:
            logger.error(f"Failed to load system.md: {e}")
            return ""
    
    def generate_full_script(
        self,
        slides: List[Dict[str, Any]],
        audience: str = "General audience",
        purpose: str = "Introduce the topic",
        context: str = "Formal meeting",
        tone: str = "Professional and natural",
        duration_sec: int = 300,
        include_transitions: bool = True,
        language: str = "Traditional Chinese",
        provider: str = "gemini",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        avatar_name: Optional[str] = None,
        custom_system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a full presentation script.
        
        Args:
            slides: List of slide data with titles and bullets
            audience: Target audience description
            purpose: Presentation purpose
            context: Presentation context
            tone: Desired tone
            duration_sec: Target duration in seconds
            include_transitions: Whether to include transitions
            language: Target language
            provider: AI provider
            model: Model override
            api_key: API key override
            avatar_name: Name of the AI avatar
            custom_system_prompt: Custom system prompt template
            
        Returns:
            Dict with 'opening', 'slides', and 'full_script' keys
        """
        # Build prompt
        system_prompt, user_prompt = self._build_generation_prompt(
            slides, audience, purpose, context, tone, 
            duration_sec, include_transitions, language, avatar_name,
            custom_system_prompt
        )
        
        logger.info(f"Generating script with {provider} for {len(slides)} slides.")
        
        # Decide which provider to use and handle fallback
        active_provider = provider
        
        # Check if Gemini key is available (either passed in or in env)
        has_gemini_key = (api_key and api_key.strip()) or os.getenv("GEMINI_API_KEY")
        
        # Fallback logic: if provider is gemini but no key, and it's not explicitly requested otherwise, use ollama
        if active_provider == "gemini" and not has_gemini_key:
            logger.info("Gemini API key not found, falling back to Ollama.")
            active_provider = "ollama"

        # Combine prompts for maximum impact across all providers
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Generate script using selected provider
        if active_provider == "ollama":
            # For Ollama, we keep it combined to ensure instructions are always in view
            full_script = self.ollama.generate(full_prompt, model=model)
        else:
            # For Gemini, we also use the combined version
            full_script = self.gemini.generate(full_prompt, model=model, api_key=api_key)
        
        # Parse into structured format
        result = self.parser.parse_script(full_script, slides, include_transitions)
        
        return result

    def translate_and_parse(
        self, 
        full_script: str, 
        target_language: str, 
        api_key: Optional[str] = None,
        provider: str = "gemini"
    ) -> str:
        """
        Translate a script to target language.
        
        Args:
            full_script: The script to translate
            target_language: Target language name
            api_key: API key override
            provider: AI provider
            
        Returns:
            Translated script text
        """
        has_gemini_key = (api_key and api_key.strip()) or os.getenv("GEMINI_API_KEY")
        
        if provider == "ollama" or (provider == "gemini" and not has_gemini_key):
            return self.ollama.translate(full_script, target_language)
            
        return self.gemini.translate(full_script, target_language, api_key=api_key)

    def _build_generation_prompt(
        self,
        slides: List[Dict[str, Any]],
        audience: str,
        purpose: str,
        context: str,
        tone: str,
        duration_sec: int,
        include_transitions: bool,
        language: str,
        avatar_name: Optional[str] = None,
        custom_system_prompt: Optional[str] = None
    ) -> Any:
        """
        Build the system and user prompts for script generation.
        
        Args:
            slides: List of slide data dictionaries with title and bullets
            audience: Target audience description (e.g., "General audience", "Executives")
            purpose: Presentation purpose (e.g., "Introduce the topic")
            context: Presentation context (e.g., "Formal meeting")
            tone: Desired tone (e.g., "Professional and natural")
            duration_sec: Target duration in seconds
            include_transitions: Whether to include slide transitions
            language: Output language (e.g., "Traditional Chinese")
            avatar_name: Optional AI avatar name for self-introduction
            custom_system_prompt: Optional custom system prompt template with placeholders.
                                  If provided, it should contain format placeholders like
                                  {language}, {tone}, {min_length}, etc.
                                  If None, uses default system prompt.
        
        Returns:
            Tuple of (system_prompt, user_prompt) strings
        """
        
        # Format slides for prompt
        slides_text = self._format_slides(slides)
        
        # Calculate timing
        total_slides = len(slides)
        avg_time_per_slide = duration_sec / total_slides if total_slides > 0 else 30
        
        # Content length guidance based on language
        is_chinese = "chinese" in language.lower() or "中文" in language
        length_unit = "繁體中文字" if is_chinese else "words"
        # 3-4 chars per second is typical for professional Chinese speaking
        min_length = int(avg_time_per_slide * 3.5) if is_chinese else int(avg_time_per_slide * 3)
        
        # Variables for template substitution
        template_vars = {
            "language": language,
            "tone": tone,
            "min_length": min_length,
            "total_slides": total_slides,
            "int_avg_time_per_slide": int(avg_time_per_slide),
            "avatar_name_display": avatar_name if avatar_name else "",
            "avatar_name": avatar_name if avatar_name else ""
        }

        # Select template
        template = custom_system_prompt if custom_system_prompt and custom_system_prompt.strip() else self.get_default_system_prompt()
        
        # Apply substitution safely
        try:
            system_prompt = template.format(**template_vars)
        except (KeyError, ValueError) as e:
            logger.warning(f"Error formatting custom prompt: {e}. Falling back to default.")
            system_prompt = self.get_default_system_prompt().format(**template_vars)
        
        # Prepare examples based on language
        if is_chinese:
            ex_title = "假設投影片內容為：市場成長 - 15% 增加"
            ex_bad = "不良文稿：我們的市場今年成長了 15%。 (太短、沒內容)"
            ex_good = "優質文稿：回顧我們在上一季度的表現，我們看到了令人矚目的 15% 市場份額增長。這一增長主要得益於我們在東南亞地區的積極擴張，以及新推出的企業級功能的成功上線。這是一個明確的信號，表明我們向服務導向架構的戰略轉型正在取得回報，且我們預計這種蓬勃發展的勢頭將持續延續到下一個財政年度。"
        else:
            ex_title = "Example: Market Growth - 15% increase"
            ex_bad = "BAD Script: Our market grew by 15 percent this year."
            ex_good = "GOOD Script: Looking at our performance over the last quarter, we've seen a remarkable 15% increase in market share. This growth is primarily driven by our expansion into the Southeast Asian region and the successful launch of our new enterprise features. It's a clear indicator that our strategic pivot towards service-oriented architecture is paying off, and we expect this momentum to carry forward into the next fiscal year."

        user_prompt = f"""
**Presentation Details:**
- Audience: {audience}
- Purpose: {purpose}
- Context: {context}
- Total Duration: {duration_sec} seconds
- Target Slide Count: {total_slides}

**Slides Content:**
{slides_text}

**Example of High-Quality Elaboration ({length_unit}):**
*{ex_title}*
*{ex_bad}*
*{ex_good}*

Generate the complete script for all {total_slides} slides now:
"""
        return system_prompt, user_prompt
    
    def _format_slides(self, slides: List[Dict[str, Any]]) -> str:
        """Format slides for inclusion in prompt"""
        formatted = []
        
        for slide in slides:
            slide_no = slide.get("slide_no", 0)
            title = slide.get("title", "")
            bullets = slide.get("bullets", [])
            
            slide_text = f"Slide {slide_no}: {title}\n"
            if bullets:
                for bullet in bullets:
                    slide_text += f"  - {bullet}\n"
            
            formatted.append(slide_text)
        
        return "\n".join(formatted)
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file"""
        try:
            prompt_path = self.prompts_dir / filename
            if prompt_path.exists():
                return prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to load prompt {filename}: {e}")
        return ""

    def list_prompts(self) -> List[str]:
        """List all available prompt names (without extension)"""
        try:
            if not self.prompts_dir.exists():
                return []
            return [f.stem for f in self.prompts_dir.glob("*.md")]
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            return []

    def get_prompt(self, name: str) -> str:
        """Get content of a specific prompt"""
        return self._load_prompt(f"{name}.md")

    def save_prompt(self, name: str, content: str) -> bool:
        """Save content to a specific prompt file"""
        try:
            if not self.prompts_dir.exists():
                self.prompts_dir.mkdir(parents=True, exist_ok=True)
            
            prompt_path = self.prompts_dir / f"{name}.md"
            prompt_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save prompt {name}: {e}")
            return False
