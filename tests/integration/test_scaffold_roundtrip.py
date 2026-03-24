"""Integration tests for the scaffold roundtrip workflow."""

from __future__ import annotations

import ast
import json
import textwrap

import pytest

from docvet.checks import Finding, check_enrichment, scaffold_missing_sections
from docvet.config import EnrichmentConfig
from docvet.reporting import format_json

pytestmark = pytest.mark.integration


def _enrich(source: str, *, config: EnrichmentConfig | None = None) -> list[Finding]:
    tree = ast.parse(source)
    return check_enrichment(source, tree, config or EnrichmentConfig(), "test.py")


def _scaffold(source: str, findings: list[Finding]) -> str:
    tree = ast.parse(source)
    return scaffold_missing_sections(source, tree, findings)


# ---------------------------------------------------------------------------
# AC 9: Enrichment → scaffold → re-check shows scaffold-incomplete
# ---------------------------------------------------------------------------


class TestEnrichmentToScaffoldRoundtrip:
    """Enrichment finds missing-* → scaffold inserts → re-check finds scaffold-incomplete."""

    def test_missing_raises_becomes_scaffold_incomplete(self):
        """missing-raises replaced by scaffold-incomplete after scaffolding."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate input data.

                Args:
                    data: The input.
                """
                if not data:
                    raise ValueError("empty")
        ''')
        # Step 1: enrichment finds missing-raises
        findings = _enrich(source)
        raises_findings = [f for f in findings if f.rule == "missing-raises"]
        assert len(raises_findings) >= 1

        # Step 2: scaffold inserts Raises section
        scaffolded = _scaffold(source, raises_findings)
        assert "Raises:" in scaffolded
        assert "ValueError: [TODO: describe when this is raised]" in scaffolded

        # Step 3: re-check — missing-raises gone, scaffold-incomplete present
        new_findings = _enrich(scaffolded)
        new_raises = [f for f in new_findings if f.rule == "missing-raises"]
        scaffold_findings = [f for f in new_findings if f.rule == "scaffold-incomplete"]
        assert len(new_raises) == 0
        assert len(scaffold_findings) >= 1
        assert scaffold_findings[0].category == "scaffold"

    def test_complete_roundtrip_zero_findings(self):
        """After filling placeholders, enrichment produces zero findings."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate input data.

                Args:
                    data: The input.
                """
                if not data:
                    raise ValueError("empty")
        ''')
        # Step 1: scaffold
        findings = _enrich(source)
        scaffolded = _scaffold(
            source, [f for f in findings if f.rule == "missing-raises"]
        )

        # Step 2: fill in the placeholder
        filled = scaffolded.replace(
            "[TODO: describe when this is raised]",
            "When the input data is empty or None.",
        )

        # Step 3: re-check — zero findings for this symbol
        new_findings = _enrich(filled)
        scaffold_findings = [f for f in new_findings if f.rule == "scaffold-incomplete"]
        assert len(scaffold_findings) == 0


# ---------------------------------------------------------------------------
# AC 10: scaffold-incomplete findings have correct category/rule/message
# ---------------------------------------------------------------------------


class TestScaffoldFindingFormat:
    """Scaffold findings have correct category, rule, and message format."""

    def test_scaffold_finding_attributes(self):
        """Scaffold finding has category=scaffold, rule=scaffold-incomplete."""
        source = textwrap.dedent('''\
            def f():
                """Do stuff.

                Raises:
                    ValueError: [TODO: describe when this is raised]
                """
                raise ValueError("x")
        ''')
        findings = _enrich(source)
        scaffold = [f for f in findings if f.rule == "scaffold-incomplete"]
        assert len(scaffold) == 1
        assert scaffold[0].category == "scaffold"
        assert scaffold[0].rule == "scaffold-incomplete"
        assert "fill in" in scaffold[0].message
        assert "Raises" in scaffold[0].message

    def test_json_output_scaffold_category(self):
        """JSON output includes scaffold category and medium severity."""
        source = textwrap.dedent('''\
            def f():
                """Do stuff.

                Raises:
                    ValueError: [TODO: describe when this is raised]
                """
                raise ValueError("x")
        ''')
        findings = _enrich(source)
        scaffold = [f for f in findings if f.rule == "scaffold-incomplete"]
        result = json.loads(format_json(scaffold, 1))
        assert result["findings"][0]["category"] == "scaffold"
        assert result["findings"][0]["severity"] == "medium"
        assert result["summary"]["by_category"]["scaffold"] == 1
