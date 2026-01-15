"""WTFE Analyze - Unified Analysis Orchestrator.

This module coordinates all analysis pipelines and produces a comprehensive
project analysis report by integrating:

- Pipeline A1: wtfe_file (single file analysis)
- Pipeline A2: wtfe_folder (folder aggregation)
- Pipeline B1: wtfe_run (entry point detection)
- Pipeline C: wtfe_context (project context signals)
- Author-Intent Channel: wtfe_intent (documentation extraction)
Output: Unified JSON structure ready for AI-powered README generation.
"""
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import core models
from core.models import FileFact, ModuleSummary, RunConfig, ProjectContext, AuthorIntent


class ProjectAnalyzer:
    """Orchestrates all analysis pipelines."""
    
    def __init__(self, project_path: str, detail: bool = False):
        """Initialize analyzer.
        
        Args:
            project_path: Path to project root directory
            detail: Enable detailed analysis mode (includes full entry file contents)
        """
        self.project_path = Path(project_path).resolve()
        self.wtfe_root = Path(__file__).parent.parent.resolve()
        self.detail = detail
        
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not self.project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")
    
    def analyze(self) -> Dict[str, Any]:
        """Run complete analysis pipeline.
        
        Returns:
            Unified analysis result
        """
        print(f"[WTFE] Analyzing project: {self.project_path.name}", file=sys.stderr)
        
        # Initialize analysis log
        analysis_log = {
            "mode": "detail" if self.detail else "default",
            "modules": {}
        }
        
        # Pipeline A2: Folder analysis (includes A1 file analysis)
        print("[WTFE] Running Pipeline A: Folder analysis...", file=sys.stderr)
        folder_summary = self._run_folder_analysis()
        analysis_log["modules"]["folder"] = "completed"
        
        # Pipeline B1: Entry point detection (using folder analysis results)
        print("[WTFE] Running Pipeline B: Entry point detection...", file=sys.stderr)
        run_config, entry_log = self._run_entry_point_analysis(folder_summary)
        analysis_log["modules"]["entry_detection"] = "completed"
        if entry_log:
            analysis_log["entry_details"] = entry_log
        
        # Pipeline C: Project context
        print("[WTFE] Running Pipeline C: Project context signals...", file=sys.stderr)
        project_context = self._run_context_analysis()
        analysis_log["modules"]["context"] = "completed"
        
        # Author-Intent Channel
        print("[WTFE] Running Author-Intent Channel: Documentation extraction...", file=sys.stderr)
        author_intent = self._run_intent_extraction()
        analysis_log["modules"]["intent"] = "completed"
        
        # Assemble unified output
        result = {
            "metadata": {
                "project_name": self.project_path.name,
                "project_path": str(self.project_path),
                "analysis_timestamp": datetime.now().isoformat(),
                "wtfe_version": "0.1.0"
            },
            "folder_analysis": folder_summary,
            "entry_points": run_config,
            "context_signals": project_context,
            "author_intent": author_intent,
            "summary": self._generate_summary(
                folder_summary, 
                run_config, 
                project_context, 
                author_intent
            ),
            "analysis_log": analysis_log
        }
        
        print("[WTFE] Analysis complete!", file=sys.stderr)
        return result
    
    def _run_folder_analysis(self) -> Dict[str, Any]:
        """Run wtfe_folder analysis."""
        try:
            folder_module_path = self.wtfe_root / 'wtfe_folder'
            if str(folder_module_path) not in sys.path:
                sys.path.insert(0, str(folder_module_path))
            
            from wtfe_folder import FolderAnalyzer
            
            analyzer = FolderAnalyzer(str(self.project_path))
            summary = analyzer.analyze()

            out = {
                "path": summary.path,
                "name": summary.name,
                "files": summary.files,
                "core_files": summary.core_files,
                "primary_role": summary.primary_role.value if summary.primary_role else None,
                "capabilities": summary.capabilities,
                "external_deps": summary.external_deps,
                "confidence": summary.confidence
            }

            # Build compressed per-file facts to include in prompts (concise summary)
            try:
                # load configuration defaults
                cfg_path = self.wtfe_root / 'wtfe_readme' / 'config.yaml'
                max_files = 20
                max_chars_per_item = 800
                max_total_chars = 10000
                if cfg_path.exists():
                    try:
                        import yaml
                        with open(cfg_path, 'r', encoding='utf-8') as cf:
                            cfg = yaml.safe_load(cf) or {}
                            max_files = int(cfg.get('max_compressed_files', max_files))
                            max_chars_per_item = int(cfg.get('max_chars_per_item', max_chars_per_item))
                            max_total_chars = int(cfg.get('max_compressed_chars', max_total_chars))
                    except Exception:
                        pass

                file_facts = []
                total_chars = 0
                for fact in analyzer.facts:
                    # Skip markdown files from compressed facts — README(s) handled by author_intent
                    try:
                        suffix = Path(fact.path).suffix.lower()
                    except Exception:
                        suffix = ''
                    if suffix in {'.md', '.markdown'}:
                        continue
                    if len(file_facts) >= max_files or total_chars >= max_total_chars:
                        break

                    # skip external / likely third-party by simple heuristic (path contains site-packages or node_modules)
                    try:
                        p = Path(fact.path)
                        parts = {pp.lower() for pp in p.parts}
                    except Exception:
                        parts = set()
                    if parts & {"site-packages", "node_modules", "dist", "build"}:
                        continue

                    # one-line doc: prefer module_doc then first class/function doc
                    one_line = None
                    try:
                        one_line = (fact.signals or {}).get('module_doc')
                    except Exception:
                        one_line = None
                    if not one_line:
                        try:
                            structs = fact.structures or {}
                            if structs.get('classes'):
                                one_line = structs['classes'][0].get('doc')
                            elif structs.get('functions'):
                                one_line = structs['functions'][0].get('doc')
                        except Exception:
                            one_line = None

                    # top defs
                    top_defs = []
                    try:
                        structs = fact.structures or {}
                        for c in structs.get('classes', [])[:2]:
                            top_defs.append({"name": c.get('name'), "signature": None, "doc": (c.get('doc') or '')[:140]})
                        for fct in structs.get('functions', [])[:3]:
                            top_defs.append({"name": fct.get('name'), "signature": fct.get('signature'), "doc": (fct.get('doc') or '')[:140]})
                    except Exception:
                        top_defs = []

                    # top calls
                    top_calls = []
                    try:
                        calls = (fact.signals or {}).get('calls_sample', [])
                        for c in calls[:3]:
                            top_calls.append(c.get('sample') if isinstance(c, dict) else str(c))
                    except Exception:
                        top_calls = []

                    # estimate size (chars)
                    est_size = 0
                    try:
                        p = Path(fact.path)
                        if p.exists():
                            est_size = len(p.read_text(encoding='utf-8', errors='ignore'))
                    except Exception:
                        est_size = 0

                    item = {
                        "path": fact.path,
                        "filename": fact.filename,
                        "roles": [r.value for r in fact.roles] if fact.roles else [],
                        "one_line": (one_line or '')[:140],
                        "top_defs": top_defs,
                        "top_calls": top_calls,
                        "calls_from_core": fact.filename in summary.core_files,
                        "est_size": est_size,
                        "confidence": getattr(fact, 'confidence', 0.0)
                    }

                    approx_chars = len(item['one_line']) + sum(len(d.get('doc','')) for d in top_defs) + sum(len(c) for c in top_calls)
                    approx_chars = min(approx_chars, max_chars_per_item)
                    if total_chars + approx_chars > max_total_chars and file_facts:
                        break

                    file_facts.append(item)
                    total_chars += approx_chars

                out['file_facts_compressed'] = file_facts
            except Exception:
                # non-fatal; don't attach compressed facts on error
                pass

            return out
        except Exception as e:
            print(f"[WTFE] Warning: Folder analysis failed: {e}", file=sys.stderr)
            return {"error": str(e)}
    
    def _run_entry_point_analysis(self, folder_summary: Optional[Dict[str, Any]] = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Run wtfe_run analysis.

        Args:
            folder_summary: Optional result from folder analysis

        Returns:
            Tuple of (config_dict, analysis_log_dict)
        """
        try:
            run_module_path = self.wtfe_root / 'wtfe_run'
            if str(run_module_path) not in sys.path:
                sys.path.insert(0, str(run_module_path))

            from wtfe_run import EntryPointDetector

            detector = EntryPointDetector(str(self.project_path))
            config, entry_log = detector.detect(detail=self.detail, folder_analysis_result=folder_summary)
            
            config_dict = {
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
                    "requires_queue": config.requires_queue,
                    "external_services": config.external_services
                }
            }
            
            return config_dict, entry_log
        except Exception as e:
            print(f"[WTFE] Warning: Entry point analysis failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return {"error": str(e)}, {}
    
    def _run_context_analysis(self) -> Dict[str, Any]:
        """Run wtfe_context analysis."""
        try:
            context_module_path = self.wtfe_root / 'wtfe_context'
            if str(context_module_path) not in sys.path:
                sys.path.insert(0, str(context_module_path))
            if str(self.wtfe_root) not in sys.path:
                sys.path.insert(0, str(self.wtfe_root))
            
            from wtfe_context import ContextAnalyzer
            
            analyzer = ContextAnalyzer(str(self.project_path))
            context = analyzer.analyze()
            signals = analyzer._collect_signals()
            
            return {
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
        except Exception as e:
            print(f"[WTFE] Warning: Context analysis failed: {e}", file=sys.stderr)
            return {"error": str(e)}
    
    def _run_intent_extraction(self) -> Dict[str, Any]:
        """Run wtfe_intent extraction."""
        try:
            intent_module_path = self.wtfe_root / 'wtfe_intent'
            if str(intent_module_path) not in sys.path:
                sys.path.insert(0, str(intent_module_path))
            
            from wtfe_intent import IntentExtractor
            
            extractor = IntentExtractor(str(self.project_path))
            intent = extractor.extract()
            
            return intent.to_dict()
        except Exception as e:
            print(f"[WTFE] Warning: Intent extraction failed: {e}", file=sys.stderr)
            return {"error": str(e)}
    
    def _generate_summary(
        self, 
        folder: Dict, 
        run: Dict, 
        context: Dict, 
        intent: Dict
    ) -> Dict[str, Any]:
        """Generate high-level summary."""
        summary = {
            "has_documentation": intent.get("project_readme") is not None,
            "documentation_coverage": {
                "project_readme": intent.get("project_readme") is not None,
                "module_readmes": len(intent.get("module_readmes", {})),
                "changelog": intent.get("changelog") is not None,
                "license": intent.get("license_text") is not None
            },
            "primary_role": folder.get("primary_role"),
            "can_run": len(run.get("entry_points", [])) > 0,
            "entry_point_count": len(run.get("entry_points", [])),
            "external_deps_count": len(folder.get("external_deps", [])),
            "file_count": len(folder.get("files", [])),
            "has_tests": context.get("maturity", {}).get("has_tests", False),
            "has_ci": context.get("maturity", {}).get("has_ci", False),
            "has_typing": context.get("maturity", {}).get("has_typing", False)
        }
        
        return summary


def main():
    """Command-line interface."""
    if len(sys.argv) < 2:
        print("Usage: python wtfe_analyze.py <project_path> [--detail]")
        print("\nExample:")
        print("  python wtfe_analyze.py ./example/example_folder")
        print("  python wtfe_analyze.py /path/to/project --detail")
        sys.exit(1)
    
    project_path = sys.argv[1]
    detail = '--detail' in sys.argv
    
    try:
        analyzer = ProjectAnalyzer(project_path, detail=detail)
        result = analyzer.analyze()
        
        # Output JSON to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
