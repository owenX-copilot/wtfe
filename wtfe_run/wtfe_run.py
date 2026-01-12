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
        # Directories we should never read file contents from (present but not sent to AI)
        self.EXCLUDE_DIRS = {
            'venv', '.venv', 'env', '.env', 'node_modules',
            'site-packages', 'dist', 'build', '.pytest_cache', '__pycache__'
        }
        
    def detect(self, detail: bool = False) -> tuple[RunConfig, Dict]:
        """Main detection entry point.
        
        Args:
            detail: Enable detailed analysis mode (extract full file contents)
            
        Returns:
            Tuple of (RunConfig, analysis_log_dict)
        """
        config = RunConfig()
        analysis_log = {}
        
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
        
        # Extract detailed file content if requested
        if detail and config.entry_points:
            analysis_log = self._extract_entry_details(config.entry_points)
        
        return config, analysis_log
    
    def _find_entry_point_files(self) -> List[EntryPoint]:
        """Find common entry point files."""
        entries = []
        
        for pattern in self.COMMON_ENTRY_FILES:
            matches = list(self.root.rglob(pattern))
            for m in matches:
                if self._is_likely_entry_point(m):
                    # Skip files under excluded dirs (virtualenv, node_modules, site-packages, etc.)
                    try:
                        mparts = {p.lower() for p in m.parts}
                    except Exception:
                        mparts = set()
                    if mparts & {d.lower() for d in self.EXCLUDE_DIRS}:
                        continue
                    ep = EntryPoint(
                        file_path=str(m.relative_to(self.root)),
                        entry_type=self._guess_entry_type(m),
                        confidence=0.7
                    )
                    ep.command = self._guess_command(m)
                    entries.append(ep)
        
        # Also check for __main__ in Python files
        entries.extend(self._find_python_main())

        # De-duplicate entries by file_path: keep the entry with higher confidence
        dedup: Dict[str, EntryPoint] = {}
        for ep in entries:
            key = ep.file_path
            if key not in dedup:
                dedup[key] = ep
            else:
                # Prefer higher confidence; if equal, prefer entry_type == 'main'
                existing = dedup[key]
                if ep.confidence > existing.confidence:
                    dedup[key] = ep
                elif ep.confidence == existing.confidence:
                    if ep.entry_type == 'main' and existing.entry_type != 'main':
                        dedup[key] = ep

        return list(dedup.values())
    
    def _is_likely_entry_point(self, path: Path) -> bool:
        """Check if file looks like an entry point."""
        if not path.is_file():
            return False
        
        # Skip tests, examples and virtualenv/vendor dirs
        path_str = str(path).lower()
        if any(x in path_str for x in ["test", "example", "demo", "__pycache__"]):
            return False
        # If path is inside excluded directory names, skip
        try:
            parts = {p.lower() for p in path.parts}
        except Exception:
            parts = set()
        if parts & {d.lower() for d in self.EXCLUDE_DIRS}:
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
    
    def _extract_entry_details(self, entry_points: List[EntryPoint]) -> Dict:
        """Extract detailed content from entry point files with token counting.
        
        Args:
            entry_points: List of detected entry points
            
        Returns:
            Dictionary with file processing statistics and details
        """
        # Try to import tiktoken for accurate token counting
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            use_tiktoken = True
        except ImportError:
            use_tiktoken = False
            print("[WTFE] Warning: tiktoken not installed, using character-based approximation", file=sys.stderr)
        
        # Load config
        config_path = Path(__file__).parent.parent / 'wtfe_readme' / 'config.yaml'
        detail_max_tokens = 8000
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
                detail_max_tokens = cfg.get('detail_max_tokens', 8000)
        except:
            pass
        
        files_processed = 0
        files_full_content = 0
        files_downgraded = 0
        total_tokens = 0
        downgraded_tokens = 0
        files_details = []
        
        for ep in entry_points:
            try:
                file_path = self.root / ep.file_path
                if not file_path.exists():
                    continue

                # Skip reading files that are inside excluded dirs (virtualenv / site-packages / node_modules)
                try:
                    fparts = {p.lower() for p in file_path.parts}
                except Exception:
                    fparts = set()
                if fparts & {d.lower() for d in self.EXCLUDE_DIRS}:
                    files_processed += 1
                    files_details.append({
                        "file": ep.file_path,
                        "mode": "excluded",
                        "tokens": 0,
                        "reason": "Excluded directory (virtualenv/vendor)"
                    })
                    continue

                files_processed += 1

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Count tokens
                if use_tiktoken:
                    tokens = len(encoding.encode(content))
                else:
                    # Approximate: ~4 characters per token
                    tokens = len(content) // 4
                
                mode = "full"
                reason = ""
                if tokens > detail_max_tokens:
                    # Downgrade to snippet mode
                    lines = content.split('\n')
                    if len(lines) > 150:
                        snippet = '\n'.join(lines[:100] + ['...'] + lines[-50:])
                        if use_tiktoken:
                            tokens = len(encoding.encode(snippet))
                        else:
                            tokens = len(snippet) // 4
                        mode = "snippet"
                        reason = f"File too large ({tokens} tokens > {detail_max_tokens} limit)"
                        files_downgraded += 1
                        downgraded_tokens += tokens
                    else:
                        files_full_content += 1
                else:
                    files_full_content += 1

                # Determine content to include in return (respecting size threshold)
                try:
                    chars_threshold = int(detail_max_tokens * 4)
                except Exception:
                    chars_threshold = detail_max_tokens * 4

                content_for_return = ""
                if mode == "snippet":
                    # use snippet variable if created, else create safe snippet
                    try:
                        snippet
                    except NameError:
                        lines = content.split('\n')
                        snippet = '\n'.join(lines[:100] + ['...'] + lines[-50:]) if len(lines) > 150 else content
                    content_for_return = snippet[:chars_threshold] + ("\n...TRUNCATED..." if len(snippet) > chars_threshold else "")
                elif mode == "full":
                    content_for_return = content[:chars_threshold] + ("\n...TRUNCATED..." if len(content) > chars_threshold else "")

                total_tokens += tokens

                files_details.append({
                    "file": ep.file_path,
                    "mode": mode,
                    "tokens": tokens,
                    "reason": reason,
                    "content": content_for_return
                })
                
            except Exception as e:
                print(f"[WTFE] Warning: Failed to process {ep.file_path}: {e}", file=sys.stderr)
        
        return {
            "files_processed": files_processed,
            "files_full_content": files_full_content,
            "files_downgraded": files_downgraded,
            "total_tokens": total_tokens,
            "downgraded_tokens": downgraded_tokens,
            "files_details": files_details
        }


def main():
    """CLI for testing."""
    if len(sys.argv) < 2:
        print("Usage: python wtfe_run.py <project_dir> [--detail]")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    detail = '--detail' in sys.argv
    
    detector = EntryPointDetector(project_dir)
    config, analysis_log = detector.detect(detail=detail)
    
    # Print results
    result = {
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
    }
    
    if analysis_log:
        result["analysis_log"] = analysis_log
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
