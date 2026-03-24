"""Section scaffolding engine for the ``docvet fix`` command.

Inserts missing docstring sections as scaffolded placeholders based on
enrichment findings.  Uses AST line numbers and string-level operations
for insertion (no libcst dependency).  Processes symbols in reverse line
order to preserve line numbers across multiple insertions within the
same file.

The engine is deterministic and idempotent: same input always produces
same output, and running twice on the same file produces no changes.

Examples:
    Scaffold missing sections from enrichment findings:

    ```python
    from docvet.checks.fix import scaffold_missing_sections

    modified = scaffold_missing_sections(source, tree, findings)
    ```

See Also:
    [`docvet.checks.enrichment`][]: Produces the findings consumed here.
    [`docvet.ast_utils`][]: Provides ``get_docstring_range``.
"""

from __future__ import annotations

import ast
import re

from docvet.ast_utils import get_docstring_range
from docvet.checks._finding import Finding

__all__ = ["scaffold_missing_sections"]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Canonical Google-style section order.
SECTION_ORDER: tuple[str, ...] = (
    "Args",
    "Other Parameters",
    "Returns",
    "Yields",
    "Receives",
    "Raises",
    "Warns",
    "Attributes",
    "Examples",
    "See Also",
)

# Map enrichment rule names to section header names.
RULE_TO_SECTION: dict[str, str] = {
    "missing-raises": "Raises",
    "missing-yields": "Yields",
    "missing-receives": "Receives",
    "missing-warns": "Warns",
    "missing-other-parameters": "Other Parameters",
    "missing-attributes": "Attributes",
    "missing-typed-attributes": "Attributes",
    "missing-examples": "Examples",
    "missing-cross-references": "See Also",
    "missing-returns": "Returns",
}

# Section header pattern for idempotency (existing section detection).
_SECTION_PATTERN = re.compile(
    r"^\s*(Args|Returns|Raises|Yields|Receives|Warns"
    r"|Other Parameters|Attributes|Examples|See Also"
    r"|Notes|References|Warnings|Extended Summary|Methods):\s*$",
    re.MULTILINE,
)

_TODO_MARKER = "[TODO: describe]"


# ---------------------------------------------------------------------------
# AST extraction helpers
# ---------------------------------------------------------------------------


def _extract_raised_exceptions(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    """Extract unique exception class names from raise statements.

    Args:
        node: A function or async function AST node.

    Returns:
        Ordered list of unique exception names found in the body.
    """
    names: list[str] = []
    seen: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, ast.Raise) or child.exc is None:
            continue
        name: str | None = None
        exc = child.exc
        if isinstance(exc, ast.Name):
            name = exc.id
        elif isinstance(exc, ast.Call):
            if isinstance(exc.func, ast.Name):
                name = exc.func.id
            elif isinstance(exc.func, ast.Attribute):
                name = exc.func.attr
        elif isinstance(exc, ast.Attribute):
            name = exc.attr
        if name and name not in seen:
            names.append(name)
            seen.add(name)
    return names


def _extract_class_fields(node: ast.ClassDef) -> list[str]:
    """Extract field names from annotated assignments in a class body.

    Works for dataclasses, NamedTuples, and TypedDicts whose fields
    are expressed as ``name: type`` annotations in the class body.

    Args:
        node: A ``ClassDef`` AST node.

    Returns:
        Ordered list of field names.
    """
    fields: list[str] = []
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fields.append(item.target.id)
    return fields


