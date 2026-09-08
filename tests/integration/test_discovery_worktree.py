"""Integration tests for discovery under an inherited ``GIT_DIR``.

Git exports ``GIT_DIR`` into every hook process, and inside a git
worktree it points at ``<checkout>/.git/worktrees/<name>`` rather than
at the checkout. A git child process that inherits it stops resolving
the repository — and the cwd-relative path prefix — from its working
directory, so ``git ls-files`` run from ``<root>/src`` reports paths
relative to the worktree root instead of relative to ``src``. Joining
those onto the source root yields a doubled root such as
``<root>/src/src/pkg/mod.py``, and the presence runner then dies with
``FileNotFoundError`` while reading it.

These tests pin that discovery resolves the same real files whether or
not ``GIT_DIR`` is set.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from docvet.config import DocvetConfig
from docvet.discovery import DiscoveryMode, discover_files, git_env

pytestmark = pytest.mark.integration


def _git(args: list[str], cwd: Path) -> str:
    """Run a git command in *cwd* and return its stripped stdout."""
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


@pytest.fixture
def worktree_repo(git_repo: Path, tmp_path: Path) -> tuple[Path, Path]:
    """Build a ``src``-layout repo plus a linked worktree of it.

    Returns:
        A tuple of ``(worktree_root, git_dir)`` where *git_dir* is the
        absolute path git reports for the worktree, i.e. the value git
        exports as ``GIT_DIR`` when it runs a hook inside that worktree.
    """
    (git_repo / "src" / "pkg").mkdir(parents=True)
    (git_repo / "src" / "pkg" / "__init__.py").write_text('"""Pkg."""\n')
    (git_repo / "src" / "pkg" / "mod.py").write_text('"""Mod."""\n')
    # A .py file OUTSIDE src_root: it must stay out of the results, and
    # under the bug it was the first path to be mis-joined onto src/.
    (git_repo / "tooling").mkdir()
    (git_repo / "tooling" / "helper.py").write_text('"""Helper."""\n')
    _git(["add", "-A"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    worktree = tmp_path / "wt"
    _git(["worktree", "add", str(worktree), "-b", "wt-branch"], cwd=git_repo)
    git_dir = Path(_git(["rev-parse", "--absolute-git-dir"], cwd=worktree))
    # Precondition: this is a linked worktree gitdir, not the checkout's.
    assert "worktrees" in git_dir.parts
    return worktree, git_dir


def test_walk_all_resolves_real_paths_with_git_dir_set(
    worktree_repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """ALL discovery ignores an inherited ``GIT_DIR`` when joining paths."""
    worktree, git_dir = worktree_repo
    config = DocvetConfig(project_root=worktree, src_root="src", exclude=[])

    monkeypatch.setenv("GIT_DIR", str(git_dir))
    discovered = discover_files(config, DiscoveryMode.ALL)

    assert discovered == sorted(
        [
            worktree / "src" / "pkg" / "__init__.py",
            worktree / "src" / "pkg" / "mod.py",
        ]
    )
    # The defect signature: a second source root spliced into the path.
    assert not any("src/src" in path.as_posix() for path in discovered)
    # Every discovered path must be readable — this is the exact call
    # the presence runner makes, and where the crash surfaced.
    for path in discovered:
        assert path.read_text(encoding="utf-8")


def test_walk_all_matches_unset_git_dir(
    worktree_repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """ALL discovery returns identical results with and without ``GIT_DIR``."""
    worktree, git_dir = worktree_repo
    config = DocvetConfig(project_root=worktree, src_root="src", exclude=[])

    monkeypatch.delenv("GIT_DIR", raising=False)
    without = discover_files(config, DiscoveryMode.ALL)
    monkeypatch.setenv("GIT_DIR", str(git_dir))
    with_git_dir = discover_files(config, DiscoveryMode.ALL)

    assert with_git_dir == without
    assert len(without) == 2


def test_diff_mode_matches_unset_git_dir(
    worktree_repo: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    """DIFF discovery is unaffected by an inherited ``GIT_DIR``."""
    worktree, git_dir = worktree_repo
    (worktree / "src" / "pkg" / "mod.py").write_text('"""Mod changed."""\n')
    config = DocvetConfig(project_root=worktree, src_root="src", exclude=[])

    monkeypatch.delenv("GIT_DIR", raising=False)
    without = discover_files(config, DiscoveryMode.DIFF)
    monkeypatch.setenv("GIT_DIR", str(git_dir))
    with_git_dir = discover_files(config, DiscoveryMode.DIFF)

    assert without == [worktree / "src" / "pkg" / "mod.py"]
    assert with_git_dir == without


def test_git_env_strips_location_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """``git_env`` drops location overrides and keeps everything else."""
    monkeypatch.setenv("GIT_DIR", "/somewhere/.git/worktrees/wt")
    monkeypatch.setenv("GIT_WORK_TREE", "/somewhere")
    monkeypatch.setenv("GIT_INDEX_FILE", "/somewhere/.git/index")
    monkeypatch.setenv("GIT_PREFIX", "src/")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Preserved")
    monkeypatch.setenv("DOCVET_SENTINEL", "kept")

    env = git_env()

    assert "GIT_DIR" not in env
    assert "GIT_WORK_TREE" not in env
    assert "GIT_INDEX_FILE" not in env
    assert "GIT_PREFIX" not in env
    assert env["GIT_AUTHOR_NAME"] == "Preserved"
    assert env["DOCVET_SENTINEL"] == "kept"
