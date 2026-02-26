"""Unit tests for CLI per-check timing and total execution time."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from docvet.cli import app
from docvet.config import DocvetConfig

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

TIMING_LINE_RE = re.compile(
    r"^(enrichment|freshness|coverage|griffe): \d+ files in \d+\.\d+s$", re.MULTILINE
)
SUMMARY_LINE_RE = re.compile(
    r"^Vetted \d+ files \[.+\] \u2014 .+\. \(\d+\.\d+s\)$", re.MULTILINE
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_runner():
    """Typer CliRunner for invoking commands."""
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture
def _mock_check_internals(mocker):
    """Mock discovery, config, _run_* functions, and _output_and_exit.

    Also mocks ``importlib.util.find_spec`` to report griffe as installed,
    ensuring tests are hermetic regardless of the test environment.
    """
    fake_files = [Path("/fake/file.py")]
    fake_config = DocvetConfig(project_root=Path("/fake"))

    mocker.patch("docvet.cli._resolve_discovery_mode")
    mocker.patch("docvet.cli._discover_and_handle", return_value=fake_files)
    mocker.patch("docvet.cli._run_enrichment", return_value=[])
    mocker.patch("docvet.cli._run_freshness", return_value=[])
    mocker.patch("docvet.cli._run_coverage", return_value=[])
    mocker.patch("docvet.cli._run_griffe", return_value=[])
    mocker.patch("docvet.cli._output_and_exit")
    mocker.patch("docvet.cli.load_config", return_value=fake_config)
    mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())

    return fake_files


@pytest.fixture
def _mock_perf_counter(mocker):
    """Mock time.perf_counter to return controlled incrementing values.

    Returns 100.0, 100.1, 100.2, ... for each successive call.
    """
    counter = iter([100.0 + x * 0.1 for x in range(100)])
    mocker.patch("docvet.cli.time.perf_counter", side_effect=counter)


# ---------------------------------------------------------------------------
# Task 4.1: check() writes per-check timing to stderr when verbose
# ---------------------------------------------------------------------------


class TestCheckVerbosePerCheckTiming:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_per_check_timing_lines_present_when_verbose(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])
        output = result.output

        assert "enrichment:" in output
        assert "freshness:" in output
        assert "coverage:" in output
        assert "griffe:" in output
        assert "files in" in output

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_per_check_timing_format_matches_pattern(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])

        matches = TIMING_LINE_RE.findall(result.output)
        assert len(matches) == 4


# ---------------------------------------------------------------------------
# Task 4.2: check() does NOT write per-check timing when not verbose
# ---------------------------------------------------------------------------


class TestCheckNonVerboseNoPerCheckTiming:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_no_per_check_timing_without_verbose(self, cli_runner):
        result = cli_runner.invoke(app, ["check", "--all"])

        matches = TIMING_LINE_RE.findall(result.output)
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Task 4.3: check() writes total time to stderr unconditionally
# ---------------------------------------------------------------------------


class TestCheckSummaryLine:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_present_without_verbose(self, cli_runner):
        result = cli_runner.invoke(app, ["check", "--all"])

        matches = SUMMARY_LINE_RE.findall(result.output)
        assert len(matches) == 1

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_present_with_verbose(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])

        matches = SUMMARY_LINE_RE.findall(result.output)
        assert len(matches) == 1

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_includes_finding_count_when_findings_present(
        self, cli_runner, mocker, make_finding
    ):
        mocker.patch(
            "docvet.cli._run_enrichment",
            return_value=[make_finding(category="required")],
        )
        mocker.patch(
            "docvet.cli._run_freshness",
            return_value=[make_finding(line=2, category="recommended")],
        )

        result = cli_runner.invoke(app, ["check", "--all"])

        summary = [
            line for line in result.output.splitlines() if line.startswith("Vetted")
        ]
        assert len(summary) == 1
        assert "2 findings" in summary[0]
        assert "1 required" in summary[0]
        assert "1 recommended" in summary[0]


# ---------------------------------------------------------------------------
# Task 4.4: Individual subcommands write only total time (no per-check)
# ---------------------------------------------------------------------------


class TestIndividualSubcommandTiming:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_enrichment_subcommand_shows_total_only(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "enrichment", "--all"])

        assert len(SUMMARY_LINE_RE.findall(result.output)) == 1
        assert len(TIMING_LINE_RE.findall(result.output)) == 0

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_freshness_subcommand_shows_total_only(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "freshness", "--all"])

        assert len(SUMMARY_LINE_RE.findall(result.output)) == 1
        assert len(TIMING_LINE_RE.findall(result.output)) == 0

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_coverage_subcommand_shows_total_only(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "coverage", "--all"])

        assert len(SUMMARY_LINE_RE.findall(result.output)) == 1
        assert len(TIMING_LINE_RE.findall(result.output)) == 0

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_griffe_subcommand_shows_total_only(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "griffe", "--all"])

        assert len(SUMMARY_LINE_RE.findall(result.output)) == 1
        assert len(TIMING_LINE_RE.findall(result.output)) == 0


# ---------------------------------------------------------------------------
# Task 4.5: Timing format matches expected pattern
# ---------------------------------------------------------------------------


class TestTimingFormat:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_per_check_format_is_name_colon_count_files_in_seconds(self, cli_runner):
        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])

        for line in result.output.splitlines():
            if "files in" in line:
                assert TIMING_LINE_RE.match(line), f"Bad format: {line!r}"

    @pytest.mark.usefixtures("_mock_check_internals")
    def test_per_check_elapsed_value_reflects_mock_gap(self, cli_runner, mocker):
        """Verify the subtraction is correct, not just the format."""
        # Two calls per check: start (100.0) and end (100.5) → 0.5s
        # Then remaining calls for subsequent checks and total.
        mocker.patch(
            "docvet.cli.time.perf_counter",
            side_effect=[100.0, 100.0, 100.5] + [200.0] * 50,
        )

        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])

        assert "enrichment: 1 files in 0.5s" in result.output

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_total_format_is_vetted_summary_line(self, cli_runner):
        result = cli_runner.invoke(app, ["check", "--all"])

        vetted = [
            line for line in result.output.splitlines() if line.startswith("Vetted")
        ]
        assert len(vetted) == 1
        assert SUMMARY_LINE_RE.match(vetted[0]), f"Bad format: {vetted[0]!r}"


# ---------------------------------------------------------------------------
# Task 4.6: Griffe timing suppressed when griffe not installed
# ---------------------------------------------------------------------------


class TestGriffeTimingSuppressed:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_no_griffe_timing_line_when_griffe_not_installed(self, cli_runner, mocker):
        mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)

        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])
        lines = result.output.splitlines()

        griffe_timing = [
            line for line in lines if line.startswith("griffe:") and "files in" in line
        ]
        assert len(griffe_timing) == 0

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_griffe_timing_line_present_when_griffe_installed(self, cli_runner, mocker):
        mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())

        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])
        lines = result.output.splitlines()

        griffe_timing = [
            line for line in lines if line.startswith("griffe:") and "files in" in line
        ]
        assert len(griffe_timing) == 1

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_only_three_timing_lines_when_griffe_not_installed(
        self, cli_runner, mocker
    ):
        mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)

        result = cli_runner.invoke(app, ["--verbose", "check", "--all"])

        matches = TIMING_LINE_RE.findall(result.output)
        assert len(matches) == 3


# ---------------------------------------------------------------------------
# Story 21.1, Task 3: Conditional griffe in summary check list
# ---------------------------------------------------------------------------


class TestSummaryConditionalGriffe:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_includes_griffe_when_installed(self, cli_runner, mocker):
        mocker.patch("docvet.cli.importlib.util.find_spec", return_value=MagicMock())

        result = cli_runner.invoke(app, ["check", "--all"])
        summary = [
            line for line in result.output.splitlines() if line.startswith("Vetted")
        ]
        assert len(summary) == 1
        assert "griffe" in summary[0]

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_omits_griffe_when_not_installed(self, cli_runner, mocker):
        mocker.patch("docvet.cli.importlib.util.find_spec", return_value=None)

        result = cli_runner.invoke(app, ["check", "--all"])
        summary = [
            line for line in result.output.splitlines() if line.startswith("Vetted")
        ]
        assert len(summary) == 1
        assert "griffe" not in summary[0]
        assert "[enrichment, freshness, coverage]" in summary[0]


# ---------------------------------------------------------------------------
# Story 21.1, Task 4: Summary on stderr regardless of output format
# ---------------------------------------------------------------------------


class TestSummaryAlwaysOnStderr:
    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_present_with_format_markdown(self, cli_runner):
        result = cli_runner.invoke(app, ["--format", "markdown", "check", "--all"])

        assert "Vetted" not in result.stdout
        matches = SUMMARY_LINE_RE.findall(result.stderr)
        assert len(matches) == 1

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_summary_present_with_output_flag(self, cli_runner, tmp_path):
        out = tmp_path / "report.md"
        result = cli_runner.invoke(app, ["--output", str(out), "check", "--all"])

        assert "Vetted" not in result.stdout
        matches = SUMMARY_LINE_RE.findall(result.stderr)
        assert len(matches) == 1

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_enrichment_summary_on_stderr_with_format_markdown(self, cli_runner):
        """Enrichment subcommand: summary on stderr, not in markdown stdout."""
        result = cli_runner.invoke(app, ["--format", "markdown", "enrichment", "--all"])

        assert "Vetted" not in result.stdout
        matches = SUMMARY_LINE_RE.findall(result.stderr)
        assert len(matches) == 1
        assert "[enrichment]" in result.stderr

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_griffe_summary_on_stderr_with_format_markdown(self, cli_runner):
        """Griffe subcommand: summary on stderr, not in markdown stdout."""
        result = cli_runner.invoke(app, ["--format", "markdown", "griffe", "--all"])

        assert "Vetted" not in result.stdout
        matches = SUMMARY_LINE_RE.findall(result.stderr)
        assert len(matches) == 1
        assert "[griffe]" in result.stderr

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_enrichment_summary_on_stderr_with_output_flag(self, cli_runner, tmp_path):
        """Enrichment subcommand: summary on stderr when --output writes to file."""
        out = tmp_path / "report.md"
        result = cli_runner.invoke(app, ["--output", str(out), "enrichment", "--all"])

        assert "Vetted" not in result.stdout
        matches = SUMMARY_LINE_RE.findall(result.stderr)
        assert len(matches) == 1
        assert "[enrichment]" in result.stderr

    @pytest.mark.usefixtures("_mock_check_internals", "_mock_perf_counter")
    def test_griffe_summary_on_stderr_with_output_flag(self, cli_runner, tmp_path):
        """Griffe subcommand: summary on stderr when --output writes to file."""
        out = tmp_path / "report.md"
        result = cli_runner.invoke(app, ["--output", str(out), "griffe", "--all"])

        assert "Vetted" not in result.stdout
        matches = SUMMARY_LINE_RE.findall(result.stderr)
        assert len(matches) == 1
        assert "[griffe]" in result.stderr
