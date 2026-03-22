"""Unit tests for the docvet MCP server module."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import textwrap
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

mcp_pkg = pytest.importorskip("mcp")

from docvet.checks import Finding, PresenceStats, check_enrichment  # noqa: E402
from docvet.config import (  # noqa: E402
    _VALID_CHECK_NAMES,
    DocvetConfig,
    EnrichmentConfig,
)
from docvet.mcp import (  # noqa: E402
    _DEFAULT_MCP_CHECKS,
    _RULE_CATALOG,
    _build_summary,
    _load_config_for_path,
    _run_checks,
    _serialize_finding,
    docvet_check,
    docvet_rules,
    start_server,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config() -> DocvetConfig:
    return DocvetConfig(project_root=Path("/fake/project"), src_root="src")


@pytest.fixture()
def sample_finding() -> Finding:
    return Finding(
        file="app.py",
        line=10,
        symbol="foo",
        rule="missing-raises",
        message="Docstring missing Raises section for ValueError.",
        category="required",
    )


@pytest.fixture()
def recommended_finding() -> Finding:
    return Finding(
        file="app.py",
        line=5,
        symbol="bar",
        rule="missing-examples",
        message="Docstring missing Examples section.",
        category="recommended",
    )


@pytest.fixture()
def isolated_tmp(tmp_path: Path) -> Path:
    """Create a tmp_path with its own pyproject.toml for config isolation."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname = 'test'\n", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def py_file(isolated_tmp: Path) -> Path:
    p = isolated_tmp / "sample.py"
    p.write_text(
        textwrap.dedent("""\
        def greet(name):
            print(f"Hello, {name}")
        """),
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def py_dir(isolated_tmp: Path) -> Path:
    d = isolated_tmp / "pkg"
    d.mkdir()
    (d / "__init__.py").write_text("", encoding="utf-8")
    (d / "mod.py").write_text(
        textwrap.dedent("""\
        def add(a, b):
            return a + b
        """),
        encoding="utf-8",
    )
    return d


# ---------------------------------------------------------------------------
# Task 6.1 — docvet_check single file returns findings + summary
# ---------------------------------------------------------------------------


class TestDocvetCheckSingleFile:
    def test_single_file_returns_findings_and_summary(self, py_file: Path):
        result = json.loads(
            docvet_check(str(py_file), checks=["presence", "enrichment"])
        )

        assert "findings" in result
        assert "summary" in result
        assert isinstance(result["findings"], list)
        assert result["summary"]["files_checked"] >= 1

    def test_single_file_findings_have_all_fields(self, py_file: Path):
        result = json.loads(
            docvet_check(str(py_file), checks=["presence", "enrichment"])
        )

        expected_keys = {"file", "line", "symbol", "rule", "message", "category"}
        for finding in result["findings"]:
            assert set(finding.keys()) == expected_keys

    def test_single_file_summary_has_expected_keys(self, py_file: Path):
        result = json.loads(
            docvet_check(str(py_file), checks=["presence", "enrichment"])
        )

        summary = result["summary"]
        assert "total" in summary
        assert "by_category" in summary
        assert "files_checked" in summary
        assert "by_check" in summary


# ---------------------------------------------------------------------------
# Task 6.2 — docvet_check with filtered checks
# ---------------------------------------------------------------------------


class TestDocvetCheckFiltered:
    def test_only_requested_checks_run(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file), checks=["presence"]))

        summary = result["summary"]
        assert "presence" in summary["by_check"]
        # Enrichment should not appear when only presence requested
        assert summary["by_check"].get("enrichment", 0) == 0

    def test_multiple_checks_filtered(self, py_file: Path):
        result = json.loads(
            docvet_check(str(py_file), checks=["presence", "enrichment"])
        )

        summary = result["summary"]
        assert "presence" in summary["by_check"]
        assert "enrichment" in summary["by_check"]

    def test_default_excludes_freshness(self):
        assert "freshness" not in _DEFAULT_MCP_CHECKS

    def test_default_excludes_griffe_when_unavailable(self):
        with patch("docvet.mcp._GRIFFE_AVAILABLE", False):
            # Re-compute to verify logic (module-level constant is already set)
            computed = frozenset(
                name
                for name in _VALID_CHECK_NAMES
                if name != "freshness" and (False or name != "griffe")
            )
            assert "griffe" not in computed
            assert "freshness" not in computed


