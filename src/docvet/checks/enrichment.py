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
        if isinstance(child, ast.Call):
            # Pattern 1: warnings.warn(...)
            if (
                isinstance(child.func, ast.Attribute)
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "warnings"
                and child.func.attr == "warn"
            ):
                has_warn = True
                break
            # Pattern 2: warn(...) after from warnings import warn
            if isinstance(child.func, ast.Name) and child.func.id == "warn":
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


def _is_dataclass(node: ast.ClassDef) -> bool:
    """Check whether a class is decorated with ``@dataclass``.

    Recognises three decorator forms:

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
    for dec in node.decorator_list:
        # Pattern 1: @dataclass
        if isinstance(dec, ast.Name) and dec.id == "dataclass":
            return True
        # Pattern 2: @dataclasses.dataclass
        if isinstance(dec, ast.Attribute) and dec.attr == "dataclass":
            return True
        # Pattern 3: @dataclass(...) or @dataclasses.dataclass(...)
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name) and dec.func.id == "dataclass":
                return True
            if isinstance(dec.func, ast.Attribute) and dec.func.attr == "dataclass":
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


def _has_self_assignments(node: ast.ClassDef) -> bool:
    """Check whether a class has ``self.*`` assignments in ``__init__``.

    Finds the ``__init__`` method via direct ``.body`` iteration (not
    ``ast.walk``) and walks its body with a scope-aware iterative walk
    that stops at nested ``FunctionDef``, ``AsyncFunctionDef``, and
    ``ClassDef`` boundaries. Detects both ``self.x = value``
    (``ast.Assign``) and ``self.x: int = value`` (``ast.AnnAssign``).

    Args:
        node: The ``ClassDef`` AST node to inspect.

    Returns:
        ``True`` when a ``self.*`` assignment is found in ``__init__``,
        ``False`` otherwise.
    """
    init_node = None
    for item in node.body:
        if (
            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            and item.name == "__init__"
        ):
            init_node = item
            break

    if init_node is None:
        return False

    stack = list(ast.iter_child_nodes(init_node))
    while stack:
        child = stack.pop()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Assign):
            for target in child.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    return True
        if (
            isinstance(child, ast.AnnAssign)
            and isinstance(child.target, ast.Attribute)
            and isinstance(child.target.value, ast.Name)
            and child.target.value.id == "self"
        ):
            return True
        stack.extend(ast.iter_child_nodes(child))

    return False


def _is_init_module(file_path: str) -> bool:
    """Check whether a file path points to an ``__init__.py`` module.

    Uses ``str.endswith()`` which handles both absolute and relative
    paths cross-platform since ``__init__.py`` is always the filename.

    Args:
        file_path: The source file path to check.

    Returns:
        ``True`` for ``__init__.py`` paths, ``False`` otherwise.
    """
    return file_path == "__init__.py" or file_path.endswith("/__init__.py")


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
    5. ``__init__.py`` module

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
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=symbol.name,
            rule="missing-attributes",
            message=f"Module '{symbol.name}' has no Attributes: section",
            category="required",
        )

    return None


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
        if config.require_yields:
            if f := _check_missing_yields(
                symbol, sections, node_index, config, file_path
            ):
                findings.append(f)
        if config.require_receives:
            if f := _check_missing_receives(
                symbol, sections, node_index, config, file_path
            ):
                findings.append(f)
        if config.require_warns:
            if f := _check_missing_warns(
                symbol, sections, node_index, config, file_path
            ):
                findings.append(f)
        if config.require_other_parameters:
            if f := _check_missing_other_parameters(
                symbol, sections, node_index, config, file_path
            ):
                findings.append(f)
        if config.require_attributes:
            if f := _check_missing_attributes(
                symbol, sections, node_index, config, file_path
            ):
                findings.append(f)
        # Future rules dispatched here in taxonomy-table order

    return findings
