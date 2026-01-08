"""Entry point detection and run configuration analysis (Pipeline B1-B3)."""
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import EntryPoint, RunConfig


class EntryPointDetector:
    """Detects entry points and startup methods for a project."""
    
    COMMON_ENTRY_FILES = [
        "main.py", "app.py", "server.py", "run.py", "__main__.py",
        "index.js", "app.js", "server.js", "main.js",
        "main.go", "cmd/main.go",
        "Main.java", "Application.java",
        "main.rs", "src/main.rs",
    ]
    
    def __init__(self, project_root: str):
        self.root = Path(project_root).resolve()
        
    def detect(self) -> RunConfig:
        """Main detection entry point."""
        config = RunConfig()
        
        # Detect entry point files
        config.entry_points = self._find_entry_point_files()
        
        # Parse Makefile
        config.makefile_targets = self._parse_makefile()
        
        # Parse package.json
        config.package_scripts = self._parse_package_json()
        
        # Parse Dockerfile
        config.dockerfile_cmds = self._parse_dockerfile()
        
        # Infer runtime dependencies
        self._infer_runtime_deps(config)
        
        return config
    
    def _find_entry_point_files(self) -> List[EntryPoint]:
        """Find common entry point files."""
        entries = []
        
        for pattern in self.COMMON_ENTRY_FILES:
            matches = list(self.root.rglob(pattern))
            for m in matches:
                if self._is_likely_entry_point(m):
                    ep = EntryPoint(
                        file_path=str(m.relative_to(self.root)),
                        entry_type=self._guess_entry_type(m),
                        confidence=0.7
                    )
                    ep.command = self._guess_command(m)
                    entries.append(ep)
        
        # Also check for __main__ in Python files
        entries.extend(self._find_python_main())
        
        return entries
    
    def _is_likely_entry_point(self, path: Path) -> bool:
        """Check if file looks like an entry point."""
        if not path.is_file():
            return False
        
        # Skip tests, examples
        path_str = str(path).lower()
        if any(x in path_str for x in ["test", "example", "demo", "__pycache__"]):
            return False
        
        return True
    
    def _guess_entry_type(self, path: Path) -> str:
        """Guess entry point type from filename."""
        name = path.stem.lower()
        if "server" in name or "app" in name:
            return "server"
        elif "cli" in name or "cmd" in name:
            return "cli"
        elif "main" in name:
            return "main"
        return "script"
    
    def _guess_command(self, path: Path) -> Optional[str]:
        """Guess how to run this file."""
        ext = path.suffix
        rel = path.relative_to(self.root)
        
        if ext == ".py":
            return f"python {rel}"
        elif ext == ".js":
            return f"node {rel}"
        elif ext == ".go":
            return f"go run {rel}"
        elif ext == ".java":
            # Simplified
            return f"java {path.stem}"
        return None
    
    def _find_python_main(self) -> List[EntryPoint]:
        """Find Python files with if __name__ == '__main__'."""
        entries = []
        
        for py_file in self.root.rglob("*.py"):
            if not self._is_likely_entry_point(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"if\s+__name__\s*==\s*['\"]__main__['\"]", content):
                    ep = EntryPoint(
                        file_path=str(py_file.relative_to(self.root)),
                        entry_type="main",
                        command=f"python {py_file.relative_to(self.root)}",
                        confidence=0.8
                    )
                    entries.append(ep)
            except Exception:
                pass
        
        return entries
    
    def _parse_makefile(self) -> List[str]:
        """Extract targets from Makefile."""
        makefile = self.root / "Makefile"
        if not makefile.exists():
            return []
        
        targets = []
        try:
            content = makefile.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                match = re.match(r"^([a-zA-Z0-9_\-]+)\s*:", line)
                if match:
                    targets.append(match.group(1))
        except Exception:
            pass
        
        return targets
    
    def _parse_package_json(self) -> Dict[str, str]:
        """Extract scripts from package.json."""
        pkg_json = self.root / "package.json"
        if not pkg_json.exists():
            return {}
        
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            return data.get("scripts", {})
        except Exception:
            return {}
    
    def _parse_dockerfile(self) -> List[str]:
        """Extract CMD/ENTRYPOINT from Dockerfile."""
        dockerfile = self.root / "Dockerfile"
        if not dockerfile.exists():
            return []
        
        cmds = []
        try:
            content = dockerfile.read_text(encoding="utf-8", errors="ignore")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("CMD ") or line.startswith("ENTRYPOINT "):
                    cmds.append(line)
        except Exception:
            pass
        
        return cmds
    
    def _infer_runtime_deps(self, config: RunConfig):
        """Infer runtime dependencies from various signals."""
        # Look for DB-related files
        if any((self.root / f).exists() for f in ["db", "database", "migrations"]):
            config.requires_db = True
        
        # Look for redis/cache mentions
        if any((self.root / f).exists() for f in ["cache", ".redis"]):
            config.requires_cache = True
        
        # Check docker-compose for services
        compose = self.root / "docker-compose.yml"
        if compose.exists():
            try:
                content = compose.read_text()
                if "postgres" in content or "mysql" in content or "mongodb" in content:
                    config.requires_db = True
                if "redis" in content or "memcached" in content:
                    config.requires_cache = True
                if "rabbitmq" in content or "kafka" in content:
                    config.requires_queue = True
            except Exception:
                pass


def main():
    """CLI for testing."""
    if len(sys.argv) < 2:
        print("Usage: python wtfe_run.py <project_dir>")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    detector = EntryPointDetector(project_dir)
    config = detector.detect()
    
    # Print results
    print(json.dumps({
        "entry_points": [
            {
                "file": ep.file_path,
                "type": ep.entry_type,
                "command": ep.command,
                "confidence": ep.confidence
            } for ep in config.entry_points
        ],
        "makefile_targets": config.makefile_targets,
        "package_scripts": config.package_scripts,
        "dockerfile_cmds": config.dockerfile_cmds,
        "runtime_deps": {
            "requires_db": config.requires_db,
            "requires_cache": config.requires_cache,
            "requires_queue": config.requires_queue
        }
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