# ---------------------------------------------------------------------------
# Task 6.3 — presence_coverage in response when presence runs
# ---------------------------------------------------------------------------


class TestPresenceCoverage:
    def test_presence_coverage_included_when_presence_runs(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file), checks=["presence"]))

        assert "presence_coverage" in result
        pc = result["presence_coverage"]
        assert "documented" in pc
        assert "total" in pc
        assert "percentage" in pc
        assert "threshold" in pc
        assert "passed" in pc

    def test_presence_coverage_absent_when_presence_not_run(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file), checks=["enrichment"]))

        assert "presence_coverage" not in result

    def test_presence_coverage_values_are_numeric(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file), checks=["presence"]))

        pc = result["presence_coverage"]
        assert isinstance(pc["documented"], int)
        assert isinstance(pc["total"], int)
        assert isinstance(pc["percentage"], float)
        assert isinstance(pc["threshold"], (int, float))
        assert isinstance(pc["passed"], bool)


# ---------------------------------------------------------------------------
# Task 6.4 — docvet_rules returns complete catalog
# ---------------------------------------------------------------------------


class TestDocvetRules:
    def test_rules_returns_list(self):
        result = json.loads(docvet_rules())

        assert "rules" in result
        assert isinstance(result["rules"], list)

    def test_rules_have_all_required_fields(self):
        result = json.loads(docvet_rules())

        expected_keys = {
            "name",
            "check",
            "description",
            "category",
            "guidance",
            "fix_example",
        }
        for rule in result["rules"]:
            assert set(rule.keys()) == expected_keys

    def test_rules_names_are_unique(self):
        result = json.loads(docvet_rules())

        names = [r["name"] for r in result["rules"]]
        assert len(names) == len(set(names))

    def test_rules_checks_are_valid(self):
        result = json.loads(docvet_rules())

        valid_checks = {"presence", "enrichment", "freshness", "coverage", "griffe"}
        for rule in result["rules"]:
            assert rule["check"] in valid_checks

    def test_rules_categories_are_valid(self):
        result = json.loads(docvet_rules())

        for rule in result["rules"]:
            assert rule["category"] in {"required", "recommended"}


# ---------------------------------------------------------------------------
# Task 6.5 — config respected (exclude patterns, thresholds)
# ---------------------------------------------------------------------------


class TestConfigRespected:
    def test_exclude_patterns_filter_files(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
            [project]
            name = "test"
            [tool.docvet]
            exclude = ["ignored"]
            """),
            encoding="utf-8",
        )
        src = tmp_path / "src"
        src.mkdir()
        (src / "good.py").write_text("def f(): pass\n", encoding="utf-8")
        ignored = tmp_path / "ignored"
        ignored.mkdir()
        (ignored / "bad.py").write_text("def g(): pass\n", encoding="utf-8")

        result = json.loads(docvet_check(str(src / "good.py"), checks=["presence"]))

        files_in_findings = {f["file"] for f in result["findings"]}
        for f in files_in_findings:
            assert "ignored" not in f

    def test_presence_threshold_from_config(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
            [project]
            name = "test"
            [tool.docvet.presence]
            min-coverage = 50.0
            """),
            encoding="utf-8",
        )
        p = tmp_path / "sample.py"
        p.write_text("def f(): pass\n", encoding="utf-8")

        result = json.loads(docvet_check(str(p), checks=["presence"]))

        assert result["presence_coverage"]["threshold"] == 50.0


