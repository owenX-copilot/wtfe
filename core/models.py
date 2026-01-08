"""Core data models for WTFE framework.

All modules output and consume these standardized data structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class FileRole(str, Enum):
    """Possible roles a file can have."""
    SERVICE = "service"
    CLI = "cli"
    LIBRARY = "library"
    TEST = "test"
    CONFIG = "config"
    BUILD = "build"
    DOCUMENTATION = "documentation"
    ENTRY_POINT = "entry_point"
    UTILITY = "utility"
    UNKNOWN = "unknown"


@dataclass
class Evidence:
    """A piece of evidence supporting a conclusion."""
    location: str  # file:line or file:line-line
    snippet: str  # actual code/text
    signal_type: str  # e.g., "import", "function_def", "network_call"
    weight: float = 1.0  # confidence weight


@dataclass
class FileFact:
    """Structured representation of a single file's extracted facts."""
    path: str
    filename: str
    language: str
    
    # Structural elements
    structures: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"classes": [...], "functions": [...], "globals": [...]}
    
    # Behavioral signals
    signals: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"imports": [...], "network": [...], "io": [...]}
    
    # Inferred roles (can be multiple)
    roles: List[FileRole] = field(default_factory=list)
    
    # Supporting evidence
    evidence: List[Evidence] = field(default_factory=list)
    
    # Confidence score (0.0-1.0)
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "path": self.path,
            "filename": self.filename,
            "language": self.language,
            "structures": self.structures,
            "signals": self.signals,
            "roles": [r.value for r in self.roles],
            "evidence": [
                {
                    "location": e.location,
                    "snippet": e.snippet,
                    "signal_type": e.signal_type,
                    "weight": e.weight
                } for e in self.evidence
            ],
            "confidence": self.confidence
        }


@dataclass
class ModuleSummary:
    """Aggregated summary of a folder/module."""
    path: str
    name: str
    
    # Files in this module
    files: List[str] = field(default_factory=list)
    core_files: List[str] = field(default_factory=list)
    helper_files: List[str] = field(default_factory=list)
    
    # Aggregated roles
    primary_role: Optional[FileRole] = None
    secondary_roles: List[FileRole] = field(default_factory=list)
    
    # Key capabilities
    capabilities: List[str] = field(default_factory=list)
    
    # Dependencies
    external_deps: List[str] = field(default_factory=list)
    
    confidence: float = 0.0


@dataclass
class EntryPoint:
    """An identified entry point for running the project."""
    file_path: str
    entry_type: str  # "main", "cli", "server", "script"
    command: Optional[str] = None  # e.g., "python main.py"
    args: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class RunConfig:
    """How to run/start the project."""
    entry_points: List[EntryPoint] = field(default_factory=list)
    
    # Build/run commands from various sources
    makefile_targets: List[str] = field(default_factory=list)
    package_scripts: Dict[str, str] = field(default_factory=dict)
    dockerfile_cmds: List[str] = field(default_factory=list)
    
    # Runtime dependencies
    requires_db: bool = False
    requires_cache: bool = False
    requires_queue: bool = False
    external_services: List[str] = field(default_factory=list)
    
    # Environment
    required_env_vars: List[str] = field(default_factory=list)


@dataclass
class ProjectContext:
    """Project-level metadata and maturity signals."""
    root_path: str
    project_name: str
    
    # Type
    project_type: str  # "application", "library", "tool", "demo", "mixed"
    
    # Maturity signals
    has_tests: bool = False
    has_ci: bool = False
    has_typing: bool = False
    has_linting: bool = False
    has_docs: bool = False
    
    # Scale
    file_count: int = 0
    line_count: int = 0
    
    # Tech stack
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
