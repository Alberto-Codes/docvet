"""Observable git prerequisite reporting for the freshness check."""

import json
import subprocess

import pytest
from typer.testing import CliRunner

from docvet.cli import app

pytestmark = pytest.mark.unit

_COMMANDS = [["check"], ["freshness"], ["freshness", "--mode", "drift"]]
_GATES = [(True, False), (True, True), (False, False)]


def _write_project(tmp_path, gated):
    (tmp_path / "a.py").write_text('"""A module."""\n')
    gate = '["freshness"]' if gated else "[]"
    (tmp_path / "pyproject.toml").write_text(f"[tool.docvet]\nfail-on = {gate}\n")


def _assert_freshness_unavailable(result, command, gated, optout, reason):
    assert result.exit_code == int(gated and not optout), result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == (
        "unavailable" if gated and not optout else "passed"
    )
    unavailable = data["run"]["unavailable_checks"]
    freshness = [item for item in unavailable if item["check"] == "freshness"]
    assert len(freshness) == 1
    assert reason in freshness[0]["reason"]
    assert freshness[0]["configured_gate"] is gated
    assert freshness[0]["blocking"] is (gated and not optout)
    assert "git" in freshness[0]["remedy"]
    assert data["summary"]["files_checked"] == 1
    assert data["run"]["input_errors"] == []
    if command[0] == "freshness":
        assert data["summary"]["files_analyzed"] == 0
    if gated:
        assert "configured to gate" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("command", _COMMANDS)
@pytest.mark.parametrize("gated,optout", _GATES)
def test_missing_git_produces_unavailable_json(
    tmp_path, monkeypatch, command, gated, optout
):
    """Missing git is an execution prerequisite, governed by availability gates."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    _write_project(tmp_path, gated)
    options = ["--no-fail-on-unavailable"] if optout else []
    result = CliRunner().invoke(app, ["--format", "json", *options, *command, "--all"])
    _assert_freshness_unavailable(result, command, gated, optout, "not installed")


@pytest.mark.parametrize("command", _COMMANDS)
@pytest.mark.parametrize("gated,optout", _GATES)
def test_non_repository_produces_unavailable_json(
    tmp_path, monkeypatch, command, gated, optout
):
    """With git installed, a tree outside any repository is the same prerequisite."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "elsewhere"))
    _write_project(tmp_path, gated)
    options = ["--no-fail-on-unavailable"] if optout else []
    result = CliRunner().invoke(app, ["--format", "json", *options, *command, "--all"])
    _assert_freshness_unavailable(
        result, command, gated, optout, "not a git repository"
    )


@pytest.mark.parametrize("command", _COMMANDS)
def test_git_repository_with_no_changes_passes(tmp_path, monkeypatch, command):
    """A real repository with a clean history is a legitimate zero-diff result."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _write_project(tmp_path, gated=True)
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
    subprocess.run([*git, "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run([*git, "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [*git, "-c", "commit.gpgsign=false", "commit", "-qm", "init"],
        cwd=tmp_path,
        check=True,
    )
    result = CliRunner().invoke(app, ["--format", "json", *command, "--all"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == "passed"
    assert data["run"]["unavailable_checks"] == []
    assert data["summary"]["files_analyzed"] == 1