# ---------------------------------------------------------------------------
# Task 6.6 — error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_invalid_path_returns_error(self):
        result = json.loads(docvet_check("/nonexistent/file.py"))

        assert "error" in result
        assert "does not exist" in result["error"]

    def test_invalid_check_name_returns_error(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file), checks=["bogus"]))

        assert "error" in result
        assert "Invalid check names" in result["error"]
        assert "bogus" in result["error"]

    def test_non_python_path_returns_error(self, tmp_path: Path):
        txt = tmp_path / "readme.txt"
        txt.write_text("hello", encoding="utf-8")

        result = json.loads(docvet_check(str(txt)))

        assert "error" in result
        assert "not a Python file" in result["error"]

    def test_invalid_config_returns_error_not_crash(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            "[project]\nname = 'test'\n[tool.docvet]\nbogus-key = true\n",
            encoding="utf-8",
        )
        p = tmp_path / "sample.py"
        p.write_text("def f(): pass\n", encoding="utf-8")

        result = json.loads(docvet_check(str(p), checks=["presence"]))

        assert "error" in result
        assert (
            "Invalid" in result["error"] or "configuration" in result["error"].lower()
        )

    def test_unparseable_file_skipped(self, isolated_tmp: Path):
        bad = isolated_tmp / "bad.py"
        bad.write_text("def (broken syntax\n", encoding="utf-8")

        result = json.loads(docvet_check(str(bad), checks=["enrichment"]))

        assert "error" not in result
        assert result["summary"]["total"] == 0


# ---------------------------------------------------------------------------
# Task 6.7 — start_server function exists and is callable
# ---------------------------------------------------------------------------


class TestStartServer:
    def test_start_server_is_callable(self):
        assert callable(start_server)

    def test_start_server_exists_in_all(self):
        from docvet import mcp as mcp_mod

        assert "start_server" in mcp_mod.__all__


# ---------------------------------------------------------------------------
# Task 6.8 — ImportError guard when mcp not installed
# ---------------------------------------------------------------------------


class TestImportErrorGuard:
    def test_import_error_without_mcp_package(self):
        script = textwrap.dedent("""\
        import sys
        import importlib
        import importlib.abc
        import importlib.machinery

        # Remove all mcp-related modules
        for key in list(sys.modules):
            if key == "mcp" or key.startswith("mcp."):
                del sys.modules[key]
        for key in list(sys.modules):
            if key == "docvet.mcp":
                del sys.modules[key]

        # Block mcp import using sys.modules sentinel
        sys.modules["mcp"] = None
        sys.modules["mcp.server"] = None
        sys.modules["mcp.server.fastmcp"] = None

        try:
            importlib.import_module("docvet.mcp")
            print("FAIL: no ImportError raised")
            sys.exit(1)
        except ImportError as e:
            if "pip install docvet[mcp]" in str(e):
                print("OK")
                sys.exit(0)
            else:
                print(f"FAIL: wrong message: {e}")
                sys.exit(1)
        """)
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stdout={result.stdout} stderr={result.stderr}"
        assert "OK" in result.stdout


# ---------------------------------------------------------------------------
# Task 6.9 — empty directory returns zero findings
# ---------------------------------------------------------------------------


class TestEmptyDirectory:
    def test_empty_dir_returns_zero_findings(self, isolated_tmp: Path):
        empty = isolated_tmp / "empty"
        empty.mkdir()

        result = json.loads(docvet_check(str(empty), checks=["presence", "enrichment"]))

        assert result["findings"] == []
        assert result["summary"]["total"] == 0
        assert result["summary"]["files_checked"] == 0


# ---------------------------------------------------------------------------
# Task 6.10 — freshness with git unavailable
# ---------------------------------------------------------------------------


