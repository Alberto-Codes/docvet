"""Integration tests for file discovery using real git repositories."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from docvet.config import DocvetConfig
from docvet.discovery import DiscoveryMode, discover_files

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _make_config(
    git_repo: Path,
    src_root: str = ".",
    exclude: list[str] | None = None,
) -> DocvetConfig:
    return DocvetConfig(
        project_root=git_repo,
        src_root=src_root,
        exclude=exclude if exclude is not None else ["tests", "scripts"],
    )


# ---------------------------------------------------------------------------
# DIFF mode
# ---------------------------------------------------------------------------


def test_diff_mode_when_file_modified_returns_modified_file(git_repo):
    f = git_repo / "mod.py"
    f.write_text("# v1")
    _git(["add", "mod.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.write_text("# v2")

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_diff_mode_when_no_changes_returns_empty(git_repo):
    f = git_repo / "mod.py"
    f.write_text("# v1")
    _git(["add", "mod.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert result == []


def test_diff_mode_filters_non_py_from_diff(git_repo):
    txt = git_repo / "readme.txt"
    txt.write_text("v1")
    _git(["add", "readme.txt"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    txt.write_text("v2")

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert result == []


def test_diff_mode_applies_exclude_patterns(git_repo):
    tests_dir = git_repo / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_foo.py"
    f.write_text("# v1")
    _git(["add", "tests/test_foo.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.write_text("# v2")

    config = _make_config(git_repo, exclude=["tests"])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert result == []


def test_diff_mode_when_file_renamed_returns_new_name(git_repo):
    old = git_repo / "old.py"
    old.write_text("# content")
    _git(["add", "old.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    new = git_repo / "new.py"
    old.rename(new)
    _git(["add", "old.py", "new.py"], cwd=git_repo)

    # Now new.py is staged as a rename. Modify it in working tree
    # to make it appear in diff (unstaged changes).
    new.write_text("# modified content")

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.DIFF)
    names = [p.name for p in result]
    assert "new.py" in names
    assert "old.py" not in names


def test_diff_mode_when_file_deleted_returns_empty(git_repo):
    f = git_repo / "mod.py"
    f.write_text("# v1")
    _git(["add", "mod.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.unlink()

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert result == []


# ---------------------------------------------------------------------------
# STAGED mode
# ---------------------------------------------------------------------------


def test_staged_mode_when_file_staged_returns_staged_file(git_repo):
    f = git_repo / "mod.py"
    f.write_text("# v1")
    _git(["add", "mod.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.write_text("# v2")
    _git(["add", "mod.py"], cwd=git_repo)

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.STAGED)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_staged_mode_when_nothing_staged_returns_empty(git_repo):
    f = git_repo / "mod.py"
    f.write_text("# v1")
    _git(["add", "mod.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.STAGED)
    assert result == []


def test_staged_mode_applies_exclude_patterns(git_repo):
    tests_dir = git_repo / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_foo.py"
    f.write_text("# v1")
    _git(["add", "tests/test_foo.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.write_text("# v2")
    _git(["add", "tests/test_foo.py"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests"])
    result = discover_files(config, DiscoveryMode.STAGED)
    assert result == []


# ---------------------------------------------------------------------------
# ALL mode with git
# ---------------------------------------------------------------------------


def test_all_mode_with_git_returns_tracked_py_files(git_repo):
    f = git_repo / "mod.py"
    f.write_text("# module")
    _git(["add", "mod.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_all_mode_with_git_excludes_gitignored_files(git_repo):
    gitignore = git_repo / ".gitignore"
    gitignore.write_text("ignored.py\n")
    _git(["add", ".gitignore"], cwd=git_repo)
    _git(["commit", "-m", "gitignore"], cwd=git_repo)

    (git_repo / "ignored.py").write_text("# ignored")
    (git_repo / "tracked.py").write_text("# tracked")
    _git(["add", "tracked.py"], cwd=git_repo)
    _git(["commit", "-m", "add tracked"], cwd=git_repo)

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "tracked.py" in names
    assert "ignored.py" not in names


def test_all_mode_applies_exclude_on_top_of_git(git_repo):
    tests_dir = git_repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_foo.py").write_text("# test")
    (git_repo / "mod.py").write_text("# module")
    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests"])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "mod.py" in names
    assert "test_foo.py" not in names


def test_all_mode_with_src_root_scoping(git_repo):
    src_dir = git_repo / "src" / "pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "mod.py").write_text("# src module")

    other_dir = git_repo / "other"
    other_dir.mkdir()
    (other_dir / "mod.py").write_text("# other module")

    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, src_root="src", exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "mod.py" in names
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Empty repo edge cases
# ---------------------------------------------------------------------------


def test_diff_mode_when_empty_repo_returns_empty(git_repo):
    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert result == []


def test_staged_mode_when_empty_repo_with_staged_file_returns_file(git_repo):
    f = git_repo / "new.py"
    f.write_text("# new")
    _git(["add", "new.py"], cwd=git_repo)

    config = _make_config(git_repo, exclude=[])
    result = discover_files(config, DiscoveryMode.STAGED)
    assert len(result) == 1
    assert result[0].name == "new.py"


# ---------------------------------------------------------------------------
# extend-exclude integration (merged into config.exclude by load_config)
# ---------------------------------------------------------------------------


def test_diff_mode_excludes_extend_exclude_vendor_dir(git_repo):
    """DIFF mode excludes vendor/ when extend-exclude adds 'vendor' to exclude."""
    vendor_dir = git_repo / "vendor"
    vendor_dir.mkdir()
    f = vendor_dir / "lib.py"
    f.write_text("# v1")
    _git(["add", "vendor/lib.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.write_text("# v2")

    # Simulates extend-exclude = ["vendor"] merged into exclude
    config = _make_config(git_repo, exclude=["tests", "scripts", "vendor"])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert result == []


def test_diff_mode_discovers_non_excluded_alongside_extend_exclude(git_repo):
    """Non-excluded file discovered even when extend-exclude filters vendor/."""
    vendor_dir = git_repo / "vendor"
    vendor_dir.mkdir()
    (vendor_dir / "lib.py").write_text("# v1")
    (git_repo / "app.py").write_text("# v1")
    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    (vendor_dir / "lib.py").write_text("# v2")
    (git_repo / "app.py").write_text("# v2")

    config = _make_config(git_repo, exclude=["tests", "scripts", "vendor"])
    result = discover_files(config, DiscoveryMode.DIFF)
    assert len(result) == 1
    assert result[0].name == "app.py"


def test_all_mode_excludes_extend_exclude_vendor_dir(git_repo):
    """ALL mode excludes vendor/ when extend-exclude adds 'vendor' to exclude."""
    vendor_dir = git_repo / "vendor"
    vendor_dir.mkdir()
    (vendor_dir / "lib.py").write_text("# vendored")
    (git_repo / "app.py").write_text("# app")
    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests", "scripts", "vendor"])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "app.py" in names
    assert "lib.py" not in names


def test_all_mode_discovers_non_excluded_with_extend_exclude(git_repo):
    """Non-excluded files still discovered in ALL mode with extend-exclude."""
    vendor_dir = git_repo / "vendor"
    vendor_dir.mkdir()
    (vendor_dir / "lib.py").write_text("# vendored")
    (git_repo / "core.py").write_text("# core")
    (git_repo / "utils.py").write_text("# utils")
    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests", "scripts", "vendor"])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "core.py" in names
    assert "utils.py" in names
    assert len(result) == 2


def test_staged_mode_excludes_extend_exclude_vendor_dir(git_repo):
    """STAGED mode excludes vendor/ when extend-exclude adds 'vendor' to exclude."""
    vendor_dir = git_repo / "vendor"
    vendor_dir.mkdir()
    f = vendor_dir / "lib.py"
    f.write_text("# v1")
    _git(["add", "vendor/lib.py"], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)
    f.write_text("# v2")
    _git(["add", "vendor/lib.py"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests", "scripts", "vendor"])
    result = discover_files(config, DiscoveryMode.STAGED)
    assert result == []


def test_all_mode_excludes_component_level_pattern(git_repo):
    """Component-level pattern *.generated excludes matching directory names."""
    gen_dir = git_repo / "api.generated"
    gen_dir.mkdir()
    (gen_dir / "client.py").write_text("# generated")
    (git_repo / "app.py").write_text("# app")
    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests", "scripts", "*.generated"])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "app.py" in names
    assert "client.py" not in names


def test_all_mode_excludes_path_level_pattern(git_repo):
    """Path-level pattern vendor/legacy/*.py excludes only matching full paths."""
    legacy_dir = git_repo / "vendor" / "legacy"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "old.py").write_text("# legacy")

    modern_dir = git_repo / "vendor" / "modern"
    modern_dir.mkdir(parents=True)
    (modern_dir / "new.py").write_text("# modern")

    (git_repo / "app.py").write_text("# app")
    _git(["add", "."], cwd=git_repo)
    _git(["commit", "-m", "init"], cwd=git_repo)

    config = _make_config(git_repo, exclude=["tests", "scripts", "vendor/legacy/*.py"])
    result = discover_files(config, DiscoveryMode.ALL)
    names = [p.name for p in result]
    assert "app.py" in names
    assert "new.py" in names
    assert "old.py" not in names
