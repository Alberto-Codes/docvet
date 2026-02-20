"""File discovery module for locating Python files to analyze."""

from __future__ import annotations

import enum
import fnmatch
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from docvet.config import DocvetConfig

__all__: list[str] = []

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DiscoveryMode(enum.Enum):
    """Internal discovery mode for file selection."""

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


def _is_excluded(rel_path: str, exclude: list[str]) -> bool:
    """Check whether a relative path matches any exclude pattern.

    Follows ``.gitignore`` semantics: patterns without ``/`` match against
    every path component; patterns with ``/`` match the full relative path.

    Args:
        rel_path: File path relative to the project root (forward slashes).
        exclude: List of exclude patterns from configuration.

    Returns:
        *True* if the path matches any exclude pattern.
    """
    normalized = rel_path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    for pattern in exclude:
        if "/" in pattern:
            if fnmatch.fnmatch(normalized, pattern):
                return True
        else:
            for component in parts:
                if fnmatch.fnmatch(component, pattern):
                    return True
    return False


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
        paths: list[Path] = []
        for line in lines:
            raw_path = root / line
            if raw_path.is_symlink():
                continue
            abs_path = raw_path.resolve()
            if abs_path.suffix != ".py":
                continue
            try:
                rel = PurePosixPath(
                    abs_path.relative_to(config.project_root)
                ).as_posix()
            except ValueError:
                continue
            if _is_excluded(rel, config.exclude):
                continue
            paths.append(abs_path)
        return sorted(paths)

    # Fallback: non-git directory — walk with rglob.
    paths = []
    for path in root.rglob("*.py"):
        if path.is_symlink():
            continue
        try:
            rel = PurePosixPath(path.relative_to(config.project_root)).as_posix()
        except ValueError:
            continue
        if _is_excluded(rel, config.exclude):
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
