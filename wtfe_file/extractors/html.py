import re
from .base import BaseExtractor

HANDLES = [".html"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()

        tags = re.findall(r"<([a-zA-Z0-9]+)", src)
        scripts = re.findall(r"<script", src, re.IGNORECASE)
        forms = re.findall(r"<form", src, re.IGNORECASE)

        structures = {
            "tags": sorted(set(tags)),
            "script_blocks": len(scripts),
            "forms": len(forms)
        }

        signals = {
            "client_logic": bool(scripts),
            "user_input": bool(forms)
        }

        return self._create_fact("html", structures, signals)
