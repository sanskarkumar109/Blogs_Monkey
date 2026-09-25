import re
from typing import List
from .parser import ContentBlock

class CodeDetector:
    """
    Detects code blocks in ContentBlocks, infers programming language, and preserves exact code structure.
    """

    LANGUAGE_PATTERNS = [
        ('python', r'^\s*(def\s+\w+\(|class\s+\w+:|import\s+\w+|from\s+\w+\s+import|print\(|if\s+__name__\s*==\s*[\'"]__main__[\'"]:)', re.MULTILINE),
        ('javascript', r'^\s*(const\s+\w+|let\s+\w+|var\s+\w+|function\s+\w+\(|export\s+default|console\.log\(|=>)', re.MULTILINE),
        ('html', r'^\s*<!DOCTYPE\s+html>|^\s*<(div|html|body|head|span|p|a|script|style)\b', re.MULTILINE | re.IGNORECASE),
        ('css', r'^\s*([\.#]?[\w\-]+\s*\{[^}]*\}|@media|@keyframes)', re.MULTILINE),
        ('sql', r'\b(SELECT\s+.*?\s+FROM|INSERT\s+INTO|UPDATE\s+.*?\s+SET|DELETE\s+FROM|CREATE\s+TABLE)\b', re.IGNORECASE),
        ('bash', r'^\s*(\$|#!\/bin\/bash|sudo\s+|apt\s+install|npm\s+install|pip\s+install|git\s+commit|cd\s+|ls\s+-)', re.MULTILINE),
        ('json', r'^\s*[\{\[]\s*["\']\w+["\']\s*:', re.MULTILINE),
        ('cpp', r'#include\s+<[\w\.]+>|std::cout|int\s+main\(\)', re.MULTILINE),
        ('java', r'public\s+class\s+\w+|System\.out\.println\(|public\s+static\s+void\s+main', re.MULTILINE),
    ]

    def detect_and_enhance(self, blocks: List[ContentBlock]) -> List[ContentBlock]:
        for block in blocks:
            if block.block_type == 'code_block':
                code_text = str(block.content)
                existing_lang = block.metadata.get('language', '').strip()

                if not existing_lang:
                    detected = self.infer_language(code_text)
                    block.metadata['language'] = detected
                else:
                    block.metadata['language'] = existing_lang.lower()

            elif block.block_type == 'paragraph':
                text = str(block.content)
                # Check if a paragraph block is actually raw code (e.g. pasted code without ```)
                if self._looks_like_raw_code(text):
                    inferred_lang = self.infer_language(text)
                    block.block_type = 'code_block'
                    block.metadata['language'] = inferred_lang

        return blocks

    def infer_language(self, code_str: str) -> str:
        code_str = code_str.strip()
        for lang, pattern, flags in self.LANGUAGE_PATTERNS:
            if re.search(pattern, code_str, flags):
                return lang
        return 'text'

    def _looks_like_raw_code(self, text: str) -> bool:
        lines = text.splitlines()
        if len(lines) < 2:
            return False
        
        indented_lines = sum(1 for line in lines if line.startswith('    ') or line.startswith('\t'))
        has_syntax_keywords = bool(re.search(r'\b(def|function|const|let|var|import|class|return|if|else|for|while)\b', text))
        
        return (indented_lines >= 2 and has_syntax_keywords) or (len(lines) >= 3 and has_syntax_keywords and ('{' in text or ';' in text or ':' in text))
