"""Forward missing-section enrichment checks.

Detects missing docstring sections (Raises, Returns, Yields, Receives,
Warns, Other Parameters) by walking the function's AST subtree.  Each
check function follows the uniform five-parameter dispatch signature
used by ``_RULE_DISPATCH`` in the enrichment orchestrator.  Also provides
shared helpers for stub detection (``_is_stub_function``,
``_is_stub_statement``) and abstract decorator detection
(``_is_abstract``, ``_ABSTRACT_DECORATORS``).

See Also:
    [`docvet.checks.enrichment`][]: Orchestrator and dispatch table.
    [`docvet.checks._finding`][]: ``Finding`` dataclass.

Examples:
    Invoke a single forward check directly:

    ```python
    finding = _check_missing_raises(symbol, sections, node_index, config, path)
    ```
"""

from __future__ import annotations

import ast

from docvet.ast_utils import Symbol
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

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


def _extract_exception_name(node: ast.Raise) -> str | None:
    """Extract the exception class name from a ``raise`` statement.

    Handles four AST patterns:

    - ``raise exc`` where ``exc`` is a bare ``ast.Name``
    - ``raise Exc(...)`` where the call target is ``ast.Name``
    - ``raise mod.Exc(...)`` where the call target is ``ast.Attribute``
    - ``raise mod.Exc`` where ``exc`` is a bare ``ast.Attribute``

    Bare ``raise`` (re-raise) returns ``"(re-raise)"``.

    Args:
        node: The ``ast.Raise`` node to inspect.

    Returns:
        The exception class name string, or ``None`` when the pattern
        is unrecognised.
    """
    if node.exc is None:
        return "(re-raise)"
    if isinstance(node.exc, ast.Name):
        return node.exc.id
    if isinstance(node.exc, ast.Call):
        if isinstance(node.exc.func, ast.Name):
            return node.exc.func.id
        if isinstance(node.exc.func, ast.Attribute):
            return node.exc.func.attr
    if isinstance(node.exc, ast.Attribute):
        return node.exc.attr
    return None


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

    The walk is scope-aware: it stops at nested ``FunctionDef``,
    ``AsyncFunctionDef``, and ``ClassDef`` boundaries so that raises
    inside nested scopes are not attributed to the outer function.

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
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    if node is None:
        return None

    if "Raises" in sections:
        return None

    names: set[str] = set()
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Raise):
            name = _extract_exception_name(child)
            if name is not None:
                names.add(name)
        stack.extend(ast.iter_child_nodes(child))

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


def _is_meaningful_return(node: ast.Return) -> bool:
    """Check whether a ``return`` statement returns a meaningful value.

    Bare ``return`` and ``return None`` are control-flow idioms, not
    meaningful return values that need a ``Returns:`` section.

    Args:
        node: The ``ast.Return`` node to inspect.

    Returns:
        ``False`` for bare ``return`` and ``return None``, ``True``
        otherwise.
    """
    if node.value is None:
        return False
    if isinstance(node.value, ast.Constant) and node.value.value is None:
        return False
    return True


def _is_property(node: _NodeT) -> bool:
    """Check whether a function node is a ``@property`` or ``@cached_property``.

    Handles both ``ast.Name`` (bare decorator) and ``ast.Attribute``
    (qualified decorator, e.g. ``functools.cached_property``) forms.

    Args:
        node: The function or class AST node to inspect.

    Returns:
        ``True`` when the node has a ``property`` or ``cached_property``
        decorator.
    """
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Name) and dec.id in ("property", "cached_property"):
            return True
        if isinstance(dec, ast.Attribute) and dec.attr in (
            "property",
            "cached_property",
        ):
            return True
    return False


def _has_decorator(node: _NodeT, name: str) -> bool:
    """Check whether a function node has a specific decorator.

    Handles both ``ast.Name`` (bare decorator) and ``ast.Attribute``
    (qualified decorator, e.g. ``abc.abstractmethod``) forms.

    Args:
        node: The function or class AST node to inspect.
        name: The decorator name to search for (unqualified).

    Returns:
        ``True`` when the node has a decorator matching *name*.
    """
    for dec in getattr(node, "decorator_list", []):
        if isinstance(dec, ast.Name) and dec.id == name:
            return True
        if isinstance(dec, ast.Attribute) and dec.attr == name:
            return True
    return False


_ABSTRACT_DECORATORS = frozenset(
    {
        "abstractmethod",
        "abstractclassmethod",
        "abstractstaticmethod",
        "abstractproperty",
    }
)


def _is_abstract(node: _NodeT) -> bool:
    """Check whether a function has any abstract decorator.

    Detects ``@abstractmethod`` and its deprecated predecessors
    (``@abstractclassmethod``, ``@abstractstaticmethod``,
    ``@abstractproperty``).  Aligned with ruff's ``is_abstract()``
    in ``crates/ruff_python_semantic/src/analyze/visibility.rs``.

    Args:
        node: The function or class AST node to inspect.

    Returns:
        ``True`` when the node has any abstract decorator.
    """
    return any(_has_decorator(node, name) for name in _ABSTRACT_DECORATORS)


