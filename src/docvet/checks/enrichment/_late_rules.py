"""Late enrichment rules — trivial docstring, return type, init params.

Rules that were added after the initial enrichment rule set.  Includes
trivial-docstring detection (summary restates symbol name),
missing-return-type (no typed Returns entry or annotation), and
undocumented-init-params (class ``__init__`` has parameters but no
``Args:`` section).

See Also:
    [`docvet.checks.enrichment`][]: Orchestrator and dispatch table.
    [`docvet.checks._finding`][]: ``Finding`` dataclass.

Examples:
    Invoke the trivial-docstring check directly:

    ```python
    finding = _check_trivial_docstring(symbol, sections, node_index, config, path)
    ```
"""

from __future__ import annotations

import ast
import re

import docvet.checks.enrichment as _enrichment_pkg
from docvet.ast_utils import Symbol, module_display_name
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

from . import _extract_section_content, _parse_sections
from ._class_module import _find_init_method
from ._forward import _is_property, _NodeT

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
    if _enrichment_pkg._active_style == "sphinx":
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
        init_sections = _parse_sections(
            init_docstring, style=_enrichment_pkg._active_style
        )
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
