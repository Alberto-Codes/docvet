"""Regression tests for complete suppression directive grammar."""

from __future__ import annotations

import pytest

from docvet.checks import Finding
from docvet.cli._suppression import filter_findings, parse_suppression_directives

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("kind", ["ignore", "ignore-file"])
@pytest.mark.parametrize(
    "suffix",
    [
        "[missing-raises",
        "d",
        "-next-line",
        "]",
        "[missing-raises]]",
        "[[missing-raises]",
        "[missing-raises][missing-returns]",
        " [missing-raises",
        " [missing-raises]",
        "[missing-raises] ]",
    ],
)
def test_malformed_directive_warns_and_suppresses_nothing(kind, suffix, capsys):
    """Malformed directives cannot degrade into broader suppression."""
    source = f"def foo():  # docvet: {kind}{suffix}\n    pass\n"
    findings = [Finding("test.py", 1, "foo", "missing-raises", "msg", "required")]
    parsed = parse_suppression_directives(source, "test.py")
    assert filter_findings(findings, "test.py", parsed) == (findings, [])
    assert "warning: test.py:1:" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["ignore", "ignore-file"])
@pytest.mark.parametrize(
    "rules", ["", "[missing-raises]", "[missing-raises,missing-returns]"]
)
@pytest.mark.parametrize(
    "suffix", ["", "  ", " # intentional", " -- intentional", " because intentional"]
)
def test_valid_directive_preserves_rule_and_line_scope(kind, rules, suffix, capsys):
    """Valid bare forms, rule lists, and explanations retain exact scope."""
    source = f"def foo():  # docvet: {kind}{rules}{suffix}\n    pass\n"
    findings = [
        Finding("test.py", line, "foo", rule, "msg", "required")
        for line in (1, 3)
        for rule in ("missing-raises", "missing-returns", "missing-examples")
    ]
    expected = [
        f
        for f in findings
        if (kind == "ignore-file" or f.line == 1) and (not rules or f.rule in rules)
    ]
    parsed = parse_suppression_directives(source, "test.py")
    active, suppressed = filter_findings(findings, "test.py", parsed)
    assert suppressed == expected
    assert active == [f for f in findings if f not in expected]
    assert capsys.readouterr().err == ""