def _is_stub_statement(stmt: ast.stmt) -> bool:
    """Check whether a single AST statement is a stub-like statement.

    Recognises ``pass``, ``...`` (Ellipsis), ``raise NotImplementedError``,
    and string literals (extra docstrings).  Aligned with ruff's ``is_stub()``
    in ``crates/ruff_python_semantic/src/analyze/function_type.rs``.

    Args:
        stmt: The AST statement node to inspect.

    Returns:
        ``True`` when the statement is a stub-like statement.
    """
    if isinstance(stmt, ast.Pass):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
        # Ellipsis (...) or string literal (extra docstring).
        return stmt.value.value is ... or isinstance(stmt.value.value, str)
    if isinstance(stmt, ast.Raise) and isinstance(stmt.exc, (ast.Name, ast.Call)):
        exc = stmt.exc.func if isinstance(stmt.exc, ast.Call) else stmt.exc
        return isinstance(exc, ast.Name) and exc.id == "NotImplementedError"
    return False


def _is_stub_function(node: _NodeT) -> bool:
    """Check whether a function body is a stub (no real implementation).

    Stubs are bodies consisting entirely of stub-like statements:
    ``pass``, ``...`` (Ellipsis), ``raise NotImplementedError``, or
    string literals.  A leading docstring ``Expr(Constant(str))`` is
    stripped before evaluating so the helper works for both documented
    and undocumented functions.  A docstring-only body (empty after
    stripping) is also a stub — this covers ``typing.Protocol`` methods
    and interface contracts.

    Multi-statement stub bodies (e.g. ``pass; ...``) are accepted,
    aligning with ruff's ``is_stub()`` semantics.

    Args:
        node: The function AST node to inspect.

    Returns:
        ``True`` when the function body is a stub.
    """
    body = list(getattr(node, "body", []))
    # Strip leading docstring node if present.
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if not body:
        return True  # Docstring-only body is a stub.
    return all(_is_stub_statement(stmt) for stmt in body)


def _should_skip_returns_check(
    symbol: Symbol,
    node: _NodeT,
    sections: set[str],
) -> bool:
    """Determine whether the missing-returns rule should be skipped.

    Centralises guard clauses for :func:`_check_missing_returns` to keep
    the main function focused on AST walking. Skips when the symbol
    already has a ``Returns:`` section, is a dunder method,
    ``@property``/``@cached_property``, any abstract decorator
    (``@abstractmethod`` and deprecated variants), ``@overload``, or a
    stub function.

    Args:
        symbol: The documented symbol to inspect.
        node: The AST node for the symbol.
        sections: Parsed section headers from the symbol's docstring.

    Returns:
        ``True`` when the rule should be skipped for this symbol.
    """
    if "Returns" in sections:
        return True
    # Dunder methods (__init__, __repr__, __len__, __new__, etc.)
    if symbol.name.startswith("__") and symbol.name.endswith("__"):
        return True
    # @property and @cached_property methods
    if _is_property(node):
        return True
    # Abstract methods (interface contracts, not implementations)
    if _is_abstract(node):
        return True
    # Stub functions (pass, ..., raise NotImplementedError)
    if _is_stub_function(node):
        return True
    # @overload (defensive — 34.4 owns overload detection)
    if _has_decorator(node, "overload"):
        return True
    return False


def _check_missing_returns(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a function that returns values without a Returns section.

    Walks the function's AST subtree to find ``return`` statements with
    meaningful values (not bare ``return`` or ``return None``). Returns a
    finding when such returns exist but no ``Returns:`` section is present.

    The walk is scope-aware: it stops at nested ``FunctionDef``,
    ``AsyncFunctionDef``, and ``ClassDef`` boundaries so that returns
    inside nested scopes are not attributed to the outer function.

    Skips dunder methods, ``@property``/``@cached_property``,
    ``@abstractmethod``, ``@overload``, and stub functions via
    :func:`_should_skip_returns_check`.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-returns"`` when meaningful
        return statements exist without documentation, or ``None``
        otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    if node is None:
        return None

    if _should_skip_returns_check(symbol, node, sections):
        return None

    # Scope-aware walk for meaningful return statements
    has_meaningful_return = False
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Return) and _is_meaningful_return(child):
            has_meaningful_return = True
            break
        stack.extend(ast.iter_child_nodes(child))

    if not has_meaningful_return:
        return None

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-returns",
        message=f"Function '{symbol.name}' returns a value but has no Returns: section",
        category="required",
    )


