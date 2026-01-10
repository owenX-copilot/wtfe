import re
from .base import BaseExtractor

HANDLES = ["Dockerfile"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        froms = re.findall(r"^FROM\s+(.+)$", src, re.MULTILINE)
        expos = re.findall(r"^EXPOSE\s+(.+)$", src, re.MULTILINE)

        structures = {"from": froms, "expose": expos}

        signals = {"has_entrypoint": "ENTRYPOINT" in src or "CMD" in src}

        return self._create_fact("dockerfile", structures, signals)
