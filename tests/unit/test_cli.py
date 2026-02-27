"""Unit tests for the docvet CLI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
import typer
from typer.testing import CliRunner

from docvet.cli import (
    FreshnessMode,
    _merge_file_args,
    _run_coverage,
    _run_enrichment,
    _run_freshness,
    _run_griffe,
    app,
)
from docvet.config import DocvetConfig, load_config
from docvet.discovery import DiscoveryMode

pytestmark = pytest.mark.unit

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _non_timing_lines(output: str) -> list[str]:
    """Return output lines excluding summary lines."""
    return [line for line in output.splitlines() if not line.startswith("Vetted ")]


# ---------------------------------------------------------------------------
# Autouse fixture — mock config loading and file discovery for all tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_config_and_discovery(mocker):
    mocker.patch("docvet.cli.load_config", return_value=DocvetConfig())
    mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake/file.py")])
    mocker.patch("docvet.cli._run_enrichment", return_value=[])
    mocker.patch("docvet.cli._run_freshness", return_value=[])
    mocker.patch("docvet.cli._run_coverage", return_value=[])
    mocker.patch("docvet.cli._run_griffe", return_value=[])


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
# --version flag
# ---------------------------------------------------------------------------


def test_app_when_invoked_with_version_flag_outputs_version_string():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "docvet" in result.output


def test_app_when_invoked_with_version_flag_includes_version_number():
    import importlib.metadata

    expected_version = importlib.metadata.version("docvet")
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert expected_version in result.output


# ---------------------------------------------------------------------------
# Subcommand exit codes & output
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_no_flags_exits_successfully():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0


def test_check_when_invoked_runs_all_checks_in_order(mocker):
    from docvet.checks import Finding

    mocker.patch(
        "docvet.cli._run_enrichment",
        return_value=[
            Finding(
                file="a.py",
                line=1,
                symbol="f",
                rule="enrichment-rule",
                message="enrichment: ok",
                category="required",
            )
        ],
    )
    mocker.patch(
        "docvet.cli._run_freshness",
        return_value=[
            Finding(
                file="a.py",
                line=2,
                symbol="f",
                rule="freshness-rule",
                message="freshness: ok",
                category="required",
            )
        ],
    )
    mocker.patch(
        "docvet.cli._run_coverage",
        return_value=[
            Finding(
                file="a.py",
                line=3,
                symbol="f",
                rule="coverage-rule",
                message="coverage: ok",
                category="required",
            )
        ],
    )
    mocker.patch(
        "docvet.cli._run_griffe",
        return_value=[
            Finding(
                file="a.py",
                line=4,
                symbol="f",
                rule="griffe-rule",
                message="griffe: ok",
                category="required",
            )
        ],
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


def test_freshness_when_invoked_with_mode_drift_exits_successfully():
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0


def test_coverage_when_invoked_exits_successfully():
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0


def test_griffe_when_invoked_exits_successfully():
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0


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
    assert "only one of" in result.output.lower()


def test_check_when_invoked_with_staged_and_files_fails_with_error():
    result = runner.invoke(app, ["check", "--staged", "--files", "f.py"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_check_when_invoked_with_all_and_files_fails_with_error():
    result = runner.invoke(app, ["check", "--all", "--files", "f.py"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_check_when_invoked_with_all_three_flags_fails_with_error():
    result = runner.invoke(app, ["check", "--staged", "--all", "--files", "f.py"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_enrichment_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["enrichment", "--staged", "--all"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_freshness_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["freshness", "--staged", "--all"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_coverage_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["coverage", "--staged", "--all"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_griffe_when_invoked_with_staged_and_all_fails_with_error():
    result = runner.invoke(app, ["griffe", "--staged", "--all"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


# ---------------------------------------------------------------------------
# Global options
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_verbose_prints_verbose_header():
    result = runner.invoke(app, ["--verbose", "check"])
    assert result.exit_code == 0
    assert "Checking" in result.output


def test_check_when_invoked_with_format_markdown_exits_successfully():
    result = runner.invoke(app, ["--format", "markdown", "check"])
    assert result.exit_code == 0


def test_check_when_invoked_with_output_flag_exits_successfully():
    result = runner.invoke(app, ["--output", "report.md", "check"])
    assert result.exit_code == 0


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
    non_summary = _non_timing_lines(result.output)
    output = "\n".join(line.lower() for line in non_summary)
    assert "staged" not in output
    assert "all" not in output


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
    mock_enrichment = mocker.patch("docvet.cli._run_enrichment", return_value=[])
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    mock_coverage = mocker.patch("docvet.cli._run_coverage", return_value=[])
    mock_griffe = mocker.patch("docvet.cli._run_griffe", return_value=[])
    runner.invoke(app, ["check"])
    mock_enrichment.assert_called_once_with(
        fake_files, fake_config, show_progress=False
    )
    mock_freshness.assert_called_once_with(
        fake_files, fake_config, discovery_mode=DiscoveryMode.DIFF, show_progress=False
    )
    mock_coverage.assert_called_once_with(fake_files, fake_config)
    mock_griffe.assert_called_once_with(
        fake_files, fake_config, verbose=False, quiet=False
    )


def test_check_when_discovery_returns_empty_does_not_call_stubs(mocker):
    mocker.patch("docvet.cli.discover_files", return_value=[])
    mock_enrichment = mocker.patch("docvet.cli._run_enrichment", return_value=[])
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    mock_coverage = mocker.patch("docvet.cli._run_coverage", return_value=[])
    mock_griffe = mocker.patch("docvet.cli._run_griffe", return_value=[])
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
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    runner.invoke(app, ["freshness", "--mode", "drift"])
    mock_freshness.assert_called_once_with(
        ANY,
        ANY,
        freshness_mode=FreshnessMode.DRIFT,
        discovery_mode=DiscoveryMode.DIFF,
        show_progress=False,
    )


def test_coverage_when_invoked_calls_discover_and_run_coverage(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    mock_run = mocker.patch("docvet.cli._run_coverage", return_value=[])
    runner.invoke(app, ["coverage"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.DIFF, files=())
    mock_run.assert_called_once_with([Path("/fake/file.py")], ANY)


def test_coverage_when_invoked_with_all_calls_discover_with_all_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["coverage", "--all"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.ALL, files=())


def test_coverage_when_invoked_with_staged_calls_discover_with_staged_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["coverage", "--staged"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.STAGED, files=())


def test_griffe_when_invoked_calls_discover_and_run_griffe(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    mock_run = mocker.patch("docvet.cli._run_griffe", return_value=[])
    runner.invoke(app, ["griffe"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.DIFF, files=())
    mock_run.assert_called_once_with(
        [Path("/fake/file.py")], ANY, verbose=False, quiet=False
    )


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
    assert _non_timing_lines(result.output) == []


def test_run_enrichment_when_syntax_error_skips_file_with_warning(mocker):
    mocker.patch("docvet.cli._run_enrichment", side_effect=_run_enrichment)
    mocker.patch.object(Path, "read_text", return_value="def bad(:\n")
    mock_check = mocker.patch("docvet.cli.check_enrichment", return_value=[])
    mocker.patch("docvet.cli.ast.parse", side_effect=SyntaxError("invalid syntax"))
    result = runner.invoke(app, ["enrichment"])
    assert result.exit_code == 0
    # Warning is emitted with err=True; consider both stdout and stderr.
    output = result.output + getattr(result, "stderr", "")
    assert "warning:" in output
    assert "failed to parse, skipping" in output
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


# ---------------------------------------------------------------------------
# _run_freshness behavior tests
# ---------------------------------------------------------------------------


def test_run_freshness_when_file_has_findings_prints_formatted_output(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="do_stuff",
            rule="stale-docstring",
            message="Docstring may be stale: body changed",
            category="recommended",
        ),
    ]
    mocker.patch("docvet.cli.check_freshness_diff", return_value=findings)
    mocker.patch("docvet.cli.subprocess.run")
    mocker.patch.object(Path, "read_text", return_value="def do_stuff(): pass\n")
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/app.py")])
    result = runner.invoke(app, ["freshness"])
    assert result.exit_code == 0
    assert (
        "src/app.py:10: stale-docstring Docstring may be stale: body changed"
        in result.output
    )


def test_run_freshness_when_no_findings_produces_no_output(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
    mocker.patch("docvet.cli.subprocess.run")
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    result = runner.invoke(app, ["freshness"])
    assert result.exit_code == 0
    assert _non_timing_lines(result.output) == []


def test_run_freshness_when_syntax_error_skips_file_with_warning(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch.object(Path, "read_text", return_value="def bad(:\n")
    mock_check = mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
    mocker.patch("docvet.cli.ast.parse", side_effect=SyntaxError("invalid syntax"))
    result = runner.invoke(app, ["freshness"])
    assert result.exit_code == 0
    output = result.output + getattr(result, "stderr", "")
    assert "warning:" in output
    assert "failed to parse, skipping" in output
    mock_check.assert_not_called()


def test_run_freshness_when_multiple_files_processes_all(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mocker.patch("docvet.cli.subprocess.run")
    mock_check = mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
    files = [Path("/a.py"), Path("/b.py"), Path("/c.py")]
    mocker.patch("docvet.cli.discover_files", return_value=files)
    result = runner.invoke(app, ["freshness"])
    assert result.exit_code == 0
    assert mock_check.call_count == 3


def test_run_freshness_passes_file_path_diff_output_and_tree(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "diff --git a/f.py b/f.py\n"
    mock_check = mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
    file_path = Path("/fake/file.py")
    mocker.patch("docvet.cli.discover_files", return_value=[file_path])
    result = runner.invoke(app, ["freshness"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(
        str(file_path), "diff --git a/f.py b/f.py\n", ANY
    )


# ---------------------------------------------------------------------------
# _run_freshness drift mode behavior tests
# ---------------------------------------------------------------------------


def test_run_freshness_drift_calls_check_freshness_drift_per_file(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mock_blame = mocker.patch("docvet.cli._get_git_blame", return_value="blame data")
    mock_check = mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
    mock_diff_check = mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
    file_path = Path("/fake/file.py")
    mocker.patch("docvet.cli.discover_files", return_value=[file_path])
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0
    mock_blame.assert_called_once_with(file_path, ANY)
    mock_check.assert_called_once_with(str(file_path), "blame data", ANY, ANY)
    mock_diff_check.assert_not_called()


def test_run_freshness_drift_prints_findings_in_correct_format(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="do_stuff",
            rule="stale-drift",
            message="Function 'do_stuff' code modified 2025-12-14, "
            "docstring last modified 2025-10-02 (73 days drift)",
            category="recommended",
        ),
    ]
    mocker.patch("docvet.cli.check_freshness_drift", return_value=findings)
    mocker.patch("docvet.cli._get_git_blame", return_value="blame data")
    mocker.patch.object(Path, "read_text", return_value="def do_stuff(): pass\n")
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/app.py")])
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0
    assert "src/app.py:10: stale-drift" in result.output
    assert "73 days drift" in result.output


def test_run_freshness_drift_no_findings_produces_no_output(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
    mocker.patch("docvet.cli._get_git_blame", return_value="blame data")
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0
    assert _non_timing_lines(result.output) == []


def test_run_freshness_drift_passes_config_freshness_to_check(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    from docvet.config import FreshnessConfig

    fake_config = DocvetConfig(
        freshness=FreshnessConfig(drift_threshold=15, age_threshold=45)
    )
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mocker.patch("docvet.cli._get_git_blame", return_value="blame data")
    mock_check = mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
    file_path = Path("/fake/file.py")
    mocker.patch("docvet.cli.discover_files", return_value=[file_path])
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(
        str(file_path), "blame data", ANY, fake_config.freshness
    )


def test_run_freshness_drift_handles_syntax_error_with_warning(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch.object(Path, "read_text", return_value="def bad(:\n")
    mock_check = mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
    mocker.patch("docvet.cli.ast.parse", side_effect=SyntaxError("invalid syntax"))
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0
    output = result.output + getattr(result, "stderr", "")
    assert "warning:" in output
    assert "failed to parse, skipping" in output
    mock_check.assert_not_called()


def test_run_freshness_drift_processes_multiple_files(mocker):
    mocker.patch("docvet.cli._run_freshness", side_effect=_run_freshness)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    mocker.patch(
        "docvet.cli._get_git_blame",
        side_effect=lambda fp, _root: f"blame-{fp.stem}",
    )
    mock_check = mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
    files = [Path("/a.py"), Path("/b.py"), Path("/c.py")]
    mocker.patch("docvet.cli.discover_files", return_value=files)
    result = runner.invoke(app, ["freshness", "--mode", "drift"])
    assert result.exit_code == 0
    assert mock_check.call_count == 3
    for file_path in files:
        mock_check.assert_any_call(str(file_path), f"blame-{file_path.stem}", ANY, ANY)


# ---------------------------------------------------------------------------
# _get_git_diff tests
# ---------------------------------------------------------------------------


def test_get_git_diff_when_diff_mode_runs_git_diff(mocker):
    from docvet.cli import _get_git_diff

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "diff output"
    result = _get_git_diff(Path("/f.py"), Path("/project"), DiscoveryMode.DIFF)
    assert result == "diff output"
    mock_subprocess.assert_called_once_with(
        ["git", "diff", "--", str(Path("/f.py"))],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path("/project"),
    )


def test_get_git_diff_when_files_mode_runs_git_diff(mocker):
    from docvet.cli import _get_git_diff

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "diff output"
    result = _get_git_diff(Path("/f.py"), Path("/project"), DiscoveryMode.FILES)
    assert result == "diff output"
    mock_subprocess.assert_called_once_with(
        ["git", "diff", "--", str(Path("/f.py"))],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path("/project"),
    )


def test_get_git_diff_when_staged_mode_runs_git_diff_cached(mocker):
    from docvet.cli import _get_git_diff

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "cached diff"
    result = _get_git_diff(Path("/f.py"), Path("/project"), DiscoveryMode.STAGED)
    assert result == "cached diff"
    mock_subprocess.assert_called_once_with(
        ["git", "diff", "--cached", "--", str(Path("/f.py"))],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path("/project"),
    )


def test_get_git_diff_when_all_mode_runs_git_diff_head(mocker):
    from docvet.cli import _get_git_diff

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "head diff"
    result = _get_git_diff(Path("/f.py"), Path("/project"), DiscoveryMode.ALL)
    assert result == "head diff"
    mock_subprocess.assert_called_once_with(
        ["git", "diff", "HEAD", "--", str(Path("/f.py"))],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path("/project"),
    )


def test_get_git_diff_when_git_fails_returns_empty_string(mocker):
    from docvet.cli import _get_git_diff

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 128
    mock_subprocess.return_value.stdout = ""
    result = _get_git_diff(Path("/f.py"), Path("/project"), DiscoveryMode.DIFF)
    assert result == ""


# ---------------------------------------------------------------------------
# _get_git_blame tests
# ---------------------------------------------------------------------------


def test_get_git_blame_runs_correct_command(mocker):
    from docvet.cli import _get_git_blame

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "blame output"
    result = _get_git_blame(Path("/f.py"), Path("/project"))
    assert result == "blame output"
    mock_subprocess.assert_called_once_with(
        ["git", "blame", "--line-porcelain", "--", str(Path("/f.py"))],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path("/project"),
    )


def test_get_git_blame_returns_stdout_on_success(mocker):
    from docvet.cli import _get_git_blame

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_subprocess.return_value.stdout = "porcelain blame data\n"
    result = _get_git_blame(Path("/f.py"), Path("/project"))
    assert result == "porcelain blame data\n"


def test_get_git_blame_returns_empty_on_failure(mocker):
    from docvet.cli import _get_git_blame

    mock_subprocess = mocker.patch("docvet.cli.subprocess.run")
    mock_subprocess.return_value.returncode = 128
    mock_subprocess.return_value.stdout = ""
    result = _get_git_blame(Path("/f.py"), Path("/project"))
    assert result == ""


def test_freshness_subcommand_passes_discovery_mode_to_run_freshness(mocker):
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    runner.invoke(app, ["freshness", "--staged"])
    mock_freshness.assert_called_once_with(
        ANY,
        ANY,
        freshness_mode=FreshnessMode.DIFF,
        discovery_mode=DiscoveryMode.STAGED,
        show_progress=False,
    )


def test_check_subcommand_passes_discovery_mode_to_run_freshness(mocker):
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    runner.invoke(app, ["check", "--all"])
    mock_freshness.assert_called_once_with(
        ANY, ANY, discovery_mode=DiscoveryMode.ALL, show_progress=False
    )


def test_check_subcommand_passes_show_progress_true_when_tty(mocker):
    mock_sys = mocker.patch("docvet.cli.sys")
    mock_sys.stderr.isatty.return_value = True
    mock_sys.stdout.isatty.return_value = True
    mock_enrichment = mocker.patch("docvet.cli._run_enrichment", return_value=[])
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    runner.invoke(app, ["check"])
    mock_enrichment.assert_called_once_with(ANY, ANY, show_progress=True)
    mock_freshness.assert_called_once_with(
        ANY, ANY, discovery_mode=DiscoveryMode.DIFF, show_progress=True
    )


def test_enrichment_subcommand_passes_show_progress_true_when_tty(mocker):
    mock_sys = mocker.patch("docvet.cli.sys")
    mock_sys.stderr.isatty.return_value = True
    mock_sys.stdout.isatty.return_value = True
    mock_enrichment = mocker.patch("docvet.cli._run_enrichment", return_value=[])
    runner.invoke(app, ["enrichment"])
    mock_enrichment.assert_called_once_with(ANY, ANY, show_progress=True)


def test_freshness_subcommand_passes_show_progress_true_when_tty(mocker):
    mock_sys = mocker.patch("docvet.cli.sys")
    mock_sys.stderr.isatty.return_value = True
    mock_sys.stdout.isatty.return_value = True
    mock_freshness = mocker.patch("docvet.cli._run_freshness", return_value=[])
    runner.invoke(app, ["freshness"])
    mock_freshness.assert_called_once_with(
        ANY,
        ANY,
        freshness_mode=FreshnessMode.DIFF,
        discovery_mode=DiscoveryMode.DIFF,
        show_progress=True,
    )


# ---------------------------------------------------------------------------
# _run_coverage behavior tests
# ---------------------------------------------------------------------------


def test_run_coverage_when_files_have_missing_init_prints_formatted_output(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/pkg/sub/module.py",
            line=1,
            symbol="<module>",
            rule="missing-init",
            message="Directory 'pkg/sub' lacks __init__.py (1 file affected)",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_coverage", return_value=findings)
    mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("src/pkg/sub/module.py")]
    )
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    assert "src/pkg/sub/module.py:1: missing-init" in result.output
    assert "Directory 'pkg/sub' lacks __init__.py (1 file affected)" in result.output


def test_run_coverage_when_no_findings_produces_no_output(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    mocker.patch("docvet.cli.check_coverage", return_value=[])
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    assert _non_timing_lines(result.output) == []


def test_run_coverage_passes_correct_src_root_path(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    fake_config = DocvetConfig(src_root="src", project_root=Path("/project"))
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_coverage", return_value=[])
    mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/project/src/app.py")]
    )
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(Path("/project/src"), ANY)


def test_run_coverage_with_default_config_uses_project_root_as_src_root(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    fake_config = DocvetConfig(project_root=Path("/project"))
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_coverage", return_value=[])
    mocker.patch("docvet.cli.discover_files", return_value=[Path("/project/app.py")])
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(Path("/project/."), ANY)


def test_run_coverage_passes_discovered_files(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    files = [Path("/a.py"), Path("/b.py")]
    mocker.patch("docvet.cli.discover_files", return_value=files)
    mock_check = mocker.patch("docvet.cli.check_coverage", return_value=[])
    result = runner.invoke(app, ["coverage"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(ANY, files)


def test_check_command_includes_coverage_findings(mocker):
    mocker.patch("docvet.cli._run_coverage", side_effect=_run_coverage)
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/pkg/mod.py",
            line=1,
            symbol="<module>",
            rule="missing-init",
            message="Directory 'pkg' lacks __init__.py (1 file affected)",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_coverage", return_value=findings)
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/pkg/mod.py")])
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "missing-init" in result.output


# ---------------------------------------------------------------------------
# _run_griffe behavior tests
# ---------------------------------------------------------------------------


def test_run_griffe_when_file_has_findings_prints_formatted_output(tmp_path, mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    from docvet.checks import Finding

    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    fake_config = DocvetConfig(project_root=tmp_path)
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    findings = [
        Finding(
            file="src/app.py",
            line=15,
            symbol="do_stuff",
            rule="griffe-unknown-param",
            message="Function 'do_stuff' does not appear in the function signature",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_griffe_compat", return_value=findings)
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/app.py")])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    assert (
        "src/app.py:15: griffe-unknown-param "
        "Function 'do_stuff' does not appear in the function signature"
    ) in result.output


def test_run_griffe_when_no_findings_produces_no_output(tmp_path, mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    fake_config = DocvetConfig(project_root=tmp_path)
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    assert _non_timing_lines(result.output) == []


def test_run_griffe_passes_correct_src_root_path(tmp_path, mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    fake_config = DocvetConfig(src_root="src", project_root=tmp_path)
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    mocker.patch("docvet.cli.discover_files", return_value=[src_dir / "app.py"])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(src_dir, ANY)


def test_run_griffe_with_default_config_uses_project_root_dot(tmp_path, mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    fake_config = DocvetConfig(project_root=tmp_path)
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    mocker.patch("docvet.cli.discover_files", return_value=[tmp_path / "app.py"])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(tmp_path / ".", ANY)


def test_run_griffe_passes_discovered_files(tmp_path, mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    fake_config = DocvetConfig(project_root=tmp_path)
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    files = [Path("/a.py"), Path("/b.py")]
    mocker.patch("docvet.cli.discover_files", return_value=files)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    mock_check.assert_called_once_with(ANY, files)


def test_run_griffe_when_griffe_not_installed_skips_silently(mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    assert _non_timing_lines(result.output) == []
    mock_check.assert_not_called()


def test_run_griffe_when_griffe_not_installed_and_verbose_emits_note(mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    result = runner.invoke(app, ["--verbose", "griffe"])
    output = result.output + getattr(result, "stderr", "")
    assert "griffe: skipped (griffe not installed)" in output
    mock_check.assert_not_called()


def test_run_griffe_when_griffe_not_installed_and_fail_on_emits_warning(mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)
    fake_config = DocvetConfig(fail_on=["griffe"])
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    result = runner.invoke(app, ["griffe"])
    output = result.output + getattr(result, "stderr", "")
    assert "warning: griffe check skipped (griffe not installed)" in output
    mock_check.assert_not_called()


def test_run_griffe_when_src_root_not_exists_returns_silently(mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    fake_config = DocvetConfig(project_root=Path("/nonexistent"), src_root="nope")
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    mocker.patch("docvet.cli.discover_files", return_value=[Path("/fake.py")])
    result = runner.invoke(app, ["griffe"])
    assert result.exit_code == 0
    assert _non_timing_lines(result.output) == []
    mock_check.assert_not_called()


def test_check_command_includes_griffe_findings(tmp_path, mocker):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    from docvet.checks import Finding

    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    fake_config = DocvetConfig(project_root=tmp_path)
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    findings = [
        Finding(
            file="src/mod.py",
            line=5,
            symbol="func",
            rule="griffe-unknown-param",
            message="Function 'func' does not appear in the function signature",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_griffe_compat", return_value=findings)
    mocker.patch("docvet.cli.discover_files", return_value=[Path("src/mod.py")])
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "griffe-unknown-param" in result.output


def test_check_passes_verbose_to_run_griffe(mocker):
    mock_griffe = mocker.patch("docvet.cli._run_griffe", return_value=[])
    runner.invoke(app, ["--verbose", "check"])
    mock_griffe.assert_called_once_with(ANY, ANY, verbose=True, quiet=False)


def test_griffe_when_invoked_with_all_calls_discover_with_all_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["griffe", "--all"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.ALL, files=())


def test_griffe_when_invoked_with_staged_calls_discover_with_staged_mode(mocker):
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["griffe", "--staged"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.STAGED, files=())


def test_run_griffe_when_griffe_not_installed_fail_on_takes_priority_over_verbose(
    mocker,
):
    mocker.patch("docvet.cli._run_griffe", side_effect=_run_griffe)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)
    fake_config = DocvetConfig(fail_on=["griffe"])
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mock_check = mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    result = runner.invoke(app, ["--verbose", "griffe"])
    output = result.output + getattr(result, "stderr", "")
    assert "warning: griffe check skipped (griffe not installed)" in output
    assert "griffe: skipped (griffe not installed)" not in output
    mock_check.assert_not_called()


# ---------------------------------------------------------------------------
# Direct-call tests: _run_enrichment returns list[Finding]
# ---------------------------------------------------------------------------


def test_run_enrichment_direct_returns_list_of_findings(mocker):
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
    result = _run_enrichment([Path("src/app.py")], DocvetConfig())
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].file == "src/app.py"
    assert result[0].line == 10
    assert result[0].symbol == "do_stuff"
    assert result[0].rule == "missing-raises"
    assert result[0].message == "Missing Raises: ValueError"
    assert result[0].category == "required"


def test_run_enrichment_direct_empty_findings_returns_empty_list(mocker):
    mocker.patch("docvet.cli.check_enrichment", return_value=[])
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    result = _run_enrichment([Path("src/app.py")], DocvetConfig())
    assert result == []


def test_run_enrichment_direct_syntax_error_skips_file(mocker):
    mocker.patch.object(Path, "read_text", return_value="def bad(:\n")
    mocker.patch("docvet.cli.ast.parse", side_effect=SyntaxError("invalid syntax"))
    mock_check = mocker.patch("docvet.cli.check_enrichment", return_value=[])
    result = _run_enrichment([Path("src/bad.py")], DocvetConfig())
    assert result == []
    mock_check.assert_not_called()


def test_run_enrichment_direct_multiple_files_accumulates_findings(mocker):
    from docvet.checks import Finding

    call_count = 0

    def _fake_check(source, tree, enrichment_config, file_path):
        nonlocal call_count
        call_count += 1
        return [
            Finding(
                file=file_path,
                line=call_count,
                symbol="func",
                rule="test-rule",
                message=f"finding {call_count}",
                category="required",
            )
        ]

    mocker.patch("docvet.cli.check_enrichment", side_effect=_fake_check)
    mocker.patch.object(Path, "read_text", return_value="x = 1\n")
    result = _run_enrichment([Path("a.py"), Path("b.py"), Path("c.py")], DocvetConfig())
    assert len(result) == 3
    assert result[0].file == "a.py"
    assert result[1].file == "b.py"
    assert result[2].file == "c.py"


# ---------------------------------------------------------------------------
# Direct-call tests: _run_freshness returns list[Finding]
# ---------------------------------------------------------------------------


def test_run_freshness_diff_direct_returns_list_of_findings(mocker):
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="do_stuff",
            rule="stale-docstring",
            message="Docstring may be stale: body changed",
            category="recommended",
        ),
    ]
    mocker.patch("docvet.cli.check_freshness_diff", return_value=findings)
    mocker.patch("docvet.cli.subprocess.run")
    mocker.patch.object(Path, "read_text", return_value="def do_stuff(): pass\n")
    result = _run_freshness([Path("src/app.py")], DocvetConfig())
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].rule == "stale-docstring"
    assert result[0].file == "src/app.py"
    assert result[0].line == 10
    assert result[0].symbol == "do_stuff"
    assert result[0].message == "Docstring may be stale: body changed"
    assert result[0].category == "recommended"


def test_run_freshness_drift_direct_returns_list_of_findings(mocker):
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="do_stuff",
            rule="stale-drift",
            message="73 days drift",
            category="recommended",
        ),
    ]
    mocker.patch("docvet.cli.check_freshness_drift", return_value=findings)
    mocker.patch("docvet.cli._get_git_blame", return_value="blame data")
    mocker.patch.object(Path, "read_text", return_value="def do_stuff(): pass\n")
    result = _run_freshness(
        [Path("src/app.py")], DocvetConfig(), freshness_mode=FreshnessMode.DRIFT
    )
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].file == "src/app.py"
    assert result[0].line == 10
    assert result[0].symbol == "do_stuff"
    assert result[0].rule == "stale-drift"
    assert result[0].message == "73 days drift"
    assert result[0].category == "recommended"


def test_run_freshness_drift_direct_mixed_files_skips_syntax_errors(mocker):
    from docvet.checks import Finding

    good_findings = [
        Finding(
            file="good.py",
            line=5,
            symbol="func",
            rule="stale-drift",
            message="drift found",
            category="recommended",
        ),
    ]

    def _fake_read(self, encoding="utf-8"):
        if "bad" in str(self):
            return "def bad(:\n"
        return "def func(): pass\n"

    mocker.patch.object(Path, "read_text", _fake_read)
    mocker.patch("docvet.cli._get_git_blame", return_value="blame data")
    mocker.patch("docvet.cli.check_freshness_drift", return_value=good_findings)
    result = _run_freshness(
        [Path("good.py"), Path("bad.py")],
        DocvetConfig(),
        freshness_mode=FreshnessMode.DRIFT,
    )
    assert len(result) == 1
    assert result[0].file == "good.py"


# ---------------------------------------------------------------------------
# Direct-call tests: _run_coverage returns list[Finding]
# ---------------------------------------------------------------------------


def test_run_coverage_direct_returns_list_of_findings(mocker):
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/pkg/mod.py",
            line=1,
            symbol="<module>",
            rule="missing-init",
            message="Directory 'pkg' lacks __init__.py (1 file affected)",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_coverage", return_value=findings)
    result = _run_coverage([Path("src/pkg/mod.py")], DocvetConfig())
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].rule == "missing-init"
    assert result[0].file == "src/pkg/mod.py"
    assert result[0].line == 1
    assert result[0].symbol == "<module>"
    assert result[0].message == "Directory 'pkg' lacks __init__.py (1 file affected)"
    assert result[0].category == "required"


def test_run_coverage_direct_no_findings_returns_empty_list(mocker):
    mocker.patch("docvet.cli.check_coverage", return_value=[])
    result = _run_coverage([Path("src/app.py")], DocvetConfig())
    assert result == []


# ---------------------------------------------------------------------------
# Direct-call tests: _run_griffe returns list[Finding]
# ---------------------------------------------------------------------------


def test_run_griffe_direct_returns_list_of_findings(tmp_path, mocker):
    from docvet.checks import Finding

    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    findings = [
        Finding(
            file="src/app.py",
            line=15,
            symbol="do_stuff",
            rule="griffe-unknown-param",
            message="Function 'do_stuff' unknown param",
            category="required",
        ),
    ]
    mocker.patch("docvet.cli.check_griffe_compat", return_value=findings)
    config = DocvetConfig(project_root=tmp_path)
    result = _run_griffe([Path("src/app.py")], config)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].rule == "griffe-unknown-param"
    assert result[0].file == "src/app.py"
    assert result[0].line == 15
    assert result[0].symbol == "do_stuff"
    assert result[0].message == "Function 'do_stuff' unknown param"
    assert result[0].category == "required"


def test_run_griffe_direct_griffe_not_installed_returns_empty_list(mocker):
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)
    result = _run_griffe([Path("src/app.py")], DocvetConfig())
    assert result == []


def test_run_griffe_direct_src_root_not_exists_returns_empty_list(mocker):
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    config = DocvetConfig(project_root=Path("/nonexistent"), src_root="nope")
    result = _run_griffe([Path("src/app.py")], config)
    assert result == []


def test_run_griffe_direct_no_findings_returns_empty_list(tmp_path, mocker):
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    mocker.patch("docvet.cli.check_griffe_compat", return_value=[])
    config = DocvetConfig(project_root=tmp_path)
    result = _run_griffe([Path("src/app.py")], config)
    assert result == []


# ---------------------------------------------------------------------------
# _output_and_exit unit tests
# ---------------------------------------------------------------------------


class TestOutputAndExit:
    """Tests for the _output_and_exit helper function."""

    @pytest.fixture(autouse=True)
    def _mock_reporting(self, mocker):
        """Mock all reporting functions to isolate _output_and_exit logic."""
        self.mock_format_terminal = mocker.patch(
            "docvet.cli.format_terminal", return_value="terminal output\n"
        )
        self.mock_format_markdown = mocker.patch(
            "docvet.cli.format_markdown", return_value="| markdown output |\n"
        )
        self.mock_format_verbose_header = mocker.patch(
            "docvet.cli.format_verbose_header",
            return_value="Checking 1 files [enrichment]\n",
        )
        self.mock_format_json = mocker.patch(
            "docvet.cli.format_json", return_value='{"findings":[]}\n'
        )
        self.mock_write_report = mocker.patch("docvet.cli.write_report")
        self.mock_determine_exit_code = mocker.patch(
            "docvet.cli.determine_exit_code", return_value=0
        )

    def _make_ctx(self, verbose=False, fmt=None, output=None):
        """Build a minimal typer.Context-like with obj dict."""
        ctx = MagicMock()
        ctx.obj = {
            "verbose": verbose,
            "format": fmt,
            "output": output,
        }
        return ctx

    def _call(self, ctx, findings_by_check, config, file_count, checks):
        """Call _output_and_exit and return the exit code."""
        from click.exceptions import Exit as ClickExit

        from docvet.cli import _output_and_exit

        with pytest.raises(ClickExit) as exc_info:
            _output_and_exit(ctx, findings_by_check, config, file_count, checks)
        return exc_info.value.exit_code

    def test_terminal_format_is_default_when_format_not_set(self, make_finding):
        finding = make_finding()
        ctx = self._make_ctx()
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        self.mock_format_terminal.assert_called_once_with([finding], no_color=ANY)
        self.mock_format_markdown.assert_not_called()

    def test_format_markdown_selects_format_markdown(self, make_finding):
        finding = make_finding()
        ctx = self._make_ctx(fmt="markdown")
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        self.mock_format_markdown.assert_called_once_with([finding])
        self.mock_format_terminal.assert_not_called()

    def test_output_writes_file_via_write_report(self, make_finding):
        finding = make_finding()
        ctx = self._make_ctx(output="report.md")
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        self.mock_write_report.assert_called_once_with(
            [finding], Path("report.md"), fmt="markdown"
        )
        self.mock_format_terminal.assert_not_called()
        self.mock_format_markdown.assert_not_called()

    def test_output_without_format_defaults_to_markdown_for_file(self, make_finding):
        finding = make_finding()
        ctx = self._make_ctx(output="report.md")
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        self.mock_write_report.assert_called_once_with(
            [finding], Path("report.md"), fmt="markdown"
        )

    def test_output_with_explicit_format_terminal_writes_terminal_to_file(
        self, make_finding
    ):
        finding = make_finding()
        ctx = self._make_ctx(fmt="terminal", output="report.md")
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        self.mock_write_report.assert_called_once_with(
            [finding], Path("report.md"), fmt="terminal"
        )

    def test_output_with_zero_findings_skips_write_report(self):
        ctx = self._make_ctx(output="report.md")
        self._call(ctx, {"enrichment": []}, DocvetConfig(), 1, ["enrichment"])
        self.mock_write_report.assert_not_called()

    def test_output_verbose_zero_findings_no_file_header_stderr_no_stdout(self, capsys):
        self.mock_format_verbose_header.return_value = (
            "Checking 1 files [enrichment, freshness]\n"
        )
        ctx = self._make_ctx(verbose=True, output="report.md")
        self._call(
            ctx,
            {"enrichment": [], "freshness": []},
            DocvetConfig(),
            1,
            ["enrichment", "freshness"],
        )
        self.mock_write_report.assert_not_called()
        captured = capsys.readouterr()
        assert "Checking 1 files [enrichment, freshness]" in captured.err
        assert captured.out == ""

    def test_verbose_with_findings_prints_header_to_stderr(self, capsys, make_finding):
        self.mock_format_verbose_header.return_value = (
            "Checking 1 files [enrichment, freshness]\n"
        )
        ctx = self._make_ctx(verbose=True)
        self._call(
            ctx,
            {"enrichment": [make_finding()], "freshness": []},
            DocvetConfig(),
            1,
            ["enrichment", "freshness"],
        )
        captured = capsys.readouterr()
        assert "Checking 1 files [enrichment, freshness]" in captured.err
        assert "terminal output" in captured.out

    def test_verbose_with_zero_findings_prints_header_stderr_nothing_stdout(
        self, capsys
    ):
        self.mock_format_verbose_header.return_value = (
            "Checking 1 files [enrichment, freshness]\n"
        )
        ctx = self._make_ctx(verbose=True)
        self._call(
            ctx,
            {"enrichment": [], "freshness": []},
            DocvetConfig(),
            1,
            ["enrichment", "freshness"],
        )
        captured = capsys.readouterr()
        assert "Checking 1 files [enrichment, freshness]" in captured.err
        assert captured.out == ""

    def test_verbose_single_check_suppresses_header(self, capsys):
        ctx = self._make_ctx(verbose=True)
        self._call(ctx, {"enrichment": []}, DocvetConfig(), 1, ["enrichment"])
        captured = capsys.readouterr()
        assert "Checking" not in captured.err
        self.mock_format_verbose_header.assert_not_called()

    def test_exit_code_1_when_fail_on_check_has_findings(self, make_finding):
        self.mock_determine_exit_code.return_value = 1
        finding = make_finding()
        ctx = self._make_ctx()
        config = DocvetConfig(fail_on=["enrichment"])
        code = self._call(ctx, {"enrichment": [finding]}, config, 1, ["enrichment"])
        assert code == 1
        self.mock_determine_exit_code.assert_called_once_with(
            {"enrichment": [finding]}, config
        )

    def test_exit_code_0_when_fail_on_check_has_no_findings(self):
        self.mock_determine_exit_code.return_value = 0
        ctx = self._make_ctx()
        config = DocvetConfig(fail_on=["enrichment"])
        findings_by_check = {"enrichment": []}
        code = self._call(ctx, findings_by_check, config, 1, ["enrichment"])
        assert code == 0
        self.mock_determine_exit_code.assert_called_once_with(findings_by_check, config)

    def test_exit_code_0_when_fail_on_is_empty(self, make_finding):
        self.mock_determine_exit_code.return_value = 0
        finding = make_finding()
        ctx = self._make_ctx()
        config = DocvetConfig()
        findings_by_check = {"enrichment": [finding]}
        code = self._call(ctx, findings_by_check, config, 1, ["enrichment"])
        assert code == 0
        self.mock_determine_exit_code.assert_called_once_with(findings_by_check, config)

    def test_no_color_env_var_suppresses_ansi(self, monkeypatch, make_finding):
        monkeypatch.setenv("NO_COLOR", "1")
        ctx = self._make_ctx()
        self._call(
            ctx, {"enrichment": [make_finding()]}, DocvetConfig(), 1, ["enrichment"]
        )
        self.mock_format_terminal.assert_called_once()
        assert self.mock_format_terminal.call_args[1]["no_color"] is True

    def test_non_tty_stdout_suppresses_ansi(self, monkeypatch, make_finding):
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setattr("sys.stdout.isatty", lambda: False)
        ctx = self._make_ctx()
        self._call(
            ctx, {"enrichment": [make_finding()]}, DocvetConfig(), 1, ["enrichment"]
        )
        self.mock_format_terminal.assert_called_once()
        assert self.mock_format_terminal.call_args[1]["no_color"] is True

    def test_output_flag_forces_no_color_true(self, make_finding):
        finding = make_finding()
        ctx = self._make_ctx(fmt="terminal", output="report.md")
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        self.mock_write_report.assert_called_once_with(
            [finding], Path("report.md"), fmt="terminal"
        )
        self.mock_format_terminal.assert_not_called()
        self.mock_format_markdown.assert_not_called()

    def test_standalone_subcommand_exit_code_when_check_not_in_fail_on(
        self, make_finding
    ):
        self.mock_determine_exit_code.return_value = 0
        finding = make_finding()
        ctx = self._make_ctx()
        config = DocvetConfig(fail_on=["freshness"])
        findings_by_check = {"enrichment": [finding]}
        code = self._call(ctx, findings_by_check, config, 1, ["enrichment"])
        assert code == 0
        self.mock_determine_exit_code.assert_called_once_with(findings_by_check, config)

    def test_format_json_calls_format_json_with_findings(self, capsys, make_finding):
        """AC#1: --format json routes to format_json and emits to stdout."""
        finding = make_finding()
        ctx = self._make_ctx(fmt="json")
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 5, ["enrichment"])
        self.mock_format_json.assert_called_once_with([finding], 5)
        captured = capsys.readouterr()
        assert captured.out == '{"findings":[]}\n'

    def test_format_json_emits_even_with_zero_findings(self, capsys):
        """AC#6: --format json always emits JSON, even with no findings."""
        ctx = self._make_ctx(fmt="json")
        self._call(ctx, {"enrichment": []}, DocvetConfig(), 5, ["enrichment"])
        self.mock_format_json.assert_called_once_with([], 5)
        captured = capsys.readouterr()
        assert captured.out == '{"findings":[]}\n'

    def test_format_json_writes_to_file_when_output_set(self, tmp_path, make_finding):
        """AC#1: --format json --output writes JSON to file."""
        output_file = tmp_path / "report.json"
        finding = make_finding()
        ctx = self._make_ctx(fmt="json", output=str(output_file))
        self._call(ctx, {"enrichment": [finding]}, DocvetConfig(), 1, ["enrichment"])
        assert output_file.read_text() == '{"findings":[]}\n'


