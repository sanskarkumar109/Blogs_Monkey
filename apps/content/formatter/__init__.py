import nh3
from typing import Dict, Any
from .parser import ContentParser
from .heading_normalizer import HeadingNormalizer
from .code_detector import CodeDetector
from .block_formatter import BlockFormatter
from .ai_assistant import AIAssistant
from .validator import ContentValidator

def format_article(
    content: str,
    mode: str = 'smart',  # 'manual', 'smart', 'ai'
    title: str = "",
    seo_title: str = "",
    seo_desc: str = "",
    user = None
) -> Dict[str, Any]:
    """
    Main entrypoint for the Smart Standard Article Formatter.
    Returns formatted HTML, TOC, changes stats, AI suggestions, and validation report.
    """
    if not content or not content.strip():
        return {
            'formatted_html': '',
            'toc': [],
            'stats': {},
            'suggestions': [],
            'warnings': [],
            'ai_analysis': {}
        }

    # 1. Parse raw content into ContentBlocks
    parser = ContentParser(content)
    blocks = parser.parse()

    # 2. Heading Hierarchy Normalization
    normalizer = HeadingNormalizer()
    blocks = normalizer.normalize(blocks, title=title)

    # 3. Code Detection & Language Inference
    code_detector = CodeDetector()
    blocks = code_detector.detect_and_enhance(blocks)

    # 4. Block HTML Assembly & TOC Generation
    block_formatter = BlockFormatter()
    formatted_html, toc_items, stats = block_formatter.render(blocks, title=title)

    # 5. Sanitize HTML output with nh3 against XSS
    allowed_tags = {
        'a', 'b', 'blockquote', 'code', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'i', 'img', 'li', 'ol', 'p', 'pre', 'strong', 'ul', 'span', 'div', 'br', 'hr',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'mark', 'section', 'article', 'button'
    }
    allowed_attrs = {
        'a': {'href', 'title', 'target', 'rel', 'class'},
        'img': {'src', 'alt', 'title', 'width', 'height', 'class', 'loading'},
        'code': {'class', 'data-lang'},
        'pre': {'class'},
        'button': {'type', 'onclick', 'class'},
        '*': {'class', 'style', 'id', 'data-*'}
    }
    sanitized_html = nh3.clean(formatted_html, tags=allowed_tags, attributes=allowed_attrs, link_rel=None)

    # 6. Quality Validation
    validator = ContentValidator()
    warnings = validator.validate(blocks, title=title)

    # 7. AI Semantic Analysis (Mode == 'ai' or 'smart')
    ai_assistant = AIAssistant()
    use_llm = (mode == 'ai')
    ai_analysis = ai_assistant.analyze(
        blocks,
        title=title,
        current_seo_title=seo_title,
        current_seo_desc=seo_desc,
        use_llm=use_llm,
        user=user
    )

    return {
        'formatted_html': sanitized_html,
        'toc': toc_items,
        'stats': stats,
        'warnings': warnings,
        'ai_analysis': ai_analysis,
        'mode': mode
    }
