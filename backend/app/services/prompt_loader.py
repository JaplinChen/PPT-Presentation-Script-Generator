from pathlib import Path
from typing import Dict

class PromptLoader:
    """載入與處理 Prompt 模板的工具類"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")
    
    def load_prompt(self, template_name: str, variables: Dict[str, str] = None) -> str:
        """
        載入 Prompt 模板並替換變數
        
        Args:
            template_name: 模板名稱（不含 .md 副檔名）
            variables: 要替換的變數字典，格式為 {key: value}
            
        Returns:
            處理後的 Prompt 文字
        """
        template_path = self.prompts_dir / f"{template_name}.md"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 替換變數
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                template = template.replace(placeholder, str(value))
        
        return template
    
    def get_available_templates(self) -> list:
        """取得所有可用的模板名稱"""
        return [f.stem for f in self.prompts_dir.glob("*.md")]