class TestFreshnessGitUnavailable:
    def test_freshness_without_git_returns_error_message(self, py_file: Path):
        with patch(
            "docvet.mcp.subprocess.run",
            side_effect=FileNotFoundError("git not found"),
        ):
            result = json.loads(docvet_check(str(py_file), checks=["freshness"]))

        assert "errors" in result
        assert any("freshness" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Task 6.11 — griffe with package unavailable
# ---------------------------------------------------------------------------


class TestGriffeUnavailable:
    def test_griffe_unavailable_returns_error_message(self, py_file: Path):
        with patch("docvet.mcp._GRIFFE_AVAILABLE", False):
            result = json.loads(docvet_check(str(py_file), checks=["griffe"]))

        assert "errors" in result
        assert any("griffe" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Task 6.12 — finding dict structure matches format_json schema
# ---------------------------------------------------------------------------


class TestFindingSchemaParity:
    def test_serialize_finding_keys_match_format_json_base_fields(
        self, sample_finding: Finding
    ):
        serialized = _serialize_finding(sample_finding)

        # The 6 core Finding fields (format_json adds a 7th 'severity')
        expected = {"file", "line", "symbol", "rule", "message", "category"}
        assert set(serialized.keys()) == expected

    def test_serialize_finding_values_match_finding(self, sample_finding: Finding):
        d = _serialize_finding(sample_finding)

        assert d["file"] == sample_finding.file
        assert d["line"] == sample_finding.line
        assert d["symbol"] == sample_finding.symbol
        assert d["rule"] == sample_finding.rule
        assert d["message"] == sample_finding.message
        assert d["category"] == sample_finding.category


# ---------------------------------------------------------------------------
# Task 6.13 — rule catalog length staleness guard
# ---------------------------------------------------------------------------


class TestRuleCatalogStaleness:
    def test_rule_catalog_has_expected_count(self):
        assert len(_RULE_CATALOG) == 31

    def test_rule_catalog_entries_have_required_keys(self):
        expected_keys = {
            "name",
            "check",
            "description",
            "category",
            "guidance",
            "fix_example",
        }
        for entry in _RULE_CATALOG:
            assert set(entry.keys()) == expected_keys

    def test_rule_catalog_names_match_emitted_rules(self):
        expected_rules = {
            # presence (2)
            "missing-docstring",
            "overload-has-docstring",
            # enrichment (20)
            "missing-raises",
            "missing-returns",
            "missing-yields",
            "missing-receives",
            "missing-warns",
            "missing-deprecation",
            "missing-other-parameters",
            "missing-attributes",
            "missing-typed-attributes",
            "missing-examples",
            "missing-cross-references",
            "prefer-fenced-code-blocks",
            "missing-param-in-docstring",
            "extra-param-in-docstring",
            "extra-raises-in-docstring",
            "extra-yields-in-docstring",
            "extra-returns-in-docstring",
            "trivial-docstring",
            "missing-return-type",
            "undocumented-init-params",
            # freshness (5)
            "stale-signature",
            "stale-body",
            "stale-import",
            "stale-drift",
            "stale-age",
            # coverage (1)
            "missing-init",
            # griffe (3)
            "griffe-unknown-param",
            "griffe-missing-type",
            "griffe-format-warning",
        }
        catalog_names = {entry["name"] for entry in _RULE_CATALOG}
        assert catalog_names == expected_rules


# ---------------------------------------------------------------------------
# Additional helper tests
# ---------------------------------------------------------------------------


class TestSerializeFinding:
    def test_required_finding(self, sample_finding: Finding):
        d = _serialize_finding(sample_finding)

        assert d["file"] == "app.py"
        assert d["line"] == 10
        assert d["symbol"] == "foo"
        assert d["rule"] == "missing-raises"
        assert d["category"] == "required"

    def test_recommended_finding(self, recommended_finding: Finding):
        d = _serialize_finding(recommended_finding)

        assert d["file"] == "app.py"
        assert d["line"] == 5
        assert d["symbol"] == "bar"
        assert d["rule"] == "missing-examples"
        assert d["category"] == "recommended"


class TestBuildSummary:
    def test_empty_findings(self):
        summary = _build_summary([], 0, frozenset(["enrichment"]))

        assert summary["total"] == 0
        assert summary["files_checked"] == 0
        assert summary["by_category"] == {"required": 0, "recommended": 0}

    def test_counts_by_category(
        self, sample_finding: Finding, recommended_finding: Finding
    ):
        summary = _build_summary(
            [sample_finding, recommended_finding],
            5,
            frozenset(["enrichment"]),
        )

        assert summary["total"] == 2
        assert summary["files_checked"] == 5
        assert summary["by_category"] == {"required": 1, "recommended": 1}


class TestRunChecks:
    def test_with_no_files(self, config: DocvetConfig):
        findings, stats, errors = _run_checks([], config, frozenset(["enrichment"]))

        assert findings == []
        assert stats is None
        assert errors == []

    def test_with_presence_check(self, py_file: Path, config: DocvetConfig):
        findings, stats, errors = _run_checks(
            [py_file], config, frozenset(["presence"])
        )

        assert stats is not None
        assert isinstance(stats, PresenceStats)
        assert stats.total >= 0

    def test_enrichment_check_produces_findings(
        self, py_file: Path, config: DocvetConfig
    ):
        findings, stats, errors = _run_checks(
            [py_file], config, frozenset(["enrichment"])
        )

        assert isinstance(findings, list)
        assert stats is None  # presence not requested


class TestLoadConfigForPath:
    def test_finds_pyproject_in_parent(self, tmp_path: Path):
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            textwrap.dedent("""\
            [project]
            name = "test"
            [tool.docvet.presence]
            min-coverage = 42.0
            """),
            encoding="utf-8",
        )
        child = tmp_path / "src"
        child.mkdir()

        config = _load_config_for_path(child)

        assert config.presence.min_coverage == 42.0

    def test_defaults_when_no_pyproject(self, tmp_path: Path):
        # Create a pyproject.toml without [tool.docvet] to get defaults
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'test'\n", encoding="utf-8")

        config = _load_config_for_path(tmp_path)

        assert config.presence.min_coverage == 0.0


class TestDocvetCheckDefaultChecks:
    def test_default_checks_run_without_error(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file)))

        assert "error" not in result
        assert "findings" in result
        assert "summary" in result

    def test_default_checks_exclude_freshness(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file)))

        by_check = result["summary"]["by_check"]
        assert "freshness" not in by_check

    def test_default_checks_include_presence_and_enrichment(self, py_file: Path):
        result = json.loads(docvet_check(str(py_file)))

        by_check = result["summary"]["by_check"]
        assert "presence" in by_check
        assert "enrichment" in by_check


