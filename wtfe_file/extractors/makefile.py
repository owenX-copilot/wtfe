import re
from .base import BaseExtractor

HANDLES = ["Makefile", "makefile"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        targets = re.findall(r"^([a-zA-Z0-9_\-]+)\s*:\s*", src, re.MULTILINE)

        structures = {"targets": targets[:20]}
        signals = {"has_default_target": any(t == "all" for t in targets)}

        return self._create_fact("makefile", structures, signals)
