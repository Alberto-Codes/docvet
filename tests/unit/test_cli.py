"""Unit tests for the docvet CLI."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from docvet.cli import app

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


# ---------------------------------------------------------------------------
# Help & discovery
# ---------------------------------------------------------------------------


def test_app_when_invoked_with_no_args_shows_help():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "docstring quality vetting" in result.output.lower()


def test_app_when_invoked_with_help_shows_all_subcommands():
    result = runner.invoke(app, ["--help"])
    output = result.output
    assert "check" in output
    assert "enrichment" in output
    assert "freshness" in output
    assert "coverage" in output
    assert "griffe" in output


def test_check_help_when_invoked_shows_discovery_flags():
    result = runner.invoke(app, ["check", "--help"])
    output = _strip_ansi(result.output)
    assert "--staged" in output
    assert "--all" in output
    assert "--files" in output


def test_check_help_when_invoked_shows_correct_description():
    result = runner.invoke(app, ["check", "--help"])
    assert "Run all enabled checks" in result.output


def test_enrichment_help_when_invoked_shows_correct_description():
    result = runner.invoke(app, ["enrichment", "--help"])
    assert "missing docstring sections" in result.output


def test_freshness_help_when_invoked_shows_mode_flag():
    result = runner.invoke(app, ["freshness", "--help"])
    assert "--mode" in _strip_ansi(result.output)


def test_freshness_help_when_invoked_shows_correct_description():
    result = runner.invoke(app, ["freshness", "--help"])
    assert "stale docstrings" in result.output


def test_coverage_help_when_invoked_shows_correct_description():
    result = runner.invoke(app, ["coverage", "--help"])
    assert "invisible to mkdocs" in result.output


def test_griffe_help_when_invoked_shows_correct_description():
    result = runner.invoke(app, ["griffe", "--help"])
    assert "rendering compatibility" in result.output


# ---------------------------------------------------------------------------
# Subcommand exit codes & output
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_no_flags_exits_successfully():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0


def test_check_when_invoked_runs_all_checks_in_order():
    result = runner.invoke(app, ["check"])
    output = result.output
    assert output.index("enrichment:") < output.index("freshness:")
    assert output.index("freshness:") < output.index("coverage:")
    assert output.index("coverage:") < output.index("griffe:")


def test_enrichment_when_invoked_exits_successfully():
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    assert "enrichment: not yet implemented" in result.output


def test_freshness_when_invoked_exits_successfully():
    result = runner.invoke(app, ["freshness"])
    assert result.exit_code == 0
    assert "freshness: not yet implemented" in result.output


def test_freshness_when_invoked_with_mode_drift_exits_successfully():
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0


def test_coverage_when_invoked_exits_successfully():
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    assert "coverage: not yet implemented" in result.output


def test_griffe_when_invoked_exits_successfully():
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    assert "griffe: not yet implemented" in result.output


# ---------------------------------------------------------------------------
# Discovery flag parsing
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_staged_exits_successfully():
    result = runner.invoke(app, ["check", "--staged"])
    assert result.exit_code == 0


def test_check_when_invoked_with_all_exits_successfully():
    result = runner.invoke(app, ["check", "--all"])
    assert result.exit_code == 0


def test_check_when_invoked_with_single_file_exits_successfully():
    result = runner.invoke(app, ["check", "--files", "foo.py"])
    assert result.exit_code == 0


def test_check_when_invoked_with_multiple_files_exits_successfully():
    result = runner.invoke(app, ["check", "--files", "foo.py", "--files", "bar.py"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Mutual exclusivity
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["check", "--staged", "--all"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_check_when_invoked_with_staged_and_files_fails_with_error():
    result = runner.invoke(app, ["check", "--staged", "--files", "f.py"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_check_when_invoked_with_all_and_files_fails_with_error():
    result = runner.invoke(app, ["check", "--all", "--files", "f.py"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_check_when_invoked_with_all_three_flags_fails_with_error():
    result = runner.invoke(app, ["check", "--staged", "--all", "--files", "f.py"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_enrichment_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["enrichment", "--staged", "--all"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_freshness_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["freshness", "--staged", "--all"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_coverage_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["coverage", "--staged", "--all"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_griffe_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["griffe", "--staged", "--all"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


# ---------------------------------------------------------------------------
# Global options
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_verbose_prints_verbose_enabled():
    result = runner.invoke(app, ["--verbose", "check"])
    assert result.exit_code == 0
    assert "verbose: enabled" in result.output


def test_check_when_invoked_with_format_markdown_prints_format():
    result = runner.invoke(app, ["--format", "markdown", "check"])
    assert result.exit_code == 0
    assert "format: markdown" in result.output


def test_check_when_invoked_with_output_flag_prints_output_path():
    result = runner.invoke(app, ["--output", "report.md", "check"])
    assert result.exit_code == 0
    assert "output: report.md" in result.output


def test_app_when_invoked_with_format_invalid_fails():
    result = runner.invoke(app, ["--format", "invalid", "check"])
    assert result.exit_code != 0


def test_app_when_invoked_with_format_uppercase_fails():
    result = runner.invoke(app, ["--format", "TERMINAL", "check"])
    assert result.exit_code != 0


def test_help_when_invoked_shows_config_flag():
    result = runner.invoke(app, ["--help"])
    assert "--config" in _strip_ansi(result.output)


def test_check_when_invoked_with_config_flag_exits_successfully(tmp_path):
    p = tmp_path / "pyproject.toml"
    p.write_text("")
    result = runner.invoke(app, ["--config", str(p), "check"])
    assert result.exit_code == 0


def test_check_when_invoked_with_config_nonexistent_path_stores_string():
    result = runner.invoke(app, ["--config", "/nonexistent/pyproject.toml", "check"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Default discovery mode
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_no_flags_uses_diff_mode():
    # Negative assertion: placeholder until real discovery produces positive
    # evidence of DIFF mode. Verifies no other mode keywords leak into output.
    result = runner.invoke(app, ["check"])
    output = result.output.lower()
    assert "staged" not in output
    assert "all" not in output
    assert "files" not in output


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def test_app_entry_point_is_importable_and_callable():
    from docvet.cli import app as entry_app

    assert callable(entry_app)
