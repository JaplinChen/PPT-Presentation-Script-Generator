"""
Script parser for converting generated text into structured format.
"""
import re
from typing import Dict, List

class ScriptParser:
    """Parses generated scripts into structured slide-by-slide format"""
    
    @staticmethod
    def parse_script(full_script: str, slides: List[Dict], include_transitions: bool = True) -> Dict:
        """
        Parse generated script text into structured format.
        
        Args:
            full_script: The full generated script text
            slides: Original slide data for reference
            include_transitions: Whether transitions were included
            
        Returns:
            Dict with 'opening', 'slides', and 'full_script' keys
        """
        # Extract sections using markers
        sections = ScriptParser._extract_sections(full_script)
        
        # Parse opening
        opening = ""
        for sec in sections:
            if "opening" in sec["header"] or "開場" in sec["header"]:
                opening = sec["content"]
                break
        
        # If no opening found with marker, but there are more sections than slides,
        # the first section might be the opening
        if not opening and len(sections) > len(slides) and len(sections) > 0:
            opening = sections[0]["content"]

        # Parse slide sections
        slide_scripts = []
        for i, slide in enumerate(slides):
            slide_no = slide.get("slide_no", i + 1)
            
            # Find matching section
            script_text = ScriptParser._find_slide_script(sections, slide_no)
            
            if not script_text:
                script_text = f"(Slide {slide_no} - No script generated)"
            
            # Split into sentences for segments
            segments = ScriptParser._split_into_segments(script_text)
            
            slide_scripts.append({
                "slide_no": str(slide_no),  # Convert to string for API model
                "title": slide.get("title", ""),
                "script": script_text,
                "segments": segments
            })
        
        return {
            "opening": opening,
            "slide_scripts": slide_scripts,
            "full_script": full_script,
            "metadata": {
                "total_slides": len(slides),
                "has_opening": bool(opening),
                "parser_version": "2.0"
            }
        }
    
    @staticmethod
    def _extract_sections(text: str) -> List[Dict[str, str]]:
        """
        Extract sections from script text by looking for slide markers line by line.
        """
        lines = text.split('\n')
        sections = []
        current_header = "opening"
        current_content = []

        # Patterns to look for in a line to identify it as a header
        # 1. Opening/開場
        # 2. Slide X or 投影片 X or 第 X 頁
        # 3. Just "X" surrounded by markers like === 5 === or --- 5 ---
        opening_pattern = re.compile(r'^[\s#\-=*]*\s*(Opening|開場)[\s#\-=*:：]*$', re.IGNORECASE)
        slide_pattern = re.compile(r'^[\s#\-=*]*(?:Slide|投影片)\s*(\d+)[\s#\-=*]*$', re.IGNORECASE)
        fallback_num_pattern = re.compile(r'^[\s#\-=*]+(\d+)[\s#\-=*]+$', re.IGNORECASE)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_content:
                    current_content.append("")
                continue

            # Check for header matches
            is_header = False
            new_header = ""

            if opening_pattern.match(stripped):
                is_header = True
                new_header = "opening"
            else:
                slide_match = slide_pattern.match(stripped)
                if slide_match:
                    is_header = True
                    new_header = f"slide {slide_match.group(1)}"
                else:
                    num_match = fallback_num_pattern.match(stripped)
                    if num_match:
                        is_header = True
                        new_header = f"slide {num_match.group(1)}"

            if is_header:
                # Save previous section
                if current_content:
                    sections.append({
                        "header": current_header,
                        "content": "\n".join(current_content).strip()
                    })
                current_header = new_header
                current_content = []
            else:
                current_content.append(line)

        # Add the last section
        if current_content:
            sections.append({
                "header": current_header,
                "content": "\n".join(current_content).strip()
            })

        # Final cleanup: if first section is "opening" and empty, remove it
        if sections and sections[0]["header"] == "opening" and not sections[0]["content"]:
            sections.pop(0)

        return sections

    @staticmethod
    def _find_slide_script(sections: List[Dict[str, str]], slide_no: int) -> str:
        """Find the script section for a specific slide number"""
        # 1. Search by keyword in header
        search_terms = [f"slide {slide_no}", f"投影片 {slide_no}", str(slide_no)]
        for sec in sections:
            header = sec["header"]
            if any(term == header or f"slide {term}" in header or f"slide{term}" in header for term in search_terms):
                return sec["content"]
        
        # 2. Search for the first numerical value in the header and compare
        for sec in sections:
            header_numbers = re.findall(r'\d+', sec["header"])
            if header_numbers and int(header_numbers[0]) == slide_no:
                return sec["content"]
        
        return ""
    
    @staticmethod
    def _split_into_segments(text: str) -> List[Dict]:
        """
        Split script text into sentence segments.
        Each segment represents a logical speaking unit.
        """
        if not text:
            return []
        
        # Split by sentence endings
        sentences = re.split(r'([。！？.!?])', text)
        
        segments = []
        current = ""
        
        for i, part in enumerate(sentences):
            current += part
            
            # If this is a sentence ending, create a segment
            if part in '。！？.!?':
                cleaned = current.strip()
                if cleaned and len(cleaned) > 2:
                    segments.append({
                        "text": cleaned,
                        "type": "content"
                    })
                current = ""
        
        # Add any remaining text
        if current.strip():
            segments.append({
                "text": current.strip(),
                "type": "content"
            })
        
        return segments if segments else [{"text": text, "type": "content"}]