# ---------------------------------------------------------------------------
# Story 21.3: Verbose & Quiet Flag Redesign
# ---------------------------------------------------------------------------


# --- Task 1.3: quiet flag sets ctx.obj ---


def test_check_when_invoked_with_quiet_flag_sets_ctx_obj_quiet(mocker):
    captured = {}
    original_discover = mocker.patch(
        "docvet.cli._discover_and_handle",
        return_value=[Path("/fake/file.py")],
    )

    def _capture_ctx(ctx, *a, **kw):
        captured["quiet"] = ctx.obj.get("quiet")
        return original_discover.return_value

    original_discover.side_effect = _capture_ctx
    mocker.patch("docvet.cli._output_and_exit")
    result = runner.invoke(app, ["-q", "check", "--all"])
    assert result.exit_code == 0
    assert captured["quiet"] is True


# --- Task 2.6: subcommand-level verbose ---


def test_check_when_verbose_on_subcommand_produces_verbose_output():
    result = runner.invoke(app, ["check", "--all", "--verbose"])
    assert result.exit_code == 0
    assert "Checking" in result.output
    assert "Found" in result.output
    assert "files in" in result.output


# --- Task 2.7: both positions verbose ---


def test_check_when_verbose_on_both_positions_produces_verbose_output():
    result = runner.invoke(app, ["--verbose", "check", "--all", "--verbose"])
    assert result.exit_code == 0
    assert "Checking" in result.output
    assert "Found" in result.output
    assert "files in" in result.output


