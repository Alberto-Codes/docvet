"""Enrichment check for docstring completeness.

Orchestrates enrichment rules that detect missing or incomplete docstring
sections by combining AST analysis with section header parsing.  Rules
are organized into submodules: ``_forward`` (missing Raises, Returns,
Yields, Receives, Warns, Other Parameters), ``_class_module`` (missing
Attributes, typed attributes, Examples, cross-references, fenced code
blocks).  This module retains section parsing, parameter agreement,
deprecation, reverse checks, late rules, and the ``check_enrichment``
dispatch orchestrator.

Supports both Google-style and Sphinx/RST docstring conventions via the
``style`` parameter on :func:`check_enrichment`. NumPy-style section
headers are recognized as section boundaries alongside Google colon
format. Implements Layer 3 (completeness) of the docstring quality
model.

Examples:
    Run the enrichment check on a source file:

    ```python
    from docvet.checks import check_enrichment
    from docvet.config import EnrichmentConfig

    findings = check_enrichment(source, tree, EnrichmentConfig(), "app.py")
    ```

Attributes:
    check_enrichment: Public entry point — runs all enabled enrichment
        rules on a parsed source file.

See Also:
    [`docvet.config`][]: ``EnrichmentConfig`` dataclass for rule toggles.
    [`docvet.ast_utils`][]: Symbol extraction consumed by enrichment rules.
    [`docvet.checks`][]: Package-level re-exports.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable

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


# ---------------------------------------------------------------------------
# Forward check functions (extracted to _forward.py)
# ---------------------------------------------------------------------------

from ._forward import (  # noqa: E402
    _build_node_index,
    _check_missing_other_parameters,
    _check_missing_raises,
    _check_missing_receives,
    _check_missing_returns,
    _check_missing_warns,
    _check_missing_yields,
    _extract_exception_name,
    _has_decorator,
    _is_meaningful_return,
    _is_property,
    _is_stub_function,
    _is_warn_call,
    _NodeT,
)


def _should_skip_reverse_check(node: _NodeT) -> bool:
    """Determine whether reverse enrichment checks should be skipped.

    Skips interface-documentation functions whose docstrings describe
    intended behaviour for implementers, not current implementation.
    This aligns with ruff DOC202/403/502 and pydoclint skip logic.

    Skips when the node is ``@abstractmethod`` or a stub function
    (body is ``pass``, ``...``, or ``raise NotImplementedError``).

    Args:
        node: The AST node for the symbol.

    Returns:
        ``True`` when reverse checks should be skipped for this node.
    """
    if _has_decorator(node, "abstractmethod"):
        return True
    if _is_stub_function(node):
        return True
    return False


from ._class_module import (  # noqa: E402
    _check_fenced_code_blocks_extra,
    _check_missing_attributes,
    _check_missing_cross_references,
    _check_missing_examples,
    _check_missing_typed_attributes,
    _check_prefer_fenced_code_blocks,
    _find_init_method,
    _has_self_assignments,  # noqa: F401 – re-exported for tests
    _is_dataclass,  # noqa: F401 – re-exported for tests
    _is_enum,  # noqa: F401 – re-exported for tests
    _is_init_module,  # noqa: F401 – re-exported for tests
    _is_namedtuple,  # noqa: F401 – re-exported for tests
    _is_protocol,  # noqa: F401 – re-exported for tests
    _is_typeddict,  # noqa: F401 – re-exported for tests
)

# ---------------------------------------------------------------------------
# Param agreement helpers (Story 35.1)
# ---------------------------------------------------------------------------

# Active docstring style, set by the orchestrator before dispatch.
# Allows param agreement checks to use the correct parser without
# changing the uniform check function signature.
_active_style: str = "google"

# Regex to extract param names from Google-style Args: section entries.
# Matches at detected base indent, with optional leading */** for varargs.
_ARGS_ENTRY_PATTERN = re.compile(r"\*{0,2}(\w+)[^\S\n]*[\s(:]")

# Regex to extract param names from Sphinx :param name: entries.
_SPHINX_PARAM_PATTERN = re.compile(r":param\s+(\w+)\s*:")


def _parse_args_entries(
    docstring: str,
    *,
    style: str = "google",
) -> set[str]:
    """Extract documented parameter names from a docstring.

    In Google mode, extracts the ``Args:`` section via
    :func:`_extract_section_content` and parses entry lines at the
    detected base indent level.  In Sphinx mode, scans the full
    docstring for ``:param name:`` patterns.

    Returns an empty set when no ``Args:`` section is found or when
    content extraction fails (e.g. NumPy underline format, which
    ``_extract_section_content`` does not yet support).

    Args:
        docstring: The raw docstring text to parse.
        style: Docstring convention: ``"google"`` or ``"sphinx"``.

    Returns:
        A set of documented parameter names (stars stripped).
    """
    if style == "sphinx":
        return set(_SPHINX_PARAM_PATTERN.findall(docstring))

    content = _extract_section_content(docstring, "Args")
    if content is None:
        # NumPy underline Args format — not yet supported for content
        # extraction. Return empty set; future story will add support.
        return set()

    lines = content.splitlines()
    if not lines:
        return set()

    # Detect base indent from first non-empty content line.
    base_indent = ""
    for line in lines:
        stripped = line.lstrip()
        if stripped:
            base_indent = line[: len(line) - len(stripped)]
            break

    if not base_indent:
        return set()

    params: set[str] = set()
    for line in lines:
        # Only process lines at exactly the base indent level.
        if not line.startswith(base_indent):
            continue
        after_indent = line[len(base_indent) :]
        # Skip continuation lines (deeper indent).
        if after_indent and after_indent[0] == " ":
            continue
        m = _ARGS_ENTRY_PATTERN.match(after_indent)
        if m:
            params.add(m.group(1))

    return params


# Regex to extract exception names from Google-style Raises: section entries.
# Matches ClassName followed by colon at entry level (analogous to _ARGS_ENTRY_PATTERN).
_RAISES_ENTRY_PATTERN = re.compile(r"(\w+)\s*:")

# Regex to extract exception names from Sphinx :raises ExcType: entries.
_SPHINX_RAISES_PATTERN = re.compile(r":raises\s+(\w+)\s*:")


def _parse_raises_entries(
    docstring: str,
    *,
    style: str = "google",
) -> set[str]:
    """Extract documented exception names from a docstring.

    In Google mode, extracts the ``Raises:`` section via
    :func:`_extract_section_content` and parses entry lines at the
    detected base indent level.  In Sphinx mode, scans the full
    docstring for ``:raises ExcType:`` patterns.

    Returns an empty set when no ``Raises:`` section is found or when
    content extraction fails.

    Args:
        docstring: The raw docstring text to parse.
        style: Docstring convention: ``"google"`` or ``"sphinx"``.

    Returns:
        A set of documented exception class names.
    """
    if style == "sphinx":
        return set(_SPHINX_RAISES_PATTERN.findall(docstring))

    content = _extract_section_content(docstring, "Raises")
    if content is None:
        return set()

    lines = content.splitlines()
    if not lines:
        return set()

    # Detect base indent from first non-empty content line.
    base_indent = ""
    for line in lines:
        stripped = line.lstrip()
        if stripped:
            base_indent = line[: len(line) - len(stripped)]
            break

    if not base_indent:
        return set()

    exceptions: set[str] = set()
    for line in lines:
        # Only process lines at exactly the base indent level.
        if not line.startswith(base_indent):
            continue
        after_indent = line[len(base_indent) :]
        # Skip continuation lines (deeper indent).
        if after_indent and after_indent[0] == " ":
            continue
        m = _RAISES_ENTRY_PATTERN.match(after_indent)
        if m:
            exceptions.add(m.group(1))

    return exceptions


def _extract_signature_params(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    config: EnrichmentConfig,
) -> set[str]:
    """Extract parameter names from a function's AST arguments node.

    Always excludes ``self`` and ``cls``.  Conditionally excludes
    ``*args`` and ``**kwargs`` based on ``config.exclude_args_kwargs``.
    Collects positional-only, regular, keyword-only, vararg, and kwarg
    parameters.

    Args:
        node: The function AST node whose arguments to extract.
        config: Enrichment config controlling ``*args``/``**kwargs``
            exclusion.

    Returns:
        A set of parameter name strings (bare names, no stars).
    """
    args = node.args
    params: set[str] = set()

    # Positional-only params (before /).
    for arg in args.posonlyargs:
        params.add(arg.arg)

    # Regular params (includes self/cls).
    for arg in args.args:
        params.add(arg.arg)

    # Keyword-only params (after *).
    for arg in args.kwonlyargs:
        params.add(arg.arg)

    # *args and **kwargs — already bare names via .arg attribute.
    if not config.exclude_args_kwargs:
        if args.vararg:
            params.add(args.vararg.arg)
        if args.kwarg:
            params.add(args.kwarg.arg)

    # Always exclude self/cls.
    params.discard("self")
    params.discard("cls")

    return params


def _check_missing_param_in_docstring(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect signature parameters not documented in the ``Args:`` section.

    Guards: returns ``None`` if ``Args`` is not in *sections* (missing
    section is a different concern) or if the symbol is not a function.

    Args:
        symbol: The documented symbol to check.
        sections: Set of section header names found in the docstring.
        node_index: Line-number-to-AST-node lookup table.
        config: Enrichment configuration (used for ``exclude_args_kwargs``).
        file_path: Source file path for finding records.

    Returns:
        A finding naming the undocumented parameters, or ``None``.
    """
    if "Args" not in sections:
        return None
    if symbol.docstring is None:
        return None
    node = node_index.get(symbol.line)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None

    sig_params = _extract_signature_params(node, config)
    doc_params = _parse_args_entries(symbol.docstring, style=_active_style)
    missing = sorted(sig_params - doc_params)

    if not missing:
        return None

    names = ", ".join(missing)
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-param-in-docstring",
        message=(
            f"Function '{symbol.name}' has parameters not documented in Args: {names}"
        ),
        category="required",
    )