# ---------------------------------------------------------------------------
# L2 — griffe exception handling path
# ---------------------------------------------------------------------------


class TestGriffeExceptionHandling:
    def test_griffe_check_exception_returns_error_message(self, py_file: Path):
        with (
            patch("docvet.mcp._GRIFFE_AVAILABLE", True),
            patch(
                "docvet.mcp.check_griffe_compat",
                side_effect=OSError("griffe loader failed"),
            ),
        ):
            result = json.loads(docvet_check(str(py_file), checks=["griffe"]))

        assert "errors" in result
        assert any("griffe check failed" in e for e in result["errors"])


class TestDocvetCheckDirectory:
    def test_directory_discovers_files(self, py_dir: Path):
        result = json.loads(
            docvet_check(str(py_dir), checks=["presence", "enrichment"])
        )

        assert result["summary"]["files_checked"] >= 1
        assert "error" not in result

    def test_directory_scoped_to_target(self, isolated_tmp: Path):
        """Files outside the target directory are excluded."""
        target = isolated_tmp / "inner"
        target.mkdir()
        (target / "in_scope.py").write_text("def a(): pass\n", encoding="utf-8")

        outer = isolated_tmp / "outer"
        outer.mkdir()
        (outer / "out_scope.py").write_text("def b(): pass\n", encoding="utf-8")

        result = json.loads(docvet_check(str(target), checks=["presence"]))

        files_in_findings = {f["file"] for f in result["findings"]}
        for f in files_in_findings:
            assert "out_scope" not in f


