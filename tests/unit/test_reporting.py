"""Tests for the reporting module."""

from __future__ import annotations

import json

import pytest
import typer

from docvet.checks import Finding
from docvet.config import DocvetConfig, PresenceConfig
from docvet.reporting import (
    CheckQuality,
    compute_quality,
    determine_exit_code,
    format_json,
    format_markdown,
    format_quality_summary,
    format_summary,
    format_terminal,
    format_verbose_header,
    write_report,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# format_terminal tests (Task 8)
# ---------------------------------------------------------------------------


class TestFormatTerminal:
    """Tests for format_terminal."""

    def test_multi_file_sorted_grouped_summary(self, make_finding):
        """AC#1: Multi-file findings sorted by (file, line) with grouping and summary."""
        findings = [
            make_finding(file="src/b.py", line=10, rule="r1", message="msg1"),
            make_finding(file="src/a.py", line=5, rule="r2", message="msg2"),
            make_finding(file="src/a.py", line=20, rule="r3", message="msg3"),
        ]
        result = format_terminal(findings, no_color=True)
        lines = result.rstrip("\n").split("\n")

        # Sorted: a.py:5, a.py:20, blank, b.py:10, blank, summary
        assert lines[0] == "src/a.py:5: r2 msg2 [required]"
        assert lines[1] == "src/a.py:20: r3 msg3 [required]"
        assert lines[2] == ""  # blank between file groups
        assert lines[3] == "src/b.py:10: r1 msg1 [required]"
        assert lines[4] == ""  # blank before summary
        assert lines[5] == "3 findings (3 required, 0 recommended)"

    def test_single_file_no_blank_separators(self, make_finding):
        """AC#2: Single-file findings have no blank-line separators between findings."""
        findings = [
            make_finding(file="test.py", line=10, rule="r1", message="msg1"),
            make_finding(file="test.py", line=20, rule="r2", message="msg2"),
        ]
        result = format_terminal(findings, no_color=True)
        lines = result.rstrip("\n").split("\n")

        # Two findings, blank before summary, summary
        assert lines[0] == "test.py:10: r1 msg1 [required]"
        assert lines[1] == "test.py:20: r2 msg2 [required]"
        assert lines[2] == ""  # blank before summary only
        assert lines[3] == "2 findings (2 required, 0 recommended)"
        assert len(lines) == 4

    def test_color_present_by_default(self, make_finding):
        """AC#3: ANSI codes present with correct color mapping."""
        findings = [
            make_finding(category="required"),
            make_finding(line=2, category="recommended"),
        ]
        result = format_terminal(findings)
        assert "\033[" in result
        # Verify correct color mapping: red for required, yellow for recommended
        expected_required = typer.style("[required]", fg=typer.colors.RED)
        expected_recommended = typer.style("[recommended]", fg=typer.colors.YELLOW)
        assert expected_required in result
        assert expected_recommended in result

    def test_no_color_suppresses_ansi(self, make_finding):
        """AC#4: no_color=True removes all ANSI codes."""
        findings = [
            make_finding(category="required"),
            make_finding(line=2, category="recommended"),
        ]
        result = format_terminal(findings, no_color=True)
        assert "\033[" not in result
        assert "[required]" in result
        assert "[recommended]" in result

    def test_empty_returns_empty_string(self):
        """AC#5: Empty findings returns empty string."""
        assert format_terminal([]) == ""

    def test_summary_shows_both_counts_including_zeros(self, make_finding):
        """AC#19: Summary always shows both category counts even when one is zero."""
        findings = [make_finding(category="recommended")]
        result = format_terminal(findings, no_color=True)
        assert "0 required" in result
        assert "1 recommended" in result

    def test_blank_line_before_summary(self, make_finding):
        """AC#20: Blank line before summary (ruff convention)."""
        findings = [make_finding()]
        result = format_terminal(findings, no_color=True)
        lines = result.rstrip("\n").split("\n")
        # last line is summary, second-to-last is blank
        assert lines[-2] == ""
        assert "findings" in lines[-1]

    def test_stable_sort_same_file_line(self, make_finding):
        """AC#18: Two findings with same (file, line) preserve insertion order."""
        findings = [
            make_finding(file="a.py", line=5, rule="rule-b", message="second"),
            make_finding(file="a.py", line=5, rule="rule-a", message="first"),
        ]
        result = format_terminal(findings, no_color=True)
        lines = result.rstrip("\n").split("\n")
        # Python sorted is stable, so insertion order preserved for equal keys
        assert "rule-b" in lines[0]
        assert "rule-a" in lines[1]

    def test_three_files_multiple_separators(self, make_finding):
        """Multiple file groups produce multiple blank-line separators."""
        findings = [
            make_finding(file="c.py", line=1, rule="r1", message="m1"),
            make_finding(file="a.py", line=1, rule="r2", message="m2"),
            make_finding(file="b.py", line=1, rule="r3", message="m3"),
        ]
        result = format_terminal(findings, no_color=True)
        lines = result.rstrip("\n").split("\n")

        # a.py, blank, b.py, blank, c.py, blank, summary
        assert lines[0].startswith("a.py:")
        assert lines[1] == ""
        assert lines[2].startswith("b.py:")
        assert lines[3] == ""
        assert lines[4].startswith("c.py:")
        assert lines[5] == ""
        assert "3 findings" in lines[6]

    def test_mixed_categories_summary(self, make_finding):
        """Summary with both required and recommended counts."""
        findings = [
            make_finding(category="required"),
            make_finding(line=2, category="recommended"),
        ]
        result = format_terminal(findings, no_color=True)
        assert "2 findings (1 required, 1 recommended)" in result

    def test_trailing_newline(self, make_finding):
        """Output ends with exactly one trailing newline."""
        findings = [make_finding()]
        result = format_terminal(findings, no_color=True)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")


# ---------------------------------------------------------------------------
# format_markdown tests (Task 8 continued)
# ---------------------------------------------------------------------------


class TestFormatMarkdown:
    """Tests for format_markdown."""

    def test_multi_file_table_sorted_summary(self, make_finding):
        """AC#6: GFM table with sorted findings and bold summary."""
        findings = [
            make_finding(
                file="src/b.py",
                line=10,
                symbol="func_b",
                rule="r1",
                message="msg1",
                category="required",
            ),
            make_finding(
                file="src/a.py",
                line=5,
                symbol="func_a",
                rule="r2",
                message="msg2",
                category="recommended",
            ),
        ]
        result = format_markdown(findings)
        lines = result.rstrip("\n").split("\n")

        assert lines[0] == "| File | Line | Rule | Symbol | Message | Category |"
        assert lines[1] == "|------|------|------|--------|---------|----------|"
        # Sorted: a.py first — verify full row content
        assert lines[2] == "| src/a.py | 5 | r2 | func_a | msg2 | recommended |"
        assert lines[3] == "| src/b.py | 10 | r1 | func_b | msg1 | required |"
        assert lines[4] == ""  # blank line before summary
        assert lines[5] == "**2 findings** (1 required, 1 recommended)"

    def test_pipe_escaped_in_message(self, make_finding):
        """AC#7: Pipe character escaped in message column."""
        findings = [make_finding(message="has | pipe")]
        result = format_markdown(findings)
        assert "has \\| pipe" in result

    def test_empty_returns_empty_string(self):
        """AC#8: Empty findings returns empty string."""
        assert format_markdown([]) == ""

    def test_no_ansi_codes(self, make_finding):
        """AC#9: Markdown output never contains ANSI codes."""
        findings = [
            make_finding(category="required"),
            make_finding(line=2, category="recommended"),
        ]
        result = format_markdown(findings)
        assert "\033[" not in result

    def test_stable_sort_same_file_line(self, make_finding):
        """AC#18: Stable sort preserves insertion order for same (file, line)."""
        findings = [
            make_finding(file="a.py", line=5, rule="rule-b", symbol="s1"),
            make_finding(file="a.py", line=5, rule="rule-a", symbol="s2"),
        ]
        result = format_markdown(findings)
        lines = result.rstrip("\n").split("\n")
        assert "rule-b" in lines[2]
        assert "rule-a" in lines[3]

    def test_summary_shows_both_counts_including_zeros(self, make_finding):
        """AC#19: Summary always shows both counts even when one is zero."""
        findings = [make_finding(category="required")]
        result = format_markdown(findings)
        assert "1 required" in result
        assert "0 recommended" in result

    def test_trailing_newline(self, make_finding):
        """Output ends with exactly one trailing newline."""
        findings = [make_finding()]
        result = format_markdown(findings)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")


# ---------------------------------------------------------------------------
# format_verbose_header tests (Task 9)
# ---------------------------------------------------------------------------


class TestFormatVerboseHeader:
    """Tests for format_verbose_header."""

    def test_standard_output(self):
        """AC#10: Standard header with count and check names."""
        result = format_verbose_header(12, ["enrichment", "freshness"])
        assert result == "Checking 12 files [enrichment, freshness]\n"

    def test_single_check(self):
        """Single check in the list."""
        result = format_verbose_header(3, ["coverage"])
        assert result == "Checking 3 files [coverage]\n"

    def test_all_four_checks(self):
        """All four checks enabled."""
        result = format_verbose_header(
            42, ["enrichment", "freshness", "coverage", "griffe"]
        )
        assert result == (
            "Checking 42 files [enrichment, freshness, coverage, griffe]\n"
        )


# ---------------------------------------------------------------------------
# write_report tests (Task 10)
# ---------------------------------------------------------------------------


class TestWriteReport:
    """Tests for write_report."""

    def test_markdown_write(self, make_finding, tmp_path):
        """AC#11: Writes format_markdown output to file."""
        findings = [make_finding()]
        output = tmp_path / "report.md"
        write_report(findings, output, fmt="markdown")
        content = output.read_text()
        assert content == format_markdown(findings)

    def test_terminal_write_no_color(self, make_finding, tmp_path):
        """AC#12: Terminal format writes with no_color=True."""
        findings = [make_finding()]
        output = tmp_path / "report.txt"
        write_report(findings, output, fmt="terminal")
        content = output.read_text()
        assert content == format_terminal(findings, no_color=True)
        assert "\033[" not in content

    def test_missing_parent_raises(self, make_finding, tmp_path):
        """AC#13: Missing parent directory raises FileNotFoundError."""
        findings = [make_finding()]
        output = tmp_path / "nonexistent" / "report.md"
        with pytest.raises(FileNotFoundError):
            write_report(findings, output)

    def test_empty_findings_write(self, tmp_path):
        """AC#21: Empty findings writes empty content."""
        output = tmp_path / "report.md"
        write_report([], output)
        assert output.read_text() == ""

    def test_empty_findings_terminal_write(self, tmp_path):
        """Empty findings with terminal format writes empty content."""
        output = tmp_path / "report.txt"
        write_report([], output, fmt="terminal")
        assert output.read_text() == ""

    def test_invalid_fmt_raises(self, make_finding, tmp_path):
        """Unknown fmt value raises ValueError."""
        findings = [make_finding()]
        output = tmp_path / "report.txt"
        with pytest.raises(ValueError, match="Unknown format"):
            write_report(findings, output, fmt="xml")


# ---------------------------------------------------------------------------
# format_json tests (Story 23.3)
# ---------------------------------------------------------------------------


class TestFormatJson:
    """Tests for format_json."""

    def test_all_seven_fields_present(self, make_finding):
        """AC#1: Each finding has all 7 fields."""
        findings = [make_finding(category="required")]
        result = json.loads(format_json(findings, 1))
        finding = result["findings"][0]
        assert set(finding.keys()) == {
            "file",
            "line",
            "symbol",
            "rule",
            "message",
            "category",
            "severity",
        }

    def test_severity_mapping_required_to_high(self, make_finding):
        """AC#1: required category maps to high severity."""
        findings = [make_finding(category="required")]
        result = json.loads(format_json(findings, 1))
        assert result["findings"][0]["severity"] == "high"

    def test_severity_mapping_recommended_to_low(self, make_finding):
        """AC#1: recommended category maps to low severity."""
        findings = [make_finding(category="recommended")]
        result = json.loads(format_json(findings, 1))
        assert result["findings"][0]["severity"] == "low"

    def test_summary_structure(self, make_finding):
        """AC#2: Summary has total, by_category, files_checked."""
        findings = [
            make_finding(category="required"),
            make_finding(category="recommended"),
        ]
        result = json.loads(format_json(findings, 42))
        summary = result["summary"]
        assert summary["total"] == 2
        assert summary["by_category"]["required"] == 1
        assert summary["by_category"]["recommended"] == 1
        assert summary["files_checked"] == 42

    def test_empty_findings_produces_valid_json_with_zero_summary(self):
        """AC#6: Empty findings produces valid JSON with zero summary."""
        result = json.loads(format_json([], 5))
        assert result["findings"] == []
        assert result["summary"]["total"] == 0
        assert result["summary"]["by_category"]["required"] == 0
        assert result["summary"]["by_category"]["recommended"] == 0
        assert result["summary"]["files_checked"] == 5

    def test_findings_sorted_by_file_and_line(self, make_finding):
        """Findings are sorted by (file, line)."""
        findings = [
            make_finding(file="z.py", line=10),
            make_finding(file="a.py", line=5),
            make_finding(file="a.py", line=1),
        ]
        result = json.loads(format_json(findings, 3))
        files_lines = [(f["file"], f["line"]) for f in result["findings"]]
        assert files_lines == [("a.py", 1), ("a.py", 5), ("z.py", 10)]

    def test_round_trip_valid_json(self, make_finding):
        """Output is valid parseable JSON."""
        findings = [make_finding()]
        raw = format_json(findings, 1)
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
        assert "findings" in parsed
        assert "summary" in parsed

    def test_trailing_newline(self, make_finding):
        """Output ends with a trailing newline."""
        assert format_json([make_finding()], 1).endswith("\n")

    def test_field_values_preserved_exactly(self, make_finding):
        """All Finding field values are preserved in the JSON output."""
        finding = make_finding(
            file="src/app.py",
            line=42,
            symbol="my_func",
            rule="missing-raises",
            message="Function 'my_func' raises ValueError",
            category="required",
        )
        result = json.loads(format_json([finding], 1))
        f = result["findings"][0]
        assert f["file"] == "src/app.py"
        assert f["line"] == 42
        assert f["symbol"] == "my_func"
        assert f["rule"] == "missing-raises"
        assert f["message"] == "Function 'my_func' raises ValueError"
        assert f["category"] == "required"
        assert f["severity"] == "high"

    def test_unicode_preserved_in_message(self, make_finding):
        """Non-ASCII characters survive JSON round-trip via ensure_ascii=False."""
        finding = make_finding(message="Funci\u00f3n \u2018foo\u2019 raises ValueError")
        result = json.loads(format_json([finding], 1))
        assert (
            result["findings"][0]["message"]
            == "Funci\u00f3n \u2018foo\u2019 raises ValueError"
        )


class TestWriteReportJson:
    """Tests for write_report with JSON format."""

    def test_json_write(self, make_finding, tmp_path):
        """AC#1: Writes valid JSON to file."""
        findings = [make_finding(category="required")]
        output = tmp_path / "report.json"
        write_report(findings, output, fmt="json", file_count=10)
        content = output.read_text()
        parsed = json.loads(content)
        assert len(parsed["findings"]) == 1
        assert parsed["summary"]["files_checked"] == 10

    def test_json_write_empty_findings(self, tmp_path):
        """AC#6: Empty findings writes valid JSON with empty array."""
        output = tmp_path / "report.json"
        write_report([], output, fmt="json", file_count=5)
        content = output.read_text()
        parsed = json.loads(content)
        assert parsed["findings"] == []
        assert parsed["summary"]["total"] == 0


# ---------------------------------------------------------------------------
# determine_exit_code tests (Task 11)
# ---------------------------------------------------------------------------


class TestDetermineExitCode:
    """Tests for determine_exit_code."""

    def test_fail_on_check_with_findings_returns_1(self, make_finding):
        """AC#14: Returns 1 when fail_on check has findings."""
        findings_by_check = {"enrichment": [make_finding()], "freshness": []}
        config = DocvetConfig(fail_on=["enrichment"])
        assert determine_exit_code(findings_by_check, config) == 1

    def test_empty_fail_on_returns_0(self, make_finding):
        """AC#15: Returns 0 when fail_on is empty regardless of findings."""
        findings_by_check = {"enrichment": [make_finding()]}
        config = DocvetConfig(fail_on=[])
        assert determine_exit_code(findings_by_check, config) == 0

    def test_all_empty_findings_returns_0(self):
        """AC#16: Returns 0 when all findings lists are empty."""
        findings_by_check: dict[str, list[Finding]] = {
            "enrichment": [],
            "freshness": [],
        }
        config = DocvetConfig(fail_on=["enrichment", "freshness"])
        assert determine_exit_code(findings_by_check, config) == 0

    def test_findings_in_non_fail_on_returns_0(self, make_finding):
        """AC#17: Returns 0 when findings are in a non-fail_on check."""
        findings_by_check = {"freshness": [make_finding()]}
        config = DocvetConfig(fail_on=["enrichment"])
        assert determine_exit_code(findings_by_check, config) == 0

    def test_fail_on_with_missing_key_and_present_findings(self, make_finding):
        """AC#22: Returns 1 if any fail_on check has findings, missing keys don't matter."""
        findings_by_check = {"enrichment": [make_finding()]}
        config = DocvetConfig(fail_on=["enrichment", "freshness"])
        assert determine_exit_code(findings_by_check, config) == 1

    def test_fail_on_check_not_in_findings_returns_0(self):
        """fail_on check name not present in findings_by_check returns 0."""
        findings_by_check: dict[str, list[Finding]] = {}
        config = DocvetConfig(fail_on=["enrichment"])
        assert determine_exit_code(findings_by_check, config) == 0

    def test_empty_findings_dict_with_fail_on_returns_0(self):
        """Completely empty findings_by_check with non-empty fail_on returns 0."""
        findings_by_check: dict[str, list[Finding]] = {}
        config = DocvetConfig(fail_on=["enrichment", "freshness"])
        assert determine_exit_code(findings_by_check, config) == 0


# ---------------------------------------------------------------------------
# format_summary tests (Story 21.1, Task 1)
# ---------------------------------------------------------------------------


class TestFormatSummary:
    """Tests for format_summary."""

    def test_zero_findings(self):
        """Zero findings produces 'no findings' summary with em dash."""
        result = format_summary(
            file_count=12,
            checks=["enrichment", "freshness", "coverage"],
            findings=[],
            elapsed=1.5,
        )
        assert result == (
            "Vetted 12 files [enrichment, freshness, coverage]"
            " \u2014 no findings. (1.5s)\n"
        )

    def test_mixed_findings(self, make_finding):
        """Mixed required/recommended findings include count breakdown."""
        findings = [
            make_finding(category="required"),
            make_finding(line=2, category="required"),
            make_finding(line=3, category="recommended"),
        ]
        result = format_summary(
            file_count=5,
            checks=["enrichment", "freshness"],
            findings=findings,
            elapsed=2.3,
        )
        assert result == (
            "Vetted 5 files [enrichment, freshness]"
            " \u2014 3 findings (2 required, 1 recommended). (2.3s)\n"
        )

    def test_zero_files(self):
        """Zero files still produces valid summary."""
        result = format_summary(
            file_count=0,
            checks=["enrichment", "freshness", "coverage"],
            findings=[],
            elapsed=0.0,
        )
        assert result == (
            "Vetted 0 files [enrichment, freshness, coverage]"
            " \u2014 no findings. (0.0s)\n"
        )

    def test_single_check(self):
        """Single check in the list."""
        result = format_summary(
            file_count=1,
            checks=["enrichment"],
            findings=[],
            elapsed=0.1,
        )
        assert result == "Vetted 1 files [enrichment] \u2014 no findings. (0.1s)\n"

    def test_all_checks(self, make_finding):
        """All four checks listed."""
        findings = [make_finding(category="recommended")]
        result = format_summary(
            file_count=42,
            checks=["enrichment", "freshness", "coverage", "griffe"],
            findings=findings,
            elapsed=3.7,
        )
        assert result == (
            "Vetted 42 files [enrichment, freshness, coverage, griffe]"
            " \u2014 1 findings (0 required, 1 recommended). (3.7s)\n"
        )

    def test_em_dash_character(self):
        """Uses U+2014 em dash, not hyphen or en dash."""
        result = format_summary(
            file_count=1, checks=["enrichment"], findings=[], elapsed=0.1
        )
        assert "\u2014" in result
        # Ensure no plain hyphen between ']' and 'no'
        assert "] -" not in result
        assert "] \u2013" not in result  # no en dash either

    def test_trailing_newline(self):
        """Output ends with exactly one trailing newline."""
        result = format_summary(
            file_count=1, checks=["enrichment"], findings=[], elapsed=0.1
        )
        assert result.endswith("\n")
        assert not result.endswith("\n\n")

    def test_elapsed_one_decimal(self):
        """Elapsed time is formatted to one decimal place."""
        result = format_summary(
            file_count=1, checks=["enrichment"], findings=[], elapsed=1.456
        )
        assert "(1.5s)" in result

    def test_only_required_findings(self, make_finding):
        """All-required findings show 0 recommended."""
        findings = [make_finding(category="required")]
        result = format_summary(
            file_count=1, checks=["enrichment"], findings=findings, elapsed=0.1
        )
        assert "1 findings (1 required, 0 recommended)" in result


# ---------------------------------------------------------------------------
# Presence-related reporting tests (Story 28.2)
# ---------------------------------------------------------------------------


class TestFormatSummaryWithCoverage:
    """Tests for format_summary coverage_pct parameter."""

    def test_coverage_pct_appended_when_provided(self, make_finding):
        """10.17: Summary line includes 'X.X% coverage' when presence runs."""
        result = format_summary(
            10, ["presence", "enrichment"], [], 1.0, coverage_pct=96.0
        )
        assert "96.0% coverage" in result
        assert "no findings, 96.0% coverage" in result

    def test_coverage_pct_with_findings(self, make_finding):
        """10.17: Summary with findings includes coverage."""
        findings = [make_finding()]
        result = format_summary(
            10, ["presence", "enrichment"], findings, 1.0, coverage_pct=87.0
        )
        assert "87.0% coverage" in result
        assert "1 findings" in result

    def test_no_coverage_when_none(self):
        """10.18: No coverage when coverage_pct is None."""
        result = format_summary(10, ["enrichment"], [], 1.0)
        assert "coverage" not in result


class TestFormatJsonWithPresence:
    """Tests for format_json presence_stats parameter."""

    def test_includes_presence_coverage_object(self, make_finding):
        """10.14: JSON includes presence_coverage object with all 5 fields."""
        from docvet.checks.presence import PresenceStats

        stats = PresenceStats(documented=87, total=100)
        result = format_json(
            [make_finding()], 10, presence_stats=stats, min_coverage=95.0
        )
        parsed = json.loads(result)
        cov = parsed["presence_coverage"]
        assert cov["documented"] == 87
        assert cov["total"] == 100
        assert cov["percentage"] == 87.0
        assert cov["threshold"] == 95.0
        assert cov["passed"] is False

    def test_presence_coverage_passed_true_when_above(self):
        """10.15: presence_coverage.passed reflects threshold comparison."""
        from docvet.checks.presence import PresenceStats

        stats = PresenceStats(documented=96, total=100)
        result = format_json([], 10, presence_stats=stats, min_coverage=95.0)
        parsed = json.loads(result)
        assert parsed["presence_coverage"]["passed"] is True

    def test_omits_presence_coverage_when_no_stats(self):
        """10.16: JSON omits presence_coverage when no presence stats."""
        result = format_json([], 10)
        parsed = json.loads(result)
        assert "presence_coverage" not in parsed

    def test_presence_coverage_present_with_zero_findings_and_full_coverage(self):
        """10.27: presence_coverage present even when 0 findings and 100%."""
        from docvet.checks.presence import PresenceStats

        stats = PresenceStats(documented=100, total=100)
        result = format_json([], 10, presence_stats=stats, min_coverage=0.0)
        parsed = json.loads(result)
        assert "presence_coverage" in parsed
        assert parsed["presence_coverage"]["percentage"] == 100.0
        assert parsed["presence_coverage"]["passed"] is True


class TestDetermineExitCodeWithPresence:
    """Tests for determine_exit_code with presence_stats."""

    def test_returns_1_when_coverage_below_threshold(self):
        """10.21: Returns 1 when coverage below threshold."""
        from docvet.checks.presence import PresenceStats

        config = DocvetConfig(presence=PresenceConfig(min_coverage=95.0))
        stats = PresenceStats(documented=87, total=100)
        result = determine_exit_code({}, config, presence_stats=stats)
        assert result == 1

    def test_returns_0_when_coverage_meets_threshold(self):
        """10.22: Returns 0 when coverage meets threshold."""
        from docvet.checks.presence import PresenceStats

        config = DocvetConfig(presence=PresenceConfig(min_coverage=95.0))
        stats = PresenceStats(documented=96, total=100)
        result = determine_exit_code({}, config, presence_stats=stats)
        assert result == 0

    def test_returns_0_when_coverage_exactly_at_threshold(self):
        """Boundary: coverage == threshold passes (uses < not <=)."""
        from docvet.checks.presence import PresenceStats

        config = DocvetConfig(presence=PresenceConfig(min_coverage=95.0))
        stats = PresenceStats(documented=95, total=100)
        result = determine_exit_code({}, config, presence_stats=stats)
        assert result == 0

    def test_returns_1_when_coverage_just_below_threshold(self):
        """Boundary: coverage just below threshold fails."""
        from docvet.checks.presence import PresenceStats

        config = DocvetConfig(presence=PresenceConfig(min_coverage=95.0))
        stats = PresenceStats(documented=94, total=100)
        result = determine_exit_code({}, config, presence_stats=stats)
        assert result == 1

    def test_returns_0_when_no_threshold(self):
        """No threshold (0.0) means coverage is not enforced."""
        from docvet.checks.presence import PresenceStats

        config = DocvetConfig()
        stats = PresenceStats(documented=10, total=100)
        result = determine_exit_code({}, config, presence_stats=stats)
        assert result == 0

    def test_returns_0_when_no_stats(self):
        """No stats means presence was not run."""
        config = DocvetConfig(presence=PresenceConfig(min_coverage=95.0))
        result = determine_exit_code({}, config)
        assert result == 0


# ---------------------------------------------------------------------------
# compute_quality tests (Task 3 / AC 5, 6)
# ---------------------------------------------------------------------------


class TestComputeQuality:
    """Tests for compute_quality."""

    def test_zero_findings_all_100(self):
        """All checks with zero findings produce 100%."""
        findings_by_check: dict[str, list[Finding]] = {
            "enrichment": [],
            "freshness": [],
            "coverage": [],
            "griffe": [],
        }
        check_counts = {
            "enrichment": 200,
            "freshness": 200,
            "coverage": 12,
            "griffe": 15,
        }
        result = compute_quality(findings_by_check, check_counts)
        assert len(result) == 4
        for cq in result.values():
            assert cq.percentage == 100
            assert cq.items_with_findings == 0

    def test_mixed_findings(self, make_finding):
        """Enrichment with findings produces correct percentage."""
        findings_by_check = {
            "enrichment": [
                make_finding(file="a.py", symbol="foo", rule="missing-raises"),
                make_finding(file="a.py", symbol="foo", rule="missing-yields"),
                make_finding(file="b.py", symbol="bar", rule="missing-raises"),
            ],
        }
        check_counts = {"enrichment": 50}
        result = compute_quality(findings_by_check, check_counts)
        assert result["enrichment"].items_checked == 50
        assert result["enrichment"].items_with_findings == 2  # unique (file, symbol)
        assert result["enrichment"].percentage == 96  # round((50-2)/50*100)
        assert result["enrichment"].unit == "symbols"

    def test_single_check_only(self, make_finding):
        """Only checks present in findings_by_check appear in result."""
        findings_by_check = {"coverage": [make_finding(file="pkg/")]}
        check_counts = {"coverage": 10}
        result = compute_quality(findings_by_check, check_counts)
        assert "coverage" in result
        assert "enrichment" not in result

    def test_zero_items_edge_case(self):
        """Zero items checked produces 100%."""
        findings_by_check: dict[str, list[Finding]] = {"enrichment": []}
        check_counts = {"enrichment": 0}
        result = compute_quality(findings_by_check, check_counts)
        assert result["enrichment"].percentage == 100
        assert result["enrichment"].items_checked == 0

    def test_enrichment_deduplicates_by_file_symbol(self, make_finding):
        """Same (file, symbol) with multiple findings counts as 1."""
        findings_by_check = {
            "enrichment": [
                make_finding(file="a.py", symbol="f", rule="missing-raises"),
                make_finding(file="a.py", symbol="f", rule="missing-yields"),
                make_finding(file="a.py", symbol="f", rule="missing-examples"),
            ],
        }
        check_counts = {"enrichment": 10}
        result = compute_quality(findings_by_check, check_counts)
        assert result["enrichment"].items_with_findings == 1

    def test_freshness_uses_symbols_unit(self, make_finding):
        """Freshness check uses 'symbols' as unit."""
        findings_by_check = {
            "freshness": [make_finding(file="a.py", symbol="f")],
        }
        check_counts = {"freshness": 20}
        result = compute_quality(findings_by_check, check_counts)
        assert result["freshness"].unit == "symbols"
        assert result["freshness"].items_with_findings == 1

    def test_coverage_uses_packages_unit(self, make_finding):
        """Coverage check uses 'packages' as unit."""
        findings_by_check = {
            "coverage": [
                make_finding(file="pkg1/"),
                make_finding(file="pkg2/"),
            ],
        }
        check_counts = {"coverage": 5}
        result = compute_quality(findings_by_check, check_counts)
        assert result["coverage"].unit == "packages"
        assert result["coverage"].items_with_findings == 2

    def test_griffe_uses_files_unit(self, make_finding):
        """Griffe check uses 'files' as unit."""
        findings_by_check = {
            "griffe": [make_finding(file="a.py"), make_finding(file="a.py")],
        }
        check_counts = {"griffe": 10}
        result = compute_quality(findings_by_check, check_counts)
        assert result["griffe"].unit == "files"
        assert result["griffe"].items_with_findings == 1  # unique files

    def test_coverage_zero_directories(self):
        """Coverage with zero directories produces 100%."""
        findings_by_check: dict[str, list[Finding]] = {"coverage": []}
        check_counts = {"coverage": 0}
        result = compute_quality(findings_by_check, check_counts)
        assert result["coverage"].percentage == 100

    def test_all_checks_combined(self, make_finding):
        """All four checks produce correct results together."""
        findings_by_check = {
            "enrichment": [make_finding(file="a.py", symbol="f")],
            "freshness": [],
            "coverage": [make_finding(file="pkg/")],
            "griffe": [make_finding(file="x.py")],
        }
        check_counts = {
            "enrichment": 100,
            "freshness": 100,
            "coverage": 10,
            "griffe": 20,
        }
        result = compute_quality(findings_by_check, check_counts)
        assert result["enrichment"].percentage == 99
        assert result["freshness"].percentage == 100
        assert result["coverage"].percentage == 90
        assert result["griffe"].percentage == 95


# ---------------------------------------------------------------------------
# format_quality_summary tests (Task 4 / AC 1, 3, 4)
# ---------------------------------------------------------------------------


class TestFormatQualitySummary:
    """Tests for format_quality_summary."""

    def test_single_check_format(self):
        """Single check produces one-line output."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=200, items_with_findings=8, percentage=96, unit="symbols"
            ),
        }
        result = format_quality_summary(quality)
        assert "enrichment" in result
        assert "96%" in result
        assert "8 findings" in result

    def test_only_ran_checks_appear(self):
        """Only checks present in quality dict appear."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=50, items_with_findings=0, percentage=100, unit="symbols"
            ),
        }
        result = format_quality_summary(quality)
        assert "enrichment" in result
        assert "freshness" not in result
        assert "coverage" not in result

    def test_multiple_checks_output(self):
        """Multiple checks each get their own line."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=100, items_with_findings=5, percentage=95, unit="symbols"
            ),
            "freshness": CheckQuality(
                items_checked=100, items_with_findings=0, percentage=100, unit="symbols"
            ),
            "coverage": CheckQuality(
                items_checked=10, items_with_findings=1, percentage=90, unit="packages"
            ),
        }
        result = format_quality_summary(quality)
        lines = [line for line in result.strip().splitlines() if line.strip()]
        assert len(lines) == 3

    def test_100_percent_shows_zero_findings(self):
        """100% check shows 0 findings."""
        quality = {
            "freshness": CheckQuality(
                items_checked=50, items_with_findings=0, percentage=100, unit="symbols"
            ),
        }
        result = format_quality_summary(quality)
        assert "100%" in result
        assert "0 findings" in result

    def test_trailing_newline(self):
        """Output ends with a newline."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=10, items_with_findings=0, percentage=100, unit="symbols"
            ),
        }
        result = format_quality_summary(quality)
        assert result.endswith("\n")