# --- Task 2.8: quiet suppresses summary and timing ---


def test_check_when_quiet_suppresses_summary_on_stderr(mocker):
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli._output_and_exit")
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["check", "--all", "-q"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output


def test_check_when_quiet_suppresses_timing_on_stderr(mocker):
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli._output_and_exit")
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["--verbose", "check", "--all", "-q"])
    assert result.exit_code == 0
    assert "files in" not in result.output


# --- Task 2.9: quiet wins over verbose ---


def test_check_when_quiet_and_verbose_quiet_wins(mocker):
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli._output_and_exit")
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["check", "--all", "-q", "--verbose"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output
    assert "Checking" not in result.output
    assert "files in" not in result.output


# --- Task 3.5: file discovery count gating ---


def test_check_when_quiet_suppresses_file_count(mocker):
    mocker.patch(
        "docvet.cli.discover_files",
        return_value=[Path("/a.py"), Path("/b.py"), Path("/c.py")],
    )
    result = runner.invoke(app, ["--verbose", "-q", "check"])
    assert result.exit_code == 0
    assert "Found" not in result.output


def test_check_when_verbose_and_not_quiet_shows_file_count(mocker):
    mocker.patch(
        "docvet.cli.discover_files",
        return_value=[Path("/a.py"), Path("/b.py"), Path("/c.py")],
    )
    result = runner.invoke(app, ["--verbose", "check"])
    assert result.exit_code == 0
    assert "Found 3 file(s) to check" in result.output


# --- Task 4.1: --help includes --verbose and --quiet ---


def test_check_help_shows_verbose_and_quiet_flags():
    result = runner.invoke(app, ["check", "--help"])
    output = _strip_ansi(result.output)
    assert "--verbose" in output
    assert "--quiet" in output
    assert "-q" in output


# --- Task 4.2: app --help includes --verbose and --quiet ---


def test_app_help_shows_verbose_and_quiet_flags():
    result = runner.invoke(app, ["--help"])
    output = _strip_ansi(result.output)
    assert "--verbose" in output
    assert "--quiet" in output
    assert "-q" in output


# --- Task 5.1: quiet mode with findings ---


def test_check_when_quiet_with_findings_shows_findings_on_stdout(mocker):
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="f",
            rule="missing-raises",
            message="Missing Raises: ValueError",
            category="required",
        )
    ]
    mocker.patch("docvet.cli._run_enrichment", return_value=findings)
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["check", "--all", "-q"])
    assert "missing-raises" in result.output
    assert "Vetted" not in result.output


