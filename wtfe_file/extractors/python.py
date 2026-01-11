#!/usr/bin/env python3
"""
concise_python_extractor_for_python_py.py

针对单个 Python 文件生成高度浓缩 JSON 描述。
保留：模块 docstring 摘要、imports、classes/functions（签名+doc摘要）、entry_point、外部使用分类、少量调用样本、roles。
过滤：排除 print/logging 等噪声调用，避免实现细节膨胀。
"""

import ast
import os
from typing import Any, Dict, List, Optional, Tuple
from .base import BaseExtractor
from core.models import Evidence

HANDLES = [".py", ".pyw"]



def _short_snippet(source: str, lineno: int, end_lineno: int = None, max_lines: int = 5):
    try:
        if end_lineno is None:
            end_lineno = lineno
        lines = source.splitlines()
        start = max(0, lineno - 1)
        end = min(len(lines), end_lineno)
        snippet_lines = lines[start:end]
        if len(snippet_lines) > max_lines:
            snippet_lines = snippet_lines[:max_lines]
        return "\n".join(snippet_lines)
    except Exception:
        return ""


def _summarize_docstring(doc: str, max_chars: int = 120):
    if not doc:
        return None
    doc = doc.strip()
    parts = doc.split('\n\n')
    first = parts[0].strip()
    if '\n' in first and len(first) < 80:
        lines = first.split('\n')
        return '\n'.join(lines[:2])
    if len(first) > max_chars:
        return first[:max_chars].rstrip() + '...'
    return first


MAX_DOC_CHARS = 160
CALL_BLACKLIST_ROOTS = {"print", "repr", "str", "len", "format", "pprint"}
LOGGING_MODULE_NAMES = {"logging", "loguru"}
NETWORK_MODULE_PREFIXES = ("requests", "urllib", "http", "aiohttp", "socket", "httpx")
DB_MODULE_PREFIXES = ("sqlalchemy", "psycopg2", "pymongo", "django.db", "sqlite3")
SUBPROCESS_MODULE_PREFIXES = ("subprocess",)
IO_ROOTS = {"open"}


def short_doc_summary(doc: Optional[str], max_chars: int = MAX_DOC_CHARS) -> Optional[str]:
    if not doc:
        return None
    doc = doc.strip()
    parts = [p.strip() for p in doc.split("\n\n") if p.strip()]
    first = parts[0] if parts else doc.strip()
    if "\n" in first and len(first) < 120:
        lines = first.splitlines()
        return "\n".join(lines[:2]).strip()
    if len(first) > max_chars:
        return first[: max_chars - 3].rstrip() + "..."
    return first


def safe_get_source_segment(source: str, node: ast.AST) -> Optional[str]:
    try:
        seg = ast.get_source_segment(source, node)
        if seg is not None:
            return seg.strip()
    except Exception:
        pass
    return None


def extract_signature_from_func(node: ast.FunctionDef, source: str) -> str:
    parts: List[str] = []
    try:
        for arg in node.args.args:
            name = arg.arg
            ann = None
            if getattr(arg, "annotation", None) is not None:
                ann = safe_get_source_segment(source, arg.annotation) or (ast.unparse(arg.annotation) if hasattr(ast, "unparse") else None)
            parts.append(f"{name}: {ann}" if ann else name)
        if node.args.vararg:
            parts.append(f"*{node.args.vararg.arg}")
        for arg in node.args.kwonlyargs:
            name = arg.arg
            ann = None
            if getattr(arg, "annotation", None) is not None:
                ann = safe_get_source_segment(source, arg.annotation) or (ast.unparse(arg, "unparse") if hasattr(ast, "unparse") else None)
            parts.append(f"{name}: {ann}" if ann else name)
        if node.args.kwarg:
            parts.append(f"**{node.args.kwarg.arg}")
        sig = "(" + ", ".join(parts) + ")"
        if getattr(node, "returns", None) is not None:
            ret = safe_get_source_segment(source, node.returns) or (ast.unparse(node.returns) if hasattr(ast, "unparse") else None)
            if ret:
                sig += f" -> {ret}"
        return sig
    except Exception:
        return f"({', '.join([a.arg for a in node.args.args])})"


