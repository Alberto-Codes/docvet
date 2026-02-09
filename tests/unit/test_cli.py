"""Unit tests for the docvet CLI."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import ANY

import pytest
import typer
from typer.testing import CliRunner

from docvet.cli import FreshnessMode, _run_enrichment, app
from docvet.config import DocvetConfig, load_config
from docvet.discovery import DiscoveryMode

pytestmark = pytest.mark.unit

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


# ---------------------------------------------------------------------------
# Autouse fixture — mock config loading and file discovery for all tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_config_and_discovery(mocker):
    mocker.patch("docvet.cli.load_config", return_value=DocvetConfig())
    mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake/file.py")])
    mocker.patch("docvet.cli._run_enrichment")


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


def test_check_when_invoked_runs_all_checks_in_order(mocker):
    mocker.patch(
        "docvet.cli._run_enrichment",
        side_effect=lambda f, c: typer.echo("enrichment: ok"),
    )
    result = runner.invoke(app, ["check"])
    output = result.output
    assert output.index("enrichment:") < output.index("freshness:")
    assert output.index("freshness:") < output.index("coverage:")
    assert output.index("coverage:") < output.index("griffe:")


def test_enrichment_when_invoked_exits_successfully():
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0


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


def test_check_when_invoked_with_config_flag_exits_successfully(tmp_path, mocker):
    p = tmp_path / "pyproject.toml"
    p.write_text("")
    mocker.patch("docvet.cli.load_config", wraps=load_config)
    result = runner.invoke(app, ["--config", str(p), "check"])
    assert result.exit_code == 0


def test_check_when_invoked_with_config_nonexistent_path_exits_with_error(mocker):
    mocker.patch(
        "docvet.cli.load_config",
        side_effect=FileNotFoundError("/nonexistent/pyproject.toml"),
    )
    result = runner.invoke(app, ["--config", "/nonexistent/pyproject.toml", "check"])
    assert result.exit_code != 0
    assert "Config file not found" in result.output


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


# ---------------------------------------------------------------------------
# Wiring: config loading & discovery
# ---------------------------------------------------------------------------


def test_check_when_discovery_returns_empty_exits_zero_with_message(mocker):
    mocker.patch("docvet.cli.discover_files", return_value=[])
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "No Python files to check." in result.output


def test_enrichment_when_discovery_returns_empty_exits_zero_with_message(mocker):
    mocker.patch("docvet.cli.discover_files", return_value=[])
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    assert "No Python files to check." in result.output


def test_check_when_verbose_and_files_found_shows_file_count(mocker):
    mocker.patch(
        "docvet.cli.discover_files",
        return_value=[Path("/a.py"), Path("/b.py"), Path("/c.py")],
    )
    result = runner.invoke(app, ["--verbose", "check"])
    assert result.exit_code == 0
    assert "Found 3 file(s) to check" in result.output


def test_check_when_not_verbose_does_not_show_file_count():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Found" not in result.output


def test_check_when_config_file_not_found_exits_with_error(mocker):
    mocker.patch("docvet.cli.load_config", side_effect=FileNotFoundError("bad.toml"))
    result = runner.invoke(app, ["check"])
    assert result.exit_code != 0
    assert "Config file not found" in result.output


def test_check_when_invoked_calls_discover_files_with_diff_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.DIFF, files=())


def test_check_when_invoked_with_staged_calls_discover_with_staged_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check", "--staged"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.STAGED, files=())


def test_check_when_invoked_with_all_calls_discover_with_all_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check", "--all"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.ALL, files=())


def test_check_when_invoked_with_files_calls_discover_with_files_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check", "--files", "foo.py"])
    mock_discover.assert_called_once_with(
        ANY, DiscoveryMode.FILES, files=[Path("foo.py")]
    )


def test_check_when_invoked_passes_config_to_run_stubs(mocker):
    fake_config = DocvetConfig()
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    fake_files = [Path("/fake/file.py")]
    mocker.patch("docvet.cli.discover_files", return_value=fake_files)
    mock_enrichment = mocker.patch("docvet.cli._run_enrichment")
    mock_freshness = mocker.patch("docvet.cli._run_freshness")
    mock_coverage = mocker.patch("docvet.cli._run_coverage")
    mock_griffe = mocker.patch("docvet.cli._run_griffe")
    runner.invoke(app, ["check"])
    mock_enrichment.assert_called_once_with(fake_files, fake_config)
    mock_freshness.assert_called_once_with(fake_files, fake_config)
    mock_coverage.assert_called_once_with(fake_files, fake_config)
    mock_griffe.assert_called_once_with(fake_files, fake_config)


def test_check_when_discovery_returns_empty_does_not_call_stubs(mocker):
    mocker.patch("docvet.cli.discover_files", return_value=[])
    mock_enrichment = mocker.patch("docvet.cli._run_enrichment")
    mock_freshness = mocker.patch("docvet.cli._run_freshness")
    mock_coverage = mocker.patch("docvet.cli._run_coverage")
    mock_griffe = mocker.patch("docvet.cli._run_griffe")
    runner.invoke(app, ["check"])
    mock_enrichment.assert_not_called()
    mock_freshness.assert_not_called()
    mock_coverage.assert_not_called()
    mock_griffe.assert_not_called()


def test_check_when_invoked_with_multiple_files_converts_all_paths(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check", "--files", "foo.py", "--files", "bar.py"])
    mock_discover.assert_called_once_with(
        ANY, DiscoveryMode.FILES, files=[Path("foo.py"), Path("bar.py")]
    )


def test_freshness_when_invoked_with_drift_passes_freshness_mode(mocker):
    mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake/file.py")])
    mock_freshness = mocker.patch("docvet.cli._run_freshness")
    runner.invoke(app, ["freshness", "--mode", "drift"])
    mock_freshness.assert_called_once_with(ANY, ANY, freshness_mode=FreshnessMode.DRIFT)


def test_coverage_when_invoked_calls_discover_and_run_stub(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    mock_run = mocker.patch("docvet.cli._run_coverage")
    runner.invoke(app, ["coverage"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.DIFF, files=())
    mock_run.assert_called_once_with([Path("/fake/file.py")], ANY)


def test_griffe_when_invoked_calls_discover_and_run_stub(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    mock_run = mocker.patch("docvet.cli._run_griffe")
    runner.invoke(app, ["griffe"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.DIFF, files=())
    mock_run.assert_called_once_with([Path("/fake/file.py")], ANY)


def test_enrichment_when_invoked_with_staged_calls_discover_with_staged_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["enrichment", "--staged"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.STAGED, files=())


def test_freshness_when_verbose_and_files_found_shows_file_count(mocker):
    mocker.patch(
        "docvet.cli.discover_files",
        return_value=[Path("/a.py"), Path("/b.py")],
    )
    result = runner.invoke(app, ["--verbose", "freshness"])
    assert result.exit_code == 0
    assert "Found 2 file(s) to check" in result.output


def test_check_when_invoked_calls_load_config_once(mocker):
    mock_load = mocker.patch("docvet.cli.load_config", return_value=DocvetConfig())
    runner.invoke(app, ["check"])
    assert mock_load.call_count == 1


# ---------------------------------------------------------------------------
# _run_enrichment behavior tests
# ---------------------------------------------------------------------------


def test_run_enrichment_when_file_has_findings_prints_formatted_output(mocker):
    mocker.patch("docvet.cli._run_enrichment", side_effect=_run_enrichment)
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="do_stuff",
            rule="missing-raises",
            message="Missing Raises: ValueError",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_enrichment", return_value=findings)
    mocker.patch.object(Path, "read_text", return_value="def do_stuff(): pass\n")
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/app.py")])
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    assert "src/app.py:10: missing-raises Missing Raises: ValueError" in result.output


def test_run_enrichment_when_no_findings_produces_no_output(mocker):
    mocker.patch("docvet.cli._run_enrichment", side_effect=_run_enrichment)
    mocker.patch("docvet.cli.check_enrichment", return_value=[])
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    assert result.output == ""


def test_run_enrichment_when_syntax_error_skips_file_with_warning(mocker):
    mocker.patch("docvet.cli._run_enrichment", side_effect=_run_enrichment)
    mocker.patch.object(Path, "read_text", return_value="def bad(:\n")
    mock_check = mocker.patch("docvet.cli.check_enrichment", return_value=[])
    mocker.patch("docvet.cli.ast.parse", side_effect=SyntaxError("invalid syntax"))
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    # CliRunner mixes stderr into result.output by default
    assert "warning:" in result.output
    assert "failed to parse, skipping" in result.output
    mock_check.assert_not_called()


def test_run_enrichment_when_multiple_files_processes_all(mocker):
    mocker.patch("docvet.cli._run_enrichment", side_effect=_run_enrichment)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mock_check = mocker.patch("docvet.cli.check_enrichment", return_value=[])
    files = [Path("/a.py"), Path("/b.py"), Path("/c.py")]
    mocker.patch("docvet.cli.discover_files", return_value=files)
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    assert mock_check.call_count == 3


def test_run_enrichment_passes_config_enrichment_and_str_file_path(mocker):
    mocker.patch("docvet.cli._run_enrichment", side_effect=_run_enrichment)
    fake_config = DocvetConfig()
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mock_check = mocker.patch("docvet.cli.check_enrichment", return_value=[])
    file_path = Path("/fake/file.py")
    mocker.patch("docvet.cli.discover_files", return_value=[file_path])
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(
        "x = 1\n", ANY, fake_config.enrichment, str(file_path)
    )
