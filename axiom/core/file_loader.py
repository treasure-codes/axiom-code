import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def load_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logger.debug("Skipping non-UTF-8 file: %s", path)
        return None
    except PermissionError:
        logger.warning("Permission denied reading file: %s", path)
        return None
    except OSError as e:
        logger.warning("Could not read %s: %s", path, e)
        return None
