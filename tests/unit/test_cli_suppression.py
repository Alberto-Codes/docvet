"""Unit tests for the suppression comment parser and finding filter.

Tests cover:
- ``parse_suppression_directives``: all syntax variants, edge cases
- ``filter_findings``: line-level, file-level, blanket, mixed
- Invalid rule warnings
- Negative cases: comments in strings, decorator lines, no-op suppressions

See Also:
    [`docvet.cli._suppression`][]: Suppression parsing and filtering.
"""

from __future__ import annotations

from typing import Literal

import pytest

from docvet.checks import Finding

pytestmark = pytest.mark.unit

_Category = Literal["required", "recommended", "scaffold"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _finding(
    file: str = "test.py",
    line: int = 1,
    symbol: str = "foo",
    rule: str = "missing-raises",
    message: str = "msg",
    category: _Category = "required",
) -> Finding:
    """Create a test finding with defaults."""
    return Finding(file, line, symbol, rule, message, category)


# ---------------------------------------------------------------------------
# parse_suppression_directives tests
# ---------------------------------------------------------------------------


class TestParseSuppressionDirectives:
    """Tests for parse_suppression_directives."""

    def test_line_level_single_rule(self) -> None:
        """Parse a single-rule suppression on a def line."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "def foo():  # docvet: ignore[missing-raises]\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert 1 in result.line_directives
        assert result.line_directives[1] == {"missing-raises"}

    def test_line_level_multi_rule(self) -> None:
        """Parse comma-separated rules on a def line."""
        from docvet.cli._suppression import parse_suppression_directives

        source = (
            "def foo():  # docvet: ignore[missing-raises,missing-returns]\n    pass\n"
        )
        result = parse_suppression_directives(source, "test.py")

        assert result.line_directives[1] == {"missing-raises", "missing-returns"}

    def test_line_level_blanket(self) -> None:
        """Parse blanket suppression (no rules specified)."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "def foo():  # docvet: ignore\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert 1 in result.line_directives
        assert result.line_directives[1] is None  # None = blanket

    def test_file_level_single_rule(self) -> None:
        """Parse file-level suppression for a single rule."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "# docvet: ignore-file[missing-examples]\ndef foo():\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert result.file_rules == {"missing-examples"}

    def test_file_level_multi_rule(self) -> None:
        """Parse file-level suppression for comma-separated rules."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "# docvet: ignore-file[missing-examples,missing-raises]\ndef foo():\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert result.file_rules == {"missing-examples", "missing-raises"}

    def test_file_level_blanket(self) -> None:
        """Parse blanket file-level suppression."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "# docvet: ignore-file\ndef foo():\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert result.file_blanket is True

    @pytest.mark.parametrize(
        ("comment", "expected_rules"),
        [
            ("# docvet: ignore[missing-raises]", {"missing-raises"}),
            ("#docvet:ignore[missing-raises]", {"missing-raises"}),
            ("#  docvet:  ignore[missing-raises]", {"missing-raises"}),
            ("# docvet:ignore[ missing-raises ]", {"missing-raises"}),
            (
                "# docvet: ignore[missing-raises, missing-returns]",
                {"missing-raises", "missing-returns"},
            ),
        ],
        ids=[
            "standard",
            "no-space",
            "extra-spaces",
            "spaces-in-brackets",
            "spaces-after-comma",
        ],
    )
    def test_whitespace_variations(
        self, comment: str, expected_rules: set[str]
    ) -> None:
        """Whitespace variations are handled correctly."""
        from docvet.cli._suppression import parse_suppression_directives

        source = f"def foo():  {comment}\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert result.line_directives[1] == expected_rules

    def test_comment_inside_string_not_parsed(self) -> None:
        """Comments inside string literals are not treated as suppressions."""
        from docvet.cli._suppression import parse_suppression_directives

        source = 'x = "# docvet: ignore[missing-raises]"\ndef foo():\n    pass\n'
        result = parse_suppression_directives(source, "test.py")

        assert not result.line_directives
        assert not result.file_rules
        assert result.file_blanket is False

    def test_empty_source(self) -> None:
        """Empty source returns empty suppression map."""
        from docvet.cli._suppression import parse_suppression_directives

        result = parse_suppression_directives("", "test.py")

        assert not result.line_directives
        assert not result.file_rules
        assert result.file_blanket is False

    def test_no_suppression_comments(self) -> None:
        """Source with no suppression comments returns empty map."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "def foo():\n    # regular comment\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert not result.line_directives
        assert not result.file_rules
        assert result.file_blanket is False

    def test_invalid_rule_emits_warning(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Invalid rule IDs emit a warning to stderr."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "def foo():  # docvet: ignore[nonexistent-rule]\n    pass\n"
        parse_suppression_directives(source, "test.py")

        captured = capsys.readouterr()
        assert "nonexistent-rule" in captured.err
        assert "test.py" in captured.err

    def test_invalid_rule_still_applied(self) -> None:
        """Invalid rule IDs are still added to the suppression map (fail-safe)."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "def foo():  # docvet: ignore[nonexistent-rule]\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        assert result.line_directives[1] == {"nonexistent-rule"}

    def test_multiple_symbols_different_suppressions(self) -> None:
        """Multiple symbols can have independent line-level suppressions."""
        from docvet.cli._suppression import parse_suppression_directives

        source = (
            "def foo():  # docvet: ignore[missing-raises]\n"
            "    pass\n"
            "\n"
            "def bar():  # docvet: ignore[missing-returns]\n"
            "    pass\n"
        )
        result = parse_suppression_directives(source, "test.py")

        assert result.line_directives[1] == {"missing-raises"}
        assert result.line_directives[4] == {"missing-returns"}

    def test_file_level_and_line_level_coexist(self) -> None:
        """File-level and line-level suppressions coexist in same file."""
        from docvet.cli._suppression import parse_suppression_directives

        source = (
            "# docvet: ignore-file[missing-examples]\n"
            "def foo():  # docvet: ignore[missing-raises]\n"
            "    pass\n"
        )
        result = parse_suppression_directives(source, "test.py")

        assert result.file_rules == {"missing-examples"}
        assert result.line_directives[2] == {"missing-raises"}


# ---------------------------------------------------------------------------
# filter_findings tests
# ---------------------------------------------------------------------------


class TestFilterFindings:
    """Tests for filter_findings."""

    def test_line_level_single_rule_suppression(self) -> None:
        """Finding matching line-level single rule is suppressed (AC 1)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [_finding(line=1, rule="missing-raises")]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises"}},
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 0
        assert len(suppressed) == 1
        assert suppressed[0].rule == "missing-raises"

    def test_line_level_only_suppresses_matching_rule(self) -> None:
        """Line-level suppression only suppresses the specified rule (AC 1)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [
            _finding(line=1, rule="missing-raises"),
            _finding(line=1, rule="missing-returns"),
        ]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises"}},
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 1
        assert active[0].rule == "missing-returns"
        assert len(suppressed) == 1
        assert suppressed[0].rule == "missing-raises"

    def test_line_level_multi_rule_suppression(self) -> None:
        """Multiple rules on one line are all suppressed (AC 2)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [
            _finding(line=1, rule="missing-raises"),
            _finding(line=1, rule="missing-returns"),
            _finding(line=1, rule="missing-examples"),
        ]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises", "missing-returns"}},
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 1
        assert active[0].rule == "missing-examples"
        assert len(suppressed) == 2

    def test_line_level_blanket_suppression(self) -> None:
        """Blanket suppression suppresses all findings on that line (AC 3)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [
            _finding(line=1, rule="missing-raises"),
            _finding(line=1, rule="missing-returns"),
        ]
        suppression = SuppressionMap(
            line_directives={1: None},  # None = blanket
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 0
        assert len(suppressed) == 2

    def test_file_level_single_rule_suppression(self) -> None:
        """File-level suppression suppresses a rule across the file (AC 4)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [
            _finding(line=1, rule="missing-examples"),
            _finding(line=10, rule="missing-examples"),
            _finding(line=5, rule="missing-raises"),
        ]
        suppression = SuppressionMap(
            line_directives={},
            file_rules={"missing-examples"},
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 1
        assert active[0].rule == "missing-raises"
        assert len(suppressed) == 2

    def test_file_level_blanket_suppression(self) -> None:
        """File-level blanket suppresses all findings in file (AC 5)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [
            _finding(line=1, rule="missing-raises"),
            _finding(line=10, rule="missing-examples"),
        ]
        suppression = SuppressionMap(
            line_directives={},
            file_rules=set(),
            file_blanket=True,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 0
        assert len(suppressed) == 2

    def test_no_suppression_all_active(self) -> None:
        """With no suppressions, all findings are active."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [_finding(line=1), _finding(line=5)]
        suppression = SuppressionMap(
            line_directives={},
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 2
        assert len(suppressed) == 0

    def test_empty_findings(self) -> None:
        """Empty findings list returns empty tuples."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        suppression = SuppressionMap(
            line_directives={1: None},
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings([], "test.py", suppression)

        assert active == []
        assert suppressed == []

    def test_suppression_on_different_line_not_matched(self) -> None:
        """Suppression on a different line does not match."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [_finding(line=5, rule="missing-raises")]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises"}},
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 1
        assert len(suppressed) == 0

    def test_file_level_plus_line_level_combined(self) -> None:
        """File-level and line-level suppressions work together."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [
            _finding(line=1, rule="missing-examples"),  # file-level suppressed
            _finding(line=1, rule="missing-raises"),  # line-level suppressed
            _finding(line=1, rule="missing-returns"),  # active
        ]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises"}},
            file_rules={"missing-examples"},
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 1
        assert active[0].rule == "missing-returns"
        assert len(suppressed) == 2

    def test_suppression_is_post_filter(self) -> None:
        """Suppression does not modify Finding objects — just partitions them (AC 7)."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        original = _finding(line=1, rule="missing-raises")
        findings = [original]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises"}},
            file_rules=set(),
            file_blanket=False,
        )
        _active, suppressed = filter_findings(findings, "test.py", suppression)

        assert suppressed[0] is original  # Same object, not modified


# ---------------------------------------------------------------------------
# Negative tests (Task 5.4)
# ---------------------------------------------------------------------------


class TestNegativeCases:
    """Negative tests for suppression edge cases."""

    def test_decorator_line_comment_not_matched(self) -> None:
        """Comment on decorator line does NOT suppress the decorated symbol."""
        from docvet.cli._suppression import parse_suppression_directives

        source = (
            "@abstractmethod  # docvet: ignore[missing-raises]\ndef foo():\n    pass\n"
        )
        result = parse_suppression_directives(source, "test.py")

        # The directive is on line 1 (decorator), but def is line 2.
        # Line 1 has the directive, but findings for foo are on line 2.
        assert 1 in result.line_directives
        assert 2 not in result.line_directives

    def test_decorator_suppression_does_not_match_def(self) -> None:
        """Finding on def line is NOT suppressed by decorator-line comment."""
        from docvet.cli._suppression import SuppressionMap, filter_findings

        findings = [_finding(line=2, rule="missing-raises")]
        suppression = SuppressionMap(
            line_directives={1: {"missing-raises"}},  # On decorator, not def
            file_rules=set(),
            file_blanket=False,
        )
        active, suppressed = filter_findings(findings, "test.py", suppression)

        assert len(active) == 1
        assert len(suppressed) == 0

    def test_suppression_on_symbol_with_no_findings_is_silent(self) -> None:
        """Suppression on a symbol with no findings produces no errors."""
        from docvet.cli._suppression import parse_suppression_directives

        source = "def foo():  # docvet: ignore[missing-raises]\n    pass\n"
        result = parse_suppression_directives(source, "test.py")

        # Just verify it parses cleanly — no findings to filter.
        assert 1 in result.line_directives

    def test_comment_in_multiline_string_not_parsed(self) -> None:
        """Comments inside triple-quoted strings are not parsed."""
        from docvet.cli._suppression import parse_suppression_directives

        source = (
            'x = """\n# docvet: ignore[missing-raises]\n"""\ndef foo():\n    pass\n'
        )
        result = parse_suppression_directives(source, "test.py")

        assert not result.line_directives


# ---------------------------------------------------------------------------
# _apply_suppressions integration (Task 5.5)
# ---------------------------------------------------------------------------


class TestApplySuppressions:
    """Tests for _apply_suppressions in the output pipeline."""

    def test_apply_suppressions_with_real_file(self, tmp_path: object) -> None:
        """End-to-end: findings are filtered based on source file comments."""
        import pathlib

        from docvet.cli._output import _apply_suppressions

        p = pathlib.Path(str(tmp_path)) / "test.py"
        p.write_text(
            "def foo():  # docvet: ignore[missing-raises]\n    pass\n",
            encoding="utf-8",
        )

        findings_by_check = {
            "enrichment": [
                _finding(file=str(p), line=1, rule="missing-raises"),
                _finding(file=str(p), line=1, rule="missing-returns"),
            ]
        }
        active, suppressed = _apply_suppressions(findings_by_check)

        assert len(active["enrichment"]) == 1
        assert active["enrichment"][0].rule == "missing-returns"
        assert len(suppressed) == 1
        assert suppressed[0].rule == "missing-raises"

    def test_apply_suppressions_missing_file_returns_all_active(self) -> None:
        """Findings for non-existent files are all treated as active."""
        from docvet.cli._output import _apply_suppressions

        findings_by_check = {
            "enrichment": [_finding(file="/nonexistent/test.py", line=1)],
        }
        active, suppressed = _apply_suppressions(findings_by_check)

        assert len(active["enrichment"]) == 1
        assert len(suppressed) == 0

    def test_apply_suppressions_file_level_blanket(self, tmp_path: object) -> None:
        """File-level blanket suppresses all findings in file."""
        import pathlib

        from docvet.cli._output import _apply_suppressions

        p = pathlib.Path(str(tmp_path)) / "test.py"
        p.write_text(
            "# docvet: ignore-file\ndef foo():\n    pass\n",
            encoding="utf-8",
        )

        findings_by_check = {
            "enrichment": [
                _finding(file=str(p), line=2, rule="missing-raises"),
                _finding(file=str(p), line=2, rule="missing-returns"),
            ]
        }
        active, suppressed = _apply_suppressions(findings_by_check)

        assert len(active["enrichment"]) == 0
        assert len(suppressed) == 2


# ---------------------------------------------------------------------------
# JSON suppressed array (Task 5.7 partial)
# ---------------------------------------------------------------------------


class TestJsonSuppressedArray:
    """Tests for JSON output suppressed array."""

    def test_json_includes_suppressed_array(self) -> None:
        """JSON format includes a suppressed array when suppressed findings exist (AC 10)."""
        import json

        from docvet.reporting import format_json

        findings = [_finding(line=1, rule="missing-returns")]
        suppressed = [_finding(line=5, rule="missing-raises")]

        output = format_json(findings, 10, suppressed=suppressed)
        data = json.loads(output)

        assert "suppressed" in data
        assert len(data["suppressed"]) == 1
        assert data["suppressed"][0]["rule"] == "missing-raises"

    def test_json_no_suppressed_key_when_none(self) -> None:
        """JSON format omits suppressed key when suppressed is None."""
        import json

        from docvet.reporting import format_json

        output = format_json([], 10)
        data = json.loads(output)

        assert "suppressed" not in data

    def test_json_empty_suppressed_array(self) -> None:
        """JSON format includes empty suppressed array when passed empty list."""
        import json

        from docvet.reporting import format_json

        output = format_json([], 10, suppressed=[])
        data = json.loads(output)

        assert "suppressed" in data
        assert data["suppressed"] == []
