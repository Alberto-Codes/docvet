"""Explicit target failures retain structured discovery evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from docvet.config import DocvetConfig
from docvet.discovery import DiscoveryMode, discover_files

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("target", ["missing.py", "folder.py", "notes.txt"])
def test_invalid_explicit_target_records_input_error(tmp_path: Path, target: str):
    (tmp_path / "folder.py").mkdir()
    (tmp_path / "notes.txt").write_text("not Python")
    errors = []
    result = discover_files(
        DocvetConfig(project_root=tmp_path),
        DiscoveryMode.FILES,
        files=[tmp_path / target],
        errors=errors,
    )
    assert result == []
    assert len(errors) == 1
    assert errors[0].file == str(tmp_path / target)
    assert errors[0].kind == "input"
    assert errors[0].message


def test_explicit_excluded_file_remains_selected_with_invalid_peer(tmp_path: Path):
    good = tmp_path / "good.py"
    good.write_text('"""Good."""\n')
    errors = []
    result = discover_files(
        DocvetConfig(project_root=tmp_path, exclude=["good.py"]),
        DiscoveryMode.FILES,
        files=[good, tmp_path / "missing.py"],
        errors=errors,
    )
    assert result == [good]
    assert len(errors) == 1


def test_missing_source_root_is_not_legitimate_empty_selection(tmp_path: Path):
    errors = []
    assert (
        discover_files(
            DocvetConfig(project_root=tmp_path, src_root="absent"),
            DiscoveryMode.ALL,
            errors=errors,
        )
        == []
    )
    assert len(errors) == 1
    assert errors[0].kind == "input"


def test_existing_empty_source_root_has_no_input_errors(tmp_path: Path):
    errors = []
    assert (
        discover_files(
            DocvetConfig(project_root=tmp_path, src_root="."),
            DiscoveryMode.ALL,
            errors=errors,
        )
        == []
    )
    assert errors == []


@pytest.mark.parametrize("mode", [DiscoveryMode.FILES, DiscoveryMode.ALL])
def test_symlink_loop_is_controlled_input_failure(tmp_path: Path, mode):
    loop = tmp_path / "loop.py"
    loop.symlink_to(loop)
    errors = []
    assert (
        discover_files(
            DocvetConfig(project_root=tmp_path, src_root="loop.py"),
            mode,
            files=[loop],
            errors=errors,
        )
        == []
    )
    assert len(errors) == 1
    assert errors[0].kind == "input"


def test_missing_git_all_walks_but_diff_reports_failure(tmp_path: Path, mocker):
    source = tmp_path / "good.py"
    source.write_text('"""Module."""\n')
    mocker.patch(
        "docvet.discovery.subprocess.run", side_effect=FileNotFoundError("git")
    )
    config = DocvetConfig(project_root=tmp_path, src_root=".")
    errors = []
    assert discover_files(config, DiscoveryMode.ALL, errors=errors) == [source]
    assert errors == []
    assert discover_files(config, DiscoveryMode.DIFF, errors=errors) == []
    assert len(errors) == 1
    assert errors[0].kind == "input"
