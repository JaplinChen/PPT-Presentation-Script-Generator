"""
Ollama API provider for script generation.
"""
import httpx
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class OllamaProvider:
    """Handles Ollama API interactions for script generation"""
    
    def __init__(self, base_url: str = "http://localhost:11434", default_model: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
    
    def generate(self, prompt: str, model: Optional[str] = None, system: Optional[str] = None, **kwargs) -> str:
        """
        Generate content using Ollama API.
        
        Args:
            prompt: The prompt to send to Ollama
            model: Optional model name override
            system: Optional system prompt
            
        Returns:
            Generated text response
        """
        active_model = model if model and model.strip() else self.default_model
        
        # Validate model is not empty
        if not active_model or not active_model.strip():
            raise ValueError(
                "未選擇 Ollama 模型。請在 LLM 設定中選擇一個模型，"
                "或確認 Ollama 服務正在運行且有可用的模型。"
            )
        
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": active_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 8192,
                "num_ctx": 16384,
                "repeat_penalty": 1.0
            }
        }
        
        if system:
            payload["system"] = system
        
        logger.info(f"Generating script with Ollama ({active_model}) at {self.base_url}")
        
        try:
            # Increase timeout to 30 minutes (1800s) for extremely large models like 70B/120B
            with httpx.Client(timeout=1800.0) as client:
                response = client.post(url, json=payload)
                
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", str(error_data))
                    except Exception:
                        error_msg = response.text
                    
                    if response.status_code == 404:
                        raise ValueError(f"Ollama 返回 404 錯誤。這通常意味著找不到模型 '{active_model}'。請確保您已使用 'ollama pull {active_model}' 下載該模型。或檢查 Base URL 是否正確。")
                    else:
                        raise ValueError(f"Ollama API 錯誤 ({response.status_code}): {error_msg}")
                
                data = response.json()
                if "response" not in data:
                    raise ValueError(f"Unexpected response format from Ollama: {data}")
                
                return data["response"]
                
        except httpx.ConnectError:
            raise ConnectionError(f"Could not connect to Ollama at {self.base_url}. Please ensure Ollama is running and OLLAMA_HOST is set to 0.0.0.0 for LAN access.")
        except (httpx.ReadTimeout, httpx.WriteTimeout):
            raise TimeoutError(f"Ollama 請求逾時。模型 '{active_model}' 可能太大或您的硬體運算較慢，導致無法在 30 分鐘內完成 31 頁的詳細文稿。建議嘗試較小的模型（如 qwen2.5:14b 或 llama3.1:8b）。")
        except Exception as e:
            if not isinstance(e, (ValueError, ConnectionError, TimeoutError)):
                logger.error(f"Error calling Ollama API: {e}")
            raise
    
    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text to target language using Ollama.
        """
        prompt = f"""
Translate the following presentation script to {target_language}.
Preserve all formatting markers (e.g., "--- Slide X ---", "===").
Keep the structure exactly the same.
Return ONLY the translated text.

Original text:
{text}

Translated text:
"""
        return self.generate(prompt)
