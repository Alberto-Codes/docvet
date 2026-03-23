"""Deprecation notice enrichment checks.

Detects functions using deprecation patterns (``@deprecated`` decorator
or ``warnings.warn`` with deprecation categories) without a corresponding
deprecation notice in the docstring.

See Also:
    [`docvet.checks.enrichment`][]: Orchestrator and dispatch table.
    [`docvet.checks._finding`][]: ``Finding`` dataclass.

Examples:
    Invoke the deprecation check directly:

    ```python
    finding = _check_missing_deprecation(symbol, sections, node_index, config, path)
    ```
"""

from __future__ import annotations

import ast

from docvet.ast_utils import Symbol
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

from ._forward import _is_warn_call, _NodeT

_DEPRECATION_CATEGORIES: frozenset[str] = frozenset(
    {"DeprecationWarning", "PendingDeprecationWarning", "FutureWarning"}
)


def _category_name(node: ast.expr) -> str | None:
    """Resolve the name from an ``ast.Name`` or ``ast.Attribute`` node.

    Returns the ``id`` for ``ast.Name`` or the ``attr`` for
    ``ast.Attribute``, which covers both bare (``DeprecationWarning``)
    and qualified (``warnings.DeprecationWarning``) forms.

    Args:
        node: The expression node to inspect.

    Returns:
        The resolved name string, or ``None`` for other node types.
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_deprecation_warn_call(node: ast.Call) -> bool:
    """Check whether a ``warnings.warn()`` call uses a deprecation category.

    First confirms the call is a warn invocation via :func:`_is_warn_call`,
    then inspects the second positional argument or the ``category`` keyword
    argument for ``DeprecationWarning``, ``PendingDeprecationWarning``, or
    ``FutureWarning``.  Handles both ``ast.Name`` (bare) and
    ``ast.Attribute`` (qualified) forms via :func:`_category_name`.

    Calls with no explicit category default to ``UserWarning`` at runtime
    and are intentionally **not** matched.

    Args:
        node: The ``ast.Call`` node to inspect.

    Returns:
        ``True`` when the call is a deprecation-category warn.
    """
    if not _is_warn_call(node):
        return False

    # Check second positional argument (e.g., warnings.warn("msg", DeprecationWarning))
    if len(node.args) >= 2:
        name = _category_name(node.args[1])
        if name in _DEPRECATION_CATEGORIES:
            return True

    # Check category keyword argument (e.g., warnings.warn("msg", category=DeprecationWarning))
    for kw in node.keywords:
        if kw.arg == "category":
            name = _category_name(kw.value)
            if name in _DEPRECATION_CATEGORIES:
                return True

    return False


def _has_deprecated_decorator(node: _NodeT) -> bool:
    """Check whether a function has a ``@deprecated`` call-form decorator.

    PEP 702 requires a mandatory *msg* argument, so real-world usage is
    always ``@deprecated("reason")`` — an ``ast.Call`` wrapping the name.
    This helper checks only the ``ast.Call`` form; bare ``ast.Name`` and
    ``ast.Attribute`` are intentionally ignored (the existing
    :func:`_has_decorator` handles those, but ``@deprecated`` without
    parentheses is not valid per PEP 702).

    Handles both unqualified (``@deprecated("msg")``) and qualified
    (``@typing_extensions.deprecated("msg")``,
    ``@warnings.deprecated("msg")``) forms.

    Args:
        node: The function or class AST node to inspect.

    Returns:
        ``True`` when the node has a ``@deprecated(...)`` decorator.
    """
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name) and dec.func.id == "deprecated":
                return True
            if isinstance(dec.func, ast.Attribute) and dec.func.attr == "deprecated":
                return True
    return False


def _check_missing_deprecation(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a function with deprecation patterns but no deprecation notice.

    Checks for two deprecation pattern families:

    1. ``@deprecated("reason")`` decorator (PEP 702) via
       :func:`_has_deprecated_decorator`.
    2. ``warnings.warn(..., DeprecationWarning)`` (and
       ``PendingDeprecationWarning``, ``FutureWarning``) via a scope-aware
       AST walk using :func:`_is_deprecation_warn_call`.

    A deprecation notice is satisfied by the word ``"deprecated"``
    appearing anywhere in the docstring (case-insensitive).  This
    intentionally loose check avoids false positives from different
    notice formats (Google ``Deprecated:`` section, Sphinx
    ``.. deprecated::`` directive, inline mentions).

    The walk is scope-aware: it stops at nested ``FunctionDef``,
    ``AsyncFunctionDef``, and ``ClassDef`` boundaries.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-deprecation"`` when
        deprecation patterns exist without a notice, or ``None``.
    """
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    if node is None:
        return None

    if symbol.docstring is None:
        return None

    # Loose docstring check — "deprecated" anywhere, case-insensitive.
    if "deprecated" in symbol.docstring.lower():
        return None

    # Check @deprecated decorator first (fast path).
    if _has_deprecated_decorator(node):
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=symbol.name,
            rule="missing-deprecation",
            message=(
                f"Function '{symbol.name}' has @deprecated decorator "
                "but no deprecation notice in docstring"
            ),
            category="required",
        )

    # Scope-aware walk for deprecation warn calls.
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Call) and _is_deprecation_warn_call(child):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-deprecation",
                message=(
                    f"Function '{symbol.name}' uses deprecation warnings "
                    "but has no deprecation notice in docstring"
                ),
                category="required",
            )
        stack.extend(ast.iter_child_nodes(child))

    return None