def _check_missing_yields(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a generator function that yields without a Yields section.

    Walks the function's AST subtree to find ``yield`` and ``yield from``
    expressions. Returns a finding when yields are present but no
    ``Yields:`` section is present in the docstring.

    The walk is scope-aware: it stops at nested ``FunctionDef``,
    ``AsyncFunctionDef``, and ``ClassDef`` boundaries so that yields
    inside nested scopes are not attributed to the outer function.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-yields"`` when yield
        expressions exist without documentation, or ``None`` otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    if node is None:
        return None

    if "Yields" in sections:
        return None

    has_yield = False
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, (ast.Yield, ast.YieldFrom)):
            has_yield = True
            break
        stack.extend(ast.iter_child_nodes(child))

    if not has_yield:
        return None

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-yields",
        message=f"Function '{symbol.name}' yields but has no Yields: section",
        category="required",
    )


def _check_missing_receives(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a generator using the send pattern without a Receives section.

    Walks the function's AST subtree to find ``yield`` expressions used
    as assignment targets (``value = yield``), indicating that the
    generator protocol's ``.send()`` method is intentionally used.
    Returns a finding when the send pattern is present but no
    ``Receives:`` section exists in the docstring.

    Only ``ast.Assign`` and ``ast.AnnAssign`` nodes whose value is
    ``ast.Yield`` are considered send patterns. Bare ``yield`` (not
    assigned) and ``yield from`` do not trigger this rule.

    The walk is scope-aware: it stops at nested scope boundaries.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-receives"`` when the send
        pattern is used without documentation, or ``None`` otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    if node is None:
        return None

    if "Receives" in sections:
        return None

    has_send = False
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Assign) and isinstance(child.value, ast.Yield):
            has_send = True
            break
        if (
            isinstance(child, ast.AnnAssign)
            and child.value is not None
            and isinstance(child.value, ast.Yield)
        ):
            has_send = True
            break
        stack.extend(ast.iter_child_nodes(child))

    if not has_send:
        return None

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-receives",
        message=(
            f"Function '{symbol.name}' uses yield send pattern "
            f"but has no Receives: section"
        ),
        category="required",
    )


def _is_warn_call(node: ast.Call) -> bool:
    """Check whether a call node is a ``warnings.warn()`` invocation.

    Recognises two call patterns:

    - Qualified: ``warnings.warn(...)``
    - Bare: ``warn(...)`` (after ``from warnings import warn``)

    Args:
        node: The ``ast.Call`` node to inspect.

    Returns:
        ``True`` when the call matches a warn pattern.
    """
    if isinstance(node.func, ast.Attribute):
        return (
            isinstance(node.func.value, ast.Name)
            and node.func.value.id == "warnings"
            and node.func.attr == "warn"
        )
    if isinstance(node.func, ast.Name):
        return node.func.id == "warn"
    return False


def _check_missing_warns(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a function calling ``warnings.warn()`` without a Warns section.

    Walks the function's AST subtree to find ``ast.Call`` nodes where
    the callee is ``warnings.warn`` (qualified) or bare ``warn``
    (after ``from warnings import warn``). Returns a finding when a
    warn call is present but no ``Warns:`` section exists in the
    docstring.

    The walk is scope-aware: it stops at nested ``FunctionDef``,
    ``AsyncFunctionDef``, and ``ClassDef`` boundaries so that warn
    calls inside nested scopes are not attributed to the outer function.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-warns"`` when warn calls
        exist without documentation, or ``None`` otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    if node is None:
        return None

    if "Warns" in sections:
        return None

    has_warn = False
    stack = list(ast.iter_child_nodes(node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Call) and _is_warn_call(child):
            has_warn = True
            break
        stack.extend(ast.iter_child_nodes(child))

    if not has_warn:
        return None

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-warns",
        message=(
            f"Function '{symbol.name}' calls warnings.warn() but has no Warns: section"
        ),
        category="required",
    )


def _check_missing_other_parameters(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a function with ``**kwargs`` without an Other Parameters section.

    Inspects the function signature for a ``**kwargs`` parameter via
    ``node.args.kwarg``. Returns a finding when ``**kwargs`` is present
    but no ``Other Parameters:`` section exists in the docstring.

    No body walk is needed — this rule only inspects the function
    signature.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-other-parameters"`` when
        ``**kwargs`` exists without documentation, or ``None`` otherwise.
    """
    if symbol.kind not in ("function", "method"):
        return None

    node = node_index.get(symbol.line)
    # ClassDef check narrows the union type for ty — the symbol.kind guard
    # above already excludes class symbols, so this branch is unreachable.
    if node is None or isinstance(node, ast.ClassDef):
        return None

    if "Other Parameters" in sections:
        return None

    if node.args.kwarg is None:
        return None

    kwarg_name = node.args.kwarg.arg
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-other-parameters",
        message=(
            f"Function '{symbol.name}' accepts **{kwarg_name} "
            f"but has no Other Parameters: section"
        ),
        category="recommended",
    )
