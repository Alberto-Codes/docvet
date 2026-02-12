"""Griffe compatibility check for docstring rendering issues.

Captures warnings from griffe's Google-style docstring parser to detect
parameter/type mismatches and formatting issues that would cause rendering
problems in mkdocs-material + mkdocstrings documentation.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal

try:
    import griffe
except ImportError:
    griffe = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from griffe import Object as GriffeObject

from docvet.checks import Finding

_UNKNOWN_PARAM_PATTERN = "does not appear in the function signature"
_MISSING_TYPE_PATTERN = "No type or annotation for"
_WARNING_PATTERN = re.compile(r"^(.+?):(\d+): (.+)$")


class _WarningCollector(logging.Handler):
    """Collects WARNING-level log records from the griffe logger."""

    def __init__(self) -> None:
        """Initialize the handler with WARNING level and empty records list."""
        super().__init__(level=logging.WARNING)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Store the log record.

        Args:
            record: The log record emitted by the griffe logger.
        """
        self.records.append(record)


def _classify_warning(message: str) -> tuple[str, Literal["required", "recommended"]]:
    """Classify a griffe warning message into a rule and category.

    Uses priority-ordered substring matching: unknown-param is checked
    before missing-type to handle ambiguous messages correctly.

    Args:
        message: The warning message text from a griffe log record.

    Returns:
        A tuple of (rule, category) where rule is a kebab-case identifier
        and category is "required" or "recommended".
    """
    if _UNKNOWN_PARAM_PATTERN in message:
        return ("griffe-unknown-param", "required")
    if _MISSING_TYPE_PATTERN in message:
        return ("griffe-missing-type", "recommended")
    return ("griffe-format-warning", "recommended")


def _resolve_file_set(files: Sequence[Path]) -> set[Path]:
    """Resolve file paths to absolute paths for set membership tests.

    Args:
        files: Sequence of file paths to resolve.

    Returns:
        A set of resolved absolute paths.
    """
    return {f.resolve() for f in files}


def _walk_objects(obj: GriffeObject, file_set: set[Path]) -> Iterator[GriffeObject]:
    """Walk a griffe object tree yielding objects whose files are in file_set.

    Skips alias objects (avoids AliasResolutionError), objects without
    docstrings (nothing to parse), and objects whose filepath is not in
    the target file set.

    Args:
        obj: The root griffe object (typically a package or module).
        file_set: Set of resolved file paths to include.

    Yields:
        Griffe objects that have docstrings and belong to files in file_set.
    """
    stack: list[GriffeObject] = [obj]
    while stack:
        current = stack.pop()
        if current.is_alias:
            continue
        if current.docstring is not None and current.filepath in file_set:
            yield current
        stack.extend(current.members.values())  # type: ignore[arg-type]


def _build_finding_from_record(
    record: logging.LogRecord, obj: GriffeObject
) -> Finding | None:
    """Build a Finding from a griffe log record and griffe object.

    Parses the log record message using _WARNING_PATTERN to extract the
    line number and message text, then classifies the message.

    Args:
        record: A WARNING-level log record from the griffe logger.
        obj: The griffe object that was being parsed when the warning fired.

    Returns:
        A Finding if the record message matches the expected format,
        or None if the format is unrecognized.
    """
    match = _WARNING_PATTERN.match(record.getMessage())
    if match is None:
        return None
    line = int(match.group(2))
    message_text = match.group(3)
    rule, category = _classify_warning(message_text)
    return Finding(
        file=str(obj.filepath),
        line=line,
        symbol=obj.name,
        rule=rule,
        message=f"{obj.kind.value.capitalize()} '{obj.name}' {message_text}",
        category=category,
    )


def check_griffe_compat(src_root: Path, files: Sequence[Path]) -> list[Finding]:
    """Check Python packages for griffe docstring compatibility issues.

    Loads each package under src_root via griffe, captures parser warnings,
    and converts them to Finding objects. Packages that fail to load are
    skipped without aborting other packages.

    Args:
        src_root: Root source directory containing Python packages.
        files: Sequence of file paths to check (used to filter griffe objects).

    Returns:
        A list of Finding objects for docstring rendering compatibility issues.
    """
    if griffe is None:
        return []
    if not files:
        return []

    file_set = _resolve_file_set(files)
    findings: list[Finding] = []

    griffe_logger = logging.getLogger("griffe")
    handler = _WarningCollector()
    griffe_logger.addHandler(handler)
    try:
        for child in sorted(src_root.iterdir()):
            if not child.is_dir() or not (child / "__init__.py").exists():
                continue
            try:
                package = griffe.load(
                    child.name,
                    search_paths=[str(src_root)],
                    docstring_parser="google",
                    allow_inspection=False,
                )
            except (
                griffe.LoadingError,
                ModuleNotFoundError,
                OSError,
                SyntaxError,
            ):
                continue

            for obj in _walk_objects(package, file_set):  # type: ignore[arg-type]
                before = len(handler.records)
                _ = obj.docstring.parsed  # type: ignore[union-attr]
                after = len(handler.records)
                for record in handler.records[before:after]:
                    finding = _build_finding_from_record(record, obj)
                    if finding is not None:
                        findings.append(finding)
    finally:
        griffe_logger.removeHandler(handler)

    return findings
