"""Integration tests for the docvet fix CLI subcommand."""

from __future__ import annotations

import subprocess
import textwrap

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with an incomplete Python file."""
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

    src = tmp_path / "mod.py"
    src.write_text(
        textwrap.dedent('''\
            def validate(data):
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
        ''')
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    return tmp_path


class TestFixCliIntegration:
    """End-to-end integration tests for docvet fix."""

    def test_fix_modifies_files_in_repo(self, git_repo):
        """Fix modifies files with missing sections in a git repo."""
        subprocess.run(
            ["uv", "run", "docvet", "fix", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        src = git_repo / "mod.py"
        content = src.read_text()
        assert "Raises:" in content
        assert "[TODO:" in content

    def test_dry_run_does_not_modify_files(self, git_repo):
        """Dry-run shows diff but does not modify files."""
        original = (git_repo / "mod.py").read_text()
        result = subprocess.run(
            ["uv", "run", "docvet", "fix", "--dry-run", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--- a/" in result.stdout
        assert "+++ b/" in result.stdout
        assert (git_repo / "mod.py").read_text() == original

    def test_fix_then_check_shows_scaffold_findings(self, git_repo):
        """After fix, check shows scaffold-incomplete instead of missing-raises."""
        # Step 1: fix
        subprocess.run(
            ["uv", "run", "docvet", "fix", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        # Step 2: check
        result = subprocess.run(
            ["uv", "run", "docvet", "enrichment", "--all"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "scaffold-incomplete" in result.stdout
        assert "missing-raises" not in result.stdout

    def test_fix_staged_only_modifies_staged(self, git_repo):
        """Fix --staged only modifies staged files."""
        # Create a second file (unstaged/untracked).
        unstaged = git_repo / "other.py"
        unstaged.write_text(
            textwrap.dedent('''\
                def process():
                    """Process data."""
                    raise TypeError("bad")
            ''')
        )
        # Actually modify mod.py so there is a real staged delta.
        src = git_repo / "mod.py"
        src.write_text(
            src.read_text()
            + textwrap.dedent('''\

                def transform(value):
                    """Transform a value."""
                    if not value:
                        raise KeyError("missing")
                    return value
            ''')
        )
        subprocess.run(
            ["git", "add", "mod.py"], cwd=git_repo, capture_output=True, check=True
        )
        subprocess.run(
            ["uv", "run", "docvet", "fix", "--staged"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        # Staged file should have been fixed.
        assert "Raises:" in src.read_text()
        # Unstaged file should not have been fixed.
        assert "Raises:" not in unstaged.read_text()
