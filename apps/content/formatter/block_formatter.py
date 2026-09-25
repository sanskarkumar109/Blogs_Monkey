import html
from typing import List, Dict, Any, Tuple
from .parser import ContentBlock

class BlockFormatter:
    """
    Renders structured ContentBlocks into standard, responsive, semantic HTML.
    Generates Table of Contents (TOC) when applicable.
    """

    def render(self, blocks: List[ContentBlock], title: str = "") -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        html_parts = []
        toc_items = []
        stats = {
            'headings_count': 0,
            'code_blocks_count': 0,
            'lists_count': 0,
            'tables_count': 0,
            'callouts_count': 0,
            'toc_generated': False
        }

        # First pass: collect TOC items from H2 & H3 headings
        for block in blocks:
            if block.block_type == 'heading':
                stats['headings_count'] += 1
                level = block.metadata.get('level', 2)
                anchor = block.metadata.get('anchor_id', '')
                text = str(block.content)
                if level in (2, 3) and anchor:
                    toc_items.append({'level': level, 'text': text, 'anchor': anchor})

        # Insert Table of Contents if article has 3+ H2 sections
        h2_count = sum(1 for item in toc_items if item['level'] == 2)
        if h2_count >= 3:
            stats['toc_generated'] = True
            html_parts.append(self._render_toc(toc_items))

        # Second pass: render HTML blocks
        for block in blocks:
            b_type = block.block_type

            if b_type == 'heading':
                level = block.metadata.get('level', 2)
                anchor = block.metadata.get('anchor_id', '')
                text = html.escape(str(block.content))
                html_parts.append(f'<h{level} id="{anchor}" class="font-serif text-[#1a1a1a] dark:text-[#faf9f7] scroll-mt-20 mt-8 mb-4">{text}</h{level}>')

            elif b_type == 'paragraph':
                text = str(block.content)
                html_parts.append(f'<p class="text-[#1a1a1a] dark:text-[#e5e2dc] text-sm leading-relaxed mb-4">{text}</p>')

            elif b_type == 'code_block':
                stats['code_blocks_count'] += 1
                lang = block.metadata.get('language', 'text')
                code_text = html.escape(str(block.content))
                html_parts.append(
                    f'<div class="relative group my-6 rounded-md overflow-hidden bg-[#151413] border border-[#2e2c2a]">'
                    f'  <div class="flex items-center justify-between px-4 py-1.5 bg-[#1e1d1c] border-b border-[#2e2c2a] text-[11px] font-mono text-[#9c9690]">'
                    f'    <span>{lang.upper()}</span>'
                    f'    <button type="button" onclick="navigator.clipboard.writeText(this.closest(\'.group\').querySelector(\'code\').innerText); this.innerText=\'Copied!\'; setTimeout(() => this.innerText=\'Copy\', 2000);" class="hover:text-[#faf9f7] transition">Copy</button>'
                    f'  </div>'
                    f'  <pre class="p-4 overflow-x-auto text-xs font-mono text-[#e5e2dc] leading-relaxed"><code class="language-{lang}">{code_text}</code></pre>'
                    f'</div>'
                )

            elif b_type == 'list':
                stats['lists_count'] += 1
                l_type = block.metadata.get('list_type', 'ul')
                items = block.content
                items_html = "".join([f'<li class="mb-1.5">{html.escape(item)}</li>' for item in items])
                tag = 'ol' if l_type == 'ol' else 'ul'
                cls = 'list-decimal pl-5 space-y-1 mb-4 text-sm text-[#1a1a1a] dark:text-[#e5e2dc]' if l_type == 'ol' else 'list-disc pl-5 space-y-1 mb-4 text-sm text-[#1a1a1a] dark:text-[#e5e2dc]'
                html_parts.append(f'<{tag} class="{cls}">{items_html}</{tag}>')

            elif b_type == 'blockquote':
                text = html.escape(str(block.content))
                html_parts.append(f'<blockquote class="border-l-2 border-[#b85c38] pl-4 italic text-[#6b6560] dark:text-[#9c9690] my-4 text-sm">{text}</blockquote>')

            elif b_type == 'callout':
                stats['callouts_count'] += 1
                c_type = block.metadata.get('callout_type', 'note')
                title = block.metadata.get('title', 'NOTE')
                text = html.escape(str(block.content))
                
                border_cls = "border-[#b85c38] bg-[#b85c38]/5 text-[#b85c38]" if c_type in ('important', 'warning') else "border-[#2d7a4f] bg-[#2d7a4f]/5 text-[#2d7a4f]"
                
                html_parts.append(
                    f'<div class="p-4 my-6 rounded-md border-l-4 {border_cls} bg-[#faf9f7] dark:bg-[#1e1d1c] shadow-xs">'
                    f'  <span class="block text-[11px] font-medium uppercase tracking-wider mb-1">{title}</span>'
                    f'  <p class="text-xs text-[#1a1a1a] dark:text-[#faf9f7] leading-relaxed">{text}</p>'
                    f'</div>'
                )

            elif b_type == 'table':
                stats['tables_count'] += 1
                table_data = block.content
                headers = table_data.get('headers', [])
                rows = table_data.get('rows', [])
                
                th_html = "".join([f'<th class="px-4 py-2 border-b border-[#e8e4de] dark:border-[#2e2c2a] bg-[#faf9f7] dark:bg-[#151413] text-xs font-medium text-[#1a1a1a] dark:text-[#faf9f7]">{html.escape(h)}</th>' for h in headers])
                tr_htmls = []
                for row in rows:
                    tds = "".join([f'<td class="px-4 py-2 border-b border-[#e8e4de] dark:border-[#2e2c2a] text-xs text-[#6b6560] dark:text-[#9c9690]">{html.escape(c)}</td>' for c in row])
                    tr_htmls.append(f'<tr class="hover:bg-[#faf9f7]/50 dark:hover:bg-[#292725]/50">{tds}</tr>')

                html_parts.append(
                    f'<div class="my-6 overflow-x-auto rounded-md border border-[#e8e4de] dark:border-[#2e2c2a]">'
                    f'  <table class="w-full text-left border-collapse">'
                    f'    <thead><tr>{th_html}</tr></thead>'
                    f'    <tbody>{"".join(tr_htmls)}</tbody>'
                    f'  </table>'
                    f'</div>'
                )

            elif b_type == 'key_takeaways':
                points = block.content
                points_html = "".join([f'<li class="flex items-start gap-2"><span class="text-[#b85c38]">•</span><span>{html.escape(pt)}</span></li>' for pt in points])
                html_parts.append(
                    f'<div class="p-5 my-6 rounded-md bg-[#faf9f7] dark:bg-[#1e1d1c] border border-[#e8e4de] dark:border-[#2e2c2a] space-y-2">'
                    f'  <h3 class="font-serif font-medium text-sm text-[#1a1a1a] dark:text-[#faf9f7] uppercase tracking-wider">Key Takeaways</h3>'
                    f'  <ul class="text-xs text-[#6b6560] dark:text-[#9c9690] space-y-1.5">{points_html}</ul>'
                    f'</div>'
                )

            elif b_type == 'faq':
                qa_list = block.content
                qa_htmls = []
                for item in qa_list:
                    q = html.escape(item.get('question', ''))
                    a = html.escape(item.get('answer', ''))
                    qa_htmls.append(
                        f'<div class="py-3 border-b border-[#e8e4de] dark:border-[#2e2c2a] last:border-b-0">'
                        f'  <h4 class="font-medium text-xs text-[#1a1a1a] dark:text-[#faf9f7] mb-1">Q: {q}</h4>'
                        f'  <p class="text-xs text-[#6b6560] dark:text-[#9c9690] leading-relaxed">A: {a}</p>'
                        f'</div>'
                    )
                html_parts.append(
                    f'<div class="my-8 p-5 rounded-md bg-white dark:bg-[#1e1d1c] border border-[#e8e4de] dark:border-[#2e2c2a]">'
                    f'  <h3 class="font-serif font-medium text-base text-[#1a1a1a] dark:text-[#faf9f7] mb-3">Frequently Asked Questions</h3>'
                    f'  <div>{"".join(qa_htmls)}</div>'
                    f'</div>'
                )

            elif b_type == 'divider':
                html_parts.append('<hr class="my-8 border-[#e8e4de] dark:border-[#2e2c2a]" />')

        full_html = "\n".join(html_parts)
        return full_html, toc_items, stats

    def _render_toc(self, toc_items: List[Dict[str, Any]]) -> str:
        links_html = []
        for item in toc_items:
            indent_cls = "pl-4" if item['level'] == 3 else ""
            link = f'<li class="{indent_cls}"><a href="#{item["anchor"]}" class="text-xs text-[#6b6560] dark:text-[#9c9690] hover:text-[#b85c38] transition">{html.escape(item["text"])}</a></li>'
            links_html.append(link)

        return (
            f'<div class="my-8 p-5 rounded-md bg-[#faf9f7] dark:bg-[#151413] border border-[#e8e4de] dark:border-[#2e2c2a] space-y-3">'
            f'  <h3 class="font-serif font-medium text-xs text-[#1a1a1a] dark:text-[#faf9f7] uppercase tracking-wider">Table of Contents</h3>'
            f'  <ul class="space-y-1.5 list-none">{ "".join(links_html) }</ul>'
            f'</div>'
        )
