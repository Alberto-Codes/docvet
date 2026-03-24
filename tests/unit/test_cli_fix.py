"""Tests for the docvet fix CLI subcommand and runner."""

from __future__ import annotations

import textwrap
from typing import Literal

import pytest
from typer.testing import CliRunner

from docvet.checks import Finding
from docvet.cli import app
from docvet.config import DocvetConfig

pytestmark = pytest.mark.unit

_Category = Literal["required", "recommended", "scaffold"]

runner = CliRunner()


def _finding(
    *,
    file: str = "test.py",
    line: int = 1,
    symbol: str = "func",
    rule: str = "missing-raises",
    message: str = "test message",
    category: _Category = "required",
) -> Finding:
    return Finding(
        file=file,
        line=line,
        symbol=symbol,
        rule=rule,
        message=message,
        category=category,
    )


# ---------------------------------------------------------------------------
# _run_fix runner tests (Task 1)
# ---------------------------------------------------------------------------


class TestRunFix:
    """Tests for the _run_fix runner function."""

    def test_modifies_file_with_missing_sections(self, tmp_path):
        """File with missing sections is modified in-place."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def validate(data):
                    """Validate input data."""
                    if not data:
                        raise ValueError("empty")
            ''')
        )
        from docvet.cli._runners import _run_fix

        config = DocvetConfig(project_root=tmp_path)
        findings, modified, sections, diffs = _run_fix([src], config)
        assert modified == 1
        assert sections >= 1
        assert "Raises:" in src.read_text()
        assert len(diffs) == 0

    def test_no_modification_when_complete(self, tmp_path):
        """File with complete docstrings is not modified."""
        src = tmp_path / "mod.py"
        original = textwrap.dedent('''\
            def greet(name: str) -> str:
                """Greet a person.

                Args:
                    name: The name.

                Returns:
                    str: A greeting.
                """
                return f"Hello, {name}"
        ''')
        src.write_text(original)
        from docvet.cli._runners import _run_fix

        config = DocvetConfig(project_root=tmp_path)
        findings, modified, sections, diffs = _run_fix([src], config)
        assert modified == 0
        assert sections == 0
        assert src.read_text() == original

    def test_dry_run_does_not_write(self, tmp_path):
        """Dry-run collects diffs without writing files."""
        src = tmp_path / "mod.py"
        original = textwrap.dedent('''\
            def validate(data):
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
        ''')
        src.write_text(original)
        from docvet.cli._runners import _run_fix

        config = DocvetConfig(project_root=tmp_path)
        findings, modified, sections, diffs = _run_fix([src], config, dry_run=True)
        assert modified == 1
        assert len(diffs) == 1
        assert src.read_text() == original  # not modified

    def test_syntax_error_skipped(self, tmp_path):
        """Files with syntax errors are skipped gracefully."""
        src = tmp_path / "bad.py"
        src.write_text("def f(\n")
        from docvet.cli._runners import _run_fix

        config = DocvetConfig(project_root=tmp_path)
        findings, modified, sections, diffs = _run_fix([src], config)
        assert modified == 0
        assert len(findings) == 0

    def test_scaffold_findings_collected(self, tmp_path):
        """Scaffold-incomplete findings are collected after fix."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def validate(data):
                    """Validate input data."""
                    if not data:
                        raise ValueError("empty")
            ''')
        )
        from docvet.cli._runners import _run_fix

        config = DocvetConfig(project_root=tmp_path)
        findings, modified, sections, diffs = _run_fix([src], config)
        scaffold = [f for f in findings if f.category == "scaffold"]
        assert len(scaffold) >= 1
        assert all(f.rule == "scaffold-incomplete" for f in scaffold)

    def test_empty_file_list(self):
        """Empty file list produces zero results."""
        from docvet.cli._runners import _run_fix

        config = DocvetConfig()
        findings, modified, sections, diffs = _run_fix([], config)
        assert modified == 0
        assert sections == 0
        assert len(findings) == 0

    def test_mixed_files_partial_modification(self, tmp_path):
        """Only files needing fixes are modified; complete files are untouched."""
        incomplete = tmp_path / "incomplete.py"
        incomplete.write_text(
            textwrap.dedent('''\
                def validate(data):
                    """Validate data."""
                    if not data:
                        raise ValueError("empty")
            ''')
        )
        complete = tmp_path / "complete.py"
        complete_text = textwrap.dedent('''\
            def greet() -> str:
                """Greet.

                Returns:
                    str: Hi.
                """
                return "hi"
        ''')
        complete.write_text(complete_text)

        from docvet.cli._runners import _run_fix

        config = DocvetConfig(project_root=tmp_path)
        findings, modified, sections, diffs = _run_fix([incomplete, complete], config)
        assert modified == 1
        assert complete.read_text() == complete_text


# ---------------------------------------------------------------------------
# CLI subcommand tests (Task 2, 3, 4)
# ---------------------------------------------------------------------------


class TestFixSubcommand:
    """Tests for the docvet fix CLI subcommand."""

    def test_help_shows_fix_options(self):
        """Fix command help includes --dry-run, --staged, --all."""
        result = runner.invoke(app, ["fix", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--staged" in result.output
        assert "--all" in result.output

    def test_dry_run_produces_diff_output(self, tmp_path, monkeypatch):
        """Dry-run prints unified diff to stdout."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def validate(data):
                    """Validate data."""
                    if not data:
                        raise ValueError("empty")
            ''')
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["fix", "--dry-run", str(src)])
        assert result.exit_code == 0
        assert "--- a/" in result.output
        assert "+++ b/" in result.output
        assert "+    Raises:" in result.output

    def test_dry_run_no_fixes_needed(self, tmp_path, monkeypatch):
        """Dry-run with no fixes shows appropriate message."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def f():
                    """Do stuff."""
                    pass
            ''')
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["fix", "--dry-run", str(src)])
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "flag",
        ["--staged", "--all"],
        ids=["staged", "all"],
    )
    def test_discovery_flags_accepted(self, flag):
        """Discovery flags are accepted without error."""
        result = runner.invoke(app, ["fix", flag, "--dry-run"])
        # Should not crash (may exit 0 with no files or findings)
        assert result.exit_code == 0

    def test_fix_modifies_file_in_place(self, tmp_path, monkeypatch):
        """Fix without dry-run writes modified files."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def validate(data):
                    """Validate data."""
                    if not data:
                        raise ValueError("empty")
            ''')
        )
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["fix", str(src)])
        assert "Raises:" in src.read_text()

    def test_summary_format_with_fixes(self, tmp_path, monkeypatch):
        """Summary line shows fixed count and scaffold findings."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def validate(data):
                    """Validate data."""
                    if not data:
                        raise ValueError("empty")
            ''')
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["fix", str(src)])
        assert "Fixed 1 of 1 files" in result.output
        assert "scaffold" in result.output

    def test_summary_format_no_fixes(self, tmp_path, monkeypatch):
        """Summary line shows 'no fixes needed' when nothing to do."""
        src = tmp_path / "mod.py"
        src.write_text(
            textwrap.dedent('''\
                def f():
                    """Do stuff."""
                    pass
            ''')
        )
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["fix", str(src)])
        assert "No fixes needed" in result.output
