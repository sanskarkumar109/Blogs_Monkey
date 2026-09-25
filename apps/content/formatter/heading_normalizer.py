import re
from typing import List
from django.utils.text import slugify
from .parser import ContentBlock

class HeadingNormalizer:
    """
    Normalizes heading hierarchy across ContentBlocks.
    Rules:
    - Maximum one H1 (or normalize top sections to H2 if H1 is article title).
    - Ensures clean sequential progression (e.g., H2 -> H3 -> H3 -> H2).
    - Adds slugified anchor IDs to headings for deep-linking and TOC linking.
    """

    def normalize(self, blocks: List[ContentBlock], title: str = "") -> List[ContentBlock]:
        used_slugs = set()
        heading_blocks = [b for b in blocks if b.block_type == 'heading']

        if not heading_blocks:
            return blocks

        # Check if the first heading matches the article title or if there are multiple H1s
        h1_count = sum(1 for b in heading_blocks if b.metadata.get('level') == 1)

        for block in blocks:
            if block.block_type == 'heading':
                level = block.metadata.get('level', 2)
                text = str(block.content).strip()

                # Rule: Convert H1 to H2 if there are multiple H1s or if text matches title
                if level == 1 and (h1_count > 1 or (title and slugify(text) == slugify(title))):
                    level = 2

                # Enforce level range 2..4 for content sections
                level = max(2, min(4, level))
                block.metadata['level'] = level

                # Generate unique slugified anchor ID
                base_slug = slugify(text) or "section"
                slug = base_slug
                counter = 1
                while slug in used_slugs:
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                used_slugs.add(slug)
                block.metadata['anchor_id'] = slug

        # Smooth out hierarchy jumps (e.g., H2 -> H4 becomes H2 -> H3)
        current_level = 2
        for block in blocks:
            if block.block_type == 'heading':
                level = block.metadata.get('level', 2)
                if level > current_level + 1:
                    level = current_level + 1
                    block.metadata['level'] = level
                current_level = level

        return blocks
