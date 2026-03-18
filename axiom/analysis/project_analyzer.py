import logging

from axiom.analysis.file_analyzer import analyze_file
from axiom.core.models import ProjectIndex

logger = logging.getLogger(__name__)


def analyze_project(project_index: ProjectIndex) -> ProjectIndex:
    total = len(project_index.files)
    for i, code_file in enumerate(project_index.files.values(), 1):
        logger.debug("Analyzing file %d/%d: %s", i, total, code_file.path)
        analyze_file(code_file)
    logger.info("Analyzed %d files", total)
    return project_index
