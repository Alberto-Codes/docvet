"""Enrichment check for docstring completeness.

Detects missing docstring sections (Raises, Yields, Attributes, etc.) by
combining AST analysis with section header parsing. Implements Layer 3 of
the docstring quality model.
"""

from __future__ import annotations

import ast
import re

from docvet.ast_utils import Symbol, get_documented_symbols
from docvet.checks import Finding
from docvet.config import EnrichmentConfig

# ---------------------------------------------------------------------------
# Section header constants
# ---------------------------------------------------------------------------

# All 10 recognized Google-style section headers.
# Args and Returns are included for parsing context (FR15) — they are
# recognized but never checked for absence (layers 1-2 are ruff/interrogate).
_SECTION_HEADERS = frozenset(
    {
        "Args",
        "Returns",
        "Raises",
        "Yields",
        "Receives",
        "Warns",
        "Other Parameters",
        "Attributes",
        "Examples",
        "See Also",
    }
)

_SECTION_PATTERN = re.compile(
    r"^\s*"
    r"(Args|Returns|Raises|Yields|Receives|Warns"
    r"|Other Parameters|Attributes|Examples|See Also)"
    r":\s*$",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Shared helper functions
# ---------------------------------------------------------------------------


def _parse_sections(docstring: str) -> set[str]:
    """Extract recognized Google-style section headers from a docstring.

    Scans the raw docstring text line-by-line with a compiled regex and
    returns any of the 10 recognized section headers that match. Handles
    varied indentation gracefully (module-level with no indent, method-level
    with 8+ spaces).

    The parser does not validate overall docstring structure — a partially
    malformed docstring can still yield matches for its well-formed headers.
    Headers inside fenced code blocks may also match, which produces false
    negatives at the rule level (safe direction per NFR5) since the rule
    will believe the section exists.

    Args:
        docstring: The raw docstring text to parse.

    Returns:
        A set of header names found in the docstring. Returns an empty set
        when no recognized section headers are found.
    """
    return set(_SECTION_PATTERN.findall(docstring))


_NodeT = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef


def _build_node_index(tree: ast.Module) -> dict[int, _NodeT]:
    """Build a line-number-to-AST-node lookup table for O(1) access.

    Walks the AST tree once and collects all ``FunctionDef``,
    ``AsyncFunctionDef``, and ``ClassDef`` nodes, indexed by their line
    number. This enables rules to retrieve the AST node for a symbol via
    ``symbol.line`` without re-walking the tree for each rule.

    Args:
        tree: The parsed AST tree for the source file.

    Returns:
        A dict mapping line numbers to AST nodes. Module-level symbols
        have no corresponding node, so ``node_index.get(symbol.line)``
        returns ``None`` for them.
    """
    index: dict[int, _NodeT] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            index[node.lineno] = node
    return index


# ---------------------------------------------------------------------------
# Rule functions
# ---------------------------------------------------------------------------


def _check_missing_raises(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a function that raises exceptions without a Raises section.

    Walks the function's AST subtree to find ``raise`` statements and
    extracts exception class names. Returns a finding when exceptions are
    raised but no ``Raises:`` section is present in the docstring.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-raises"`` when exceptions are
        raised without documentation, or ``None`` otherwise.
    """
    node = node_index.get(symbol.line)
    if node is None:
        return None

    if "Raises" in sections:
        return None

    names: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Raise):
            continue
        if child.exc is None:
            names.add("(re-raise)")
        elif isinstance(child.exc, ast.Name):
            names.add(child.exc.id)
        elif isinstance(child.exc, ast.Call):
            if isinstance(child.exc.func, ast.Name):
                names.add(child.exc.func.id)
            elif isinstance(child.exc.func, ast.Attribute):
                names.add(child.exc.func.attr)
        elif isinstance(child.exc, ast.Attribute):
            names.add(child.exc.attr)

    if not names:
        return None

    exception_names = ", ".join(sorted(names))
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-raises",
        message=(
            f"Function '{symbol.name}' raises {exception_names} "
            f"but has no Raises: section"
        ),
        category="required",
    )


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------


def check_enrichment(
    source: str,
    tree: ast.Module,
    config: EnrichmentConfig,
    file_path: str,
) -> list[Finding]:
    """Run all enrichment rules on a parsed source file.

    Iterates over documented symbols, parses their docstring sections,
    and dispatches to each enabled rule function. Symbols without a
    docstring are skipped (FR20). Config gating controls which rules run.

    Args:
        source: Raw source text of the file (reserved for future rules).
        tree: Parsed AST module from ``ast.parse()``.
        config: Enrichment configuration controlling rule toggles.
        file_path: Source file path for finding records.

    Returns:
        A list of findings from all enabled enrichment rules. Returns an
        empty list when no issues are detected.
    """
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    findings: list[Finding] = []

    for symbol in symbols:
        if not symbol.docstring:
            continue
        sections = _parse_sections(symbol.docstring)

        if config.require_raises:
            if f := _check_missing_raises(
                symbol, sections, node_index, config, file_path
            ):
                findings.append(f)
        # Future rules dispatched here in taxonomy-table order

    return findings
