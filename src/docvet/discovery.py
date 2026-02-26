"""File discovery module for locating Python files to analyze.

Resolves which Python files to check based on the selected discovery
mode: git diff (default), staged files, explicit file list, or full
codebase scan.  All modes return a sorted ``list[Path]`` of absolute
file paths.

Exclude patterns support four dispatch branches following ``.gitignore``
semantics: trailing-slash directory patterns (``build/``), double-star
recursive globs (``**/test_*.py``), path-level ``fnmatch`` patterns
(``scripts/gen_*.py``), and component-level patterns (``tests``).

Examples:
    Discover staged files via the CLI::

        $ docvet check --staged

    Discover the full codebase::

        $ docvet check --all

See Also:
    [`docvet.cli`][]: Subcommands that invoke discovery.
    [`docvet.checks`][]: Check functions that consume discovered files.
"""

from __future__ import annotations

import enum
import fnmatch
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path, PurePosixPath

from docvet.config import DocvetConfig

__all__: list[str] = []

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DiscoveryMode(enum.Enum):
    """Internal discovery mode for file selection.

    Examples:
        Diff mode checks files changed since the last commit:

        ```python
        mode = DiscoveryMode.DIFF
        ```

        Staged mode checks files in the git index:

        ```python
        mode = DiscoveryMode.STAGED
        ```

        All mode scans the entire codebase:

        ```python
        mode = DiscoveryMode.ALL
        ```
    """

    DIFF = enum.auto()
    STAGED = enum.auto()
    ALL = enum.auto()
    FILES = enum.auto()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _run_git(args: list[str], cwd: Path, *, warn: bool = True) -> list[str] | None:
    """Run a git command and return stdout lines.

    Args:
        args: Git subcommand and arguments (e.g. ``["diff", "--name-only"]``).
        cwd: Working directory for the git process.
        warn: If *True*, print a warning to stderr on failure. When
            *False*, fail silently (used by ``_walk_all`` fallback).

    Returns:
        List of stripped, non-empty stdout lines on success, or *None*
        on failure. An empty list means git succeeded but produced no
        output.

    Examples:
        List changed files:

        ```python
        _run_git(["diff", "--name-only"], cwd=Path("/repo"))
        # ['src/foo.py', 'src/bar.py']
        ```
    """
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )
    if result.returncode != 0:
        if warn:
            stderr = result.stderr.strip()
            print(
                f"docvet: git {args[0]} failed: {stderr}",
                file=sys.stderr,
            )
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _matches_double_star(normalized: str, pattern: str) -> bool:
    """Match a path against a pattern containing ``**``.

    ``fnmatch.fnmatch`` treats ``**`` as ``*`` (matches any characters
    including ``/``), which handles the 1+ directory-segment case.  This
    helper adds zero-segment fallbacks so that leading ``**/`` also
    matches root-level files and middle ``/**/`` also matches adjacent
    directories.

    Args:
        normalized: Forward-slash-normalized relative path.
        pattern: Glob pattern containing ``**``.

    Returns:
        *True* if the path matches the pattern.
    """
    if fnmatch.fnmatch(normalized, pattern):
        return True
    if pattern.startswith("**/") and fnmatch.fnmatch(normalized, pattern[3:]):
        return True
    if "/**/" in pattern and fnmatch.fnmatch(
        normalized, pattern.replace("/**/", "/", 1)
    ):
        return True
    return False


def _is_excluded(rel_path: str, exclude: list[str]) -> bool:
    """Check whether a relative path matches any exclude pattern.

    Follows ``.gitignore`` semantics with four pattern dispatch branches:

    1. **Trailing-slash** (``build/``): match directory components only.
       Simple names match at any depth; paths with ``/`` are root-anchored.
    2. **Double-star** (``**/test_*.py``): delegate to
       :func:`_matches_double_star` for recursive glob matching.
    3. **Path-level** (``scripts/gen_*.py``): ``fnmatch`` against the full
       relative path.
    4. **Component-level** (``tests``): ``fnmatch`` against each individual
       path component.

    Args:
        rel_path: File path relative to the project root (forward slashes).
        exclude: List of exclude patterns from configuration.

    Returns:
        *True* if the path matches any exclude pattern.
    """
    normalized = rel_path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    for pattern in exclude:
        if pattern.endswith("/"):
            dirname = pattern.rstrip("/")
            if "/" in dirname:
                if normalized.startswith(dirname + "/"):
                    return True
            elif dirname in parts[:-1]:
                return True
        elif "**" in pattern:
            if _matches_double_star(normalized, pattern):
                return True
        elif "/" in pattern:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        else:
            for component in parts:
                if fnmatch.fnmatch(component, pattern):
                    return True
    return False


