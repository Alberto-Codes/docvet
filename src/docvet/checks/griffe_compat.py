"""Griffe compatibility check for docstring rendering issues.

Captures warnings from griffe's Google-style docstring parser to detect
parameter/type mismatches and formatting issues that would cause rendering
problems in mkdocs-material + mkdocstrings documentation. CLI and MCP runs
share decoded sources through an encoding-aware loader that retains griffe
package context and inherited signatures.

Examples:
    Run the griffe compatibility check on a list of files:

    ```python
    from docvet.checks import check_griffe_compat

    findings = check_griffe_compat(file_paths)
    ```

See Also:
    [`docvet.checks`][]: Package-level re-exports.
    [`docvet.config`][]: Configuration dataclasses for check modules.
"""

from __future__ import annotations

import logging
import re
import types
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from griffe import Alias as GriffeAlias
    from griffe import Module as GriffeModule
    from griffe import Object as GriffeObject

from docvet.ast_utils import split_physical_lines
from docvet.checks._finding import Finding
from docvet.source import SourceCache

try:
    import griffe
except ImportError:
    griffe: types.ModuleType | None = None

__all__ = ["check_griffe_compat"]

_UNKNOWN_PARAM_PATTERN = "does not appear in the function signature"
_MISSING_TYPE_PATTERN = "No type or annotation for"
_WARNING_PATTERN = re.compile(r"^(.+?):(\d+): (.+)$")


class _WarningCollector(logging.Handler):
    """Collects WARNING-level log records from the griffe logger.

    Attributes:
        records (list[logging.LogRecord]): Captured warning-level log records.

    Examples:
        Attach to a logger to capture warnings:

        ```python
        handler = _WarningCollector()
        logger.addHandler(handler)
        # ... trigger warnings ...
        print(handler.records)
        ```
    """

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


def _walk_objects(
    obj: GriffeObject | GriffeAlias, file_set: set[Path]
) -> Iterator[GriffeObject]:
    """Walk a griffe object tree yielding objects whose files are in file_set.

    Skips alias objects (avoids AliasResolutionError), objects without
    docstrings (nothing to parse), and objects whose filepath is not in
    the target file set. Past the alias guard each entry is cast to a
    concrete ``Object`` so the yield type holds without an ignore.

    Args:
        obj: The root griffe object (typically a package or module).
        file_set: Set of resolved file paths to include.

    Yields:
        Griffe objects that have docstrings and belong to files in file_set.
    """
    stack: list[GriffeObject | GriffeAlias] = [obj]
    while stack:
        current = stack.pop()
        if current.is_alias:
            continue
        # ``is_alias`` is a runtime property ty cannot narrow on; past the
        # guard, ``current`` is a concrete object.
        obj_ = cast("GriffeObject", current)
        if obj_.docstring is not None and obj_.filepath in file_set:
            yield obj_
        stack.extend(obj_.members.values())


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


def _collect_object_findings(
    obj: GriffeObject,
    handler: _WarningCollector,
) -> list[Finding]:
    """Collect docstring findings for a single griffe object.

    Returns early if the object has no docstring (callers guarantee one
    exists, but the guard keeps production code safe). Otherwise, triggers
    docstring parsing, captures any new warning records, and converts them
    to findings.

    Args:
        obj: A griffe object with a docstring to parse.
        handler: Attached warning collector for the griffe logger.

    Returns:
        A list of findings from docstring compatibility warnings for
        this object.
    """
    if obj.docstring is None:  # guaranteed by _walk_objects filter
        return []
    before = len(handler.records)
    _ = obj.docstring.parsed
    after = len(handler.records)
    findings: list[Finding] = []
    for record in handler.records[before:after]:
        finding = _build_finding_from_record(record, obj)
        if finding is not None:
            findings.append(finding)
    return findings


def _load_and_check_packages(
    src_root: Path,
    file_set: set[Path],
    handler: _WarningCollector,
) -> list[Finding]:
    """Load griffe packages under *src_root* and collect docstring findings.

    Iterates directories that look like Python packages, loads them via
    griffe, triggers docstring parsing to capture warnings, and converts
    captured records to findings.

    Args:
        src_root: Root source directory containing Python packages.
        file_set: Resolved absolute paths to filter griffe objects.
        handler: Attached warning collector for the griffe logger.

    Returns:
        A list of findings from docstring compatibility warnings.
    """
    if griffe is None:
        return []

    findings: list[Finding] = []
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

        for obj in _walk_objects(package, file_set):
            findings.extend(_collect_object_findings(obj, handler))
    return findings


