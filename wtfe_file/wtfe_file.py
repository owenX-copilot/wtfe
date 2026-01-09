import sys
import os
import json
import ast
import re
from pathlib import Path

# Import core models
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import FileFact, Evidence, FileRole

# ---------- Base Extractor ----------

class BaseExtractor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

    def extract(self) -> FileFact:
        """Extract facts and return FileFact object."""
        raise NotImplementedError
    
    def _create_fact(self, language: str, structures: dict, signals: dict) -> FileFact:
        """Helper to create FileFact with basic role inference."""
        fact = FileFact(
            path=self.filepath,
            filename=self.filename,
            language=language,
            structures=structures,
            signals=signals
        )
        
        # Basic role inference
        fact.roles = self._infer_roles(structures, signals)
        fact.confidence = self._calculate_confidence(structures, signals)
        
        return fact
    
    def _infer_roles(self, structures: dict, signals: dict) -> list:
        """Infer file roles from structures and signals."""
        roles = []
        
        # Test file detection
        if any(kw in self.filename.lower() for kw in ["test_", "_test", "spec_"]):
            roles.append(FileRole.TEST)
        
        # Config file detection
        if self.filename.lower() in ["config.py", "settings.py", "config.json", "config.yml"]:
            roles.append(FileRole.CONFIG)
        
        # Entry point detection
        if signals.get("entry_point") or "main" in structures.get("functions", []):
            roles.append(FileRole.ENTRY_POINT)
        
        # Service detection (network + no main)
        if signals.get("network") and not signals.get("entry_point"):
            roles.append(FileRole.SERVICE)
        
        # CLI detection
        if any(lib in signals.get("imports", []) for lib in ["argparse", "click", "typer"]):
            roles.append(FileRole.CLI)
        
        if not roles:
            roles.append(FileRole.UNKNOWN)
        
        return roles
    
    def _calculate_confidence(self, structures: dict, signals: dict) -> float:
        """Calculate confidence score based on extracted facts."""
        confidence = 0.5  # baseline
        
        # More structures = higher confidence
        if structures.get("classes"):
            confidence += 0.1
        if structures.get("functions"):
            confidence += 0.1
        
        # Clear signals boost confidence
        if signals.get("imports"):
            confidence += 0.1
        if signals.get("entry_point"):
            confidence += 0.2
        
        return min(confidence, 1.0)


# ---------- Python Extractor ----------

class PythonExtractor(BaseExtractor):
    def extract(self) -> FileFact:
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


# ---------- HTML Extractor ----------

class HtmlExtractor(BaseExtractor):
    def extract(self) -> FileFact:
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


# ---------- Java Extractor ----------

class JavaExtractor(BaseExtractor):
    def extract(self) -> FileFact:
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


# ---------- JS Extractor ----------

class JsExtractor(BaseExtractor):
    def extract(self) -> FileFact:
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


# ---------- TS Extractor ----------

class TsExtractor(BaseExtractor):
    def extract(self) -> FileFact:
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


# ---------- JSON Extractor ----------

class JsonExtractor(BaseExtractor):
    def extract(self) -> FileFact:
        try:
            import json as _json
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = _json.load(f)
        except Exception:
            data = None

        signals = {}
        if isinstance(data, dict):
            signals["keys"] = list(data.keys())[:10]
            signals["is_package_json"] = "name" in data and ("dependencies" in data or "scripts" in data)
        
        structures = {
            "top": type(data).__name__
        }
        
        return self._create_fact("json", structures, signals)


# ---------- YAML Extractor ----------

class YamlExtractor(BaseExtractor):
    def extract(self) -> FileFact:
        try:
            import yaml as _yaml
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = _yaml.safe_load(f)
        except Exception:
            data = None
        signals = {}
        if isinstance(data, dict):
            keys = list(data.keys())
            signals["keys"] = keys[:10]
            signals["looks_like_k8s"] = "apiVersion" in data or "kind" in data
            signals["looks_like_compose"] = "services" in data
        
        structures = {
            "top": type(data).__name__
        }
        
        return self._create_fact("yaml", structures, signals)


# ---------- Dockerfile Extractor ----------

class DockerfileExtractor(BaseExtractor):
    def extract(self) -> FileFact:
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        froms = re.findall(r"^FROM\s+(.+)$", src, re.MULTILINE)
        expos = re.findall(r"^EXPOSE\s+(.+)$", src, re.MULTILINE)
        
        structures = {
            "from": froms,
            "expose": expos
        }
        
        signals = {
            "has_entrypoint": "ENTRYPOINT" in src or "CMD" in src,
        }
        
        return self._create_fact("dockerfile", structures, signals)


# ---------- Markdown Extractor ----------

class MarkdownExtractor(BaseExtractor):
    def extract(self) -> FileFact:
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        headings = re.findall(r"^#+\s+(.+)$", src, re.MULTILINE)
        code_blocks = len(re.findall(r"```", src))
        
        structures = {
            "headings": headings[:10],
            "code_block_count": code_blocks
        }
        
        signals = {
            "has_install_steps": bool(re.search(r"install|usage|run", src, re.IGNORECASE)),
        }
        
        return self._create_fact("markdown", structures, signals)


# ---------- Notebook Extractor ----------

class NotebookExtractor(BaseExtractor):
    def extract(self) -> FileFact:
        try:
            import json as _json
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                doc = _json.load(f)
            cells = doc.get("cells", [])
            code_cells = sum(1 for c in cells if c.get("cell_type") == "code")
            md_cells = sum(1 for c in cells if c.get("cell_type") == "markdown")
        except Exception:
            code_cells = md_cells = 0
        
        structures = {
            "code_cells": code_cells,
            "markdown_cells": md_cells
        }
        
        signals = {
            "is_reproducible": code_cells > md_cells
        }
        
        return self._create_fact("notebook", structures, signals)


# ---------- Makefile Extractor ----------

class MakefileExtractor(BaseExtractor):
    def extract(self) -> FileFact:
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        targets = re.findall(r"^([a-zA-Z0-9_\-]+)\s*:\s*", src, re.MULTILINE)
        
        structures = {
            "targets": targets[:20]
        }
        
        signals = {
            "has_default_target": any(t == "all" for t in targets)
        }
        
        return self._create_fact("makefile", structures, signals)


# ---------- Dispatcher ----------

def get_extractor(filepath):
    base = os.path.basename(filepath)
    ext = os.path.splitext(filepath)[1].lower()

    # exact filename checks
    if base == "Dockerfile":
        return DockerfileExtractor(filepath)
    if base in ("Makefile", "makefile"):
        return MakefileExtractor(filepath)
    if base == "package.json":
        return JsonExtractor(filepath)

    # extension based
    if ext == ".py":
        return PythonExtractor(filepath)
    elif ext == ".html":
        return HtmlExtractor(filepath)
    elif ext == ".java":
        return JavaExtractor(filepath)
    elif ext in (".js", ".jsx"):
        return JsExtractor(filepath)
    elif ext in (".ts", ".tsx"):
        return TsExtractor(filepath)
    elif ext == ".json":
        return JsonExtractor(filepath)
    elif ext in (".yml", ".yaml"):
        return YamlExtractor(filepath)
    elif ext == ".md":
        return MarkdownExtractor(filepath)
    elif ext == ".ipynb":
        return NotebookExtractor(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# ---------- Main ----------

def main():
    if len(sys.argv) != 2:
        print("Usage: python wtfe_file.py <file>")
        sys.exit(1)

    filepath = sys.argv[1]
    extractor = get_extractor(filepath)
    fact = extractor.extract()

    # Output as JSON
    print(json.dumps(fact.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
