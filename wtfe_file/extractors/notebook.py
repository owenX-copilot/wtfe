import json
from .base import BaseExtractor

HANDLES = [".ipynb"]


class Extractor(BaseExtractor):
    def extract(self):
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                doc = json.load(f)
            cells = doc.get("cells", [])
            code_cells = sum(1 for c in cells if c.get("cell_type") == "code")
            md_cells = sum(1 for c in cells if c.get("cell_type") == "markdown")
        except Exception:
            code_cells = md_cells = 0

        structures = {"code_cells": code_cells, "markdown_cells": md_cells}
        signals = {"is_reproducible": code_cells > md_cells}

        return self._create_fact("notebook", structures, signals)
