"""Shared AST helpers for docstring range extraction and symbol mapping."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Literal

__all__: list[str] = []

_ScopeNode = ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Symbol:
    """An extracted documentable symbol from a Python AST.

    Attributes:
        name (str): Symbol name, or ``"<module>"`` for the module
            itself.
        kind (str): One of ``"function"``, ``"class"``, ``"method"``,
            or ``"module"``.
        line (int): The ``def``/``class`` keyword line
            (``node.lineno``).
        end_line (int): Last line of the symbol's body.
        definition_start (int): First decorator line, or ``line`` when
            undecorated.
        docstring (str | None): Raw docstring text, or *None* if
            absent.
        docstring_range (tuple[int, int] | None): Line range of the
            docstring expression, or *None*.
        signature_range (tuple[int, int] | None): Line range of the
            function signature, or *None* for classes and modules.
        body_range (tuple[int, int]): Line range of the body excluding
            the docstring.
        parent (str | None): Immediate enclosing class name, or
            *None*.
    """

    name: str
    kind: Literal["function", "class", "method", "module"]
    line: int
    end_line: int
    definition_start: int
    docstring: str | None
    docstring_range: tuple[int, int] | None
    signature_range: tuple[int, int] | None
    body_range: tuple[int, int]
    parent: str | None


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _node_end_line(node: ast.AST) -> int:
    """Return the end line for an AST node.

    ``Module`` nodes lack ``end_lineno``, so this derives the value
    from the last body statement when necessary.

    Args:
        node: Any AST node.

    Returns:
        The last source line occupied by *node*.
    """
    end = getattr(node, "end_lineno", None)
    if end is not None:
        return end
    body = getattr(node, "body", None)
    if body:
        return _node_end_line(body[-1])
    return 1


# ---------------------------------------------------------------------------
# Range helpers
# ---------------------------------------------------------------------------


def get_docstring_range(node: ast.AST) -> tuple[int, int] | None:
    """Return the line range of a node's docstring expression.

    Args:
        node: An AST node (typically ``Module``, ``FunctionDef``,
            ``AsyncFunctionDef``, or ``ClassDef``).

    Returns:
        A ``(start_line, end_line)`` tuple for the docstring, or
        *None* if the node has no docstring.
    """
    if not isinstance(node, _ScopeNode):
        return None
    body = node.body
    if not body:
        return None
    first = body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return (first.lineno, first.end_lineno or first.lineno)
    return None


def get_body_range(node: ast.AST) -> tuple[int, int]:
    """Return the line range of a node's body, excluding the docstring.

    Args:
        node: An AST node with a ``body`` attribute.

    Returns:
        A ``(start_line, end_line)`` tuple. When the body is
        effectively empty, both values equal the node's end line.
    """
    if not isinstance(node, _ScopeNode):
        end = _node_end_line(node)
        return (end, end)

    body = node.body
    end_lineno = _node_end_line(node)

    if not body:
        return (end_lineno, end_lineno)

    doc_range = get_docstring_range(node)
    if doc_range is not None:
        start = doc_range[1] + 1
        if start > end_lineno:
            return (end_lineno, end_lineno)
        return (start, end_lineno)

    return (body[0].lineno, end_lineno)


def get_signature_range(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[int, int]:
    """Return the line range of a function's signature.

    The range starts at the ``def``/``async def`` keyword line and ends
    just before the body begins. Decorator lines are excluded.

    Args:
        node: A ``FunctionDef`` or ``AsyncFunctionDef`` AST node.

    Returns:
        A ``(start_line, end_line)`` tuple for the signature.
    """
    return (node.lineno, max(node.lineno, node.body[0].lineno - 1))


# ---------------------------------------------------------------------------
# Symbol extraction
# ---------------------------------------------------------------------------


def _walk_node(
    node: ast.AST,
    symbols: list[Symbol],
    parent_class: str | None,
) -> None:
    """Recursively extract documentable symbols from an AST subtree.

    Args:
        node: The current AST node to inspect.
        symbols: Accumulator list for discovered symbols.
        parent_class: Enclosing class name, or *None* when not inside
            a class body.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            doc_range = get_docstring_range(child)
            docstring = ast.get_docstring(child, clean=False)
            symbols.append(
                Symbol(
                    name=child.name,
                    kind="class",
                    line=child.lineno,
                    end_line=child.end_lineno or child.lineno,
                    definition_start=(
                        child.decorator_list[0].lineno
                        if child.decorator_list
                        else child.lineno
                    ),
                    docstring=docstring,
                    docstring_range=doc_range,
                    signature_range=None,
                    body_range=get_body_range(child),
                    parent=parent_class,
                )
            )
            _walk_node(child, symbols, parent_class=child.name)

        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            kind: Literal["function", "method"] = (
                "method" if parent_class is not None else "function"
            )
            doc_range = get_docstring_range(child)
            docstring = ast.get_docstring(child, clean=False)
            symbols.append(
                Symbol(
                    name=child.name,
                    kind=kind,
                    line=child.lineno,
                    end_line=child.end_lineno or child.lineno,
                    definition_start=(
                        child.decorator_list[0].lineno
                        if child.decorator_list
                        else child.lineno
                    ),
                    docstring=docstring,
                    docstring_range=doc_range,
                    signature_range=get_signature_range(child),
                    body_range=get_body_range(child),
                    parent=parent_class,
                )
            )
            # Nested functions lose class context.
            _walk_node(child, symbols, parent_class=None)


def get_documented_symbols(tree: ast.Module) -> list[Symbol]:
    """Extract all documentable symbols from a parsed module.

    Returns a flat list containing a module symbol followed by every
    ``class``, ``function``, and ``method`` found in the tree.

    Args:
        tree: A parsed ``ast.Module`` from ``ast.parse()``.

    Returns:
        Flat list of :class:`Symbol` instances ordered by line number.
    """
    end_line = _node_end_line(tree)
    doc_range = get_docstring_range(tree)
    docstring = ast.get_docstring(tree, clean=False)

    module_symbol = Symbol(
        name="<module>",
        kind="module",
        line=1,
        end_line=end_line,
        definition_start=1,
        docstring=docstring,
        docstring_range=doc_range,
        signature_range=None,
        body_range=get_body_range(tree),
        parent=None,
    )

    symbols: list[Symbol] = [module_symbol]
    _walk_node(tree, symbols, parent_class=None)
    symbols.sort(key=lambda s: s.line)
    return symbols


# ---------------------------------------------------------------------------
# Line mapping
# ---------------------------------------------------------------------------


def map_lines_to_symbols(tree: ast.Module) -> dict[int, Symbol]:
    """Map each source line to its innermost containing symbol.

    Args:
        tree: A parsed ``ast.Module`` from ``ast.parse()``.

    Returns:
        A dict mapping line numbers (1-based) to the most specific
        :class:`Symbol` whose definition range contains that line.
    """
    symbols = get_documented_symbols(tree)

    # Sort by range size ascending — smallest (innermost) first.
    # Tiebreaker: non-module symbols before module (more specific wins).
    symbols_by_size = sorted(
        symbols,
        key=lambda s: (s.end_line - s.definition_start, s.kind == "module"),
    )

    module_sym = next(s for s in symbols if s.kind == "module")
    line_map: dict[int, Symbol] = {}

    for line in range(1, module_sym.end_line + 1):
        for sym in symbols_by_size:
            if sym.definition_start <= line <= sym.end_line:
                line_map[line] = sym
                break

    return line_map