def _check_extra_param_in_docstring(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect ``Args:`` entries not matching any signature parameter.

    Guards: returns ``None`` if ``Args`` is not in *sections* or if the
    symbol is not a function.

    Args:
        symbol: The documented symbol to check.
        sections: Set of section header names found in the docstring.
        node_index: Line-number-to-AST-node lookup table.
        config: Enrichment configuration (used for ``exclude_args_kwargs``).
        file_path: Source file path for finding records.

    Returns:
        A finding naming the extraneous entries, or ``None``.
    """
    if "Args" not in sections:
        return None
    if symbol.docstring is None:
        return None
    node = node_index.get(symbol.line)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return None

    sig_params = _extract_signature_params(node, config)
    doc_params = _parse_args_entries(symbol.docstring, style=_active_style)
    extra = sorted(doc_params - sig_params)

    if not extra:
        return None

    names = ", ".join(extra)
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="extra-param-in-docstring",
        message=(
            f"Function '{symbol.name}' documents parameters not in signature: {names}"
        ),
        category="required",
    )


# ---------------------------------------------------------------------------
# Deprecation helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------

_CheckFn = Callable[
    [Symbol, set[str], dict[int, _NodeT], EnrichmentConfig, str],
    Finding | None,
]

# ---------------------------------------------------------------------------
# Reverse enrichment checks — docstring claims behaviour code doesn't exhibit
# ---------------------------------------------------------------------------


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

    doc_raises = _parse_raises_entries(symbol.docstring, style=_active_style)
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


# ---------------------------------------------------------------------------
# Trivial docstring detection
# ---------------------------------------------------------------------------

_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "of",
        "for",
        "to",
        "in",
        "is",
        "it",
        "and",
        "or",
        "this",
        "that",
        "with",
        "from",
        "by",
        "on",
    }
)

_CAMEL_SPLIT_PATTERN = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z][a-z0-9]*|[a-z][a-z0-9]*")


def _decompose_name(name: str) -> set[str]:
    """Split a symbol name into a set of lowercase word tokens.

    Handles ``snake_case`` (split on underscores) and ``CamelCase``
    (split on uppercase boundaries with acronym-aware grouping).
    Leading and trailing underscores are stripped before decomposition.

    Args:
        name: The symbol name to decompose.

    Returns:
        A set of lowercase word tokens, or an empty set when the name
        produces no meaningful tokens.

    Examples:
        ```python
        _decompose_name("get_user") == {"get", "user"}
        _decompose_name("HTTPSConnection") == {"https", "connection"}
        ```
    """
    stripped = name.strip("_")
    if not stripped:
        return set()
    if "_" in stripped:
        return {t.lower() for t in stripped.split("_") if t}
    tokens = _CAMEL_SPLIT_PATTERN.findall(stripped)
    return {t.lower() for t in tokens if t}


def _extract_summary_words(docstring: str) -> set[str]:
    """Extract meaningful words from the first line of a docstring.

    Takes the first non-empty line, strips the trailing period, tokenises
    on non-alphanumeric characters, lowercases every token, and filters
    out stop words.

    Args:
        docstring: The full docstring text.

    Returns:
        A set of lowercase content words from the summary line, with
        stop words removed.

    Examples:
        ```python
        _extract_summary_words("Process the data.") == {"process", "data"}
        ```
    """
    for line in docstring.split("\n"):
        stripped = line.strip()
        if stripped:
            break
    else:
        return set()
    summary = stripped.rstrip(".")
    tokens = re.split(r"[^a-zA-Z0-9]+", summary)
    return {t.lower() for t in tokens if t and t.lower() not in _STOP_WORDS}


def _check_trivial_docstring(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect docstrings whose summary line trivially restates the symbol name.

    Decomposes the symbol name into a word set and compares against the
    summary-line word set (after stop-word removal).  When the summary
    words are a subset of the name words, the docstring adds no
    information beyond what the name already communicates.

    ``@property`` and ``@cached_property`` methods are skipped because
    PEP 257 and the Google Style Guide prescribe attribute-style
    docstrings (e.g. ``"The user name."``) that naturally restate the
    attribute name.  Module-kind symbols use
    :func:`~docvet.ast_utils.module_display_name` for the finding's
    ``symbol`` and message fields.

    Args:
        symbol: The documented symbol to check.
        sections: Set of section headers found in the docstring (unused).
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="trivial-docstring"`` when the summary
        restates the name, or ``None`` otherwise.
    """
    if symbol.docstring is None:
        return None
    node = node_index.get(symbol.line)
    if node is not None and _is_property(node):
        return None
    name_words = _decompose_name(symbol.name)
    if not name_words:
        return None
    summary_words = _extract_summary_words(symbol.docstring)
    if not summary_words:
        return None
    if summary_words <= name_words:
        display_name = (
            module_display_name(file_path) if symbol.kind == "module" else symbol.name
        )
        return Finding(
            file=file_path,
            line=symbol.line,
            symbol=display_name,
            rule="trivial-docstring",
            message=(
                f"Docstring for '{display_name}' restates the name"
                f" — add details about behavior, constraints, or return value"
            ),
            category="recommended",
        )
    return None


# ---------------------------------------------------------------------------
# Rule: missing-return-type
# ---------------------------------------------------------------------------

_RETURNS_TYPE_PATTERN = re.compile(r"^\s*[A-Za-z_][\w\[\], |.]*\s*:")


def _has_return_type_in_docstring(docstring: str) -> bool:
    """Check whether the Returns section contains a typed entry.

    In Google/NumPy mode, extracts the ``Returns:`` section content via
    :func:`_extract_section_content` and checks the first non-empty line
    for a type pattern (``type: description``).  In Sphinx mode, checks
    for the presence of ``:rtype:`` in the raw docstring.

    Args:
        docstring: The raw docstring text to inspect.

    Returns:
        ``True`` when return type information is found, ``False``
        otherwise.  Returns ``True`` conservatively when content
        cannot be extracted (e.g. NumPy underline format).
    """
    if _active_style == "sphinx":
        return ":rtype:" in docstring

    content = _extract_section_content(docstring, "Returns")
    if content is None:
        # NumPy underline format — can't parse, don't false-positive.
        return True

    for line in content.splitlines():
        if line.strip():
            return bool(_RETURNS_TYPE_PATTERN.match(line))

    # Empty Returns section — no content to inspect.
    return True


def _check_missing_return_type(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect functions with a Returns section that lacks type information.

    Flags functions whose ``Returns:`` section has no typed entry AND
    whose signature has no ``->`` return annotation.  Either a typed
    docstring entry or a return annotation satisfies the check (FR20).

    Skips ``__init__``, ``__del__``, ``@property``, and
    ``@cached_property`` methods.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (unused — config gating is in
            the orchestrator).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="missing-return-type"`` when the
        return type is undocumented, or ``None`` otherwise.
    """
    if symbol.docstring is None:
        return None

    if "Returns" not in sections:
        return None

    if symbol.kind not in ("function", "method"):
        return None

    # Skip __init__ and __del__ — constructors/destructors.
    if symbol.name in ("__init__", "__del__"):
        return None

    node = node_index.get(symbol.line)
    if node is None or isinstance(node, ast.ClassDef):
        return None

    if _is_property(node):
        return None

    # FR20: return annotation satisfies the check.
    if node.returns is not None:
        return None

    if _has_return_type_in_docstring(symbol.docstring):
        return None

    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="missing-return-type",
        message=(
            f"Function '{symbol.name}' has a Returns section with no type"
            f" and no return annotation"
        ),
        category="recommended",
    )


def _check_undocumented_init_params(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, _NodeT],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
    """Detect a class with parameterized ``__init__`` but no Args section.

    Fires when a class has an explicit ``__init__`` method with parameters
    beyond ``self``, but neither the class docstring nor the ``__init__``
    docstring contains an ``Args:`` section.  Either location satisfies
    the check (FR24).

    Parameter extraction uses ``posonlyargs + args`` to correctly handle
    PEP 570 positional-only syntax (``/``), where ``self`` may appear in
    ``posonlyargs`` rather than ``args``.

    Structural types (``@dataclass``, ``NamedTuple``, ``TypedDict``) whose
    ``__init__`` is auto-generated at runtime are naturally skipped because
    ``_find_init_method`` returns ``None`` for them.

    Args:
        symbol: The documented symbol to inspect.
        sections: Parsed section headers from the symbol's docstring.
        node_index: Line-number-to-node mapping for the module.
        config: Enrichment configuration (``exclude_args_kwargs``
            controls ``*args``/``**kwargs`` filtering).
        file_path: Source file path for the finding record.

    Returns:
        A ``Finding`` with ``rule="undocumented-init-params"`` when
        constructor parameters are undocumented, or ``None`` otherwise.
    """
    if symbol.kind != "class":
        return None

    node = node_index.get(symbol.line)
    if node is None or not isinstance(node, ast.ClassDef):
        return None

    init_node = _find_init_method(node)
    if init_node is None:
        return None

    # Collect documentable params.  The full positional list is
    # posonlyargs + args; self is always the first element regardless
    # of whether ``/`` appears in the signature (PEP 570).
    all_positional = init_node.args.posonlyargs + init_node.args.args
    params: list[str] = [a.arg for a in all_positional[1:]]
    params.extend(a.arg for a in init_node.args.kwonlyargs)
    if not config.exclude_args_kwargs:
        if init_node.args.vararg:
            params.append(f"*{init_node.args.vararg.arg}")
        if init_node.args.kwarg:
            params.append(f"**{init_node.args.kwarg.arg}")

    if not params:
        return None

    # Check class docstring sections (already parsed by orchestrator).
    if "Args" in sections:
        return None

    # Check __init__ docstring (FR24 — either location satisfies).
    init_docstring = ast.get_docstring(init_node)
    if init_docstring:
        init_sections = _parse_sections(init_docstring, style=_active_style)
        if "Args" in init_sections:
            return None

    param_list = ", ".join(params)
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule="undocumented-init-params",
        message=(
            f"class '{symbol.name}' __init__ has parameters"
            f" ({param_list}) but no Args section in class"
            f" or __init__ docstring"
        ),
        category="required",
    )


# Rules auto-disabled in sphinx mode unless the user explicitly enables them.
_SPHINX_AUTO_DISABLE_RULES: frozenset[str] = frozenset(
    {
        "require_yields",
        "check_extra_yields",
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
    ("require_param_agreement", _check_missing_param_in_docstring),
    ("require_param_agreement", _check_extra_param_in_docstring),
    ("require_deprecation_notice", _check_missing_deprecation),
    ("check_extra_raises", _check_extra_raises_in_docstring),
    ("check_extra_yields", _check_extra_yields_in_docstring),
    ("check_extra_returns", _check_extra_returns_in_docstring),
    ("check_trivial_docstrings", _check_trivial_docstring),
    ("require_return_type", _check_missing_return_type),
    ("require_init_params", _check_undocumented_init_params),
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
    Sets the module-level ``_active_style`` before dispatch so param
    agreement checks use the correct parser. For
    ``prefer_fenced_code_blocks``, a second-pass helper receives an
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
    global _active_style  # noqa: PLW0603
    _active_style = style

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