def _extract_return_type(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    """Extract the return type annotation as a source string.

    Args:
        node: A function AST node.

    Returns:
        The unparsed return annotation, or ``None`` when absent.
    """
    if node.returns is not None:
        return ast.unparse(node.returns)
    return None


# ---------------------------------------------------------------------------
# Section content builders
# ---------------------------------------------------------------------------


def _build_section_lines(
    section: str,
    node: ast.AST,
    indent: str,
    newline: str,
) -> list[str]:
    r"""Build scaffold content lines for a section.

    Uses AST re-extraction to produce section-specific placeholders
    (exception names for Raises, field names for Attributes, etc.).
    Examples sections use fenced code block placeholders to avoid
    triggering ``prefer-fenced-code-blocks`` findings.

    Args:
        section: The section header name (e.g. ``"Raises"``).
        node: The AST node for the symbol being scaffolded.
        indent: Whitespace prefix for section header lines.
        newline: Line ending style (``"\n"`` or ``"\r\n"``).

    Returns:
        List of lines (including newlines) for the scaffold block.
    """
    ci = indent + "    "  # content indent

    if section == "Raises" and isinstance(
        node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        exceptions = _extract_raised_exceptions(node)
        if exceptions:
            result = [f"{indent}{section}:{newline}"]
            for exc in exceptions:
                result.append(
                    f"{ci}{exc}: [TODO: describe when this is raised]{newline}"
                )
            return result

    if section == "Returns" and isinstance(
        node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        ret_type = _extract_return_type(node)
        if ret_type:
            return [
                f"{indent}{section}:{newline}",
                f"{ci}{ret_type}: [TODO: describe return value]{newline}",
            ]
        return [
            f"{indent}{section}:{newline}",
            f"{ci}[TODO: describe return value]{newline}",
        ]

    if section == "Attributes" and isinstance(node, ast.ClassDef):
        fields = _extract_class_fields(node)
        if fields:
            result = [f"{indent}{section}:{newline}"]
            for field_name in fields:
                result.append(f"{ci}{field_name}: {_TODO_MARKER}{newline}")
            return result

    if section == "Examples":
        return [
            f"{indent}{section}:{newline}",
            f"{ci}```python{newline}",
            f"{ci}# [TODO: add example usage]{newline}",
            f"{ci}```{newline}",
        ]

    # Generic placeholder for Yields, Receives, Warns, Other Parameters,
    # See Also, and any section without specific extraction logic.
    return [
        f"{indent}{section}:{newline}",
        f"{ci}{_TODO_MARKER}{newline}",
    ]


# ---------------------------------------------------------------------------
# Indentation detection
# ---------------------------------------------------------------------------


def _detect_indent(lines: list[str], doc_start_0: int, doc_end_0: int) -> str:
    """Detect docstring section header indentation.

    For multi-line docstrings, uses the closing ``\"\"\"`` line's leading
    whitespace.  For one-liners, uses the opening line's leading
    whitespace.

    Args:
        lines: Source file split into lines (with endings).
        doc_start_0: Zero-based start line index of the docstring.
        doc_end_0: Zero-based end line index of the docstring.

    Returns:
        The indentation whitespace string for section headers.
    """
    if doc_start_0 != doc_end_0:
        closing = lines[doc_end_0]
        stripped = closing.lstrip()
        return closing[: len(closing) - len(stripped)]
    line = lines[doc_start_0]
    stripped = line.lstrip()
    return line[: len(line) - len(stripped)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scaffold_missing_sections(
    source: str,
    tree: ast.Module,
    findings: list[Finding],
) -> str:
    """Insert scaffolded sections into docstrings based on findings.

    Takes enrichment findings (``missing-raises``, ``missing-returns``,
    etc.) and inserts the corresponding section headers with placeholder
    content into the source file.  Existing sections are preserved
    byte-for-byte.

    Args:
        source: Raw source text of the file.
        tree: Parsed AST module matching *source*.
        findings: Enrichment findings with ``rule`` values that map to
            section names via ``RULE_TO_SECTION``.

    Returns:
        Modified source text with scaffolded sections inserted.
        Returns *source* unchanged when there are no actionable findings.
    """
    if not findings:
        return source

    # Group findings by symbol def/class line.
    by_line: dict[int, list[Finding]] = {}
    for f in findings:
        if f.rule in RULE_TO_SECTION:
            by_line.setdefault(f.line, []).append(f)
    if not by_line:
        return source

    _ScopeNode = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef

    # Build node index for O(1) lookup.
    node_map: dict[int, _ScopeNode] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node_map[node.lineno] = node

    lines = source.splitlines(keepends=True)

    # Detect newline style from file content.
    newline = "\n"
    for ln in lines:
        if ln.endswith("\r\n"):
            newline = "\r\n"
            break
        if ln.endswith("\n"):
            break

    # Process in reverse line order to preserve line numbers.
    for sym_line in sorted(by_line.keys(), reverse=True):
        node = node_map.get(sym_line)
        if not node:
            continue
        doc_range = get_docstring_range(node)
        if not doc_range:
            continue

        doc_start_0, doc_end_0 = doc_range[0] - 1, doc_range[1] - 1
        docstring = ast.get_docstring(node, clean=False) or ""
        existing = set(_SECTION_PATTERN.findall(docstring))

        # Collect sections to add, skipping existing for idempotency.
        to_add: list[str] = []
        seen: set[str] = set()
        for f in by_line[sym_line]:
            s = RULE_TO_SECTION.get(f.rule)
            if s and s not in existing and s not in seen:
                to_add.append(s)
                seen.add(s)
        if not to_add:
            continue

        # Sort by canonical section order.
        order_map = {s: i for i, s in enumerate(SECTION_ORDER)}
        to_add.sort(key=lambda s: order_map.get(s, 999))
        indent = _detect_indent(lines, doc_start_0, doc_end_0)

        if doc_start_0 == doc_end_0:
            # One-liner expansion.
            _expand_oneliner(lines, doc_start_0, to_add, node, indent, newline)
            continue

        # Multi-line: insert scaffold before closing """.
        scaffold: list[str] = []
        prev = lines[doc_end_0 - 1].rstrip("\r\n") if doc_end_0 > 0 else ""
        prev_blank = not prev.strip()
        for i, section in enumerate(to_add):
            if not (i == 0 and prev_blank):
                scaffold.append(newline)
            scaffold.extend(_build_section_lines(section, node, indent, newline))
        lines[doc_end_0:doc_end_0] = scaffold

    return "".join(lines)


def _expand_oneliner(
    lines: list[str],
    line_idx: int,
    sections: list[str],
    node: ast.AST,
    indent: str,
    newline: str,
) -> None:
    """Expand a one-liner docstring to multi-line with scaffolded sections.

    Detects the quote style (``\"\"\"`` or ``'''``) and preserves any
    raw-string prefix (``r\"\"\"``).

    Args:
        lines: Mutable list of source lines (modified in place).
        line_idx: Zero-based index of the one-liner line.
        sections: Section names to scaffold.
        node: AST node for the symbol.
        indent: Whitespace prefix for section headers.
        newline: Line ending style.
    """
    content = lines[line_idx].rstrip("\r\n")
    for q in ('"""', "'''"):
        first_q = content.find(q)
        last_q = content.rfind(q)
        if first_q != -1 and last_q != -1 and first_q != last_q:
            prefix = content[:first_q]
            summary = content[first_q + 3 : last_q].strip()
            new_lines = [f"{prefix}{q}{summary}{newline}"]
            for section in sections:
                new_lines.append(newline)
                new_lines.extend(_build_section_lines(section, node, indent, newline))
            new_lines.append(f"{indent}{q}{newline}")
            lines[line_idx : line_idx + 1] = new_lines
            break
