"""Extractor package: dynamic discovery and dispatcher."""
import pkgutil
import importlib
import os

_registry = []  # list of (match_callable, ExtractorClass)


def _make_match(handle):
    # handle can be ext like '.py' or exact filename like 'Dockerfile'
    if handle.startswith('.'):
        def m(path):
            return os.path.splitext(path)[1].lower() == handle
        return m
    else:
        def m(path):
            return os.path.basename(path) == handle
        return m


def _load_modules():
    import wtfe_file.extractors as pkg
    for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
        if name.startswith('_'):
            continue
        mod = importlib.import_module(f"{pkg.__name__}.{name}")
        Extractor = getattr(mod, "Extractor", None)
        if Extractor is None:
            continue
        handles = getattr(mod, "HANDLES", [])
        # optional custom match function
        match_fn = getattr(mod, "match", None)
        if match_fn:
            _registry.append((match_fn, Extractor))
        else:
            for h in handles:
                _registry.append((_make_match(h), Extractor))


def get_extractor(filepath):
    if not _registry:
        _load_modules()
    for match, Extractor in _registry:
        try:
            if match(filepath):
                return Extractor(filepath)
        except Exception:
            continue
    raise ValueError(f"Unsupported file type: {filepath}")


__all__ = ["get_extractor"]