# ---------------------------------------------------------------------------
# Task 5 — catalog guidance completeness tests
# ---------------------------------------------------------------------------

_FORMAT_FIXABLE_CHECKS = {"enrichment", "griffe", "presence"}
_ACTION_CHECKS = {"freshness", "coverage"}


class TestRuleCatalogGuidance:
    def test_check_sets_are_exhaustive(self):
        catalog_checks = {entry["check"] for entry in _RULE_CATALOG}
        assert _FORMAT_FIXABLE_CHECKS | _ACTION_CHECKS == catalog_checks

    def test_all_entries_have_guidance_string(self):
        for entry in _RULE_CATALOG:
            assert isinstance(entry["guidance"], str), entry["name"]
            assert len(entry["guidance"]) > 0, entry["name"]

    def test_format_fixable_rules_have_fix_example(self):
        for entry in _RULE_CATALOG:
            if entry["check"] in _FORMAT_FIXABLE_CHECKS:
                assert entry["fix_example"] is not None, entry["name"]

    def test_action_rules_have_null_fix_example(self):
        for entry in _RULE_CATALOG:
            if entry["check"] in _ACTION_CHECKS:
                assert entry["fix_example"] is None, entry["name"]

    def test_cross_references_description_covers_both_branches(self):
        xref = next(e for e in _RULE_CATALOG if e["name"] == "missing-cross-references")
        desc = xref["description"]
        assert isinstance(desc, str)
        assert "missing" in desc.lower()
        assert "lack" in desc.lower()

    # ------------------------------------------------------------------
    # Task 6 — structural validation for fix_example content
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "entry",
        [
            e
            for e in _RULE_CATALOG
            if e["fix_example"] is not None and e["check"] != "presence"
        ],
        ids=lambda e: e["name"],
    )
    def test_fix_example_structural_validity(self, entry: dict[str, str | None]):
        example = entry["fix_example"]
        assert example is not None
        assert "\t" not in example, f"{entry['name']} contains tabs"
        # Matching fenced block delimiters (even count of ```)
        fence_count = example.count("```")
        assert fence_count % 2 == 0, (
            f"{entry['name']} has unmatched fenced block delimiters"
        )
        # Non-header lines use 4-space indentation
        lines = example.split("\n")
        for line in lines[1:]:
            if line.strip():
                assert line.startswith("    "), (
                    f"{entry['name']}: non-header line missing 4-space indent: {line!r}"
                )


# ---------------------------------------------------------------------------
# Task 7 — round-trip tests for enrichment rules
# ---------------------------------------------------------------------------


def _isolated_config(rule_name: str) -> EnrichmentConfig:
    """Return an EnrichmentConfig with only the target rule enabled."""
    base = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_receives=False,
        require_warns=False,
        require_other_parameters=False,
        require_attributes=False,
        require_typed_attributes=False,
        require_examples=[],
        require_cross_references=False,
        prefer_fenced_code_blocks=False,
    )
    match rule_name:
        case "missing-raises":
            return replace(base, require_raises=True)
        case "missing-yields":
            return replace(base, require_yields=True)
        case "missing-receives":
            return replace(base, require_receives=True)
        case "missing-warns":
            return replace(base, require_warns=True)
        case "missing-other-parameters":
            return replace(base, require_other_parameters=True)
        case "missing-attributes":
            return replace(base, require_attributes=True)
        case "missing-typed-attributes":
            return replace(base, require_typed_attributes=True)
        case "missing-examples":
            return replace(base, require_examples=["class"])
        case "missing-cross-references":
            return replace(base, require_cross_references=True)
        case "prefer-fenced-code-blocks":
            return replace(base, prefer_fenced_code_blocks=True)
        case _:
            msg = f"Unknown enrichment rule: {rule_name}"
            raise ValueError(msg)


