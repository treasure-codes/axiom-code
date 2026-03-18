from pathlib import Path
from dataclasses import dataclass, field


# Base Paths (resolved relative to where the tool is invoked)
PROJECT_ROOT = Path.cwd()
CACHE_DIR = PROJECT_ROOT / ".axiom_cache"
ARTIFACT_DIR = PROJECT_ROOT / "axiom_artifacts"


@dataclass
class AxiomConfig:
    # Parsing
    supported_languages: list[str] = field(
        default_factory=lambda: ["python"]
    )
    # Analysis
    max_file_size_kb: int = 500
    enable_caching: bool = False  # not yet implemented
    # Smell thresholds
    complexity_threshold: int = 15
    god_file_symbol_threshold: int = 10
    # Reporting
    default_report_format: str = "markdown"
    # Optional Features
    enable_llm: bool = False
    enable_visualization: bool = False
    # Logging
    log_level: str = "INFO"


# Global singleton config
CONFIG = AxiomConfig()


def initialize_dirs() -> None:
    """Create required runtime directories. Call from main(), not at import time."""
    CACHE_DIR.mkdir(exist_ok=True)
    ARTIFACT_DIR.mkdir(exist_ok=True)
