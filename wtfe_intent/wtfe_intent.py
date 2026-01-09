"""WTFE Intent Extractor - Author Intent Channel.

This module extracts explicit documentation and intent signals from:
- README files (project/module level)
- CHANGELOG, CONTRIBUTING, LICENSE
- Package metadata (setup.py, package.json, pyproject.toml, Cargo.toml)

Philosophy: Author's explicit documentation should have the HIGHEST weight
in final analysis. This is the "truth" against which automated inference
is validated.
"""
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
import json

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import AuthorIntent


class IntentExtractor:
    """Extract author intent signals from documentation files."""
    
    # Documentation file patterns (case-insensitive)
    README_PATTERNS = ['readme.md', 'readme.txt', 'readme.rst', 'readme']
    CHANGELOG_PATTERNS = ['changelog.md', 'changelog.txt', 'changelog', 'history.md', 'changes.md']
    CONTRIBUTING_PATTERNS = ['contributing.md', 'contributing.rst', 'contributing']
    LICENSE_PATTERNS = ['license', 'license.md', 'license.txt', 'copying']
    
    # Package metadata files
    PACKAGE_FILES = {
        'python': ['setup.py', 'setup.cfg', 'pyproject.toml', 'requirements.txt'],
        'javascript': ['package.json', 'package-lock.json'],
        'rust': ['Cargo.toml', 'Cargo.lock'],
        'go': ['go.mod', 'go.sum'],
        'ruby': ['Gemfile', 'Gemfile.lock', '*.gemspec'],
        'java': ['pom.xml', 'build.gradle', 'build.gradle.kts']
    }
    
    def __init__(self, root_path: str):
        """Initialize extractor.
        
        Args:
            root_path: Project root directory
        """
        self.root_path = Path(root_path).resolve()
        
    def extract(self) -> AuthorIntent:
        """Extract all author intent signals.
        
        Returns:
            AuthorIntent object with all discovered documentation
        """
        intent = AuthorIntent()
        
        # Extract project-level README
        intent.project_readme = self._find_and_read_readme(self.root_path)
        
        # Find module-level READMEs
        intent.module_readmes = self._find_module_readmes()
        
        # Extract other documentation
        intent.changelog = self._find_and_read_file(self.CHANGELOG_PATTERNS)
        intent.contributing = self._find_and_read_file(self.CONTRIBUTING_PATTERNS)
        intent.license_text = self._find_and_read_file(self.LICENSE_PATTERNS)
        
        # Extract package metadata
        intent.package_metadata = self._extract_package_metadata()
        
        return intent
    
    def _find_and_read_readme(self, directory: Path) -> Optional[str]:
        """Find and read README in a specific directory.
        
        Args:
            directory: Directory to search in
            
        Returns:
            README content or None
        """
        for pattern in self.README_PATTERNS:
            for file in directory.iterdir():
                if file.is_file() and file.name.lower() == pattern.lower():
                    return self._read_text_file(file)
        return None
    
    def _find_module_readmes(self) -> Dict[str, str]:
        """Find all module-level README files recursively.
        
        Returns:
            Dict mapping relative path to README content
        """
        readmes = {}
        
        for readme_pattern in self.README_PATTERNS:
            for file_path in self.root_path.rglob('*'):
                if file_path.is_file() and file_path.name.lower() == readme_pattern.lower():
                    # Skip root README (already captured)
                    if file_path.parent == self.root_path:
                        continue
                    
                    # Skip common ignore directories
                    if self._should_ignore_path(file_path):
                        continue
                    
                    relative_path = str(file_path.relative_to(self.root_path))
                    content = self._read_text_file(file_path)
                    if content:
                        readmes[relative_path] = content
        
        return readmes
    
    def _find_and_read_file(self, patterns: List[str]) -> Optional[str]:
        """Find and read a file matching any pattern (root level only).
        
        Args:
            patterns: List of filename patterns to match
            
        Returns:
            File content or None
        """
        for pattern in patterns:
            for file in self.root_path.iterdir():
                if file.is_file() and file.name.lower() == pattern.lower():
                    return self._read_text_file(file)
        return None
    
    def _extract_package_metadata(self) -> Dict[str, any]:
        """Extract metadata from package definition files.
        
        Returns:
            Dict with discovered package metadata
        """
        metadata = {}
        
        # Python: package.json equivalent
        package_json = self.root_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata['package_json'] = {
                        'name': data.get('name'),
                        'version': data.get('version'),
                        'description': data.get('description'),
                        'author': data.get('author'),
                        'license': data.get('license'),
                        'keywords': data.get('keywords', []),
                        'homepage': data.get('homepage'),
                        'repository': data.get('repository'),
                        'scripts': list(data.get('scripts', {}).keys())
                    }
            except Exception as e:
                metadata['package_json_error'] = str(e)
        
        # Python: setup.py / pyproject.toml
        setup_py = self.root_path / 'setup.py'
        if setup_py.exists():
            metadata['has_setup_py'] = True
            # Could parse with ast but keeping it simple for now
        
        pyproject_toml = self.root_path / 'pyproject.toml'
        if pyproject_toml.exists():
            metadata['has_pyproject_toml'] = True
            # Could parse with toml library
        
        # Rust: Cargo.toml
        cargo_toml = self.root_path / 'Cargo.toml'
        if cargo_toml.exists():
            metadata['has_cargo_toml'] = True
        
        # Go: go.mod
        go_mod = self.root_path / 'go.mod'
        if go_mod.exists():
            metadata['has_go_mod'] = True
        
        return metadata
    
    def _read_text_file(self, file_path: Path, max_size: int = 500_000) -> Optional[str]:
        """Read text file with safety limits.
        
        Args:
            file_path: Path to file
            max_size: Maximum file size to read (default 500KB)
            
        Returns:
            File content or None if too large/error
        """
        try:
            # Check file size
            if file_path.stat().st_size > max_size:
                return f"[File too large: {file_path.stat().st_size} bytes]"
            
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None
    
    def _should_ignore_path(self, path: Path) -> bool:
        """Check if path should be ignored.
        
        Args:
            path: Path to check
            
        Returns:
            True if should be ignored
        """
        ignore_dirs = {
            '__pycache__', 'node_modules', '.git', '.svn', '.hg',
            'venv', 'env', '.venv', '.env',
            'build', 'dist', 'target',
            '.pytest_cache', '.mypy_cache', '.tox',
            'coverage', 'htmlcov',
            '.idea', '.vscode'
        }
        
        # Check if any parent directory is in ignore list
        for parent in path.parents:
            if parent.name in ignore_dirs:
                return True
        
        return False


def main():
    """Command-line interface."""
    if len(sys.argv) != 2:
        print("Usage: python wtfe_intent.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)
    
    # Extract intent
    extractor = IntentExtractor(project_path)
    intent = extractor.extract()
    
    # Output as JSON
    output = intent.to_dict()
    
    # Add summary statistics
    summary = {
        'has_project_readme': intent.project_readme is not None,
        'module_readme_count': len(intent.module_readmes),
        'has_changelog': intent.changelog is not None,
        'has_contributing': intent.contributing is not None,
        'has_license': intent.license_text is not None,
        'package_metadata_keys': list(intent.package_metadata.keys())
    }
    
    output['_summary'] = summary
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
