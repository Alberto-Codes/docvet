"""CLI and MCP report the same Git prerequisite failures and gating."""

from __future__ import annotations

import json
import subprocess

import pytest
from typer.testing import CliRunner

from docvet.cli import app
from docvet.mcp import docvet_check

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("optout", [False, True])
@pytest.mark.parametrize(
    ("failure", "reason", "remedy"),
    [
        (PermissionError("access denied"), "could not execute git", "permissions"),
        (OSError("exec format error"), "could not execute git", "executable"),
        (
            subprocess.CalledProcessError(
                128, ["git"], stderr="fatal: detected dubious ownership in repository"
            ),
            "dubious ownership",
            "ownership",
        ),
        (
            subprocess.CalledProcessError(
                128, ["git"], stderr="fatal: not a git repository (or any parent)"
            ),
            "not a git repository",
            "checkout",
        ),
        (
            subprocess.CalledProcessError(
                128, ["git"], stderr="fatal: bad config line 1 in file config"
            ),
            "bad config line 1",
            "reported git error",
        ),
        (subprocess.CalledProcessError(128, ["git"]), "exit status 128", "git error"),
    ],
)
def test_probe_failure_parity(tmp_path, monkeypatch, failure, reason, remedy, optout):
    target = tmp_path / "a.py"
    target.write_text('"""Module."""\n')
    (tmp_path / "pyproject.toml").write_text(
        '[tool.docvet]\nfail-on=["freshness"]\n'
        f"fail-on-unavailable={str(not optout).lower()}\n"
    )
    monkeypatch.chdir(tmp_path)
    original = subprocess.run

    def run(args, **kwargs):
        if args == ["git", "rev-parse", "--git-dir"]:
            raise failure
        return original(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    cli = CliRunner().invoke(app, ["--format", "json", "freshness", str(target)])
    assert cli.exit_code == int(not optout), cli.output
    cli_run = json.loads(cli.stdout)["run"]
    mcp = json.loads(docvet_check(str(target), ["freshness"]))
    assert cli_run == mcp["run"]
    assert cli_run["status"] == ("passed" if optout else "unavailable")
    unavailable = cli_run["unavailable_checks"][0]
    assert reason in unavailable["reason"]
    assert remedy in unavailable["remedy"]
    assert unavailable["configured_gate"] is True
    assert unavailable["blocking"] is (not optout)
    assert mcp["errors"] == [unavailable["reason"]]
    assert reason in cli.stderr


def test_missing_git_parity(tmp_path, monkeypatch):
    target = tmp_path / "a.py"
    target.write_text('"""Module."""\n')
    (tmp_path / "pyproject.toml").write_text('[tool.docvet]\nfail-on=["freshness"]\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "no-bin"))
    cli = CliRunner().invoke(app, ["--format", "json", "freshness", str(target)])
    mcp = json.loads(docvet_check(str(target), ["freshness"]))
    assert cli.exit_code == 1
    assert json.loads(cli.stdout)["run"] == mcp["run"]
    assert "not installed" in mcp["run"]["unavailable_checks"][0]["reason"]
