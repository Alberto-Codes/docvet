"""Reverse enrichment checks — docstring claims behaviour code doesn't exhibit.

Detects ``Raises:``, ``Yields:``, and ``Returns:`` sections that describe
behaviour the function body does not actually implement.  Each check uses
a scope-aware AST walk that stops at nested function/class boundaries.

See Also:
    [`docvet.checks.enrichment`][]: Orchestrator and dispatch table.
    [`docvet.checks._finding`][]: ``Finding`` dataclass.

Examples:
    Invoke the extra-raises check directly:

    ```python
    finding = _check_extra_raises_in_docstring(symbol, sections, idx, cfg, path)
    ```
"""

from __future__ import annotations

import ast

import docvet.checks.enrichment as _enrichment_pkg
from docvet.ast_utils import Symbol
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

from . import _should_skip_reverse_check
from ._forward import _extract_exception_name, _is_meaningful_return, _NodeT
from ._params import _parse_raises_entries


def _check_extra_raises_in_docstring(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect documented exceptions not raised in the function body.

    Parses the ``Raises:`` section to collect documented exception names,
    then walks the AST subtree (scope-aware) to collect actually raised
    exceptions.  Any documented name absent from the code is flagged.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="extra-raises-in-docstring"`` when
        documented exceptions are not raised, or ``None`` otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None
    if "Raises" not in sections:
        return None
    if symbol.docstring is None:
        return None
    node = node_index.get(symbol.line)
    if node is None:
        return None
    if _should_skip_reverse_check(node):
        return None

    doc_raises = _parse_raises_entries(
        symbol.docstring, style=_enrichment_pkg._active_style
    )
    if not doc_raises:
        return None

    # Scope-aware walk to collect actually raised exception names.
    code_raises: set[str] = set()
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Raise):
            name = _extract_exception_name(child)
            if name is not None:
                code_raises.add(name)
        stack.extend(ast.iter_child_nodes(child))

    extra = sorted(doc_raises - code_raises)
    if not extra:
        return None

    names = ", ".join(extra)
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="extra-raises-in-docstring",
        message=(f"Function '{symbol.name}' documents exceptions not raised: {names}"),
        category="recommended",
    )


def _check_extra_yields_in_docstring(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a Yields section on a function that never yields.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="extra-yields-in-docstring"`` when
        a Yields section exists but the code never yields, or ``None``
        otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None
    if "Yields" not in sections:
        return None
    node = node_index.get(symbol.line)
    if node is None:
        return None
    if _should_skip_reverse_check(node):
        return None

    # Scope-aware walk for yield/yield-from.
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            return None  # Section is truthful.
        stack.extend(ast.iter_child_nodes(child))

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="extra-yields-in-docstring",
        message=(f"Function '{symbol.name}' has a Yields: section but does not yield"),
        category="recommended",
    )


def _check_extra_returns_in_docstring(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a Returns section on a function with no meaningful return.

    A function with only bare ``return`` or ``return None`` has no
    meaningful return value — a ``Returns:`` section is misleading.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="extra-returns-in-docstring"`` when
        a Returns section exists but the code has no meaningful return,
        or ``None`` otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None
    if "Returns" not in sections:
        return None
    node = node_index.get(symbol.line)
    if node is None:
        return None
    if _should_skip_reverse_check(node):
        return None

    # Scope-aware walk for meaningful return statements.
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Return) and _is_meaningful_return(child):
            return None  # Section is truthful.
        stack.extend(ast.iter_child_nodes(child))

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="extra-returns-in-docstring",
        message=(
            f"Function '{symbol.name}' has a Returns: section "
            f"but does not return a value"
        ),
        category="recommended",
    )
