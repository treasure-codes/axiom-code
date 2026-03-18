from pathlib import Path

# Only languages with working parsers. Add entries here when a parser is implemented.
SUPPORTED_EXTENSIONS: set[str] = {".py"}


def detect_language(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".py":
        return "python"
    return "unknown"
