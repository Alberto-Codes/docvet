"""Parameter agreement enrichment checks.

Detects mismatches between function signature parameters and ``Args:``
section entries.  Supports both Google-style and Sphinx/RST conventions
via the module-level ``_active_style`` in the parent package.

See Also:
    [`docvet.checks.enrichment`][]: Orchestrator and dispatch table.
    [`docvet.checks._finding`][]: ``Finding`` dataclass.

Examples:
    Invoke the missing-param check directly:

    ```python
    finding = _check_missing_param_in_docstring(symbol, sections, idx, cfg, path)
    ```
"""

from __future__ import annotations

import ast
import re

import docvet.checks.enrichment as _enrichment_pkg
from docvet.ast_utils import Symbol
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

from . import _extract_section_content
from ._forward import _NodeT

# Regex to extract param names from Google-style Args: section entries.
# Matches at detected base indent, with optional leading */** for varargs.
_ARGS_ENTRY_PATTERN = re.compile(r"\*{0,2}(\w+)[^\S\n]*[\s(:]")

# Regex to extract param names from Sphinx :param name: entries.
_SPHINX_PARAM_PATTERN = re.compile(r":param\s+(\w+)\s*:")

# Regex to extract exception names from Google-style Raises: section entries.
# Matches ClassName followed by colon at entry level (analogous to _ARGS_ENTRY_PATTERN).
_RAISES_ENTRY_PATTERN = re.compile(r"(\w+)\s*:")

# Regex to extract exception names from Sphinx :raises ExcType: entries.
_SPHINX_RAISES_PATTERN = re.compile(r":raises\s+(\w+)\s*:")


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
    doc_params = _parse_args_entries(
        symbol.docstring, style=_enrichment_pkg._active_style
    )
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
    doc_params = _parse_args_entries(
        symbol.docstring, style=_enrichment_pkg._active_style
    )
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
