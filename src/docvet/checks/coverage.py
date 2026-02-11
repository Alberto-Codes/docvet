"""Coverage check for missing __init__.py files.

Detects directories in the source tree that lack ``__init__.py``,
making their Python files invisible to mkdocstrings documentation
generation.  Uses pure filesystem checks via ``pathlib`` — no AST,
no git, no external dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from docvet.checks import Finding

__all__ = ["check_coverage"]


def check_coverage(src_root: Path, files: Sequence[Path]) -> list[Finding]:
    """Detect missing ``__init__.py`` files in parent directories.

    Walks from each file's parent directory up to *src_root*, checking
    for ``__init__.py`` existence at each level.  Produces one finding per
    missing directory, deduplicated, with deterministic ordering.

    Args:
        src_root: Root directory of the source tree (e.g., ``src/``).
        files: Discovered Python file paths to check.

    Returns:
        Sorted list of findings for missing ``__init__.py`` directories.
    """
    # Map: missing_dir -> list of affected files
    missing_dirs: dict[Path, list[Path]] = {}
    init_cache: dict[Path, bool] = {}

    for file in files:
        if not file.is_relative_to(src_root):
            continue

        parent = file.parent
        if parent == src_root:
            continue

        # Walk parent dirs up to (but not including) src_root
        current = parent
        while current != src_root:
            if current not in init_cache:
                init_cache[current] = (current / "__init__.py").exists()
            if not init_cache[current]:
                missing_dirs.setdefault(current, []).append(file)
            current = current.parent

    # Build findings: one per directory, sorted by relative path
    findings: list[Finding] = []
    for dir_path in sorted(
        missing_dirs, key=lambda d: d.relative_to(src_root).as_posix()
    ):
        affected = missing_dirs[dir_path]
        representative = str(sorted(affected)[0])
        count = len(affected)
        dir_rel = dir_path.relative_to(src_root).as_posix()
        message = (
            f"Directory '{dir_rel}' lacks __init__.py "
            f"({count} file{'s' if count != 1 else ''} affected)"
        )
        findings.append(
            Finding(
                file=representative,
                line=1,
                symbol="<module>",
                rule="missing-init",
                message=message,
                category="required",
            )
        )

    return findings
