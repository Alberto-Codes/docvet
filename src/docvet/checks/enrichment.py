"""Enrichment check for docstring completeness.

Detects missing docstring sections (Returns, Raises, Yields, Attributes, etc.),
validates cross-reference syntax in See Also sections, and checks for
non-fenced code block patterns (reporting both doctest and rST findings
per symbol) by combining AST analysis with section header parsing.
Guard clauses for rules with broad skip sets (e.g. ``missing-returns``)
are extracted into dedicated ``_should_skip_*`` helpers to keep check
functions focused and within cognitive-complexity thresholds.
Module-kind findings use :func:`~docvet.ast_utils.module_display_name`
for human-readable symbol names. Implements Layer 3 (completeness) of
the docstring quality model. Supports both Google-style and Sphinx/RST
docstring conventions via the ``style`` parameter on
:func:`check_enrichment`. Sphinx directive matching uses literal
single-space patterns for canonical RST formatting. NumPy-style section
headers (Notes, References, Warnings, Extended Summary, Methods) and
underline format (header on one line immediately followed by
dashes/equals) are recognized as section boundaries alongside
Google colon format.

Examples:
    Run the enrichment check on a source file:

    ```python
    from docvet.checks import check_enrichment
    from docvet.config import EnrichmentConfig

    findings = check_enrichment(source, tree, EnrichmentConfig(), "app.py")
    ```

See Also:
    [`docvet.config`][]: ``EnrichmentConfig`` dataclass for rule toggles.
    [`docvet.ast_utils`][]: Symbol extraction consumed by enrichment rules.
    [`docvet.checks`][]: Package-level re-exports.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from typing import Literal

from docvet.ast_utils import Symbol, get_documented_symbols, module_display_name
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

__all__ = ["check_enrichment"]

# ---------------------------------------------------------------------------
# Section header constants
# ---------------------------------------------------------------------------

_SEE_ALSO = "See Also"

# All 15 recognized section headers (10 Google-style + 5 NumPy-style).
# Args and Returns are included for parsing context (FR15) — they are
# recognized but never checked for absence (layer 2 style is ruff).
# NumPy additions (Notes, References, Warnings, Extended Summary, Methods)
# are recognition-only — no enforcement rules fire for them.
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
        _SEE_ALSO,
        "Notes",
        "References",
        "Warnings",
        "Extended Summary",
        "Methods",
    }
)

_SECTION_PATTERN = re.compile(
    r"^\s*"
    r"(Args|Returns|Raises|Yields|Receives|Warns"
    r"|Other Parameters|Attributes|Examples|See Also"
    r"|Notes|References|Warnings|Extended Summary|Methods)"
    r":\s*$",
    re.MULTILINE,
)

# NumPy underline format: section header on its own line followed by 3+ dashes/equals.
# Built dynamically from _SECTION_HEADERS to stay in sync (Story 34.3).
_numpy_header_list = sorted(_SECTION_HEADERS, key=len, reverse=True)
_numpy_headers = "|".join(re.escape(str(h)) for h in _numpy_header_list)
_NUMPY_UNDERLINE_PATTERN = re.compile(
    rf"^\s*({_numpy_headers})[^\S\n]*\n[^\S\n]*[-=]{{3,}}\s*$",
    re.MULTILINE,
)

# Cross-reference detection patterns for See Also: sections (FR12, FR-Q12)
_XREF_MD_LINK = re.compile(r"\[[^\]]+\]\[")
_XREF_SPHINX = re.compile(r":\w+:`[^`]+`")

# Sphinx domain-qualified roles (e.g., :py:class:`Foo`, :py:func:`bar`).
# Used for body-wide cross-reference detection in sphinx mode (AC5).
_SPHINX_ROLE_PATTERN = re.compile(
    r":py:(?:class|meth|func|attr|mod|exc|data|const|obj):`[^`]+`"
)

# ---------------------------------------------------------------------------
# Sphinx/RST section detection (Story 34.1)
# ---------------------------------------------------------------------------

# Maps RST field-list / directive patterns to internal section names.
_SPHINX_SECTION_MAP: dict[str, str] = {
    ":param": "Args",
    ":type": "Args",
    ":returns:": "Returns",
    ":return:": "Returns",
    ":rtype:": "Returns",
    ":raises": "Raises",
    ":ivar": "Attributes",
    ":cvar": "Attributes",
    ".. seealso::": "See Also",
    ">>>": "Examples",
    "::": "Examples",
    ".. code-block::": "Examples",
}

# Regex to detect any Sphinx/RST section pattern in a docstring body.
# Matches field-list entries (:param, :type, :returns:, :rtype:, :raises,
# :ivar, :cvar), directives (.. seealso::, .. code-block::), doctest (>>>),
# and rST code marker (::).
_SPHINX_SECTION_PATTERN = re.compile(
    r"(?:"
    r":(?:param|type)\s"  # :param name: / :type name:
    r"|:(?:returns|return|rtype):"  # :returns: / :return: / :rtype:
    r"|:raises\s"  # :raises ExcType:
    r"|:(?:ivar|cvar)\s"  # :ivar name: / :cvar name:
    r"|\.\. seealso::"  # .. seealso::
    r"|\.\. code-block::"  # .. code-block::
    r"|>>>"  # doctest
    r"|::\s*$"  # rST code block marker
    r")",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Shared helper functions
# ---------------------------------------------------------------------------


def _parse_sections(docstring: str, *, style: str = "google") -> set[str]:
    """Extract recognized section headers from a docstring.

    When *style* is ``"google"`` (default), scans for colon-header format
    (``Args:``, ``Returns:``, etc.) and NumPy underline format
    (e.g. ``Returns`` followed by dashes). When ``"sphinx"``, scans for RST field-list
    patterns (``:param name:``, ``:returns:``, etc.), directives
    (``.. seealso::``), and code markers (``>>>``, ``::``).

    The parser does not validate overall docstring structure — a partially
    malformed docstring can still yield matches for its well-formed headers.
    Headers inside fenced code blocks may also match, which produces false
    negatives at the rule level (safe direction per NFR5) since the rule
    will believe the section exists.

    Args:
        docstring: The raw docstring text to parse.
        style: Docstring convention: ``"google"`` or ``"sphinx"``.

    Returns:
        A set of internal section names found in the docstring. Returns an
        empty set when no recognized section headers are found.
    """
    if style == "sphinx":
        return _parse_sphinx_sections(docstring)
    sections = set(_SECTION_PATTERN.findall(docstring))
    sections.update(_NUMPY_UNDERLINE_PATTERN.findall(docstring))
    return sections


def _parse_sphinx_sections(docstring: str) -> set[str]:
    """Extract section names from a Sphinx/RST-style docstring.

    Uses pattern matching (no RST parser dependency) to detect field-list
    entries, directives, and code markers. Maps each match to its
    Google-equivalent internal section name via ``_SPHINX_SECTION_MAP``
    using prefix matching against map keys.

    Args:
        docstring: The raw docstring text to parse.

    Returns:
        A set of internal section names (e.g. ``"Args"``, ``"Raises"``).
    """
    sections: set[str] = set()
    for match in _SPHINX_SECTION_PATTERN.finditer(docstring):
        text = match.group(0)
        for pattern_key, section_name in _SPHINX_SECTION_MAP.items():
            if text.startswith(pattern_key):
                sections.add(section_name)
                break
    return sections


def _extract_section_content(docstring: str, section_name: str) -> str | None:
    """Extract the text content of a specific section from a docstring.

    Finds the section header line matching the given name and collects
    all subsequent lines until the next section header (Google colon or
    NumPy underline format) or end of docstring. Returns ``None`` if the
    section is not found.

    Args:
        docstring: The raw docstring text to search.
        section_name: The section header name (e.g. ``"Attributes"``).

    Returns:
        The text content below the section header, or ``None`` if the
        section is not found.
    """
    lines = docstring.splitlines()
    header_pattern = re.compile(rf"^\s*{re.escape(section_name)}:\s*$")
    start_idx = None
    for i, line in enumerate(lines):
        if header_pattern.match(line):
            start_idx = i + 1
            break

    if start_idx is None:
        return None

    content_lines: list[str] = []
    for i, line in enumerate(lines[start_idx:], start_idx):
        if _SECTION_PATTERN.match(line):
            break
        # NumPy underline boundary: header line + next line is 3+ dashes/equals
        stripped = line.strip()
        if stripped in _SECTION_HEADERS and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if len(next_line) >= 3 and all(c in "-=" for c in next_line):
                break
        content_lines.append(line)

    return "\n".join(content_lines)


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


def _is_stub_function(node: _NodeT) -> bool:
    """Check whether a function body is a stub (no real implementation).

    Stubs are single-statement bodies consisting of ``pass``,
    ``...`` (Ellipsis), or ``raise NotImplementedError``.  A leading
    docstring ``Expr(Constant(str))`` is stripped before evaluating
    body length so the helper works for both documented and
    undocumented functions.

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
    if len(body) != 1:
        return False
    stmt = body[0]
    if isinstance(stmt, ast.Pass):
        return True
    if (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and stmt.value.value is ...
    ):
        return True
    if isinstance(stmt, ast.Raise) and isinstance(stmt.exc, (ast.Name, ast.Call)):
        exc = stmt.exc.func if isinstance(stmt.exc, ast.Call) else stmt.exc
        return isinstance(exc, ast.Name) and exc.id == "NotImplementedError"
    return False


