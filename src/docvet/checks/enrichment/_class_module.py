"""Class/module enrichment checks and helpers.

Detects missing Attributes, typed-attribute format, Examples, cross-references,
and non-fenced code block patterns in class and module docstrings.  Each
``_check_*`` function follows the uniform five-parameter dispatch signature
used by ``_RULE_DISPATCH`` in the enrichment orchestrator, except
``_check_fenced_code_blocks_extra`` which is called directly by the
orchestrator with a reduced signature.

See Also:
    [`docvet.checks.enrichment`][]: Orchestrator and dispatch table.
    [`docvet.checks._finding`][]: ``Finding`` dataclass.

Examples:
    Invoke a single class/module check directly:

    ```python
    finding = _check_missing_attributes(symbol, sections, node_index, config, path)
    ```
"""

from __future__ import annotations

import ast
import re
from typing import Literal

from docvet.ast_utils import Symbol, module_display_name
from docvet.checks._finding import Finding
from docvet.config import EnrichmentConfig

from . import _SEE_ALSO, _XREF_MD_LINK, _XREF_SPHINX, _extract_section_content
from ._forward import _NodeT

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