# ---------------------------------------------------------------------------
# format_json with quality tests (Task 5 / AC 2)
# ---------------------------------------------------------------------------


class TestFormatJsonQuality:
    """Tests for format_json with quality parameter."""

    def test_quality_key_present_when_provided(self, make_finding):
        """Quality object appears in JSON when quality dict is provided."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=200, items_with_findings=8, percentage=96, unit="symbols"
            ),
        }
        result = json.loads(format_json([], 10, quality=quality))
        assert "quality" in result
        assert result["quality"]["enrichment"]["items_checked"] == 200
        assert result["quality"]["enrichment"]["items_with_findings"] == 8
        assert result["quality"]["enrichment"]["percentage"] == 96
        assert result["quality"]["enrichment"]["unit"] == "symbols"

    def test_quality_key_absent_when_none(self):
        """No quality key in JSON when quality is not provided."""
        result = json.loads(format_json([], 10))
        assert "quality" not in result

    def test_existing_summary_unchanged(self, make_finding):
        """Existing summary object is not modified by quality."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=50, items_with_findings=1, percentage=98, unit="symbols"
            ),
        }
        findings = [make_finding(category="required")]
        result = json.loads(format_json(findings, 5, quality=quality))
        assert result["summary"]["total"] == 1
        assert result["summary"]["files_checked"] == 5
        assert "quality" in result

    def test_multiple_checks_in_quality(self):
        """Multiple checks appear in quality object."""
        quality = {
            "enrichment": CheckQuality(
                items_checked=100, items_with_findings=2, percentage=98, unit="symbols"
            ),
            "coverage": CheckQuality(
                items_checked=10, items_with_findings=1, percentage=90, unit="packages"
            ),
        }
        result = json.loads(format_json([], 10, quality=quality))
        assert "enrichment" in result["quality"]
        assert "coverage" in result["quality"]

    def test_backward_compat_no_quality_without_flag(self):
        """Without quality param, JSON output is identical to existing."""
        result = json.loads(format_json([], 10))
        assert set(result.keys()) == {"findings", "summary"}