def _check_source_documents(
    src_root: Path,
    file_set: set[Path],
    handler: _WarningCollector,
    source_cache: SourceCache,
) -> list[Finding]:
    """Parse selected package sources without reopening them as UTF-8.

    Override the pinned griffe 2.x loader's source-reading hook, forwarding
    decoded text to its public visitor. Retain package hierarchy, collections,
    and inherited signatures. Unselected dependency failures use a separate
    cache so loading context does not expand the requested diagnostic scope.

    Args:
        src_root: Root containing Python packages.
        file_set: Selected absolute source paths.
        handler: Collector for docstring parser warnings.
        source_cache: Invocation cache shared by analysis consumers.

    Returns:
        Rendering findings from successfully decoded selected package files.
    """
    if griffe is None:
        return []
    auxiliary_cache = SourceCache()
    griffe_api = griffe

    class EncodingAwareLoader(griffe_api.GriffeLoader):
        """Keep griffe's package context while supplying decoded source.

        Examples:
            Instantiate with the same options as ``griffe.GriffeLoader``.
        """

        def _visit_module(
            self,
            module_name: str,
            module_path: Path,
            parent: GriffeModule | None = None,
        ) -> GriffeModule:
            """Visit a decoded source while retaining loader package context.

            Args:
                module_name: Name assigned by the loader.
                module_path: Source path selected by the loader.
                parent: Containing package, when present.

            Returns:
                Visited module, or an empty shell for an unreadable source.
            """
            cache = (
                source_cache if module_path.resolve() in file_set else auxiliary_cache
            )
            document = cache.get(module_path)
            # An empty shell retains package topology when an initializer failed;
            # the shared cache already carries the selected input's error.
            code = document.text if document is not None else ""
            self.lines_collection[module_path] = split_physical_lines(code)
            return griffe_api.visit(
                module_name,
                filepath=module_path,
                code=code,
                parent=parent,
                extensions=self.extensions,
                docstring_parser=self.docstring_parser,
                docstring_options=self.docstring_options,
                lines_collection=self.lines_collection,
                modules_collection=self.modules_collection,
            )

    loader = EncodingAwareLoader(
        search_paths=[str(src_root)], docstring_parser="google", allow_inspection=False
    )
    findings: list[Finding] = []
    for child in sorted(src_root.iterdir()):
        if not child.is_dir() or not (child / "__init__.py").exists():
            continue
        try:
            package = loader.load(child.name)
        except (griffe.LoadingError, ModuleNotFoundError, OSError, SyntaxError):
            continue
        for obj in _walk_objects(package, file_set):
            findings.extend(_collect_object_findings(obj, handler))
    return findings


def check_griffe_compat(
    src_root: Path,
    files: Sequence[Path],
    *,
    source_cache: SourceCache | None = None,
) -> list[Finding]:
    """Check Python packages for griffe docstring compatibility issues.

    Loads each package under src_root via griffe, captures parser warnings,
    and converts them to Finding objects. Packages that fail to load are
    skipped without aborting other packages.

    Args:
        src_root: Root source directory containing Python packages.
        files: Sequence of file paths to check (used to filter griffe objects).
        source_cache: Shared decoded source cache. When supplied, use griffe's
            source visitor so declared encodings and failed siblings cannot
            prevent selected valid files from being checked.

    Returns:
        A list of Finding objects for docstring rendering compatibility issues.
    """
    if griffe is None:
        return []
    if not files:
        return []

    file_set = _resolve_file_set(files)
    griffe_logger = logging.getLogger("griffe")
    handler = _WarningCollector()
    griffe_logger.addHandler(handler)
    try:
        if source_cache is None:
            findings = _load_and_check_packages(src_root, file_set, handler)
        else:
            findings = _check_source_documents(
                src_root, file_set, handler, source_cache
            )
    finally:
        griffe_logger.removeHandler(handler)

    return findings