_ENRICHMENT_ROUND_TRIP_CASES = [
    (
        "missing-raises",
        textwrap.dedent('''\
        def explode(x):
            """Explode the value.

            Args:
                x: The value.
            """
            if x < 0:
                raise ValueError("negative")
        '''),
        textwrap.dedent('''\
        def explode(x):
            """Explode the value.

            Args:
                x: The value.

            Raises:
                ValueError: If x is negative.
            """
            if x < 0:
                raise ValueError("negative")
        '''),
    ),
    (
        "missing-yields",
        textwrap.dedent('''\
        def gen():
            """Generate values."""
            yield 1
        '''),
        textwrap.dedent('''\
        def gen():
            """Generate values.

            Yields:
                Integer values.
            """
            yield 1
        '''),
    ),
    (
        "missing-receives",
        textwrap.dedent('''\
        def coro():
            """Coroutine."""
            value = yield
            print(value)
        '''),
        textwrap.dedent('''\
        def coro():
            """Coroutine.

            Receives:
                Value to print.

            Yields:
                Nothing meaningful.
            """
            value = yield
            print(value)
        '''),
    ),
    (
        "missing-warns",
        textwrap.dedent('''\
        import warnings
        def check(timeout):
            """Check timeout.

            Args:
                timeout: Timeout in seconds.
            """
            if timeout < 5:
                warnings.warn("too short", stacklevel=2)
        '''),
        textwrap.dedent('''\
        import warnings
        def check(timeout):
            """Check timeout.

            Args:
                timeout: Timeout in seconds.

            Warns:
                UserWarning: If timeout is less than 5 seconds.
            """
            if timeout < 5:
                warnings.warn("too short", stacklevel=2)
        '''),
    ),
    (
        "missing-other-parameters",
        textwrap.dedent('''\
        def run(**kwargs):
            """Run something."""
            pass
        '''),
        textwrap.dedent('''\
        def run(**kwargs):
            """Run something.

            Other Parameters:
                **kwargs: Arbitrary keyword arguments.
            """
            pass
        '''),
    ),
    (
        "missing-attributes",
        textwrap.dedent('''\
        class User:
            """A user."""
            def __init__(self):
                self.name = "alice"
        '''),
        textwrap.dedent('''\
        class User:
            """A user.

            Attributes:
                name (str): The user name.
            """
            def __init__(self):
                self.name = "alice"
        '''),
    ),
    (
        "missing-typed-attributes",
        textwrap.dedent('''\
        class Server:
            """A server.

            Attributes:
                host: The hostname.
            """
            def __init__(self):
                self.host = "localhost"
        '''),
        textwrap.dedent('''\
        class Server:
            """A server.

            Attributes:
                host (str): The hostname.
            """
            def __init__(self):
                self.host = "localhost"
        '''),
    ),
    (
        "missing-examples",
        textwrap.dedent('''\
        class Widget:
            """A widget."""
            pass
        '''),
        textwrap.dedent('''\
        class Widget:
            """A widget.

            Examples:
                Create a widget:

                ```python
                w = Widget()
                ```
            """
            pass
        '''),
    ),
    (
        "missing-cross-references",
        textwrap.dedent('''\
        """Module without see also."""
        '''),
        textwrap.dedent('''\
        """Module without see also.

        See Also:
            [`os.path`][]: Path utilities.
        """
        '''),
    ),
    (
        "prefer-fenced-code-blocks",
        textwrap.dedent('''\
        def check(data):
            """Check data.

            Examples:
                >>> check(1)
            """
            pass
        '''),
        textwrap.dedent('''\
        def check(data):
            """Check data.

            Examples:
                Run a check:

                ```python
                check(1)
                ```
            """
            pass
        '''),
    ),
]