# --- Task 5.2: quiet with --format markdown ---


def test_check_when_quiet_with_format_markdown_shows_output_no_stderr(mocker):
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="f",
            rule="missing-raises",
            message="Missing Raises: ValueError",
            category="required",
        )
    ]
    mocker.patch("docvet.cli._run_enrichment", return_value=findings)
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["--format", "markdown", "check", "--all", "-q"])
    assert "missing-raises" in result.stdout
    assert "Vetted" not in result.stderr


# --- Task 5.3: quiet with --output ---


def test_check_when_quiet_with_output_flag_writes_file_no_stderr(mocker, tmp_path):
    from docvet.checks import Finding

    out = tmp_path / "report.md"
    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="f",
            rule="missing-raises",
            message="Missing Raises: ValueError",
            category="required",
        )
    ]
    mocker.patch("docvet.cli._run_enrichment", return_value=findings)
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["--output", str(out), "check", "--all", "-q"])
    assert out.exists()
    assert "Vetted" not in result.stderr


# --- Task 5.4: app-level quiet + subcommand-level verbose ---


def test_check_when_app_quiet_and_subcommand_verbose_quiet_wins(mocker):
    mocker.patch("docvet.cli._discover_and_handle", return_value=[Path("/f.py")])
    mocker.patch("docvet.cli._output_and_exit")
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["-q", "check", "--all", "--verbose"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output
    assert "Checking" not in result.output
    assert "files in" not in result.output


# --- Task 5.5: exit code in quiet mode with findings ---


def test_check_when_quiet_with_findings_exits_nonzero(mocker):
    from docvet.checks import Finding

    findings = [
        Finding(
            file="src/app.py",
            line=10,
            symbol="f",
            rule="missing-raises",
            message="Missing Raises: ValueError",
            category="required",
        )
    ]
    mocker.patch("docvet.cli._run_enrichment", return_value=findings)
    mocker.patch(
        "docvet.cli.load_config", return_value=DocvetConfig(fail_on=["enrichment"])
    )
    result = runner.invoke(app, ["check", "--all", "-q"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Story 21.4, Task 5: Summary line on each subcommand
# ---------------------------------------------------------------------------


def test_enrichment_subcommand_shows_vetted_summary_on_stderr():
    result = runner.invoke(app, ["enrichment", "--all"])
    assert result.exit_code == 0
    assert "Vetted" in result.output
    assert "[enrichment]" in result.output


def test_freshness_subcommand_shows_vetted_summary_on_stderr():
    result = runner.invoke(app, ["freshness", "--all"])
    assert result.exit_code == 0
    assert "Vetted" in result.output
    assert "[freshness]" in result.output


def test_coverage_subcommand_shows_vetted_summary_on_stderr():
    result = runner.invoke(app, ["coverage", "--all"])
    assert result.exit_code == 0
    assert "Vetted" in result.output
    assert "[coverage]" in result.output


def test_griffe_subcommand_shows_vetted_summary_on_stderr(mocker):
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    result = runner.invoke(app, ["griffe", "--all"])
    assert result.exit_code == 0
    assert "Vetted" in result.output
    assert "[griffe]" in result.output


def test_freshness_subcommand_with_findings_shows_findings_and_summary(
    mocker, make_finding
):
    findings = [make_finding(rule="stale-signature", category="required")]
    mocker.patch("docvet.cli._run_freshness", return_value=findings)
    result = runner.invoke(app, ["freshness", "--all"])
    assert "test.py:1:" in result.output
    summary = [line for line in result.output.splitlines() if line.startswith("Vetted")]
    assert len(summary) == 1
    assert "1 finding" in summary[0]
    assert "[freshness]" in summary[0]


# ---------------------------------------------------------------------------
# Story 21.4, Task 6: Verbose/quiet on subcommands
# ---------------------------------------------------------------------------


def test_enrichment_subcommand_verbose_shows_file_count_and_summary(mocker):
    mocker.patch(
        "docvet.cli.discover_files",
        return_value=[Path("/a.py"), Path("/b.py"), Path("/c.py")],
    )
    result = runner.invoke(app, ["enrichment", "--all", "--verbose"])
    assert result.exit_code == 0
    assert "Found 3 file(s) to check" in result.output
    assert "Vetted" in result.output
    assert "Checking" not in result.output


def test_enrichment_app_level_verbose_shows_file_count_and_summary(mocker):
    mocker.patch(
        "docvet.cli.discover_files",
        return_value=[Path("/a.py"), Path("/b.py")],
    )
    result = runner.invoke(app, ["--verbose", "enrichment", "--all"])
    assert result.exit_code == 0
    assert "Found 2 file(s) to check" in result.output
    assert "Vetted" in result.output


def test_enrichment_subcommand_quiet_suppresses_summary():
    result = runner.invoke(app, ["enrichment", "--all", "-q"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output


def test_enrichment_subcommand_quiet_wins_over_verbose():
    result = runner.invoke(app, ["enrichment", "--all", "-q", "--verbose"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output
    assert "Found" not in result.output


def test_coverage_subcommand_quiet_suppresses_summary():
    result = runner.invoke(app, ["coverage", "--all", "-q"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output


def test_griffe_subcommand_quiet_passes_quiet_to_run_griffe(mocker):
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    mock_run = mocker.patch("docvet.cli._run_griffe", return_value=[])
    runner.invoke(app, ["griffe", "--all", "-q"])
    mock_run.assert_called_once_with(ANY, ANY, verbose=False, quiet=True)


# ---------------------------------------------------------------------------
# Story 21.5, Task 4: Edge-case tests for subcommand quiet and staged
# ---------------------------------------------------------------------------


def test_freshness_subcommand_quiet_suppresses_summary():
    """Freshness -q suppresses Vetted summary."""
    result = runner.invoke(app, ["freshness", "--all", "-q"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output


def test_griffe_subcommand_quiet_suppresses_summary(mocker):
    """Griffe -q suppresses Vetted summary."""
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    mocker.patch("docvet.cli._run_griffe", return_value=[])
    result = runner.invoke(app, ["griffe", "--all", "-q"])
    assert result.exit_code == 0
    assert "Vetted" not in result.output


def test_check_staged_zero_files_exits_cleanly(mocker):
    """Check --staged with zero files exits 0 with no-files message."""
    mocker.patch("docvet.cli.discover_files", return_value=[])
    result = runner.invoke(app, ["check", "--staged"])
    assert result.exit_code == 0
    assert "No Python files to check." in result.output
    assert "Vetted" not in result.output


# ---------------------------------------------------------------------------
# _merge_file_args unit tests
# ---------------------------------------------------------------------------


def test_merge_file_args_returns_positional_when_only_positional_provided():
    """Positional args are returned when no --files option is given."""
    result = _merge_file_args(["a.py", "b.py"], None)
    assert result == ["a.py", "b.py"]


def test_merge_file_args_returns_option_when_only_option_provided():
    """--files option is returned when no positional args are given."""
    result = _merge_file_args(None, ["c.py"])
    assert result == ["c.py"]


def test_merge_file_args_returns_none_when_neither_provided():
    """Returns None when no file arguments are given at all."""
    result = _merge_file_args(None, None)
    assert result is None


def test_merge_file_args_raises_when_both_provided():
    """Raises BadParameter when both positional and --files are given."""
    with pytest.raises(typer.BadParameter, match="positional files"):
        _merge_file_args(["a.py"], ["b.py"])


def test_merge_file_args_falls_through_to_option_when_positional_is_empty():
    """Empty positional list (falsy) falls through to option."""
    result = _merge_file_args([], ["x.py"])
    assert result == ["x.py"]


def test_merge_file_args_returns_none_when_positional_empty_and_option_absent():
    """Empty positional list and option=None return None (no file args)."""
    result = _merge_file_args([], None)
    assert result is None


# ---------------------------------------------------------------------------
# Positional file arguments — CLI integration
# ---------------------------------------------------------------------------


def test_check_when_invoked_with_positional_args_exits_successfully():
    """Positional file arguments are accepted by the check subcommand."""
    result = runner.invoke(app, ["check", "foo.py", "bar.py"])
    assert result.exit_code == 0


def test_check_when_invoked_with_positional_args_calls_discover_with_files_mode(mocker):
    """Positional args trigger FILES discovery mode with correct paths."""
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check", "foo.py", "bar.py"])
    mock_discover.assert_called_once_with(
        ANY, DiscoveryMode.FILES, files=[Path("foo.py"), Path("bar.py")]
    )


def test_check_when_invoked_with_positional_and_files_flag_fails_with_error():
    """Using both positional args and --files produces an error."""
    result = runner.invoke(app, ["check", "foo.py", "--files", "bar.py"])
    assert result.exit_code != 0
    assert "positional files" in result.output.lower()


def test_check_when_invoked_without_args_uses_diff_mode(mocker):
    """No positional args and no --files falls back to DIFF mode."""
    mock_discover = mocker.patch(
        "docvet.cli.discover_files", return_value=[Path("/fake/file.py")]
    )
    runner.invoke(app, ["check"])
    mock_discover.assert_called_once_with(ANY, DiscoveryMode.DIFF, files=())


def test_enrichment_when_invoked_with_positional_args_exits_successfully():
    """Positional file arguments are accepted by the enrichment subcommand."""
    result = runner.invoke(app, ["enrichment", "foo.py"])
    assert result.exit_code == 0


def test_freshness_when_invoked_with_positional_args_exits_successfully():
    """Positional file arguments are accepted by the freshness subcommand."""
    result = runner.invoke(app, ["freshness", "foo.py"])
    assert result.exit_code == 0


def test_coverage_when_invoked_with_positional_args_exits_successfully():
    """Positional file arguments are accepted by the coverage subcommand."""
    result = runner.invoke(app, ["coverage", "foo.py"])
    assert result.exit_code == 0


def test_griffe_when_invoked_with_positional_args_exits_successfully(mocker):
    """Positional file arguments are accepted by the griffe subcommand."""
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())
    mocker.patch("docvet.cli._run_griffe", return_value=[])
    result = runner.invoke(app, ["griffe", "foo.py"])
    assert result.exit_code == 0


def test_files_option_continues_to_work_for_backward_compatibility():
    """The --files option still works identically for backward compat."""
    result = runner.invoke(app, ["check", "--files", "foo.py"])
    assert result.exit_code == 0


def test_check_when_invoked_with_positional_and_staged_fails_with_error():
    """Positional args and --staged are mutually exclusive."""
    result = runner.invoke(app, ["check", "foo.py", "--staged"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


def test_check_when_invoked_with_positional_and_all_fails_with_error():
    """Positional args and --all are mutually exclusive."""
    result = runner.invoke(app, ["check", "foo.py", "--all"])
    assert result.exit_code != 0
    assert "only one of" in result.output.lower()


# ---------------------------------------------------------------------------
# Story 23.3: JSON format CLI-level tests
# ---------------------------------------------------------------------------


def _extract_json(output: str) -> dict:
    """Extract JSON object from mixed CLI output (may contain stderr text)."""
    start = output.index("{")
    end = output.rindex("}") + 1
    return json.loads(output[start:end])


def test_check_when_invoked_with_format_json_exits_successfully():
    """AC#4: --format json accepted by check subcommand."""
    result = runner.invoke(app, ["--format", "json", "check"])
    assert result.exit_code == 0


def test_enrichment_when_invoked_with_format_json_exits_successfully():
    """AC#4: --format json accepted by enrichment subcommand."""
    result = runner.invoke(app, ["--format", "json", "enrichment"])
    assert result.exit_code == 0


def test_freshness_when_invoked_with_format_json_exits_successfully():
    """AC#4: --format json accepted by freshness subcommand."""
    result = runner.invoke(app, ["--format", "json", "freshness"])
    assert result.exit_code == 0


def test_coverage_when_invoked_with_format_json_exits_successfully():
    """AC#4: --format json accepted by coverage subcommand."""
    result = runner.invoke(app, ["--format", "json", "coverage"])
    assert result.exit_code == 0


def test_griffe_when_invoked_with_format_json_exits_successfully():
    """AC#4: --format json accepted by griffe subcommand."""
    result = runner.invoke(app, ["--format", "json", "griffe"])
    assert result.exit_code == 0


def test_check_with_format_json_valid_json_output():
    """AC#1: --format json produces valid JSON on stdout."""
    result = runner.invoke(app, ["--format", "json", "check"])
    assert result.exit_code == 0
    parsed = _extract_json(result.output)
    assert "findings" in parsed
    assert "summary" in parsed


def test_check_with_format_json_empty_findings_returns_empty_array():
    """AC#6: --format json with no findings returns empty array."""
    result = runner.invoke(app, ["--format", "json", "check"])
    assert result.exit_code == 0
    parsed = _extract_json(result.output)
    assert parsed["findings"] == []
    assert parsed["summary"]["total"] == 0


def test_check_with_format_json_exit_code_1_when_findings(mocker):
    """AC#3: --format json returns exit code 1 when findings exist."""
    from docvet.checks import Finding

    finding = Finding("f.py", 1, "s", "missing-raises", "msg", "required")
    mocker.patch("docvet.cli._run_enrichment", return_value=[finding])
    mocker.patch(
        "docvet.cli.load_config",
        return_value=DocvetConfig(fail_on=["enrichment"]),
    )
    result = runner.invoke(app, ["--format", "json", "check", "--all"])
    assert result.exit_code == 1
    parsed = _extract_json(result.output)
    assert len(parsed["findings"]) >= 1


def test_check_with_format_text_output_unchanged():
    """AC#5: Default text format is unchanged."""
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "{" not in result.output or "findings" not in result.output
