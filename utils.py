import hashlib
from pathlib import Path


def read_file_safe(path: Path) -> str:
    """
    Safely read a file as text.
    Returns empty string if file cannot be read.
    """
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def hash_content(content: str) -> str:
    """
    Generate a stable hash for caching and identity.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_python_file(path: Path) -> bool:
    return path.suffix == ".py"
