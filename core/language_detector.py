from pathlib import Path


EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
}


def detect_language(path: Path) -> str:
    return EXTENSION_LANGUAGE_MAP.get(path.suffix.lower(), "unknown")
