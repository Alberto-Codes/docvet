"""Enrichment check for docstring completeness.

Orchestrates enrichment rules that detect missing or incomplete docstring
sections by combining AST analysis with section header parsing.  Rules
are organized into submodules: ``_forward`` (missing Raises, Returns,
Yields, Receives, Warns, Other Parameters), ``_class_module`` (missing
Attributes, typed attributes, Examples, cross-references, fenced code
blocks), ``_params`` (parameter agreement), ``_deprecation`` (missing
deprecation notices), ``_reverse`` (extra Raises/Yields/Returns), and
``_late_rules`` (trivial docstrings, return types, init params,
scaffold-incomplete).  This module retains section parsing, shared
constants, and the ``check_enrichment`` dispatch orchestrator.

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

from docvet.ast_utils import Symbol, get_documented_symbols
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
    _extract_exception_name,  # noqa: F401 – re-exported for submodules
    _has_decorator,
    _is_meaningful_return,  # noqa: F401 – re-exported for submodules
    _is_property,  # noqa: F401 – re-exported for submodules
    _is_stub_function,
    _is_warn_call,  # noqa: F401 – re-exported for submodules
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
    _find_init_method,  # noqa: F401 – re-exported for tests/submodules
    _has_self_assignments,  # noqa: F401 – re-exported for tests
    _is_dataclass,  # noqa: F401 – re-exported for tests
    _is_enum,  # noqa: F401 – re-exported for tests
    _is_init_module,  # noqa: F401 – re-exported for tests
    _is_namedtuple,  # noqa: F401 – re-exported for tests
    _is_protocol,  # noqa: F401 – re-exported for tests
    _is_typeddict,  # noqa: F401 – re-exported for tests
)

# Active docstring style, set by the orchestrator before dispatch.
# Allows param agreement checks to use the correct parser without
# changing the uniform check function signature.
_active_style: str = "google"

from ._deprecation import (  # noqa: E402
    _check_missing_deprecation,
    _has_deprecated_decorator,  # noqa: F401 – re-exported for tests
    _is_deprecation_warn_call,  # noqa: F401 – re-exported for tests
)
from ._params import (  # noqa: E402
    _check_extra_param_in_docstring,
    _check_missing_param_in_docstring,
    _extract_signature_params,  # noqa: F401 – re-exported for tests
    _parse_args_entries,  # noqa: F401 – re-exported for tests
    _parse_raises_entries,  # noqa: F401 – re-exported for tests
)

# ---------------------------------------------------------------------------
# Public orchestrator
# ---------------------------------------------------------------------------

_CheckFn = Callable[
    [Symbol, set[str], dict[int, _NodeT], EnrichmentConfig, str],
    Finding | None,
]

from ._late_rules import (  # noqa: E402
    _RETURNS_TYPE_PATTERN,  # noqa: F401 – re-exported for tests
    _TODO_PATTERN,  # noqa: F401 – re-exported for tests
    _check_missing_return_type,
    _check_scaffold_incomplete,
    _check_trivial_docstring,
    _check_undocumented_init_params,
    _decompose_name,  # noqa: F401 – re-exported for tests
    _extract_summary_words,  # noqa: F401 – re-exported for tests
)
from ._reverse import (  # noqa: E402
    _check_extra_raises_in_docstring,
    _check_extra_returns_in_docstring,
    _check_extra_yields_in_docstring,
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
    ("scaffold_incomplete", _check_scaffold_incomplete),
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
