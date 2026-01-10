import sys
from pathlib import Path
import json

# ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from wtfe_file.extractors import get_extractor


def main():
    if len(sys.argv) != 2:
        print("Usage: python wtfe_file.py <file>")
        sys.exit(1)

    filepath = sys.argv[1]
    extractor = get_extractor(filepath)
    fact = extractor.extract()

    print(json.dumps(fact.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()


# Compatibility wrapper used by other imports
class FileAnalyzer:
    """Simple wrapper to analyze a single file and return FileFact."""
    def analyze(self, filepath):
        extractor = get_extractor(filepath)
        return extractor.extract()
