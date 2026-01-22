import logging
from axiom_code.config import CONFIG


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, CONFIG.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
