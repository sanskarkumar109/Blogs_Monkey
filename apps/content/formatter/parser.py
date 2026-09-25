import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ContentBlock:
    block_type: str  # heading, paragraph, code_block, list, blockquote, callout, table, key_takeaways, faq, divider
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

class ContentParser:
    """
    Parses raw article content (Markdown, plain text, or rough HTML) into an abstract list of ContentBlock objects.
    """

    def __init__(self, raw_content: str):
        self.raw_content = raw_content.strip() if raw_content else ""

    def parse(self) -> List[ContentBlock]:
        if not self.raw_content:
            return []

        # Check if content is primarily HTML or plain/markdown text
        if re.search(r'<(h[1-6]|p|div|pre|ul|ol|table|blockquote)[^>]*>', self.raw_content, re.IGNORECASE):
            return self._parse_html(self.raw_content)
        else:
            return self._parse_text_or_markdown(self.raw_content)

    def _parse_text_or_markdown(self, text: str) -> List[ContentBlock]:
        blocks = []
        lines = text.splitlines()
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].rstrip()

            if not line.strip():
                i += 1
                continue

            # Code Fences (```lang ... ```)
            if line.strip().startswith('```'):
                lang = line.strip().lstrip('`').strip()
                code_lines = []
                i += 1
                while i < n and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                if i < n and lines[i].strip().startswith('```'):
                    i += 1
                code_text = "\n".join(code_lines)
                blocks.append(ContentBlock('code_block', code_text, {'language': lang}))
                continue

            # Markdown Headings (# Heading)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                blocks.append(ContentBlock('heading', heading_text, {'level': level}))
                i += 1
                continue

            # Horizontal Rule / Divider
            if re.match(r'^---+$|^\*\*\*+$|^___+$', line.strip()):
                blocks.append(ContentBlock('divider', ''))
                i += 1
                continue

            # Callout Patterns (e.g. Important:, Warning:, Tip:, Note:, Pro Tip:)
            callout_match = re.match(r'^(Important|Warning|Tip|Note|Pro Tip|CAUTION):\s*(.+)$', line.strip(), re.IGNORECASE)
            if callout_match:
                c_type = callout_match.group(1).lower().replace(' ', '_')
                c_text = callout_match.group(2).strip()
                blocks.append(ContentBlock('callout', c_text, {'callout_type': c_type, 'title': callout_match.group(1).upper()}))
                i += 1
                continue

            # Blockquotes (> Quote)
            if line.strip().startswith('>'):
                quote_lines = [line.strip().lstrip('>').strip()]
                i += 1
                while i < n and lines[i].strip().startswith('>'):
                    quote_lines.append(lines[i].strip().lstrip('>').strip())
                    i += 1
                blocks.append(ContentBlock('blockquote', "\n".join(quote_lines)))
                continue

            # Numbered or Bullet Lists
            list_match = re.match(r'^(\d+[\.\)]|[\*\-\•])\s+(.+)$', line.strip())
            if list_match:
                list_type = 'ol' if re.match(r'^\d+', list_match.group(1)) else 'ul'
                items = [list_match.group(2).strip()]
                i += 1
                while i < n:
                    sub_match = re.match(r'^(\d+[\.\)]|[\*\-\•])\s+(.+)$', lines[i].strip())
                    if sub_match:
                        items.append(sub_match.group(2).strip())
                        i += 1
                    elif lines[i].startswith('  ') or lines[i].startswith('\t'):
                        # Continuation line
                        items[-1] += " " + lines[i].strip()
                        i += 1
                    else:
                        break
                blocks.append(ContentBlock('list', items, {'list_type': list_type}))
                continue

            # Key Takeaways Section Block
            if re.match(r'^(Key Takeaways|Summary Points|Highlights):', line.strip(), re.IGNORECASE):
                takeaway_lines = []
                i += 1
                while i < n and (re.match(r'^[\*\-\•]\s+', lines[i].strip()) or not lines[i].strip()):
                    if lines[i].strip():
                        takeaway_lines.append(re.sub(r'^[\*\-\•]\s+', '', lines[i].strip()))
                    i += 1
                blocks.append(ContentBlock('key_takeaways', takeaway_lines))
                continue

            # FAQ Block (Q: ... A: ...)
            if re.match(r'^Q:\s*(.+)$', line.strip(), re.IGNORECASE):
                q_text = re.sub(r'^Q:\s*', '', line.strip(), flags=re.IGNORECASE)
                a_text = ""
                i += 1
                if i < n and re.match(r'^A:\s*(.+)$', lines[i].strip(), re.IGNORECASE):
                    a_text = re.sub(r'^A:\s*', '', lines[i].strip(), flags=re.IGNORECASE)
                    i += 1
                blocks.append(ContentBlock('faq', [{'question': q_text, 'answer': a_text}]))
                continue

            # Tables (Markdown Table Format | col1 | col2 |)
            if '|' in line and line.strip().startswith('|') and line.strip().endswith('|'):
                table_lines = [line.strip()]
                i += 1
                while i < n and '|' in lines[i] and lines[i].strip().startswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                table_data = self._parse_markdown_table(table_lines)
                if table_data:
                    blocks.append(ContentBlock('table', table_data))
                    continue

            # Default: Paragraph block
            para_lines = [line.strip()]
            i += 1
            while i < n and lines[i].strip() and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('```') and not lines[i].strip().startswith('>'):
                para_lines.append(lines[i].strip())
                i += 1
            blocks.append(ContentBlock('paragraph', " ".join(para_lines)))

        return blocks

    def _parse_html(self, html: str) -> List[ContentBlock]:
        """
        Parses HTML string into ContentBlock representations.
        """
        blocks = []
        # Split by top-level HTML tags
        tag_pattern = r'(<h[1-6][^>]*>.*?</h[1-6]>|<pre[^>]*>.*?</pre>|<blockquote[^>]*>.*?</blockquote>|<ul[^>]*>.*?</ul>|<ol[^>]*>.*?</ol>|<table[^>]*>.*?</table>|<p[^>]*>.*?</p>|<hr/?>)'
        tokens = re.split(tag_pattern, html, flags=re.DOTALL | re.IGNORECASE)

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            h_match = re.match(r'<h([1-6])(?:[^>]*id=["\']([^"\']+)["\'])?[^>]*>(.*?)</h\1>', token, re.DOTALL | re.IGNORECASE)
            if h_match:
                level = int(h_match.group(1))
                clean_text = re.sub(r'<[^>]+>', '', h_match.group(3)).strip()
                blocks.append(ContentBlock('heading', clean_text, {'level': level}))
                continue

            pre_match = re.match(r'<pre[^>]*><code(?:[^>]*class=["\'](.*?)["\'])?[^>]*>(.*?)</code></pre>', token, re.DOTALL | re.IGNORECASE)
            if pre_match:
                cls = pre_match.group(1) or ""
                lang_match = re.search(r'language-([a-zA-Z0-9_\-]+)', cls)
                lang = lang_match.group(1) if lang_match else ""
                code_content = pre_match.group(2).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                blocks.append(ContentBlock('code_block', code_content, {'language': lang}))
                continue

            quote_match = re.match(r'<blockquote[^>]*>(.*?)</blockquote>', token, re.DOTALL | re.IGNORECASE)
            if quote_match:
                clean_text = re.sub(r'<[^>]+>', '', quote_match.group(1)).strip()
                blocks.append(ContentBlock('blockquote', clean_text))
                continue

            list_match = re.match(r'<(ul|ol)[^>]*>(.*?)</\1>', token, re.DOTALL | re.IGNORECASE)
            if list_match:
                l_type = list_match.group(1).lower()
                items = re.findall(r'<li[^>]*>(.*?)</li>', list_match.group(2), re.DOTALL | re.IGNORECASE)
                clean_items = [re.sub(r'<[^>]+>', '', item).strip() for item in items]
                blocks.append(ContentBlock('list', clean_items, {'list_type': l_type}))
                continue

            p_match = re.match(r'<p[^>]*>(.*?)</p>', token, re.DOTALL | re.IGNORECASE)
            if p_match:
                p_inner = p_match.group(1).strip()
                # Check callout inside paragraph
                c_match = re.match(r'^(Important|Warning|Tip|Note|Pro Tip):\s*(.+)$', re.sub(r'<[^>]+>', '', p_inner), re.IGNORECASE)
                if c_match:
                    blocks.append(ContentBlock('callout', c_match.group(2).strip(), {'callout_type': c_match.group(1).lower(), 'title': c_match.group(1).upper()}))
                else:
                    blocks.append(ContentBlock('paragraph', p_inner))
                continue

            # Fallback for plain text fragments
            clean_fragment = re.sub(r'<[^>]+>', '', token).strip()
            if clean_fragment:
                blocks.append(ContentBlock('paragraph', clean_fragment))

        return blocks

    def _parse_markdown_table(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        headers = []
        rows = []
        for index, line in enumerate(lines):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if index == 0:
                headers = cells
            elif index == 1 and all(set(cell) <= set('-: ') for cell in cells):
                # Separator line
                continue
            else:
                rows.append(cells)
        if headers:
            return {'headers': headers, 'rows': rows}
        return None
