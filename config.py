from pathlib import Path
from dataclasses import dataclass, field


# -----------------------------
# Base Paths
# -----------------------------

PROJECT_ROOT = Path.cwd()
CACHE_DIR = PROJECT_ROOT / ".axiom_cache"
ARTIFACT_DIR = PROJECT_ROOT / "axiom_artifacts"

CACHE_DIR.mkdir(exist_ok=True)
ARTIFACT_DIR.mkdir(exist_ok=True)


# -----------------------------
# Core Configuration
# -----------------------------

@dataclass
class AxiomConfig:
    # Parsing
    supported_languages: list[str] = field(
        default_factory=lambda: ["python"]
    )

    # Analysis
    max_file_size_kb: int = 500
    enable_caching: bool = True

    # Reporting
    default_report_format: str = "markdown"

    # Optional Features
    enable_llm: bool = False
    enable_visualization: bool = False

    # Logging
    log_level: str = "INFO"


# Global singleton-style config
CONFIG = AxiomConfig()
