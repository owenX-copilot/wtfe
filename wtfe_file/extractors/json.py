from .base import BaseExtractor
import json as _json

HANDLES = [".json"]


class Extractor(BaseExtractor):
    def extract(self):
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                data = _json.load(f)
        except Exception:
            data = None

        signals = {}
        if isinstance(data, dict):
            signals["keys"] = list(data.keys())[:10]
            signals["is_package_json"] = "name" in data and ("dependencies" in data or "scripts" in data)

        structures = {"top": type(data).__name__}

        return self._create_fact("json", structures, signals)
