import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List

# Import core models
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import ProjectContext


class ContextAnalyzer:
    """Analyze project context and collect raw signals for AI processing."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        
    def analyze(self) -> ProjectContext:
        """Main analysis entry point - returns minimal context."""
        # Collect all raw signals
        signals = self._collect_signals()
        
        # Count files and lines
        file_count, line_count, languages = self._count_project_scale()
        
        return ProjectContext(
            root_path=str(self.project_path),
            project_name=self.project_path.name,
            project_type="unknown",  # Let AI decide based on signals
            has_tests=signals['has_tests'],
            has_ci=signals['has_ci'],
            has_typing=signals['has_typing'],
            file_count=file_count,
            line_count=line_count,
            languages=list(languages.keys()),
            frameworks=[]  # Raw signals replace this
        )
    
    def _collect_signals(self) -> Dict:
        """
        Collect all raw signals without making conclusions.
        AI will use these signals to infer project type.
        """
        signals = {
            # === Project Structure Files ===
            'has_setup_py': (self.project_path / "setup.py").exists(),
            'has_pyproject_toml': (self.project_path / "pyproject.toml").exists(),
            'has_package_json': (self.project_path / "package.json").exists(),
            'has_cargo_toml': (self.project_path / "Cargo.toml").exists(),
            'has_go_mod': (self.project_path / "go.mod").exists(),
            'has_pom_xml': (self.project_path / "pom.xml").exists(),
            'has_requirements_txt': (self.project_path / "requirements.txt").exists(),
            
            # === Common Entry Files ===
            'has_main_py': (self.project_path / "main.py").exists(),
            'has_app_py': (self.project_path / "app.py").exists(),
            'has_manage_py': (self.project_path / "manage.py").exists(),
            'has_wsgi_py': (self.project_path / "wsgi.py").exists(),
            'has_index_js': (self.project_path / "index.js").exists(),
            'has_server_js': (self.project_path / "server.js").exists(),
            'has_main_go': (self.project_path / "main.go").exists(),
            
            # === Framework Config Files ===
            'has_next_config': (self.project_path / "next.config.js").exists(),
            'has_vite_config': (self.project_path / "vite.config.js").exists() or (self.project_path / "vite.config.ts").exists(),
            'has_webpack_config': (self.project_path / "webpack.config.js").exists(),
            'has_tsconfig': (self.project_path / "tsconfig.json").exists(),
            
            # === Build/Deploy Files ===
            'has_dockerfile': (self.project_path / "Dockerfile").exists(),
            'has_docker_compose': (self.project_path / "docker-compose.yml").exists() or (self.project_path / "docker-compose.yaml").exists(),
            'has_makefile': (self.project_path / "Makefile").exists() or (self.project_path / "makefile").exists(),
            
            # === Documentation ===
            'has_readme': self._has_readme(),
            'has_license': self._has_license(),
            'has_docs_dir': (self.project_path / "docs").is_dir() or (self.project_path / "doc").is_dir(),
            'has_changelog': (self.project_path / "CHANGELOG.md").exists() or (self.project_path / "HISTORY.md").exists(),
            
            # === Testing ===
            'has_tests': self._detect_tests(),
            'has_test_dir': (self.project_path / "tests").is_dir() or (self.project_path / "test").is_dir(),
            'has_pytest_ini': (self.project_path / "pytest.ini").exists(),
            'has_jest_config': (self.project_path / "jest.config.js").exists(),
            'has_coverage_config': (self.project_path / ".coveragerc").exists(),
            
            # === CI/CD ===
            'has_ci': self._detect_ci(),
            'has_github_actions': (self.project_path / ".github" / "workflows").is_dir(),
            'has_gitlab_ci': (self.project_path / ".gitlab-ci.yml").exists(),
            'has_travis': (self.project_path / ".travis.yml").exists(),
            'has_jenkins': (self.project_path / "Jenkinsfile").exists(),
            
            # === Code Quality ===
            'has_typing': self._detect_typing(),
            'has_eslint': (self.project_path / ".eslintrc.js").exists() or (self.project_path / ".eslintrc.json").exists(),
            'has_prettier': (self.project_path / ".prettierrc").exists() or (self.project_path / ".prettierrc.json").exists(),
            'has_mypy_ini': (self.project_path / "mypy.ini").exists(),
            'has_black_config': (self.project_path / "pyproject.toml").exists(),  # Often includes black config
            
            # === Version Control ===
            'has_git': (self.project_path / ".git").is_dir(),
            'has_gitignore': (self.project_path / ".gitignore").exists(),
            
            # === Dependencies (raw extraction) ===
            'dependencies': self._extract_dependencies(),
        }
        
        return signals
    
    def _has_readme(self) -> bool:
        """Check for README file in various formats."""
        readme_variations = ['README.md', 'README.txt', 'README.rst', 'README', 'readme.md', 'Readme.md']
        return any((self.project_path / name).exists() for name in readme_variations)
    
    def _has_license(self) -> bool:
        """Check for LICENSE file."""
        license_variations = ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'license', 'License.md']
        return any((self.project_path / name).exists() for name in license_variations)
    
    def _detect_tests(self) -> bool:
        """Detect if project has tests."""
        # Check for test directories
        test_dirs = ["tests", "test", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (self.project_path / test_dir).is_dir():
                return True
        
        # Check for test files in root
        test_patterns = ["test_*.py", "*_test.py", "*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"]
        for pattern in test_patterns:
            if list(self.project_path.glob(pattern)):
                return True
        
        # Check for test config files
        if (self.project_path / "pytest.ini").exists():
            return True
        if (self.project_path / ".coveragerc").exists():
            return True
        
        return False
    
    def _detect_ci(self) -> bool:
        """Detect CI/CD configuration."""
        ci_indicators = [
            ".github/workflows",  # GitHub Actions
            ".gitlab-ci.yml",     # GitLab CI
            ".travis.yml",        # Travis CI
            "Jenkinsfile",        # Jenkins
            ".circleci/config.yml"  # CircleCI
        ]
        
        for indicator in ci_indicators:
            path = self.project_path / indicator
            if path.exists():
                return True
        
        return False
    
    def _detect_typing(self) -> bool:
        """Detect type annotation usage."""
        # Check for Python type hints
        py_files = list(self.project_path.glob("**/*.py"))[:10]  # Sample first 10 files
        
        type_hint_patterns = [
            r'def\s+\w+\([^)]*:\s*\w+',  # Function parameter type hints
            r'->\s*\w+:',                 # Return type hints
            r':\s*List\[',                # Typing module usage
            r':\s*Dict\[',
            r':\s*Optional\[',
            r'from typing import'
        ]
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for pattern in type_hint_patterns:
                        if re.search(pattern, content):
                            return True
            except:
                continue
        
        # Check for mypy configuration
        if (self.project_path / "mypy.ini").exists():
            return True
        if (self.project_path / ".mypy.ini").exists():
            return True
        
        # Check for TypeScript (inherently typed)
        if list(self.project_path.glob("**/*.ts")) or list(self.project_path.glob("**/*.tsx")):
            return True
        
        return False
    
    def _count_project_scale(self) -> tuple:
        """Count files, lines of code, and languages."""
        file_count = 0
        line_count = 0
        languages = {}
        
        code_extensions = {
            '.py': 'Python', '.js': 'JavaScript', '.jsx': 'JavaScript',
            '.ts': 'TypeScript', '.tsx': 'TypeScript', '.java': 'Java',
            '.go': 'Go', '.rs': 'Rust', '.c': 'C', '.cpp': 'C++',
            '.h': 'C/C++', '.rb': 'Ruby', '.php': 'PHP',
            '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
            '.md': 'Markdown', '.json': 'JSON', '.yml': 'YAML', '.yaml': 'YAML'
        }
        
        ignore_dirs = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', 
                      'dist', 'build', 'target', '.pytest_cache', 'coverage', '.next', 'out'}
        
        for root, dirs, files in os.walk(self.project_path):
            # Remove ignored directories from traversal
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                ext = Path(file).suffix
                if ext in code_extensions:
                    file_count += 1
                    lang = code_extensions[ext]
                    languages[lang] = languages.get(lang, 0) + 1
                    
                    # Count lines
                    try:
                        filepath = Path(root) / file
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            line_count += lines
                    except:
                        continue
        
        return file_count, line_count, languages
    
    def _extract_dependencies(self) -> Dict[str, List[str]]:
        """Extract dependencies from various package files (top 20 each)."""
        deps = {}
        
        # Python requirements
        if (self.project_path / "requirements.txt").exists():
            try:
                with open(self.project_path / "requirements.txt", 'r') as f:
                    deps['python'] = [line.split('==')[0].split('>=')[0].split('[')[0].strip() 
                                     for line in f if line.strip() and not line.startswith('#')][:20]
            except:
                deps['python'] = []
        
        # Node.js packages
        if (self.project_path / "package.json").exists():
            try:
                with open(self.project_path / "package.json", 'r') as f:
                    data = json.load(f)
                    all_deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    deps['nodejs'] = list(all_deps.keys())[:20]
            except:
                deps['nodejs'] = []
        
        return deps


def main():
    if len(sys.argv) != 2:
        print("Usage: python wtfe_context.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.isdir(project_path):
        print(f"Error: {project_path} is not a directory")
        sys.exit(1)
    
    analyzer = ContextAnalyzer(project_path)
    context = analyzer.analyze()
    signals = analyzer._collect_signals()
    
    # Output as JSON with both context and raw signals
    output = {
        "root_path": context.root_path,
        "project_name": context.project_name,
        "scale": {
            "file_count": context.file_count,
            "line_count": context.line_count,
            "languages": context.languages
        },
        "maturity": {
            "has_tests": context.has_tests,
            "has_ci": context.has_ci,
            "has_typing": context.has_typing
        },
        "signals": signals
    }
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
