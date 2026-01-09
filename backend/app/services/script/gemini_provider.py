"""
Gemini API provider for script generation.
Uses the new google-genai package (replacing deprecated google.generativeai)
"""
import os
from typing import Dict, List, Optional
try:
    from google import genai
    from google.genai import types
except ImportError:
    import google.genai as genai
    from google.genai import types

class QuotaExceededError(Exception):
    """Raised when Gemini responds with a quota/429 error."""
    pass

class GeminiProvider:
    """Handles Gemini API interactions for script generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # 使用新的 google-genai 套件初始化客戶端
        self.client = genai.Client(api_key=self.api_key)
        # Use a model confirmed to exist
        self.model_name = "gemini-2.0-flash"
    
    def generate(self, prompt: str, model: Optional[str] = None, api_key: Optional[str] = None) -> str:
        """
        Generate content using Gemini API with retry logic.
        
        Args:
            prompt: The prompt to send to Gemini
            model: Optional model name override
            api_key: Optional API key override for this request
            
        Returns:
            Generated text response
            
        Raises:
            QuotaExceededError: If API quota is exceeded after retries
        """
        import time
        import re
        
        # Determine which model to use
        active_model = model if model and model.strip() else self.model_name
        
        # Use dynamic client if api_key provided, otherwise use default client
        client = self.client
        if api_key and api_key.strip():
            client = genai.Client(api_key=api_key)

        max_retries = 5
        base_delay = 10
        
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=active_model,
                    contents=prompt
                )
                
                if not response or not response.text:
                    raise ValueError("Empty response from Gemini")
                
                return response.text
                
            except Exception as e:
                error_msg = str(e).lower()
                is_quota_error = "quota" in error_msg or "429" in error_msg
                
                if attempt < max_retries and is_quota_error:
                    # Try to parse wait time from error message
                    wait_time = base_delay * (2 ** attempt) # Default backoff
                    
                    # Pattern match for specific wait times
                    match1 = re.search(r"retry in (\d+(\.\d+)?)s", error_msg)
                    match2 = re.search(r"seconds:\s*(\d+)", error_msg)
                    
                    if match1:
                        wait_time = float(match1.group(1)) + 2.0 
                    elif match2:
                        wait_time = float(match2.group(1)) + 2.0
                        
                    wait_time = min(wait_time, 120.0) # Cap at 2 minutes
                    
                    print(f"[Gemini] Rate limit hit. Free tier quota exceeded.")
                    print(f"[Gemini] Retrying in {wait_time:.1f}s (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                
                if is_quota_error:
                    raise QuotaExceededError(
                        f"Google Gemini API Free Tier Quota Exceeded. "
                        f"Please try again in a few minutes. (Original error: {e})"
                    )
                raise
    
    def translate(self, text: str, target_language: str, api_key: Optional[str] = None) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language name
            api_key: Optional API key override
            
        Returns:
            Translated text
        """
        prompt = f"""
Translate the following presentation script to {target_language}.
Preserve all formatting markers (e.g., "--- Slide X ---", "===").
Keep the structure exactly the same.

Original text:
{text}

Translated text:
"""
        return self.generate(prompt, api_key=api_key)
