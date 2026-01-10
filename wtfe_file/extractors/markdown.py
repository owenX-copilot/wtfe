import re
from .base import BaseExtractor

HANDLES = [".md"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        headings = re.findall(r"^#+\s+(.+)$", src, re.MULTILINE)
        code_blocks = len(re.findall(r"```", src))

        structures = {"headings": headings[:10], "code_block_count": code_blocks}

        signals = {"has_install_steps": bool(re.search(r"install|usage|run", src, re.IGNORECASE))}

        return self._create_fact("markdown", structures, signals)
