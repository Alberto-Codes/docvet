"""Integration test for git environment isolation in the test suite.

Tests build throwaway repositories and shell out to ``git`` with a
``cwd``. Git overrides that ``cwd`` when ``GIT_DIR`` or ``GIT_INDEX_FILE``
is set, and it exports both into every hook process — so a suite launched
from the ``pre-push`` hook would drive those commands against the
repository being pushed rather than the temp repository.

This test reproduces that environment against a scratch repository and
asserts the suite both passes and leaves the scratch repository alone.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]

REPO_ROOT = Path(__file__).resolve().parents[2]

# A suite file that builds a temp repo and commits inside it, which is
# exactly the pattern that reaches for the ambient git environment.
INNER_SUITE = "tests/integration/test_fix_cli.py"


def _git(*args: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Run a git command with an explicit environment."""
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


@pytest.fixture
def clean_env() -> dict[str, str]:
    """An environment carrying no inherited git variables."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


@pytest.fixture
def scratch_repo(tmp_path, clean_env) -> Path:
    """A committed repository standing in for the one being pushed."""
    repo = tmp_path / "scratch"
    repo.mkdir()
    _git("init", cwd=repo, env=clean_env)
    _git("config", "user.email", "test@test.com", cwd=repo, env=clean_env)
    _git("config", "user.name", "Test", cwd=repo, env=clean_env)
    (repo / "tracked.py").write_text('"""Track a file."""\n')
    _git("add", "tracked.py", cwd=repo, env=clean_env)
    _git("commit", "-m", "init", cwd=repo, env=clean_env)
    return repo


def test_suite_under_hook_env_passes_and_spares_the_outer_repo(scratch_repo, clean_env):
    """The suite survives the environment a git hook hands it.

    Without ``GIT_*`` isolation the inner suite's git calls retarget the
    scratch repository: its tests fail and its index is rewritten.
    """
    hook_env = {
        **clean_env,
        "GIT_DIR": str(scratch_repo / ".git"),
        "GIT_INDEX_FILE": str(scratch_repo / ".git" / "index"),
        "GIT_WORK_TREE": str(scratch_repo),
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            INNER_SUITE,
            "-q",
            "-p",
            "no:randomly",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        env=hook_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )

    assert result.returncode == 0, (
        f"suite failed under a git hook environment:\n{result.stdout}\n{result.stderr}"
    )

    status = _git("status", "--porcelain", cwd=scratch_repo, env=clean_env)
    assert status.stdout == "", (
        f"the suite rewrote the outer repository's index:\n{status.stdout}"
    )

    log = _git("log", "--oneline", cwd=scratch_repo, env=clean_env)
    assert len(log.stdout.strip().splitlines()) == 1, (
        f"the suite committed to the outer repository:\n{log.stdout}"
    )
