import re
from typing import List, Dict, Any
from .parser import ContentBlock

class AIAssistant:
    """
    Semantic NLP / AI analysis assistant for article structure, section suggestions, takeaways, and SEO optimization.
    Operates heuristically & semantically without hard external API locking, giving instantaneous author feedback.
    """

    ARTICLE_TYPES = {
        'tutorial': 'Tutorial / Technical Guide',
        'opinion': 'Opinion / Editorial',
        'news': 'News / Current Events',
        'listicle': 'Listicle',
        'case_study': 'Case Study / Research',
        'general': 'General Article'
    }

    def analyze(self, blocks: List[ContentBlock], title: str = "", current_seo_title: str = "", current_seo_desc: str = "", use_llm: bool = False, user=None) -> Dict[str, Any]:
        suggestions = []
        takeaways = []
        
        # 1. If LLM requested and available, attempt OpenRouter call via AIService
        if use_llm:
            try:
                from content.services import AIService
                ai_service = AIService()
                raw_text = " ".join(str(b.content) for b in blocks[:15])
                llm_res = ai_service.format_article(content=raw_text, title=title, user=user)
                if llm_res and not llm_res.get('is_fallback') and llm_res.get('ai_analysis'):
                    res_data = llm_res['ai_analysis']
                    paragraphs = [b for b in blocks if b.block_type == 'paragraph']
                    res_data['word_count'] = sum(len(str(b.content).split()) for b in paragraphs)
                    return res_data
            except Exception:
                pass  # Gracefully fall back to local heuristics below

        detected_type = self._classify_article_type(blocks, title)
        
        paragraphs = [b for b in blocks if b.block_type == 'paragraph']
        headings = [b for b in blocks if b.block_type == 'heading']
        code_blocks = [b for b in blocks if b.block_type == 'code_block']

        # 1. Missing Introduction check
        if not paragraphs or len(paragraphs[0].content.split()) < 15:
            suggestions.append({
                'type': 'missing_intro',
                'title': 'Suggested Improvement: Add Introduction',
                'message': 'Your article lacks a clear intro. Adding 2-3 sentences explaining what readers will learn improves engagement.',
                'action_label': 'Add Draft Intro'
            })

        # 2. Missing Conclusion check
        has_conclusion = any(h for h in headings if re.search(r'conclusion|summary|wrapping up|final thoughts', str(h.content), re.IGNORECASE))
        if len(paragraphs) > 4 and not has_conclusion:
            suggestions.append({
                'type': 'missing_conclusion',
                'title': 'Suggested Improvement: Add Conclusion',
                'message': 'Consider adding a short "Conclusion" section to summarize key outcomes for the reader.',
                'action_label': 'Add Conclusion Heading'
            })

        # 3. Key Takeaways Extraction
        if len(paragraphs) >= 3:
            takeaways = self._extract_key_takeaways(paragraphs, headings)

        # 4. SEO Suggestions
        seo_suggestions = {}
        if title:
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            if not current_seo_title:
                seo_suggestions['seo_title'] = clean_title[:70]
            if not current_seo_desc and paragraphs:
                first_para_text = re.sub(r'<[^>]+>', '', str(paragraphs[0].content)).strip()
                seo_suggestions['seo_description'] = first_para_text[:157] + ('...' if len(first_para_text) > 160 else '')

        return {
            'article_type': detected_type,
            'article_type_label': self.ARTICLE_TYPES.get(detected_type, 'General Article'),
            'suggestions': suggestions,
            'suggested_takeaways': takeaways,
            'seo_suggestions': seo_suggestions,
            'word_count': sum(len(str(b.content).split()) for b in paragraphs)
        }

    def _classify_article_type(self, blocks: List[ContentBlock], title: str) -> str:
        text_full = (title + " " + " ".join(str(b.content) for b in blocks)).lower()
        code_count = sum(1 for b in blocks if b.block_type == 'code_block')
        list_count = sum(1 for b in blocks if b.block_type == 'list')

        if code_count >= 2 or re.search(r'how to|tutorial|step-by-step|guide|install|building|setup', text_full):
            return 'tutorial'
        elif list_count >= 2 and re.search(r'\b\d+\s+(reasons|ways|tips|tools|best|top)\b', text_full):
            return 'listicle'
        elif re.search(r'my opinion|in my view|i think|why i believe|perspective', text_full):
            return 'opinion'
        elif re.search(r'case study|analysis|benchmark|performance results|research', text_full):
            return 'case_study'
        else:
            return 'general'

    def _extract_key_takeaways(self, paragraphs: List[ContentBlock], headings: List[ContentBlock]) -> List[str]:
        takeaways = []
        # Extract 2 to 4 salient points from paragraphs
        for p in paragraphs:
            text = str(p.content).strip()
            # Find sentences starting with key terms or active verbs
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for s in sentences:
                s_clean = s.strip()
                if 20 <= len(s_clean) <= 120 and not s_clean.startswith('http'):
                    if re.search(r'\b(key|important|main|always|remember|essential|first|solution)\b', s_clean, re.IGNORECASE):
                        takeaways.append(s_clean)
                        if len(takeaways) >= 3:
                            break
            if len(takeaways) >= 3:
                break

        if not takeaways and paragraphs:
            # Fallback to first sentences of initial paragraphs
            for p in paragraphs[:3]:
                s = str(p.content).strip().split('.')[0]
                if 20 <= len(s) <= 120:
                    takeaways.append(s + '.')

        return takeaways[:4]