class TestRuleCatalogGuidanceRoundTrip:
    @pytest.mark.parametrize(
        ("rule_name", "before_source", "after_source"),
        _ENRICHMENT_ROUND_TRIP_CASES,
        ids=[name for name, _, _ in _ENRICHMENT_ROUND_TRIP_CASES],
    )
    def test_round_trip(self, rule_name: str, before_source: str, after_source: str):
        config = _isolated_config(rule_name)

        # Before: should trigger the rule
        tree_before = ast.parse(before_source)
        findings_before = check_enrichment(
            before_source, tree_before, config, "test.py"
        )
        matching_before = [f for f in findings_before if f.rule == rule_name]
        assert len(matching_before) >= 1, (
            f"Expected {rule_name} finding in before source"
        )

        # After: should have zero findings for this rule
        tree_after = ast.parse(after_source)
        findings_after = check_enrichment(after_source, tree_after, config, "test.py")
        matching_after = [f for f in findings_after if f.rule == rule_name]
        assert len(matching_after) == 0, (
            f"Expected zero {rule_name} findings in after source, got:"
            f" {[f.message for f in matching_after]}"
        )


# ---------------------------------------------------------------------------
# Task 8 — round-trip tests for griffe rules (gated)
# ---------------------------------------------------------------------------


class TestRuleCatalogGuidanceRoundTripGriffe:
    @pytest.mark.parametrize(
        ("rule_name", "before_source", "after_source"),
        [
            (
                "griffe-unknown-param",
                textwrap.dedent('''\
                def greet(name):
                    """Greet someone.

                    Args:
                        nme (str): The name.
                    """
                    print(name)
                '''),
                textwrap.dedent('''\
                def greet(name):
                    """Greet someone.

                    Args:
                        name (str): The name.
                    """
                    print(name)
                '''),
            ),
            (
                "griffe-missing-type",
                textwrap.dedent('''\
                def greet(name):
                    """Greet someone.

                    Args:
                        name: The name.
                    """
                    print(name)
                '''),
                textwrap.dedent('''\
                def greet(name):
                    """Greet someone.

                    Args:
                        name (str): The name.
                    """
                    print(name)
                '''),
            ),
            (
                "griffe-format-warning",
                textwrap.dedent('''\
                def greet(name):
                    """Greet someone.

                    Args:
                        name - The name.
                    """
                    print(name)
                '''),
                textwrap.dedent('''\
                def greet(name):
                    """Greet someone.

                    Args:
                        name (str): The name.
                    """
                    print(name)
                '''),
            ),
        ],
        ids=["griffe-unknown-param", "griffe-missing-type", "griffe-format-warning"],
    )
    def test_round_trip(
        self, rule_name: str, before_source: str, after_source: str, tmp_path: Path
    ):
        pytest.importorskip("griffe")
        from docvet.checks.griffe_compat import check_griffe_compat

        # Griffe requires a package layout (dir with __init__.py)
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        py_file = pkg / "mod.py"

        # Before: should trigger the rule
        py_file.write_text(before_source, encoding="utf-8")
        findings_before = list(check_griffe_compat(tmp_path, [py_file]))
        matching_before = [f for f in findings_before if f.rule == rule_name]
        assert len(matching_before) >= 1, (
            f"Expected {rule_name} finding in before source"
        )

        # After: overwrite and re-check
        py_file.write_text(after_source, encoding="utf-8")
        findings_after = list(check_griffe_compat(tmp_path, [py_file]))
        matching_after = [f for f in findings_after if f.rule == rule_name]
        assert len(matching_after) == 0, (
            f"Expected zero {rule_name} findings in after source, got:"
            f" {[f.message for f in matching_after]}"
        )