def _should_skip_returns_check(
    symbol: Symbol,
    node: _NodeT,
    sections: set[str],
) -> bool:
    """Determine whether the missing-returns rule should be skipped.

    Centralises guard clauses for :func:`_check_missing_returns` to keep
    the main function focused on AST walking. Skips when the symbol
    already has a ``Returns:`` section, is a dunder method,
    ``@property``/``@cached_property``, ``@abstractmethod``,
    ``@overload``, or a stub function.

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
    # @abstractmethod (interface contracts, not implementations)
    if _has_decorator(node, "abstractmethod"):
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


# ---------------------------------------------------------------------------
# Rule-specific helpers for missing-attributes
# ---------------------------------------------------------------------------


def _decorator_matches(dec: ast.expr, name: str) -> bool:
    """Check whether a decorator node matches a given name.

    Recognises three decorator forms:

    - Simple: ``@name``
    - Qualified: ``@<module>.name`` (suffix match)
    - Call: ``@name(...)`` or ``@<module>.name(...)``

    The qualified forms use suffix-based matching (checks ``attr``
    without verifying the module name).

    Args:
        dec: The decorator AST expression to inspect.
        name: The decorator name to match against.

    Returns:
        ``True`` when the decorator matches.
    """
    if isinstance(dec, ast.Name):
        return dec.id == name
    if isinstance(dec, ast.Attribute):
        return dec.attr == name
    if isinstance(dec, ast.Call):
        return _decorator_matches(dec.func, name)
    return False


def _is_dataclass(node: ast.ClassDef) -> bool:
    """Check whether a class is decorated with ``@dataclass``.

    Recognises three decorator forms via ``_decorator_matches``:

    - Simple: ``@dataclass``
    - Qualified: ``@<module>.dataclass`` (suffix match — typically
      ``@dataclasses.dataclass``)
    - Call: ``@dataclass(...)`` or ``@<module>.dataclass(...)``

    The qualified forms use suffix-based matching (checks ``attr ==
    "dataclass"`` without verifying the module name). This is intentional
    — the false positive risk is negligible and avoids brittleness with
    re-exports. Alias detection (e.g. ``from dataclasses import dataclass
    as dc``) is explicitly out of MVP scope.

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when a dataclass decorator is found, ``False`` otherwise.
    """
    return any(_decorator_matches(dec, "dataclass") for dec in node.decorator_list)


def _is_protocol(node: ast.ClassDef) -> bool:
    """Check whether a class inherits from ``Protocol``.

    Recognises two base class forms:

    - Simple: ``class Foo(Protocol)``
    - Qualified: ``class Foo(<module>.Protocol)`` (suffix match —
      typically ``typing.Protocol``)

    The qualified form uses suffix-based matching (checks ``attr ==
    "Protocol"`` without verifying the module name).

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when a Protocol base class is found, ``False`` otherwise.
    """
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "Protocol":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "Protocol":
            return True
    return False


_ENUM_NAMES = frozenset({"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"})


def _is_enum(node: ast.ClassDef) -> bool:
    """Check whether a class inherits from an ``enum`` base class.

    Recognises two base class forms:

    - Simple: ``class Color(Enum)`` (and ``IntEnum``, ``StrEnum``,
      ``Flag``, ``IntFlag``)
    - Qualified: ``class Color(<module>.Enum)`` (suffix match —
      typically ``enum.Enum``)

    The qualified form uses suffix-based matching (checks ``attr`` against
    the known enum names without verifying the module name).

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when an enum base class is found, ``False`` otherwise.
    """
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in _ENUM_NAMES:
            return True
        if isinstance(base, ast.Attribute) and base.attr in _ENUM_NAMES:
            return True
    return False


def _is_namedtuple(node: ast.ClassDef) -> bool:
    """Check whether a class inherits from ``NamedTuple``.

    Recognises two base class forms:

    - Simple: ``class Foo(NamedTuple)``
    - Qualified: ``class Foo(<module>.NamedTuple)`` (suffix match —
      typically ``typing.NamedTuple``)

    The qualified form uses suffix-based matching (checks ``attr ==
    "NamedTuple"`` without verifying the module name).

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when a NamedTuple base class is found, ``False`` otherwise.
    """
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "NamedTuple":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "NamedTuple":
            return True
    return False


def _is_typeddict(node: ast.ClassDef) -> bool:
    """Check whether a class inherits from ``TypedDict``.

    Recognises two base class forms:

    - Simple: ``class Foo(TypedDict)``
    - Qualified: ``class Foo(<module>.TypedDict)`` (suffix match —
      typically ``typing.TypedDict``)

    The qualified form uses suffix-based matching (checks ``attr ==
    "TypedDict"`` without verifying the module name).

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when a TypedDict base class is found, ``False`` otherwise.
    """
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "TypedDict":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "TypedDict":
            return True
    return False


def _find_init_method(
    node: ast.ClassDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Find the ``__init__`` method in a class body.

    Performs a direct iteration over the class body (not ``ast.walk``)
    and returns the first ``FunctionDef`` or ``AsyncFunctionDef`` node
    named ``__init__``.

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        The ``__init__`` method node, or ``None`` if not found.
    """
    for item in node.body:
        if (
            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and item.name == "__init__"
        ):
            return item
    return None


