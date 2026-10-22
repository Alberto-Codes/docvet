"""Shared Git prerequisite diagnostics for freshness consumers.

The probe preserves cwd-based discovery and the caller's Git trust settings.
Only its locale is fixed so failure categories agree across CLI and MCP.

Examples:
    Inspect freshness availability without running a check:

    ```python
    unavailable = freshness_unavailability(config)
    ```

See Also:
    [`docvet.discovery`][]: Git environment isolation.
    [`docvet.reporting`][]: Availability and run outcome records.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from docvet.config import DocvetConfig
from docvet.discovery import git_env
from docvet.reporting import UnavailableCheck


def _fatal_line(stderr: str) -> str:
    """Return Git's fatal diagnostic line, skipping trace and warning noise.

    Args:
        stderr: Raw standard error captured from a failed Git command.

    Returns:
        The first ``fatal:`` line, else the first non-empty line, else ``""``.
    """
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("fatal:"):
            return line
    return lines[0] if lines else ""


def _probe_failure(project_root: Path) -> tuple[str, str] | None:
    """Return a reason and remedy when Git cannot inspect the project.

    Args:
        project_root: Directory from which Git discovers the repository.

    Returns:
        A reason/remedy pair on failure, or *None* for an accessible repository.
    """
    if shutil.which("git") is None:
        return (
            "git is not installed or is not executable on PATH",
            "Install git and make it executable on PATH to run freshness",
        )
    env = git_env()
    env["LC_ALL"] = "C"
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
            cwd=project_root,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as exc:
        detail = _fatal_line(exc.stderr or "")
        if "fatal: detected dubious ownership" in detail:
            return (
                "git rejected the repository due to dubious ownership",
                (
                    "Verify the repository ownership and git trust configuration; "
                    "only trust a checkout after verifying its owner"
                ),
            )
        if detail.startswith("fatal: not a git repository"):
            return (
                "not a git repository; freshness requires git history",
                "Run docvet inside a git checkout, or drop freshness from fail-on",
            )
        detail = detail or f"exit status {exc.returncode}"
        return (
            f"git repository probe failed: {detail}",
            "Resolve the reported git error and retry freshness",
        )
    except OSError as exc:
        return (
            f"could not execute git repository probe: {exc}",
            (
                "Check the git executable, permissions, and project directory, "
                "then retry freshness"
            ),
        )
    return None


def freshness_unavailability(config: DocvetConfig) -> UnavailableCheck | None:
    """Describe an inaccessible Git prerequisite with the configured gate policy.

    Args:
        config: Configuration supplying the project root and availability policy.

    Returns:
        An unavailable freshness record, or *None* if the probe succeeds.

    Examples:
        Inspect the actionable remedy:

        ```python
        unavailable = freshness_unavailability(config)
        if unavailable is not None:
            print(unavailable.remedy)
        ```
    """
    failure = _probe_failure(config.project_root)
    if failure is None:
        return None
    reason, remedy = failure
    configured_gate = "freshness" in config.fail_on
    return UnavailableCheck(
        check="freshness",
        reason=reason,
        remedy=remedy,
        blocking=configured_gate and config.fail_on_unavailable,
        configured_gate=configured_gate,
    )
