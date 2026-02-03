# Axiom-Code

**Autonomous Semantic Analysis & Interpretability Engine**

Axiom-Code is a research-grade, deterministic-first static analysis platform that converts raw source code into structured, prioritized, and human-understandable insight. It combines compiler-style program analysis, graph algorithms, and explainability-focused design to help engineers understand, triage, and refactor large codebases.

> **Positioning:** This project is intentionally designed to feel like an internal developer productivity system or research prototype — not a classroom assignment.

---

## Table of Contents

1. Motivation
2. What Axiom-Code Is (and Is Not)
3. Core Capabilities
4. High-Level Architecture
5. Execution Flow
6. Key Technical Concepts
7. AI & Explainability Philosophy
8. CLI Usage
9. Outputs & Reports
10. Extensibility Model
11. Evaluation & Benchmarks
12. Project Status & Roadmap

---

## 1. Motivation

Modern codebases grow faster than human understanding. Traditional tools (linters, formatters, docstring generators) operate at the surface level and fail to answer questions like:

* *Which parts of the system actually matter most?*
* *Where is architectural risk accumulating?*
* *Why does this file exist, and how does it interact with the rest of the system?*

Axiom-Code exists to close that gap.

It treats a codebase as a **semantic system** rather than a collection of files — extracting structure, relationships, and intent using static analysis and graph theory, with optional AI-based refinement layered on top.

---

## 2. What Axiom-Code Is (and Is Not)

### Axiom-Code **is**:

* A deterministic-first static analysis engine
* A semantic indexing and prioritization system
* A platform for explainable code understanding
* Designed for onboarding, refactoring triage, and architectural insight

### Axiom-Code **is not**:

* A simple docstring generator
* A linter replacement
* An AI-only or prompt-driven system
* A cloud-dependent service

AI is treated as an *optional refinement layer*, not the source of truth.

---

## 3. Core Capabilities

### Static Program Analysis

* AST parsing (Python-first, extensible)
* Symbol extraction (functions, classes, imports)
* Call graph construction
* Dependency resolution

### Graph-Based Insight

* Function importance via centrality metrics
* Detection of architectural bottlenecks
* Identification of circular dependencies
* Project-level prioritization

### Semantic Analysis

* Heuristic explanations of files and functions
* Complexity scoring
* Smell detection (complexity, structural, architectural)
* Priority ranking for refactoring

### Explainability

* Structured explanation models
* Deterministic summaries derived from code facts
* AI-ready context objects (without AI dependency)

---

## 4. High-Level Architecture

Axiom-Code follows a strict layered architecture to maintain clarity, testability, and extensibility:

```
CLI Layer
   ↓
Orchestration Layer
   ↓
Indexing & Parsing Layer
   ↓
Analysis & Metrics Layer
   ↓
Explanation Layer
   ↓
Output Layer
```

Each layer communicates through explicit data models rather than implicit side effects.

---

## 5. Execution Flow

1. **CLI Invocation**

   * User runs `axiom analyze <path>` or `axiom explain <path>`

2. **Project Indexing**

   * Files are discovered, hashed, and language-detected
   * Code files are loaded into a `ProjectIndex`

3. **Parsing & Graph Construction**

   * ASTs are generated
   * Symbols and call relationships are extracted

4. **Analysis Pipeline**

   * Complexity metrics computed
   * Importance and priority scores calculated
   * Code smells detected

5. **Explanation Generation**

   * Structured explanations built from analysis artifacts

6. **Output Generation**

   * Markdown, JSON, or console summaries emitted

---

## 6. Key Technical Concepts

### Deterministic-First Design

All primary insights are derived from static analysis and graph algorithms. This ensures:

* Reproducibility
* Explainability
* No hallucinated behavior

### Importance vs Complexity

Axiom-Code explicitly separates:

* *Complexity*: how difficult code is internally
* *Importance*: how central code is to the system

This allows accurate prioritization (high-importance + high-complexity = urgent).

### Structured Models

Core concepts are represented as explicit dataclasses (e.g., `CodeFile`, `CodeSymbol`, `FunctionExplanation`). This enables:

* Clear reasoning
* Easy extension
* AI integration without refactoring

---

## 7. AI & Explainability Philosophy

Axiom-Code does **not** require AI to function.

Instead, it provides **AI-ready context primitives**, including:

* Symbol graphs
* Dependency graphs
* Metrics and smells
* Deterministic summaries

If enabled, an LLM can:

* Refine explanations
* Improve readability
* Assist with natural-language queries

AI is never trusted with logic inference or control flow understanding.

---

## 8. CLI Usage

```bash
axiom analyze ./repo
axiom analyze ./repo --markdown report.md
axiom analyze ./repo --json report.json
axiom explain ./repo
```

The CLI is designed to be scriptable, composable, and CI-friendly.

---

## 9. Outputs & Reports

### Markdown Reports

* Project overview
* Ranked files by priority
* Detected smells
* Key metrics

### JSON Output

* Machine-readable analysis results
* Suitable for dashboards or integrations

### Console Output

* Quick summaries for exploratory analysis

---

## 10. Extensibility Model

### Adding New Smells

* Implement the `CodeSmell` interface
* Register the detector
* Automatically included in analysis

### Adding New Metrics

* Define a metric module
* Integrate into scoring

### Adding AI Refinement

* Consume explanation context objects
* No changes required to core analysis

---

## 11. Evaluation & Benchmarks

Axiom-Code is designed to support research-style evaluation, including:

* Runtime analysis
* Memory usage
* Smell detection precision
* Explanation quality comparisons

This positions the system for academic or advanced engineering use.

---

## 12. Project Status & Roadmap

### Current State

* Fully functional Python analysis pipeline
* CLI-driven analysis and explanation
* Deterministic summaries and prioritization

### Planned Enhancements

* Multi-language parsing
* Interactive visualization
* Optional local LLM refinement
* Benchmark suite expansion

---

## License

MIT License
