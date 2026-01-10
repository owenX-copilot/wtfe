from .base import BaseExtractor
try:
    import yaml as _yaml
except Exception:
    _yaml = None

HANDLES = [".yml", ".yaml"]


class Extractor(BaseExtractor):
    def extract(self):
        data = None
        try:
            if _yaml:
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

        structures = {"top": type(data).__name__}

        return self._create_fact("yaml", structures, signals)
