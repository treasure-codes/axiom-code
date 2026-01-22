from pathlib import Path
from axiom.core.models import CodeFile, ProjectIndex
from axiom.core.file_loader import load_file
from axiom.core.language_detector import detect_language
from axiom.utils.hashing import hash_source


def scan_project(root: Path) -> ProjectIndex:
    index = ProjectIndex()

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        language = detect_language(path)
        if language == "unknown":
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

    return index
