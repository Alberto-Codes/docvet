"""Integration tests for inline suppression comments in the CLI."""

from __future__ import annotations

import json
import subprocess
import textwrap

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with Python files."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    return tmp_path


def _commit_file(repo, name: str, content: str) -> None:
    """Write a file and commit it."""
    (repo / name).write_text(textwrap.dedent(content))
    subprocess.run(["git", "add", name], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"add {name}"],
        cwd=repo,
        capture_output=True,
        check=True,
    )


def _write_config(repo, *, fail_on: list[str] | None = None) -> None:
    """Write a pyproject.toml with docvet config."""
    lines = ["[tool.docvet]", "exclude = []"]
    if fail_on is not None:
        list_str = ", ".join(f'"{c}"' for c in fail_on)
        lines.append(f"fail-on = [{list_str}]")
    (repo / "pyproject.toml").write_text("\n".join(lines) + "\n")
    subprocess.run(
        ["git", "add", "pyproject.toml"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "commit", "-m", "add config"],
        cwd=repo,
        capture_output=True,
        check=True,
    )


class TestSuppressionCliRoundtrip:
    """End-to-end CLI tests for suppression comments."""

    def test_suppressed_findings_excluded_from_exit_code(self, git_repo):
        """Suppressed findings do NOT cause exit code 1 (AC 9)."""
        _write_config(git_repo, fail_on=["enrichment"])
        _commit_file(
            git_repo,
            "mod.py",
            '''\
            def validate(data):  # docvet: ignore[missing-raises]
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
            ''',
        )
        result = subprocess.run(
            ["uv", "run", "docvet", "enrichment", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        # missing-raises is the only required enrichment finding;
        # suppressing it should yield exit code 0
        assert result.returncode == 0

    def test_verbose_shows_suppressed_findings(self, git_repo):
        """Verbose mode lists suppressed findings to stderr (AC 6)."""
        _commit_file(
            git_repo,
            "mod.py",
            '''\
            def validate(data):  # docvet: ignore[missing-raises]
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
            ''',
        )
        result = subprocess.run(
            ["uv", "run", "docvet", "enrichment", "--all", "--verbose"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "Suppressed" in result.stderr
        assert "missing-raises" in result.stderr
        assert "[suppressed]" in result.stderr

    def test_json_format_includes_suppressed_array(self, git_repo):
        """JSON output includes a suppressed array (AC 10)."""
        _commit_file(
            git_repo,
            "mod.py",
            '''\
            def validate(data):  # docvet: ignore[missing-raises]
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
            ''',
        )
        result = subprocess.run(
            ["uv", "run", "docvet", "--format", "json", "check", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert "suppressed" in data
        suppressed_rules = [f["rule"] for f in data["suppressed"]]
        assert "missing-raises" in suppressed_rules
        # active findings should not contain suppressed rule
        active_rules = [f["rule"] for f in data["findings"]]
        assert "missing-raises" not in active_rules

    def test_file_level_blanket_suppression(self, git_repo):
        """File-level blanket suppression eliminates all findings (AC 5)."""
        _commit_file(
            git_repo,
            "mod.py",
            '''\
            # docvet: ignore-file
            def validate(data):
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
            ''',
        )
        result = subprocess.run(
            ["uv", "run", "docvet", "--format", "json", "check", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert len(data["findings"]) == 0

    def test_blanket_line_suppression(self, git_repo):
        """Blanket line suppression suppresses all rules on that symbol (AC 3)."""
        _commit_file(
            git_repo,
            "mod.py",
            '''\
            def validate(data):  # docvet: ignore
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
            ''',
        )
        result = subprocess.run(
            ["uv", "run", "docvet", "--format", "json", "check", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        # All findings on validate should be suppressed
        active_symbols = [f["symbol"] for f in data["findings"]]
        assert "validate" not in active_symbols
