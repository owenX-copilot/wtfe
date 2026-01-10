import re
from .base import BaseExtractor

HANDLES = [".java"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()

        classes = re.findall(r"class\s+(\w+)", src)
        methods = re.findall(r"(public|private|protected)\s+[\w<>]+\s+(\w+)\(", src)
        imports = re.findall(r"import\s+([\w\.]+);", src)

        structures = {
            "classes": classes,
            "methods": [m[1] for m in methods]
        }

        signals = {
            "imports": imports,
            "entry_point": bool("public static void main" in src)
        }

        return self._create_fact("java", structures, signals)
