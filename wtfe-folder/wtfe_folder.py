import sys
import os
import json
import subprocess
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Set

# Import core models
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import FileFact, ModuleSummary, FileRole


class FolderAnalyzer:
    """Analyze a folder and aggregate FileFacts into ModuleSummary."""
    
    def __init__(self, folder_path: str, recursive: bool = True):
        self.folder_path = Path(folder_path).resolve()
        self.wtfe_file_script = Path(__file__).parent.parent / "wtfe-file" / "wtfe_file.py"
        self.facts: List[FileFact] = []
        self.recursive = recursive
        self.subfolder_summaries: List[ModuleSummary] = []
        
    def analyze(self) -> ModuleSummary:
        """Main analysis entry point."""
        # Step 1: Scan and analyze all files
        self._scan_files()
        
        # Step 2: Role clustering
        role_groups = self._cluster_by_role()
        
        # Step 3: Identify core files
        core_files = self._identify_core_files(role_groups)
        
        # Step 4: Infer primary role
        primary_role = self._infer_primary_role(role_groups)
        
        # Step 5: Extract capabilities
        capabilities = self._extract_capabilities()
        
        # Step 6: Analyze dependencies
        external_deps = self._analyze_dependencies()
        
        return ModuleSummary(
            path=str(self.folder_path),
            name=self.folder_path.name,
            files=[fact.path for fact in self.facts],
            core_files=core_files,
            primary_role=FileRole(primary_role) if primary_role != "unknown" else None,
            capabilities=list(capabilities.keys()),  # Convert to list of capability names
            external_deps=external_deps
        )
    
    def _scan_files(self):
        """Scan folder and analyze each file with wtfe-file."""
        supported_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.html', 
                               '.java', '.json', '.yml', '.yaml', '.md', '.ipynb'}
        special_files = {'Dockerfile', 'Makefile', 'makefile'}
        ignore_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        
        for item in self.folder_path.iterdir():
            # Skip ignored directories
            if item.is_dir() and item.name in ignore_dirs:
                continue
                
            if item.is_file():
                # Check if file is supported
                if item.suffix in supported_extensions or item.name in special_files:
                    try:
                        fact = self._analyze_file(item)
                        if fact:
                            self.facts.append(fact)
                    except Exception as e:
                        print(f"Warning: Failed to analyze {item.name}: {e}", file=sys.stderr)
            
            elif item.is_dir() and self.recursive:
                # Recursively analyze subdirectory
                try:
                    sub_analyzer = FolderAnalyzer(str(item), recursive=True)
                    sub_summary = sub_analyzer.analyze()
                    self.subfolder_summaries.append(sub_summary)
                except Exception as e:
                    print(f"Warning: Failed to analyze subfolder {item.name}: {e}", file=sys.stderr)
    
    def _analyze_file(self, filepath: Path) -> FileFact:
        """Call wtfe-file to analyze a single file."""
        try:
            result = subprocess.run(
                [sys.executable, str(self.wtfe_file_script), str(filepath)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                # Reconstruct FileFact from dict
                return FileFact(
                    path=data['path'],
                    filename=data['filename'],
                    language=data['language'],
                    structures=data['structures'],
                    signals=data['signals'],
                    roles=[FileRole(r) for r in data['roles']],
                    evidence=data.get('evidence', []),
                    confidence=data.get('confidence', 0.5)
                )
        except Exception as e:
            raise Exception(f"Analysis failed: {e}")
    
    def _cluster_by_role(self) -> Dict[FileRole, List[FileFact]]:
        """Group files by their primary role."""
        clusters = defaultdict(list)
        for fact in self.facts:
            if fact.roles:
                # Use the first role as primary
                clusters[fact.roles[0]].append(fact)
            else:
                clusters[FileRole.UNKNOWN].append(fact)
        return clusters
    
    def _identify_core_files(self, role_groups: Dict[FileRole, List[FileFact]]) -> List[str]:
        """Identify core files based on role priority and confidence."""
        # Role priority: ENTRY_POINT > SERVICE > CLI > LIBRARY > others
        priority = [
            FileRole.ENTRY_POINT,
            FileRole.SERVICE,
            FileRole.CLI,
            FileRole.LIBRARY
        ]
        
        core_files = []
        for role in priority:
            if role in role_groups:
                # Sort by confidence and take top files
                sorted_files = sorted(role_groups[role], key=lambda f: f.confidence, reverse=True)
                core_files.extend([f.filename for f in sorted_files[:3]])  # Top 3 per role
                
        return core_files[:5]  # Return top 5 overall
    
    def _infer_primary_role(self, role_groups: Dict[FileRole, List[FileFact]]) -> str:
        """Infer the primary role of the module."""
        if not role_groups:
            return "unknown"
        
        # Weight by role importance
        role_weights = {
            FileRole.ENTRY_POINT: 10,
            FileRole.SERVICE: 8,
            FileRole.CLI: 7,
            FileRole.LIBRARY: 5,
            FileRole.TEST: 3,
            FileRole.CONFIG: 2,
            FileRole.BUILD: 2,
            FileRole.DOCUMENTATION: 1,
            FileRole.UTILITY: 4,
            FileRole.UNKNOWN: 0
        }
        
        weighted_scores = {}
        for role, files in role_groups.items():
            score = len(files) * role_weights.get(role, 1)
            # Boost by average confidence
            avg_confidence = sum(f.confidence for f in files) / len(files)
            weighted_scores[role] = score * avg_confidence
        
        if not weighted_scores:
            return "unknown"
        
        primary = max(weighted_scores.items(), key=lambda x: x[1])
        return primary[0].value
    
    def _extract_capabilities(self) -> Dict[str, any]:
        """Extract module capabilities from aggregated facts."""
        capabilities = {
            "languages": Counter(),
            "has_network": False,
            "has_io": False,
            "has_tests": False,
            "frameworks": set(),
            "total_structures": {
                "classes": 0,
                "functions": 0
            }
        }
        
        for fact in self.facts:
            # Language distribution
            capabilities["languages"][fact.language] += 1
            
            # Network/IO signals
            if fact.signals.get("network"):
                capabilities["has_network"] = True
            if fact.signals.get("io"):
                capabilities["has_io"] = True
            
            # Test detection
            if FileRole.TEST in fact.roles:
                capabilities["has_tests"] = True
            
            # Framework detection
            if fact.language == "javascript" or fact.language == "typescript":
                if fact.signals.get("react"):
                    capabilities["frameworks"].add("React")
                if fact.signals.get("express"):
                    capabilities["frameworks"].add("Express")
            
            # Structure counts
            structures = fact.structures
            if "classes" in structures:
                capabilities["total_structures"]["classes"] += len(structures["classes"])
            if "functions" in structures:
                capabilities["total_structures"]["functions"] += len(structures["functions"])
        
        # Convert Counter to dict for JSON serialization
        capabilities["languages"] = dict(capabilities["languages"])
        capabilities["frameworks"] = list(capabilities["frameworks"])
        
        return capabilities
    
    def _analyze_dependencies(self) -> List[str]:
        """Extract external dependencies from all files."""
        all_imports = set()
        
        for fact in self.facts:
            imports = fact.signals.get("imports", [])
            if isinstance(imports, list):
                all_imports.update(imports)
        
        # Filter to likely external packages (heuristic)
        external = []
        stdlib_patterns = ["__future__", "sys", "os", "json", "re", "time", "datetime", 
                          "collections", "typing", "pathlib", "subprocess"]
        
        for imp in all_imports:
            # Skip standard library and relative imports
            if imp and not imp.startswith('.') and imp not in stdlib_patterns:
                external.append(imp)
        
        return sorted(set(external))[:20]  # Top 20 unique deps


def main():
    if len(sys.argv) != 2:
        print("Usage: python wtfe_folder.py <folder>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a directory")
        sys.exit(1)
    
    analyzer = FolderAnalyzer(folder_path)
    summary = analyzer.analyze()
    
    # Output as JSON
    output = {
        "path": summary.path,
        "name": summary.name,
        "files": summary.files,
        "core_files": summary.core_files,
        "primary_role": summary.primary_role.value if summary.primary_role else "unknown",
        "capabilities": summary.capabilities,
        "external_deps": summary.external_deps,
        "subfolders": len(analyzer.subfolder_summaries),
        "subfolder_details": [
            {
                "name": sub.name,
                "path": sub.path,
                "files_count": len(sub.files),
                "primary_role": sub.primary_role.value if sub.primary_role else "unknown"
            }
            for sub in analyzer.subfolder_summaries
        ]
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
