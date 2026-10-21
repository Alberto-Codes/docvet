"""Regression tests for verbatim Git filename discovery."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from docvet.cli import app
from docvet.config import DocvetConfig
from docvet.discovery import DiscoveryMode, discover_files

pytestmark = pytest.mark.integration


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture(params=["true", "false"], ids=["quoted", "unquoted"])
def unusual_paths(git_repo: Path, request: pytest.FixtureRequest) -> list[Path]:
    _git(git_repo, "config", "core.quotePath", request.param)
    names = ["café.py", " leading.py", "space name.py"]
    if os.name == "posix":
        names.append("trailing /mod.py")
        names.extend(
            ['double"quote.py', "tab\tname.py", "line\nname.py", "cr\r\nname.py"]
        )
    paths = [git_repo / name for name in names]
    for path in paths:
        path.parent.mkdir(exist_ok=True)
        path.write_text('"""Original module."""\n', encoding="utf-8")
    _git(git_repo, "add", ".")
    _git(git_repo, "commit", "-m", "baseline")
    for path in paths:
        path.write_text("def undocumented():\n    pass\n", encoding="utf-8")
    return sorted(paths)


@pytest.mark.parametrize(
    "mode", [DiscoveryMode.ALL, DiscoveryMode.DIFF, DiscoveryMode.STAGED]
)
def test_git_discovery_preserves_filenames(
    git_repo: Path, unusual_paths: list[Path], mode: DiscoveryMode
) -> None:
    if mode is DiscoveryMode.STAGED:
        _git(git_repo, "add", ".")
    config = DocvetConfig(project_root=git_repo, exclude=[])
    assert discover_files(config, mode) == unusual_paths


@pytest.mark.parametrize(
    "flags", [["--all"], [], ["--staged"]], ids=["all", "diff", "staged"]
)
def test_discovered_undocumented_files_produce_findings(
    git_repo: Path,
    unusual_paths: list[Path],
    flags: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(git_repo, "add", ".")
    if not flags:
        # Restore an unstaged change after staging for the other modes.
        for path in unusual_paths:
            path.write_text("def undocumented():\n    return None\n", encoding="utf-8")
    (git_repo / "pyproject.toml").write_text(
        '[tool.docvet]\nfail-on = ["presence"]\n', encoding="utf-8"
    )
    monkeypatch.chdir(git_repo)
    result = CliRunner().invoke(app, ["--format", "json", "presence", *flags])
    assert result.exit_code == 1, result.output
    findings = json.loads(result.stdout)["findings"]
    assert {Path(finding["file"]) for finding in findings} == set(unusual_paths)
    assert all(finding["rule"] == "missing-docstring" for finding in findings)
