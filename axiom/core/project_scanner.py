import logging
from pathlib import Path

from axiom.config import CONFIG
from axiom.core.file_loader import load_file
from axiom.core.language_detector import detect_language
from axiom.core.models import CodeFile, ProjectIndex
from axiom.utils.hashing import hash_source

logger = logging.getLogger(__name__)

SKIP_DIRS: set[str] = {
    "__pycache__", ".git", ".hg", ".svn",
    ".venv", "venv", "env", ".env",
    "node_modules", "dist", "build",
    ".tox", ".mypy_cache", ".pytest_cache",
    "axiom_artifacts", ".axiom_cache",
}


def scan_project(root: Path) -> ProjectIndex:
    root = root.resolve()

    if not root.exists():
        raise ValueError(f"Path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Path is not a directory: {root}")

    index = ProjectIndex()
    max_bytes = CONFIG.max_file_size_kb * 1024

    for path in root.rglob("*"):
        # Skip symlinks to avoid infinite loops
        if path.is_symlink():
            logger.debug("Skipping symlink: %s", path)
            continue

        if not path.is_file():
            continue

        # Skip known noisy directories
        if any(part in SKIP_DIRS for part in path.parts):
            continue

        language = detect_language(path)
        if language == "unknown":
            continue

        # Enforce file size limit
        try:
            if path.stat().st_size > max_bytes:
                logger.debug("Skipping oversized file (%d KB): %s", path.stat().st_size // 1024, path)
                continue
        except OSError:
            continue

        source = load_file(path)
        if source is None:
            continue

        code_file = CodeFile(
            path=str(path),
            language=language,
            source=source,
            hash=hash_source(source),
        )
        index.files[str(path)] = code_file
        logger.debug("Indexed: %s", path)

    logger.info("Scanned %d files in %s", len(index.files), root)
    return index
