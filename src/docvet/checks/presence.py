"""Presence check for missing and misplaced docstrings.

Detects public symbols (modules, classes, functions, methods) that lack
a docstring, flags ``@overload``-decorated functions that have docstrings
(misplaced documentation), skips definitions nested inside a function
body (unreachable by import), and reports per-file coverage statistics via
:class:`PresenceStats`.  Module-kind findings use
:func:`~docvet.ast_utils.module_display_name` for human-readable
symbol names.  Complements ruff D100–D107 by adding coverage metrics
and pipeline integration.

Examples:
    Run the presence check on a source string:

    ```python
    from docvet.checks.presence import check_presence
    from docvet.config import PresenceConfig

    findings, stats = check_presence(source, "app.py", PresenceConfig())
    ```

See Also:
    [`docvet.checks`][]: Package-level re-exports.
    [`docvet.config`][]: ``PresenceConfig`` for check configuration.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from docvet.ast_utils import Symbol, get_documented_symbols, module_display_name
from docvet.checks._finding import Finding
from docvet.config import PresenceConfig

__all__ = ["PresenceStats", "check_presence"]


@dataclass(frozen=True)
class PresenceStats:
    """Per-file docstring coverage statistics.

    Attributes:
        documented (int): Number of symbols that have a docstring.
        total (int): Total number of symbols checked (after filtering).

    Examples:
        ```python
        stats = PresenceStats(documented=3, total=5)
        assert stats.documented + 2 == stats.total
        ```
    """

    documented: int
    total: int

    @property
    def percentage(self) -> float:
        """Coverage as a percentage (0.0–100.0).

        Returns 100.0 when no symbols were checked (vacuous truth).
        """
        return (self.documented / self.total * 100.0) if self.total > 0 else 100.0


def _should_skip(symbol: Symbol, config: PresenceConfig) -> bool:
    """Determine whether a symbol should be excluded from presence checking.

    Args:
        symbol: The extracted AST symbol to evaluate.
        config: Presence configuration with ignore flags.

    Returns:
        ``True`` if the symbol should be skipped, ``False`` otherwise.
    """
    name = symbol.name

    # Module symbols are never filtered by name-based rules.
    if symbol.kind == "module":
        return False

    # __init__ has its own flag, checked before the general magic rule.
    if name == "__init__":
        return config.ignore_init

    # Magic methods: __repr__, __str__, etc.
    if name.startswith("__") and name.endswith("__"):
        return config.ignore_magic

    # Private symbols: single underscore prefix (but not dunder).
    if name.startswith("_"):
        return config.ignore_private

    return False


def _has_overload_decorator(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Check if a function node has an ``@overload`` decorator.

    Detects both bare ``@overload`` (name import) and attribute-access
    forms like ``@typing.overload`` or ``@typing_extensions.overload``.

    Args:
        node: An AST function definition node.

    Returns:
        ``True`` if any decorator matches the overload pattern.
    """
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "overload":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "overload":
            return True
    return False


def _check_overload_docstrings(
    tree: ast.Module,
    file_path: str,
) -> list[Finding]:
    """Find ``@overload``-decorated functions that have docstrings.

    Walks the AST to find function definitions decorated with
    ``@overload`` that also contain a docstring. These docstrings
    are misplaced — they belong on the implementation function instead.

    Args:
        tree: Parsed AST module.
        file_path: Relative file path for Finding construction.

    Returns:
        A list of findings for overloaded functions with docstrings.
    """
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if _has_overload_decorator(node) and ast.get_docstring(node):
            findings.append(
                Finding(
                    file=file_path,
                    line=node.lineno,
                    symbol=node.name,
                    rule="overload-has-docstring",
                    message=(
                        f"Overloaded function '{node.name}' should not have "
                        "a docstring \u2014 document the implementation instead"
                    ),
                    category="required",
                )
            )
    return findings


_FunctionNode = (ast.FunctionDef, ast.AsyncFunctionDef)
_ScopeNode = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _function_scoped_lines(tree: ast.Module) -> set[int]:
    """Collect line numbers of definitions that live inside a function.

    A function, method or class is function-scoped when any ancestor in
    its definition chain is a ``def`` or ``async def``.  Such symbols
    (closures, local helpers, classes built inside a factory and their
    methods) are unreachable by import and griffe does not list them,
    so presence does not require a docstring on them.  Definitions whose
    ancestors are only the module and classes (methods, nested classes)
    are not included.

    Args:
        tree: Parsed AST module.

    Returns:
        The ``lineno`` of every function-scoped ``FunctionDef``,
        ``AsyncFunctionDef`` and ``ClassDef`` node.
    """
    lines: set[int] = set()
    stack: list[tuple[ast.AST, bool]] = [(tree, False)]
    while stack:
        node, inside_function = stack.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, _ScopeNode) and inside_function:
                lines.add(child.lineno)
            child_inside = inside_function or isinstance(child, _FunctionNode)
            stack.append((child, child_inside))
    return lines


def check_presence(
    source: str,
    file_path: str,
    config: PresenceConfig,
) -> tuple[list[Finding], PresenceStats]:
    """Detect missing and misplaced docstrings.

    Parses *source* into an AST, extracts all documentable symbols via
    :func:`~docvet.ast_utils.get_documented_symbols`, applies the
    filtering rules from *config*, and returns one finding per
    undocumented symbol together with per-file coverage statistics.
    Module symbols use the dotted display name in findings.
    ``@overload``-decorated stubs are unconditionally excluded from
    missing-docstring checks and coverage stats (documentation belongs
    on the implementation function).  Functions and classes defined
    inside a function body (closures, local helpers, local classes and
    their methods) are likewise excluded from both findings and stats,
    because they are unreachable by import.  When
    ``config.check_overload_docstrings`` is enabled, also flags
    ``@overload``-decorated functions that have docstrings.

    Args:
        source: Raw Python source text.
        file_path: Relative file path used in Finding construction.
        config: Presence configuration controlling ignore flags.

    Returns:
        A tuple of ``(findings, stats)`` where *findings* is a list of
        :class:`~docvet.checks._finding.Finding` instances for
        undocumented symbols and *stats* is a :class:`PresenceStats`
        with coverage counts.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], PresenceStats(documented=0, total=0)

    # Empty files have no symbols worth checking.
    if not tree.body:
        return [], PresenceStats(documented=0, total=0)

    symbols = get_documented_symbols(tree)

    # Overload stubs are not documentable — documentation belongs on the
    # implementation function.  Exclude them from missing-docstring checks
    # and coverage stats unconditionally (regardless of check_overload_docstrings).
    overload_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and _has_overload_decorator(node):
            overload_lines.add(node.lineno)

    # Symbols inside a function scope are not part of the public API.
    skip_lines = overload_lines | _function_scoped_lines(tree)

    findings: list[Finding] = []
    documented = 0
    total = 0

    for symbol in symbols:
        if symbol.line in skip_lines:
            continue

        if _should_skip(symbol, config):
            continue

        total += 1

        if symbol.docstring is not None:
            documented += 1
            continue

        # Build message: module is special, others get "Public" prefix.
        if symbol.kind == "module":
            display = module_display_name(file_path)
            message = f"Module '{display}' has no docstring"
        else:
            display = symbol.name
            message = f"Public {symbol.kind} has no docstring"

        findings.append(
            Finding(
                file=file_path,
                line=symbol.line,
                symbol=display,
                rule="missing-docstring",
                message=message,
                category="required",
            )
        )

    if config.check_overload_docstrings:
        findings.extend(_check_overload_docstrings(tree, file_path))

    return findings, PresenceStats(documented=documented, total=total)
