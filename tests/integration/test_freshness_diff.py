"""Integration tests for freshness diff mode false-positive prevention."""

from __future__ import annotations

import ast
import json
import subprocess

import pytest
from typer.testing import CliRunner

from docvet.checks.freshness import check_freshness_diff
from docvet.cli import app

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("separator", ["\f", "\v", "\x85", "\u2028", "\u2029"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_payload_separator_preserves_cli_finding(
    git_repo, monkeypatch, separator, newline
):
    """A changed signature after a payload separator must not become docstring-only."""
    monkeypatch.chdir(git_repo)
    module = git_repo / "module.py"
    source = (
        '"""Module."""\n'
        f"# comment {separator} continuation\n"
        "def greet(name):\n"
        '    """Say hello."""\n'
        "    return name\n"
    )
    module.write_bytes(source.replace("\n", newline).encode())
    (git_repo / "pyproject.toml").write_text('[tool.docvet]\nfail-on=["freshness"]\n')
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "initial"],
        cwd=git_repo,
        check=True,
        capture_output=True,
    )
    modified = source.replace("def greet(name):", "def greet(name, extra=None):")
    module.write_bytes(modified.replace("\n", newline).encode())
    result = CliRunner().invoke(app, ["--format", "json", "freshness", str(module)])
    assert result.exit_code == 1, result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == "findings"
    assert [(f["symbol"], f["rule"], f["line"]) for f in data["findings"]] == [
        ("greet", "stale-signature", 3)
    ]


class TestFreshnessDiffFalsePositives:
    """End-to-end tests using real git repos to verify context-line exclusion."""

    def test_adjacent_function_not_flagged_when_neighbor_modified(
        self, git_repo
    ) -> None:
        """AC 1-3: modifying one function does not flag the adjacent unchanged one."""
        module = git_repo / "module.py"

        # Initial commit with two adjacent functions
        initial_source = (
            "def greet(name):\n"
            '    """Say hello."""\n'
            '    return f"Hello, {name}"\n'
            "\n"
            "\n"
            "def farewell(name):\n"
            '    """Say goodbye."""\n'
            '    return f"Bye, {name}"\n'
        )
        module.write_text(initial_source)
        subprocess.run(
            ["git", "add", "module.py"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

        # Modify greet's body (but not its docstring), leave farewell untouched
        modified_source = (
            "def greet(name):\n"
            '    """Say hello."""\n'
            '    return f"Hi, {name}!"\n'
            "\n"
            "\n"
            "def farewell(name):\n"
            '    """Say goodbye."""\n'
            '    return f"Bye, {name}"\n'
        )
        module.write_text(modified_source)

        # Get the diff
        result = subprocess.run(
            ["git", "diff", "--", "module.py"],
            cwd=git_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        diff_output = result.stdout

        # Parse the modified source and run freshness check
        tree = ast.parse(modified_source)
        findings = check_freshness_diff("module.py", diff_output, tree)

        # Only greet should be flagged (body changed, docstring not updated).
        # farewell must NOT be flagged — its lines are only context in the diff.
        assert len(findings) == 1
        assert findings[0].symbol == "greet"
        assert findings[0].rule == "stale-body"

        # Verify farewell is explicitly absent from findings
        farewell_findings = [f for f in findings if f.symbol == "farewell"]
        assert len(farewell_findings) == 0
