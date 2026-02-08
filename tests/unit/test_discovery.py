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
    assert result == []
    assert "docvet: git diff failed" in capsys.readouterr().err


def test_run_git_when_failure_and_warn_false_returns_empty_silently(mocker, capsys):
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
    assert result == []
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
