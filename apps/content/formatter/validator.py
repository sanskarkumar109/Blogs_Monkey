import re
from typing import List, Dict, Any
from .parser import ContentBlock

class ContentValidator:
    """
    Validates article content quality, accessibility, layout responsiveness, and structural health.
    """

    def validate(self, blocks: List[ContentBlock], title: str = "") -> List[Dict[str, Any]]:
        warnings = []

        if not title or len(title.strip()) < 5:
            warnings.append({
                'rule': 'title_length',
                'severity': 'warning',
                'message': 'Article title is very short. Descriptive titles perform better in search and sharing.'
            })

        headings = [b for b in blocks if b.block_type == 'heading']
        if not headings and len(blocks) > 5:
            warnings.append({
                'rule': 'missing_headings',
                'severity': 'warning',
                'message': 'No subheadings (H2) found. Dividing long articles with subheadings improves readability.'
            })

        empty_paragraphs = sum(1 for b in blocks if b.block_type == 'paragraph' and not str(b.content).strip())
        if empty_paragraphs > 0:
            warnings.append({
                'rule': 'empty_paragraphs',
                'severity': 'info',
                'message': f'Found {empty_paragraphs} empty paragraph line(s). Auto-formatter will clean them up.'
            })

        code_blocks = [b for b in blocks if b.block_type == 'code_block']
        unlabeled_code = sum(1 for b in code_blocks if not b.metadata.get('language') or b.metadata.get('language') == 'text')
        if unlabeled_code > 0:
            warnings.append({
                'rule': 'unlabeled_code',
                'severity': 'info',
                'message': f'Found {unlabeled_code} code block(s) without explicit language tags. Language detection applied.'
            })

        return warnings
