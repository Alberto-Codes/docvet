"""Unit tests for the docvet file discovery module."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from docvet.config import DocvetConfig
from docvet.discovery import DiscoveryMode, _is_excluded, _run_git, discover_files

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_config(tmp_path):
    def _make(
        project_root: Path | None = None,
        src_root: str = ".",
        exclude: list[str] | None = None,
    ) -> DocvetConfig:
        return DocvetConfig(
            project_root=project_root or tmp_path,
            src_root=src_root,
            exclude=exclude if exclude is not None else ["tests", "scripts"],
        )

    return _make


# ---------------------------------------------------------------------------
# _is_excluded tests
# ---------------------------------------------------------------------------


def test_is_excluded_when_component_matches_returns_true():
    assert _is_excluded("tests/unit/test_foo.py", ["tests"]) is True


def test_is_excluded_when_component_partial_match_returns_false():
    assert _is_excluded("src/docvet/test_utils.py", ["tests"]) is False


def test_is_excluded_when_filename_glob_matches_returns_true():
    assert _is_excluded("src/__pycache__/foo.pyc", ["*.pyc"]) is True


def test_is_excluded_when_path_pattern_matches_returns_true():
    assert _is_excluded("scripts/gen_docs.py", ["scripts/gen_*.py"]) is True


def test_is_excluded_when_path_pattern_wrong_root_returns_false():
    assert _is_excluded("other/scripts/gen_docs.py", ["scripts/gen_*.py"]) is False


def test_is_excluded_when_empty_exclude_returns_false():
    assert _is_excluded("src/docvet/cli.py", []) is False


# ---------------------------------------------------------------------------
# _run_git tests
# ---------------------------------------------------------------------------


def test_run_git_when_success_returns_lines(mocker):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "diff"],
            returncode=0,
            stdout="src/foo.py\nsrc/bar.py\n",
            stderr="",
        ),
    )
    result = _run_git(["diff", "--name-only"], cwd=Path("/tmp"))
    assert result == ["src/foo.py", "src/bar.py"]


def test_run_git_when_failure_returns_empty_and_warns(mocker, capsys):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "diff"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    result = _run_git(["diff", "--name-only"], cwd=Path("/tmp"))
    assert result is None
    assert "docvet: git diff failed" in capsys.readouterr().err


def test_run_git_when_failure_and_warn_false_returns_none_silently(mocker, capsys):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    result = _run_git(["ls-files"], cwd=Path("/tmp"), warn=False)
    assert result is None
    assert capsys.readouterr().err == ""


def test_run_git_when_empty_stdout_returns_empty(mocker):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "diff"],
            returncode=0,
            stdout="",
            stderr="",
        ),
    )
    result = _run_git(["diff"], cwd=Path("/tmp"))
    assert result == []


# ---------------------------------------------------------------------------
# discover_files — ALL mode
# ---------------------------------------------------------------------------


def test_discover_files_all_mode_when_src_root_missing_warns_and_returns_empty(
    make_config, capsys
):
    config = make_config(src_root="nonexistent")
    result = discover_files(config, DiscoveryMode.ALL)
    assert result == []
    assert "src-root" in capsys.readouterr().err


def test_discover_files_all_mode_git_success_empty_does_not_fallback(
    tmp_path, make_config, mocker
):
    (tmp_path / "stray.py").write_text("# should not be found")

    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=0,
            stdout="",
            stderr="",
        ),
    )
    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert result == []


def test_discover_files_all_mode_git_success_returns_py_files(
    tmp_path, make_config, mocker
):
    (tmp_path / "mod.py").write_text("# module")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "sub.py").write_text("# sub")

    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=0,
            stdout="mod.py\npkg/sub.py\n",
            stderr="",
        ),
    )
    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 2
    names = [p.name for p in result]
    assert "mod.py" in names
    assert "sub.py" in names


def test_discover_files_all_mode_git_success_applies_excludes(
    tmp_path, make_config, mocker
):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "foo.py").write_text("# test")
    (tmp_path / "mod.py").write_text("# module")

    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=0,
            stdout="mod.py\ntests/foo.py\n",
            stderr="",
        ),
    )
    config = make_config(exclude=["tests"])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_discover_files_all_mode_git_success_skips_symlinks(
    tmp_path, make_config, mocker
):
    real = tmp_path / "real.py"
    real.write_text("# real")
    link = tmp_path / "link.py"
    link.symlink_to(real)

    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=0,
            stdout="real.py\nlink.py\n",
            stderr="",
        ),
    )
    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 1
    assert result[0].name == "real.py"


def test_discover_files_all_mode_non_git_fallback_returns_py_files(
    tmp_path, make_config, mocker
):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    (tmp_path / "mod.py").write_text("# module")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "sub.py").write_text("# sub")

    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 2
    names = [p.name for p in result]
    assert "mod.py" in names
    assert "sub.py" in names


def test_discover_files_all_mode_non_git_fallback_skips_symlinks(
    tmp_path, make_config, mocker
):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    real = tmp_path / "real.py"
    real.write_text("# real")
    link = tmp_path / "link.py"
    link.symlink_to(real)

    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 1
    assert result[0].name == "real.py"


def test_discover_files_all_mode_non_git_fallback_applies_excludes(
    tmp_path, make_config, mocker
):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "foo.py").write_text("# test")
    (tmp_path / "mod.py").write_text("# module")

    config = make_config(exclude=["tests"])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 1
    assert result[0].name == "mod.py"


def test_discover_files_all_mode_non_git_fallback_filters_non_py(
    tmp_path, make_config, mocker
):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    (tmp_path / "readme.txt").write_text("hello")
    (tmp_path / "mod.py").write_text("# module")

    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 1
    assert result[0].name == "mod.py"


# ---------------------------------------------------------------------------
# discover_files — FILES mode
# ---------------------------------------------------------------------------


def test_discover_files_files_mode_returns_existing_py_files(tmp_path, make_config):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("# a")
    f2.write_text("# b")

    config = make_config()
    result = discover_files(config, DiscoveryMode.FILES, files=[f1, f2])
    assert len(result) == 2
    names = [p.name for p in result]
    assert "a.py" in names
    assert "b.py" in names


def test_discover_files_files_mode_when_file_missing_warns_and_skips(
    tmp_path, make_config, capsys
):
    missing = tmp_path / "gone.py"
    config = make_config()
    result = discover_files(config, DiscoveryMode.FILES, files=[missing])
    assert result == []
    assert "file not found" in capsys.readouterr().err


def test_discover_files_files_mode_bypasses_exclude_patterns(tmp_path, make_config):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    f = tests_dir / "test_foo.py"
    f.write_text("# test")

    config = make_config(exclude=["tests"])
    result = discover_files(config, DiscoveryMode.FILES, files=[f])
    assert len(result) == 1
    assert result[0].name == "test_foo.py"


def test_discover_files_files_mode_filters_non_py(tmp_path, make_config):
    f = tmp_path / "readme.txt"
    f.write_text("hello")

    config = make_config()
    result = discover_files(config, DiscoveryMode.FILES, files=[f])
    assert result == []


def test_discover_files_files_mode_when_empty_returns_empty(make_config):
    config = make_config()
    result = discover_files(config, DiscoveryMode.FILES, files=())
    assert result == []


# ---------------------------------------------------------------------------
# General tests
# ---------------------------------------------------------------------------


def test_discover_files_returns_sorted_absolute_paths(tmp_path, make_config, mocker):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    (tmp_path / "z.py").write_text("# z")
    (tmp_path / "a.py").write_text("# a")

    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert len(result) == 2
    assert result == sorted(result)
    assert all(p.is_absolute() for p in result)


def test_discover_files_returns_empty_list_when_no_matches(
    tmp_path, make_config, mocker
):
    mocker.patch(
        "docvet.discovery.subprocess.run",
        return_value=subprocess.CompletedProcess(
            args=["git", "ls-files"],
            returncode=128,
            stdout="",
            stderr="fatal: not a git repo",
        ),
    )
    config = make_config(exclude=[])
    result = discover_files(config, DiscoveryMode.ALL)
    assert result == []


def test_discover_files_when_project_root_relative_raises_value_error():
    config = DocvetConfig(project_root=Path("relative"))
    with pytest.raises(ValueError, match="project_root must be absolute"):
        discover_files(config, DiscoveryMode.ALL)


# ---------------------------------------------------------------------------
# _is_excluded — trailing-slash patterns (AC #1)
# ---------------------------------------------------------------------------


def test_is_excluded_trailing_slash_matches_direct_child():
    """build/ matches build/output.py (direct child)."""
    assert _is_excluded("build/output.py", ["build/"]) is True


def test_is_excluded_trailing_slash_matches_nested_child():
    """build/ matches build/sub/deep.py (nested child)."""
    assert _is_excluded("build/sub/deep.py", ["build/"]) is True


def test_is_excluded_trailing_slash_matches_at_any_depth():
    """build/ matches src/build/mod.py (any depth)."""
    assert _is_excluded("src/build/mod.py", ["build/"]) is True


def test_is_excluded_trailing_slash_rejects_partial_dir_name():
    """build/ does NOT match rebuild/main.py (partial dir name)."""
    assert _is_excluded("rebuild/main.py", ["build/"]) is False


def test_is_excluded_trailing_slash_rejects_filename():
    """build/ does NOT match buildfile.py (filename, not directory)."""
    assert _is_excluded("buildfile.py", ["build/"]) is False


def test_is_excluded_path_trailing_slash_matches_rooted_prefix():
    """vendor/legacy/ matches vendor/legacy/old.py (rooted path prefix)."""
    assert _is_excluded("vendor/legacy/old.py", ["vendor/legacy/"]) is True


def test_is_excluded_path_trailing_slash_rejects_non_root():
    """vendor/legacy/ does NOT match src/vendor/legacy/old.py (not at root)."""
    assert _is_excluded("src/vendor/legacy/old.py", ["vendor/legacy/"]) is False


# ---------------------------------------------------------------------------
# _is_excluded — double-star patterns (AC #2)
# ---------------------------------------------------------------------------


def test_is_excluded_double_star_leading_matches_root_level():
    """**/test_*.py matches test_foo.py (root level, zero-segment)."""
    assert _is_excluded("test_foo.py", ["**/test_*.py"]) is True


def test_is_excluded_double_star_leading_matches_one_level():
    """**/test_*.py matches src/test_foo.py (one level)."""
    assert _is_excluded("src/test_foo.py", ["**/test_*.py"]) is True


def test_is_excluded_double_star_leading_matches_deep_nesting():
    """**/test_*.py matches a/b/c/test_bar.py (deep nesting)."""
    assert _is_excluded("a/b/c/test_bar.py", ["**/test_*.py"]) is True


def test_is_excluded_double_star_leading_rejects_non_match():
    """**/test_*.py does NOT match src/foo.py."""
    assert _is_excluded("src/foo.py", ["**/test_*.py"]) is False


def test_is_excluded_double_star_middle_matches_zero_segment():
    """src/**/test_*.py matches src/test_foo.py (zero-segment middle)."""
    assert _is_excluded("src/test_foo.py", ["src/**/test_*.py"]) is True


def test_is_excluded_double_star_middle_matches_one_segment():
    """src/**/test_*.py matches src/a/test_foo.py (one-segment middle)."""
    assert _is_excluded("src/a/test_foo.py", ["src/**/test_*.py"]) is True


def test_is_excluded_double_star_middle_rejects_wrong_prefix():
    """src/**/test_*.py does NOT match other/test_foo.py (wrong prefix)."""
    assert _is_excluded("other/test_foo.py", ["src/**/test_*.py"]) is False


def test_is_excluded_double_star_trailing_matches_direct():
    """build/** matches build/out.py (trailing ** direct)."""
    assert _is_excluded("build/out.py", ["build/**"]) is True


def test_is_excluded_double_star_trailing_matches_nested():
    """build/** matches build/sub/out.py (trailing ** nested)."""
    assert _is_excluded("build/sub/out.py", ["build/**"]) is True


# ---------------------------------------------------------------------------
# _is_excluded — backward compatibility regression (AC #3)
# ---------------------------------------------------------------------------


def test_is_excluded_backward_compat_component_match():
    """Existing component-level pattern still works (regression)."""
    assert _is_excluded("tests/unit/test_foo.py", ["tests"]) is True
    assert _is_excluded("src/docvet/test_utils.py", ["tests"]) is False


def test_is_excluded_backward_compat_glob_match():
    """Existing filename glob still works (regression)."""
    assert _is_excluded("src/__pycache__/foo.pyc", ["*.pyc"]) is True
    assert _is_excluded("src/foo.py", ["*.pyc"]) is False


def test_is_excluded_backward_compat_path_pattern():
    """Existing path-level pattern still works (regression)."""
    assert _is_excluded("scripts/gen_docs.py", ["scripts/gen_*.py"]) is True
    assert _is_excluded("other/scripts/gen_docs.py", ["scripts/gen_*.py"]) is False


# ---------------------------------------------------------------------------
# _is_excluded — mixed patterns (AC #4)
# ---------------------------------------------------------------------------


def test_is_excluded_mixed_patterns_all_types():
    """Multiple pattern types in a single exclude list all work."""
    exclude = ["tests", "build/", "**/conftest.py"]
    # Component match
    assert _is_excluded("tests/unit/test_foo.py", exclude) is True
    # Trailing-slash match
    assert _is_excluded("build/output.py", exclude) is True
    # Double-star match
    assert _is_excluded("src/conftest.py", exclude) is True
    assert _is_excluded("conftest.py", exclude) is True
    # None match
    assert _is_excluded("src/docvet/cli.py", exclude) is False


def test_is_excluded_mixed_simple_and_advanced_from_extend_exclude():
    """Patterns from both exclude and extend-exclude evaluate correctly."""
    # Simulates merged list from config (exclude + extend-exclude)
    merged = ["*.pyc", "build/", "**/test_*.py", "scripts/gen_*.py"]
    assert _is_excluded("src/__pycache__/foo.pyc", merged) is True
    assert _is_excluded("build/out.py", merged) is True
    assert _is_excluded("a/b/test_foo.py", merged) is True
    assert _is_excluded("scripts/gen_docs.py", merged) is True
    assert _is_excluded("src/docvet/cli.py", merged) is False
