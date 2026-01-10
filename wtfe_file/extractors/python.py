import ast
import re
from .base import BaseExtractor

HANDLES = [".py"]


class Extractor(BaseExtractor):
    def extract(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()

        tree = ast.parse(source)

        classes = []
        functions = []
        globals_ = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        globals_.append(target.id)
            elif isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        structures = {
            "classes": classes,
            "functions": functions,
            "globals": globals_
        }

        signals = {
            "imports": imports,
            "network": self._detect_network(source),
            "io": self._detect_io(source),
            "entry_point": self._detect_entry_point(source)
        }

        return self._create_fact("python", structures, signals)

    def _detect_network(self, src):
        keywords = ["requests.", "http.client", "socket"]
        return [k for k in keywords if k in src]

    def _detect_io(self, src):
        return ["open()"] if "open(" in src else []

    def _detect_entry_point(self, src):
        return bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', src))
