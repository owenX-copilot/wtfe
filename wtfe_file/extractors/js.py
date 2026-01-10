import re
from .base import BaseExtractor

HANDLES = [".js", ".jsx"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        imports = re.findall(r"(?:import\s+[\w\s{},*]+from\s+['\"]([^'\"]+)['\"])|(?:require\(['\"]([^'\"]+)['\"]\))", src)
        flat = [i for tup in imports for i in tup if i]
        uses_express = "express" in src
        uses_react = "react" in src or "from 'react'" in src or 'from "react"' in src

        structures = {
            "imports": flat,
            "functions": re.findall(r"function\s+(\w+)\s*\(", src),
            "classes": re.findall(r"class\s+(\w+)", src),
        }

        signals = {
            "commonjs": "module.exports" in src or "exports." in src,
            "esm": "import " in src,
            "express": uses_express,
            "react": uses_react,
        }

        return self._create_fact("javascript", structures, signals)