def _has_self_attribute_target(node: ast.Assign | ast.AnnAssign) -> bool:
    """Check whether an assignment node targets a ``self.*`` attribute.

    Handles both ``ast.Assign`` (which may have multiple targets) and
    ``ast.AnnAssign`` (single target). Returns ``True`` when any target
    is of the form ``self.<name>``.

    Args:
        node: The AST assignment node to inspect.

    Returns:
        ``True`` when a ``self.*`` attribute target is found.
    """
    if isinstance(node, ast.Assign):
        return any(
            isinstance(t, ast.Attribute)
            and isinstance(t.value, ast.Name)
            and t.value.id == "self"
            for t in node.targets
        )
    if isinstance(node, ast.AnnAssign):
        return (
            isinstance(node.target, ast.Attribute)
            and isinstance(node.target.value, ast.Name)
            and node.target.value.id == "self"
        )
    return False


def _has_self_assignments(node: ast.ClassDef) -> bool:
    """Check whether a class has ``self.*`` assignments in ``__init__``.

    Finds the ``__init__`` method via ``_find_init_method`` and walks
    its body with a scope-aware iterative walk that stops at nested
    ``FunctionDef``, ``AsyncFunctionDef``, and ``ClassDef`` boundaries.
    Detects both ``self.x = value`` (``ast.Assign``) and
    ``self.x: int = value`` (``ast.AnnAssign``) via
    ``_has_self_attribute_target``.

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when a ``self.*`` assignment is found in ``__init__``,
        ``False`` otherwise.
    """
    init_node = _find_init_method(node)
    if init_node is None:
        return False

    stack = list(ast.iter_child_nodes(init_node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, (ast.Assign, ast.AnnAssign)):
            if _has_self_attribute_target(child):
                return True
        stack.extend(ast.iter_child_nodes(child))

    return False


# Used only by _check_missing_attributes (module Attributes: is __init__.py-only
# by design).
def _is_init_module(file_path: str) -> bool:
    """Check whether a file path points to an ``__init__.py`` module.

    Uses equality and ``str.endswith()`` with path separator prefixes
    for boundary-aware matching. Handles both forward-slash (Unix, git)
    and backslash (Windows) separators.

    Args:
        file_path: The source file path to check.

    Returns:
        ``True`` for ``__init__.py`` paths, ``False`` otherwise.
    """
    return (
        file_path == "__init__.py"
        or file_path.endswith("/__init__.py")
        or file_path.endswith("\\__init__.py")
    )


def _check_missing_attributes(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a construct missing an ``Attributes:`` section.

    Dispatches to helper functions in first-match-wins order:

    1. Dataclass (decorator inspection)
    2. NamedTuple (base class inspection)
    3. TypedDict (base class inspection)
    4. Plain class with ``__init__`` self-assignments
    5. ``__init__.py`` module (uses module display name)

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-attributes"`` when a class
        or ``__init__.py`` module lacks an ``Attributes:`` section, or
        ``None`` otherwise.
    """
    if symbol.kind not in ("class", "module"):
        return None

    if "Attributes" in sections:
        return None

    # Class branches (1-4)
    if symbol.kind == "class":
        node = node_index.get(symbol.line)
        # ClassDef check narrows the union type for ty
        if node is None or not isinstance(node, ast.ClassDef):
            return None

        # Branch 1: Dataclass
        if _is_dataclass(node):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-attributes",
                message=f"Dataclass '{symbol.name}' has no Attributes: section",
                category="required",
            )

        # Branch 2: NamedTuple
        if _is_namedtuple(node):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-attributes",
                message=f"NamedTuple '{symbol.name}' has no Attributes: section",
                category="required",
            )

        # Branch 3: TypedDict
        if _is_typeddict(node):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-attributes",
                message=f"TypedDict '{symbol.name}' has no Attributes: section",
                category="required",
            )

        # Branch 4: Plain class with __init__ self-assignments
        if _has_self_assignments(node):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-attributes",
                message=f"Class '{symbol.name}' has no Attributes: section",
                category="required",
            )

        return None

    # Branch 5: __init__.py module
    if _is_init_module(file_path):
        display = module_display_name(file_path)
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=display,
            rule="missing-attributes",
            message=f"Module '{display}' has no Attributes: section",
            category="required",
        )

    return None


# ---------------------------------------------------------------------------
# Rule: missing-typed-attributes
# ---------------------------------------------------------------------------

_TYPED_ATTR_PATTERN = re.compile(r"^\s+\w+\s+\(.*\)\s*:")


def _check_missing_typed_attributes(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect an ``Attributes:`` section with untyped entries.

    Checks each entry in the ``Attributes:`` section for the typed
    format ``name (type): description``. If any entry lacks the
    parenthesized type annotation, returns a finding.

    Only applies to class symbols — module-level ``Attributes:``
    sections document exports and typing is not applicable.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-typed-attributes"`` when
        untyped attribute entries are found, or ``None`` otherwise.
    """
    if symbol.kind != "class":
        return None

    if "Attributes" not in sections:
        return None

    if not symbol.docstring:
        return None

    content = _extract_section_content(symbol.docstring, "Attributes")
    if content is None:
        return None

    # Determine the base indentation level from the first non-empty line.
    # Attribute entries start at this level; continuation lines are
    # indented further and should be skipped.
    base_indent: int | None = None
    for line in content.splitlines():
        if not line.strip():
            continue
        base_indent = len(line) - len(line.lstrip())
        break

    if base_indent is None:
        return None

    for line in content.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        # Skip continuation lines (deeper indentation than base)
        if indent > base_indent:
            continue
        if not _TYPED_ATTR_PATTERN.match(line):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=symbol.name,
                rule="missing-typed-attributes",
                message=(
                    f"Attributes: section in class '{symbol.name}' "
                    f"lacks typed format (name (type): description)"
                ),
                category="recommended",
            )

    return None


# ---------------------------------------------------------------------------
# Rule: missing-examples
# ---------------------------------------------------------------------------


def _check_missing_examples(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a construct missing an ``Examples:`` section.

    This is the only ``_check_*`` function that reads ``config`` internally.
    Classes are gated by list membership — the classified type name
    (``"class"``, ``"dataclass"``, ``"protocol"``, ``"enum"``) must appear
    in ``config.require_examples`` for a finding to be emitted.  Modules
    trigger whenever ``require_examples`` is non-empty and use the
    module display name in findings.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration containing ``require_examples``.
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-examples"`` when a symbol
        lacks an ``Examples:`` section, or ``None`` otherwise.
    """
    if "Examples" in sections:
        return None

    if not config.require_examples:
        return None

    # Module branch: modules trigger when require_examples is non-empty
    # (any type in the list enables module checking).
    if symbol.kind == "module":
        display = module_display_name(file_path)
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=display,
            rule="missing-examples",
            message=f"Module '{display}' has no Examples: section",
            category="recommended",
        )

    # Only classes are supported for missing-examples.
    if symbol.kind != "class":
        return None

    node = node_index.get(symbol.line)
    if node is None or not isinstance(node, ast.ClassDef):
        return None

    # Classify inline: dataclass > namedtuple/typeddict (excluded) >
    # protocol > enum > class
    if _is_dataclass(node):
        type_name = "dataclass"
        label = "Dataclass"
    elif _is_namedtuple(node) or _is_typeddict(node):
        # NamedTuple and TypedDict do not map to any config type name —
        # they are excluded from missing-examples detection entirely.
        return None
    elif _is_protocol(node):
        type_name = "protocol"
        label = "Protocol"
    elif _is_enum(node):
        type_name = "enum"
        label = "Enum"
    else:
        type_name = "class"
        label = "Class"

    if type_name not in config.require_examples:
        return None

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-examples",
        message=f"{label} '{symbol.name}' has no Examples: section",
        category="recommended",
    )


# ---------------------------------------------------------------------------
# Rule: missing-cross-references
# ---------------------------------------------------------------------------

_SYMBOL_KIND_DISPLAY = {
    "function": "function",
    "method": "method",
    "class": "class",
    "module": "module",
}


def _check_missing_cross_references(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect missing or malformed cross-references in ``See Also:`` sections.

    Two detection branches:

    - **Branch A:** Any module with no ``See Also:`` section at all — the
      module should cross-reference related modules.  Uses module display
      name in findings.
    - **Branch B:** Any symbol with a ``See Also:`` section whose content
      lacks linkable cross-reference syntax (Markdown bracket references
      or Sphinx roles).  Module-kind symbols use the display name;
      others use ``symbol.name``.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-cross-references"`` when
        cross-reference issues are found, or ``None`` otherwise.
    """
    kind_display = _SYMBOL_KIND_DISPLAY.get(symbol.kind, symbol.kind)

    # Branch A: module missing See Also: entirely
    if symbol.kind == "module":
        if _SEE_ALSO not in sections:
            display = module_display_name(file_path)
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=display,
                rule="missing-cross-references",
                message=(f"Module '{display}' has no See Also: section"),
                category="recommended",
            )

    # Branch B: See Also: exists but lacks cross-reference syntax
    if _SEE_ALSO not in sections:
        return None

    if not symbol.docstring:
        return None

    content = _extract_section_content(symbol.docstring, _SEE_ALSO)
    if content is None:
        return None

    for line in content.splitlines():
        if not line.strip():
            continue
        if _XREF_MD_LINK.search(line) or _XREF_SPHINX.search(line):
            return None

    display_name = (
        module_display_name(file_path) if symbol.kind == "module" else symbol.name
    )
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=display_name,
        rule="missing-cross-references",
        message=(
            f"See Also: section in {kind_display} '{display_name}' "
            f"lacks cross-reference syntax"
        ),
        category="recommended",
    )