def normalize_imports(imports: List[str]) -> List[str]:
    seen = set()
    out = []
    for im in imports:
        if im not in seen:
            seen.add(im)
            out.append(im)
    return out



class ConciseExtractor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.source = ""
        self.tree: Optional[ast.AST] = None
        self.import_map: Dict[str, str] = {}
        self.imports: List[str] = []

    def load(self):
        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            self.source = f.read()
        self.tree = ast.parse(self.source)

    def analyze_imports(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    origin = alias.name
                    local = alias.asname if alias.asname else origin.split(".")[0]
                    self.import_map[local] = origin
                    self.imports.append(origin.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod:
                    self.imports.append(mod.split(".")[0])
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    full = f"{mod}.{alias.name}" if mod else alias.name
                    self.import_map[local] = full
                    self.imports.append((mod.split(".")[0] if mod else alias.name))
        self.imports = normalize_imports(self.imports)

    def module_doc_summary(self) -> Optional[Dict[str, Any]]:
        doc = ast.get_docstring(self.tree)
        if not doc:
            return None
        lineno = 1
        if isinstance(self.tree, ast.Module) and self.tree.body:
            first = self.tree.body[0]
            if isinstance(first, ast.Expr):
                lineno = getattr(first, "lineno", 1)
        return {"doc": short_doc_summary(doc), "lineno": lineno}

    def extract_structures(self) -> Dict[str, Any]:
        classes: List[Dict[str, Any]] = []
        functions: List[Dict[str, Any]] = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                cls_doc = ast.get_docstring(node)
                methods = []
                for cnode in node.body:
                    if isinstance(cnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = extract_signature_from_func(cnode, self.source)
                        doc = short_doc_summary(ast.get_docstring(cnode))
                        methods.append({"name": cnode.name, "lineno": getattr(cnode, "lineno", None), "signature": sig, "doc": doc})
                bases = []
                for b in node.bases:
                    try:
                        bases.append(ast.unparse(b) if hasattr(ast, "unparse") else getattr(b, "id", str(b)))
                    except Exception:
                        try:
                            bases.append(b.id)
                        except Exception:
                            bases.append(str(b))
                classes.append({"name": node.name, "lineno": getattr(node, "lineno", None), "bases": bases, "doc": short_doc_summary(cls_doc), "methods": methods})

        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = extract_signature_from_func(node, self.source)
                doc = short_doc_summary(ast.get_docstring(node))
                functions.append({"name": node.name, "lineno": getattr(node, "lineno", None), "signature": sig, "doc": doc})

        globals_vars = []
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name.startswith("_"):
                            continue
                        globals_vars.append(name)
        return {"classes": classes, "functions": functions, "globals": globals_vars}

    def detect_entry_point(self) -> bool:
        for node in ast.walk(self.tree):
            if isinstance(node, ast.If):
                try:
                    test = node.test
                    if isinstance(test, ast.Compare):
                        left = test.left
                        comparators = test.comparators
                        if isinstance(left, ast.Name) and left.id == "__name__":
                            for comp in comparators:
                                if isinstance(comp, ast.Constant) and comp.value == "__main__":
                                    return True
                                if isinstance(comp, ast.Str) and comp.s == "__main__":
                                    return True
                except Exception:
                    continue
        return False

    def analyze_calls_and_signals(self) -> Dict[str, Any]:
        calls_set = set()
        external_usage = set()
        meaningful_calls = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                func = node.func
                chain_parts: List[str] = []
                try:
                    while True:
                        if isinstance(func, ast.Attribute):
                            chain_parts.insert(0, func.attr)
                            func = func.value
                            continue
                        elif isinstance(func, ast.Name):
                            chain_parts.insert(0, func.id)
                        elif isinstance(func, ast.Call):
                            if isinstance(func.func, ast.Name):
                                chain_parts.insert(0, func.func.id)
                        break
                except Exception:
                    continue

                if not chain_parts:
                    continue
                root = chain_parts[0]
                full = ".".join(chain_parts)

                if root in CALL_BLACKLIST_ROOTS:
                    continue
                if root in LOGGING_MODULE_NAMES:
                    continue
                if len(chain_parts) >= 2 and chain_parts[0] in LOGGING_MODULE_NAMES:
                    continue

                lineno = getattr(node, "lineno", None)
                key = (full, lineno)
                if key in calls_set:
                    continue
                calls_set.add(key)

                origin = self.import_map.get(root)
                category = None
                if origin:
                    if any(origin.startswith(p) for p in NETWORK_MODULE_PREFIXES):
                        category = "network"
                    elif any(origin.startswith(p) for p in DB_MODULE_PREFIXES):
                        category = "database"
                    elif any(origin.startswith(p) for p in SUBPROCESS_MODULE_PREFIXES):
                        category = "subprocess"
                else:
                    if root in IO_ROOTS:
                        category = "io"

                if category:
                    external_usage.add(category)
                else:
                    if len(chain_parts) > 1:
                        first = chain_parts[0]
                        mapped = self.import_map.get(first)
                        if mapped:
                            if any(mapped.startswith(p) for p in NETWORK_MODULE_PREFIXES):
                                external_usage.add("network")
                            if any(mapped.startswith(p) for p in DB_MODULE_PREFIXES):
                                external_usage.add("database")
                            if any(mapped.startswith(p) for p in SUBPROCESS_MODULE_PREFIXES):
                                external_usage.add("subprocess")

                if len(meaningful_calls) < 20 and root not in CALL_BLACKLIST_ROOTS:
                    try:
                        sample_line = safe_get_source_segment(self.source, node) or full
                    except Exception:
                        sample_line = full
                    meaningful_calls.append({"call": full, "lineno": lineno, "sample": sample_line})

        return {"external_usage": sorted(list(external_usage)), "calls_sample": meaningful_calls}

        # calls handled by concise analyzer; nothing to attach here

class ExtractorWrapper(BaseExtractor):
    def extract(self):
        ce = ConciseExtractor(self.filepath)
        ce.load()
        ce.analyze_imports()
        module_doc = ce.module_doc_summary()
        structures = ce.extract_structures()
        entry_point = ce.detect_entry_point()
        signals = ce.analyze_calls_and_signals()

        # build signals for FileFact
        fact_signals = {
            "imports": ce.imports,
            "entry_point": bool(entry_point),
            "external_usage": signals.get("external_usage", []),
            "calls_sample": signals.get("calls_sample", []),
            "module_doc": module_doc["doc"] if module_doc else None,
            "module_doc_lineno": module_doc["lineno"] if module_doc else None,
        }

        fact = self._create_fact("python", structures, fact_signals)
        # attach concise module doc as evidence
        if module_doc and module_doc.get("doc"):
            fact.evidence.append(Evidence(location=f"{self.filepath}:{module_doc.get('lineno')}", snippet=module_doc.get('doc'), signal_type="module_docstring", lineno=module_doc.get('lineno'), end_lineno=module_doc.get('lineno'), weight=1.0))
        return fact


# Backwards-compatible alias expected by tests
class PythonExtractor(ExtractorWrapper):
    @staticmethod
    def can_handle(path: str) -> bool:
        p = path.lower()
        return p.endswith('.py') or p.endswith('.pyw')

# Export the expected symbol name 'Extractor' so the dynamic loader finds this module
Extractor = ExtractorWrapper


def match(path: str) -> bool:
    import os
    _, ext = os.path.splitext(path or "")
    return ext.lower() in ('.py', '.pyw')

