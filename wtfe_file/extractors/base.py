import sys
import os
from pathlib import Path

# ensure project root is importable for core.models
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.models import FileFact, Evidence, FileRole


class BaseExtractor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

    def extract(self) -> FileFact:
        raise NotImplementedError()

    def _create_fact(self, language: str, structures: dict, signals: dict) -> FileFact:
        fact = FileFact(
            path=self.filepath,
            filename=self.filename,
            language=language,
            structures=structures,
            signals=signals
        )
        fact.roles = self._infer_roles(structures, signals)
        fact.confidence = self._calculate_confidence(structures, signals)
        return fact

    def _infer_roles(self, structures: dict, signals: dict) -> list:
        roles = []
        if any(kw in self.filename.lower() for kw in ["test_", "_test", "spec_"]):
            roles.append(FileRole.TEST)
        if self.filename.lower() in ["config.py", "settings.py", "config.json", "config.yml"]:
            roles.append(FileRole.CONFIG)
        if signals.get("entry_point") or "main" in structures.get("functions", []):
            roles.append(FileRole.ENTRY_POINT)
        if signals.get("network") and not signals.get("entry_point"):
            roles.append(FileRole.SERVICE)
        if any(lib in signals.get("imports", []) for lib in ["argparse", "click", "typer"]):
            roles.append(FileRole.CLI)
        if not roles:
            roles.append(FileRole.UNKNOWN)
        return roles

    def _calculate_confidence(self, structures: dict, signals: dict) -> float:
        confidence = 0.5
        if structures.get("classes"):
            confidence += 0.1
        if structures.get("functions"):
            confidence += 0.1
        if signals.get("imports"):
            confidence += 0.1
        if signals.get("entry_point"):
            confidence += 0.2
        return min(confidence, 1.0)
