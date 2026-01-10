import re
from .base import BaseExtractor

HANDLES = [".ts", ".tsx"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        types = bool(re.search(r":\s*\w+<|interface|type\s+\w+", src))
        jsx = "<" in src and ">" in src and ("React" in src or "jsx" in src.lower())

        structures = {
            "imports": re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", src),
        }

        signals = {
            "typescript": types,
            "jsx": jsx,
        }

        return self._create_fact("typescript", structures, signals)