# ---------------------------------------------------------------------------
# Rule: prefer-fenced-code-blocks
# ---------------------------------------------------------------------------

_DOCTEST_PATTERN = re.compile(r"^\s*>>>")
_RST_BLOCK_PATTERN = re.compile(r"::\s*$")


def _has_rst_indented_block(lines: list[str], index: int) -> bool:
    """Check whether the ``::`` line at *index* is followed by an indented block.

    Determines if the line ending with ``::`` introduces a
    reStructuredText indented code block by verifying that the first
    non-blank line after ``index`` has strictly greater indentation
    than the ``::`` line itself.

    Args:
        lines: All lines from the ``Examples:`` section content.
        index: Index of the line ending with ``::``.

    Returns:
        ``True`` when a non-blank line with greater indentation follows,
        ``False`` otherwise (including when no non-blank line follows).
    """
    rst_indent = len(lines[index]) - len(lines[index].lstrip())
    for subsequent in lines[index + 1 :]:
        if not subsequent.strip():
            continue
        return (len(subsequent) - len(subsequent.lstrip())) > rst_indent
    return False


def _check_prefer_fenced_code_blocks(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect ``Examples:`` sections using non-fenced code block formats.

    Checks for ``>>>`` doctest patterns and ``::`` reStructuredText
    indented code blocks in the ``Examples:`` section content.  The
    ``>>>`` scan runs first; ``::`` detection fires only when no
    doctest pattern is found.  Module-kind symbols use the display
    name; others use ``symbol.name``.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="prefer-fenced-code-blocks"`` when
        doctest format (``>>>``) or an rST indented code block (``::``)
        is found, or ``None`` otherwise.
    """
    if "Examples" not in sections:
        return None

    if not symbol.docstring:
        return None

    content = _extract_section_content(symbol.docstring, "Examples")
    if content is None:
        return None

    kind_display = _SYMBOL_KIND_DISPLAY.get(symbol.kind, symbol.kind)
    display_name = (
        module_display_name(file_path) if symbol.kind == "module" else symbol.name
    )

    lines = content.splitlines()

    for line in lines:
        if _DOCTEST_PATTERN.match(line):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=display_name,
                rule="prefer-fenced-code-blocks",
                message=(
                    f"Examples: section in {kind_display} '{display_name}' "
                    f"uses doctest format (>>>) instead of fenced code blocks"
                ),
                category="recommended",
            )

    for i, line in enumerate(lines):
        if _RST_BLOCK_PATTERN.search(line) and _has_rst_indented_block(lines, i):
            return Finding(
                file=file_path,
                line=symbol.line,
                symbol=display_name,
                rule="prefer-fenced-code-blocks",
                message=(
                    f"Examples: section in {kind_display} '{display_name}' "
                    f"uses reStructuredText indented code block (::) "
                    f"instead of fenced code blocks"
                ),
                category="recommended",
            )

    return None


def _check_fenced_code_blocks_extra(
    symbol: Symbol,
    file_path: str,
    pattern_type: Literal["doctest", "rst"],
) -> Finding | None:
    """Check for the *other* non-fenced pattern after the first was found.

    When ``_check_prefer_fenced_code_blocks`` finds one pattern type
    (doctest ``>>>`` or rST ``::``), this helper checks whether the
    *other* pattern type also exists in the same ``Examples:`` section.
    Module-kind symbols use the display name; others use
    ``symbol.name``.

    Args:
        symbol: The documented symbol to inspect.
        file_path: Source file path for the finding record.
        pattern_type: Which pattern was already reported by the
            dispatch function (``"doctest"`` or ``"rst"``).

    Returns:
        A ``Finding`` for the other pattern type, or ``None`` if only
        one pattern type exists.
    """
    if not symbol.docstring:
        return None

    content = _extract_section_content(symbol.docstring, "Examples")
    if content is None:
        return None

    kind_display = _SYMBOL_KIND_DISPLAY.get(symbol.kind, symbol.kind)
    display_name = (
        module_display_name(file_path) if symbol.kind == "module" else symbol.name
    )
    lines = content.splitlines()

    if pattern_type == "doctest":
        # First finding was doctest — check for rST
        for i, line in enumerate(lines):
            if _RST_BLOCK_PATTERN.search(line) and _has_rst_indented_block(lines, i):
                return Finding(
                    file=file_path,
                    line=symbol.line,
                    symbol=display_name,
                    rule="prefer-fenced-code-blocks",
                    message=(
                        f"Examples: section in {kind_display} '{display_name}' "
                        f"uses reStructuredText indented code block (::) "
                        f"instead of fenced code blocks"
                    ),
                    category="recommended",
                )
    else:
        # First finding was rST — check for doctest
        for line in lines:
            if _DOCTEST_PATTERN.match(line):
                return Finding(
                    file=file_path,
                    line=symbol.line,
                    symbol=display_name,
                    rule="prefer-fenced-code-blocks",
                    message=(
                        f"Examples: section in {kind_display} '{display_name}' "
                        f"uses doctest format (>>>) instead of fenced code blocks"
                    ),
                    category="recommended",
                )

    return None


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------

_CheckFn = Callable[
    [Symbol, set[str], dict[int, _NodeT], EnrichmentConfig, str],
    Finding | None,
]

# Rules auto-disabled in sphinx mode unless the user explicitly enables them.
_SPHINX_AUTO_DISABLE_RULES: frozenset[str] = frozenset(
    {
        "require_yields",
        "require_receives",
        "require_warns",
        "require_other_parameters",
        "prefer_fenced_code_blocks",
    }
)

_RULE_DISPATCH: tuple[tuple[str, _CheckFn], ...] = (
    ("require_raises", _check_missing_raises),
    ("require_returns", _check_missing_returns),
    ("require_yields", _check_missing_yields),
    ("require_receives", _check_missing_receives),
    ("require_warns", _check_missing_warns),
    ("require_other_parameters", _check_missing_other_parameters),
    ("require_attributes", _check_missing_attributes),
    ("require_typed_attributes", _check_missing_typed_attributes),
    ("require_examples", _check_missing_examples),
    ("require_cross_references", _check_missing_cross_references),
    ("prefer_fenced_code_blocks", _check_prefer_fenced_code_blocks),
)


def check_enrichment(
    source: str,
    tree: ast.Module,
    config: EnrichmentConfig,
    file_path: str,
    *,
    style: str = "google",
) -> list[Finding]:
    """Run all enrichment rules on a parsed source file.

    Iterates over documented symbols, parses their docstring sections,
    and dispatches to each enabled rule function via ``_RULE_DISPATCH``.
    For ``prefer_fenced_code_blocks``, a second-pass helper receives an
    explicit pattern type and checks for the other pattern so both
    doctest and rST findings surface in one run. Symbols without a
    docstring are skipped (FR20). Config gating and sphinx auto-disable
    control which rules run.

    When *style* is ``"sphinx"``, rules in ``_SPHINX_AUTO_DISABLE_RULES``
    are skipped unless the user explicitly enabled them (tracked via
    ``config.user_set_keys``).

    Args:
        source: Raw source text of the file (reserved for future rules).
        tree: Parsed AST module from ``ast.parse()``.
        config: Enrichment configuration controlling rule toggles.
        file_path: Source file path for finding records.
        style: Docstring convention: ``"google"`` or ``"sphinx"``.

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
        sections = _parse_sections(symbol.docstring, style=style)

        for attr, check_fn in _RULE_DISPATCH:
            # Sphinx auto-disable: skip unless user explicitly enabled.
            if (
                style == "sphinx"
                and attr in _SPHINX_AUTO_DISABLE_RULES
                and attr not in config.user_set_keys
            ):
                continue
            if getattr(config, attr):
                if f := check_fn(symbol, sections, node_index, config, file_path):
                    # Sphinx cross-ref: roles anywhere in body satisfy check.
                    if (
                        style == "sphinx"
                        and attr == "require_cross_references"
                        and _SPHINX_ROLE_PATTERN.search(symbol.docstring)
                    ):
                        continue
                    findings.append(f)
                    if attr == "prefer_fenced_code_blocks":
                        pt = "doctest" if ">>>" in f.message else "rst"
                        if extra := _check_fenced_code_blocks_extra(
                            symbol, file_path, pt
                        ):
                            findings.append(extra)

    return findings
