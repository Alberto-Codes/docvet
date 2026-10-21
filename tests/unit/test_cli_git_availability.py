"""Observable missing-git CLI prerequisite reporting."""

import json

import pytest
from typer.testing import CliRunner

from docvet.cli import app

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "command", [["check"], ["freshness"], ["freshness", "--mode", "drift"]]
)
@pytest.mark.parametrize("gated,optout", [(True, False), (True, True), (False, False)])
def test_missing_git_produces_unavailable_json(
    tmp_path, monkeypatch, command, gated, optout
):
    """Missing git is an execution prerequisite, governed by availability gates."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))
    (tmp_path / "a.py").write_text('"""A module."""\n')
    gate = '["freshness"]' if gated else "[]"
    (tmp_path / "pyproject.toml").write_text(f"[tool.docvet]\nfail-on = {gate}\n")
    options = ["--no-fail-on-unavailable"] if optout else []
    result = CliRunner().invoke(app, ["--format", "json", *options, *command, "--all"])
    assert result.exit_code == int(gated and not optout), result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == (
        "unavailable" if gated and not optout else "passed"
    )
    unavailable = data["run"]["unavailable_checks"]
    freshness = [item for item in unavailable if item["check"] == "freshness"]
    assert len(freshness) == 1
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
