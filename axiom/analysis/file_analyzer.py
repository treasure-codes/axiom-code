from axiom.analysis.call_graph import build_call_graph
from axiom.core.models import CodeFile
from axiom.metrics.complexity import compute_complexity
from axiom.metrics.importance import compute_importance
from axiom.metrics.scoring import priority_score
from axiom.parsing.dependency_graph import extract_imports
from axiom.parsing.symbol_table import extract_symbols
from axiom.smells.complexity_smells import HighComplexitySmell
from axiom.smells.structural_smells import GodFileSmell


def analyze_file(code_file: CodeFile) -> CodeFile:
    code_file.symbols = extract_symbols(code_file.source)
    code_file.imports = extract_imports(code_file.source)
    code_file.call_graph = build_call_graph(code_file.source)
    code_file.complexity = compute_complexity(code_file.source)

    importance = compute_importance(code_file.call_graph)
    code_file.priority = {
        fn: priority_score(code_file.complexity, importance.get(fn, 0.0))
        for fn in importance
    }

    smells = []
    for detector in (HighComplexitySmell(), GodFileSmell()):
        result = detector.detect(code_file)
        if result is not None:
            smells.append(result)
    code_file.smells = smells

    return code_file
