"""Enrichment check for docstring completeness.

Detects missing docstring sections (Raises, Yields, Attributes, etc.) by
combining AST analysis with section header parsing. Implements Layer 3 of
the docstring quality model.
"""

from __future__ import annotations

import ast
import re

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
