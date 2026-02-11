"""Integration tests for griffe compatibility check with real griffe loading."""

from __future__ import annotations

from pathlib import Path

griffe = __import__("pytest").importorskip("griffe")

from docvet.checks.griffe_compat import check_griffe_compat  # noqa: E402

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestGriffeCompatSmoke:
    """Smoke tests using real griffe loading against fixture package."""

    def test_full_pipeline_produces_expected_findings(self) -> None:
        """Fixture package produces findings for all rule types (AC #21)."""
        src_root = FIXTURES_DIR
        bad_file = FIXTURES_DIR / "griffe_pkg" / "bad_docstrings.py"

        findings = check_griffe_compat(src_root, [bad_file])

        # untyped_params: 3 griffe-missing-type (x, y, z)
        # phantom_param: 1 griffe-missing-type + 1 griffe-unknown-param
        # well_documented: 0 findings
        assert len(findings) == 5

        rules = [f.rule for f in findings]
        assert rules.count("griffe-missing-type") == 4
        assert rules.count("griffe-unknown-param") == 1

        # Verify all findings reference the correct file
        for finding in findings:
            assert finding.file.endswith("bad_docstrings.py")
            assert finding.line >= 1
            assert finding.symbol != ""
            assert finding.message != ""

    def test_missing_type_findings_for_untyped_params(self) -> None:
        """untyped_params produces 3 griffe-missing-type findings (AC #1, #4)."""
        src_root = FIXTURES_DIR
        bad_file = FIXTURES_DIR / "griffe_pkg" / "bad_docstrings.py"

        findings = check_griffe_compat(src_root, [bad_file])

        untyped_findings = [
            f
            for f in findings
            if f.symbol == "untyped_params" and f.rule == "griffe-missing-type"
        ]
        assert len(untyped_findings) == 3
        for f in untyped_findings:
            assert f.category == "recommended"
            assert "Function" in f.message
            assert "'untyped_params'" in f.message

    def test_unknown_param_finding_for_phantom(self) -> None:
        """phantom_param produces griffe-unknown-param finding (AC #2)."""
        src_root = FIXTURES_DIR
        bad_file = FIXTURES_DIR / "griffe_pkg" / "bad_docstrings.py"

        findings = check_griffe_compat(src_root, [bad_file])

        unknown_findings = [f for f in findings if f.rule == "griffe-unknown-param"]
        assert len(unknown_findings) == 1
        assert unknown_findings[0].symbol == "phantom_param"
        assert unknown_findings[0].category == "required"
        assert "Function" in unknown_findings[0].message

    def test_well_documented_function_produces_no_findings(self) -> None:
        """well_documented function produces zero findings (AC #5)."""
        src_root = FIXTURES_DIR
        bad_file = FIXTURES_DIR / "griffe_pkg" / "bad_docstrings.py"

        findings = check_griffe_compat(src_root, [bad_file])

        well_doc_findings = [f for f in findings if f.symbol == "well_documented"]
        assert len(well_doc_findings) == 0

    def test_empty_files_with_real_griffe(self) -> None:
        """Empty files list returns empty with real griffe installed."""
        findings = check_griffe_compat(FIXTURES_DIR, [])
        assert findings == []