def _collect_python_files(
    path_iter: Iterable[Path],
    config: DocvetConfig,
) -> list[Path]:
    """Filter and collect Python files from a path source.

    Applies symlink, suffix, and exclusion checks to each candidate
    path, returning only valid ``.py`` files.

    Args:
        path_iter: Iterator of candidate file paths (absolute or
            relative to the project root).
        config: Configuration providing ``project_root`` and ``exclude``
            patterns.

    Returns:
        Sorted list of absolute paths to valid ``.py`` files.
    """
    paths: list[Path] = []
    for raw_path in path_iter:
        if raw_path.is_symlink():
            continue
        abs_path = raw_path.resolve()
        if abs_path.suffix != ".py":
            continue
        try:
            rel = PurePosixPath(abs_path.relative_to(config.project_root)).as_posix()
        except ValueError:
            continue
        if _is_excluded(rel, config.exclude):
            continue
        paths.append(abs_path)
    return sorted(paths)


def _walk_all(config: DocvetConfig) -> list[Path]:
    """Discover all Python files under the configured source root.

    Tries ``git ls-files`` first for automatic ``.gitignore`` respect,
    then falls back to ``rglob`` for non-git directories.

    Args:
        config: Docvet configuration with ``project_root``, ``src_root``,
            and ``exclude`` fields.

    Returns:
        Sorted list of absolute paths to discovered ``.py`` files.
    """
    root = config.project_root / config.src_root
    if not root.exists():
        print(
            f"docvet: src-root '{config.src_root}' not found",
            file=sys.stderr,
        )
        return []

    lines = _run_git(
        ["ls-files", "--cached", "--others", "--exclude-standard", "--", "*.py"],
        cwd=root,
        warn=False,
    )

    if lines is not None:
        return _collect_python_files((root / line for line in lines), config)

    # Fallback: non-git directory — walk with rglob.
    return _collect_python_files(root.rglob("*.py"), config)


def _discover_explicit_files(files: Sequence[Path]) -> list[Path]:
    """Filter explicitly provided file paths.

    Validates that each path exists and has a ``.py`` suffix, printing
    a warning for missing files.

    Args:
        files: User-provided file paths to validate.

    Returns:
        Sorted list of absolute paths to existing ``.py`` files.
    """
    paths: list[Path] = []
    for path in files:
        if path.suffix != ".py":
            continue
        if not path.exists():
            print(
                f"docvet: file not found: {path}",
                file=sys.stderr,
            )
            continue
        paths.append(path.resolve())
    return sorted(paths)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def discover_files(
    config: DocvetConfig,
    mode: DiscoveryMode,
    *,
    files: Sequence[Path] = (),
) -> list[Path]:
    """Discover Python files according to the selected mode.

    Args:
        config: Docvet configuration providing ``project_root``,
            ``src_root``, and ``exclude`` settings.
        mode: The file discovery strategy to use.
        files: Explicit file paths for ``FILES`` mode. Ignored for
            other modes.

    Returns:
        Sorted list of absolute paths to discovered ``.py`` files.

    Raises:
        ValueError: If ``config.project_root`` is not absolute.
    """
    if not config.project_root.is_absolute():
        msg = f"project_root must be absolute, got: {config.project_root}"
        raise ValueError(msg)

    if mode is DiscoveryMode.ALL:
        return _walk_all(config)

    if mode is DiscoveryMode.FILES:
        return _discover_explicit_files(files)

    if mode is DiscoveryMode.DIFF:
        git_args = ["diff", "--name-only", "--diff-filter=ACMR"]
    else:
        # STAGED
        git_args = ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]

    lines = _run_git(git_args, cwd=config.project_root)
    if lines is None:
        return []

    discovered: list[Path] = []
    for rel in lines:
        if not rel.endswith(".py") or _is_excluded(rel, config.exclude):
            continue
        abs_path = config.project_root / rel
        if abs_path.is_symlink():
            continue
        discovered.append(abs_path.resolve())
    return sorted(discovered)
