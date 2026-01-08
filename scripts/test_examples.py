"""Batch-run `wtfe-file/wtfe_file.py` against all files in `example/` and collect results.

Usage:
  python scripts/test_examples.py [--dir example] [--out example/example_results.json]
"""
import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = (ROOT / "example")
WTFE_SCRIPT = ROOT / "wtfe-file" / "wtfe_file.py"


def run_one(path: Path):
    try:
        proc = subprocess.run([sys.executable, str(WTFE_SCRIPT), str(path)], capture_output=True, text=True, timeout=5)
    except Exception as e:
        return {"file": str(path), "error": str(e)}

    if proc.returncode != 0:
        return {"file": str(path), "error": proc.stderr.strip()}

    try:
        out = json.loads(proc.stdout)
    except Exception as e:
        return {"file": str(path), "error": f"invalid json output: {e}", "raw": proc.stdout}

    return {"file": str(path), "result": out}


def main(dir_path: str | None = None, out_file: str | None = None):
    dirp = Path(dir_path) if dir_path else EXAMPLE_DIR
    results = []

    for p in sorted(dirp.iterdir()):
        if p.is_file():
            r = run_one(p)
            results.append(r)
            print(p.name, "=>", "OK" if "result" in r else "ERR")

    outp = Path(out_file) if out_file else EXAMPLE_DIR / "example_results.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Wrote results to", outp)


if __name__ == "__main__":
    main()
