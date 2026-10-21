"""Public MCP regressions for incomplete input analysis and source encodings."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("mcp")
from docvet.mcp import docvet_check

pytestmark = pytest.mark.unit


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        "[tool.docvet]\n[tool.docvet.presence]\nmin-coverage = 100.0\n"
    )
    return tmp_path


@pytest.mark.parametrize("mixed", [False, True])
def test_failed_sources_never_certify_coverage(project: Path, mixed: bool):
    (project / "broken.py").write_text("def broken(:\n")
    if mixed:
        (project / "good.py").write_text('"""Documented."""\n')
    result = json.loads(docvet_check(str(project), ["presence", "enrichment"]))
    assert result["run"]["status"] == "incomplete"
    assert result["run"]["exit_code"] == 1
    assert len(result["run"]["input_errors"]) == 1
    assert result["run"]["input_errors"][0]["kind"] == "parse"
    assert result["summary"]["files_checked"] == 1 + mixed
    assert result["summary"]["files_attempted"] == 1 + mixed
    assert result["summary"]["files_analyzed"] == int(mixed)
    assert result["summary"]["files_failed"] == 1
    coverage = result["presence_coverage"]
    assert coverage["complete"] is False
    assert coverage["passed"] is False
    assert coverage["percentage"] == (100.0 if mixed else None)


@pytest.mark.parametrize(
    "raw", [b'\xef\xbb\xbf"""Doc."""\n', b'# coding: latin-1\n"""Caf\xe9."""\n']
)
def test_python_encodings_are_supported(project: Path, raw: bytes):
    target = project / "valid.py"
    target.write_bytes(raw)
    result = json.loads(docvet_check(str(target), ["presence", "enrichment"]))
    assert result["run"]["input_errors"] == []
    assert result["summary"]["files_analyzed"] == 1
    assert result["presence_coverage"]["complete"] is True


@pytest.mark.parametrize(
    "raw", [b"\xff", b"# coding: nope\n", b"\xef\xbb\xbf# coding: latin-1\n"]
)
def test_invalid_encodings_are_controlled(project: Path, raw: bytes):
    target = project / "invalid.py"
    target.write_bytes(raw)
    result = json.loads(docvet_check(str(target), ["presence", "enrichment"]))
    assert result["run"]["status"] == "incomplete"
    assert result["run"]["input_errors"][0]["kind"] == "decode"


def test_empty_directory_has_no_measured_coverage(project: Path):
    result = json.loads(docvet_check(str(project), ["presence"]))
    assert result["summary"]["files_attempted"] == 0
    assert result["run"]["status"] == "passed"
    assert "presence_coverage" not in result


@pytest.mark.parametrize("name", ["missing.py", "notes.txt"])
def test_invalid_targets_keep_legacy_error_and_add_run(project: Path, name: str):
    target = project / name
    if target.suffix == ".txt":
        target.write_text("notes")
    result = json.loads(docvet_check(str(target), ["presence"]))
    assert "error" in result
    assert result["run"]["status"] == "incomplete"
    assert result["summary"]["files_attempted"] == 1
    assert result["summary"]["files_failed"] == 1


def test_coverage_only_does_not_parse(project: Path):
    target = project / "broken.py"
    target.write_text("def broken(:\n")
    with patch("ast.parse", side_effect=AssertionError("unexpected parse")):
        result = json.loads(docvet_check(str(target), ["coverage"]))
    assert result["run"]["input_errors"] == []
    assert result["summary"]["files_analyzed"] == 1


def test_read_failure_is_deduplicated_across_checks(project: Path):
    target = project / "unreadable.py"
    target.write_text('"""Documented."""\n')
    original = Path.read_bytes

    def fail_read(path: Path) -> bytes:
        if path == target:
            raise PermissionError("Permission denied")
        return original(path)

    with patch.object(Path, "read_bytes", fail_read):
        result = json.loads(docvet_check(str(target), ["presence", "enrichment"]))
    assert result["run"]["input_errors"] == [
        {"file": str(target), "kind": "read", "message": "Permission denied"}
    ]
    assert result["summary"]["files_analyzed"] == 0


def test_unavailable_optional_check_keeps_existing_error(project: Path):
    target = project / "valid.py"
    target.write_text('"""Documented."""\n')
    with patch("docvet.mcp._GRIFFE_AVAILABLE", False):
        result = json.loads(docvet_check(str(target), ["presence", "griffe"]))
    assert result["errors"] == [
        "griffe check requires the griffe extra: pip install docvet[griffe]"
    ]
    assert result["run"]["input_errors"] == []
    assert result["presence_coverage"]["complete"] is True


def test_freshness_handles_latin1_git_diff(project: Path):
    import subprocess

    subprocess.run(["git", "init", str(project)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(project), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(project), "config", "user.name", "Test"], check=True
    )
    target = project / "valid.py"
    target.write_bytes(b'# coding: latin-1\n"""Caf\xe9."""\n')
    subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(project), "commit", "-m", "initial"],
        check=True,
        capture_output=True,
    )
    target.write_bytes(b'# coding: latin-1\n"""Caf\xe9 changed."""\n')
    result = json.loads(docvet_check(str(target), ["freshness"]))
    assert result["run"]["input_errors"] == []
    assert result["summary"]["files_analyzed"] == 1
    assert "errors" not in result


def test_griffe_only_reports_parse_failure(project: Path):
    pytest.importorskip("griffe")
    target = project / "broken.py"
    target.write_text("def broken(:\n")
    result = json.loads(docvet_check(str(target), ["griffe"]))
    assert result["run"]["status"] == "incomplete"
    assert result["run"]["input_errors"][0]["kind"] == "parse"
    assert result["summary"]["files_analyzed"] == 0


def test_griffe_only_supports_latin1(project: Path):
    pytest.importorskip("griffe")
    target = project / "valid.py"
    target.write_bytes(b'# coding: latin-1\n"""Caf\xe9."""\n')
    result = json.loads(docvet_check(str(target), ["griffe"]))
    assert result["run"]["input_errors"] == []
    assert result["summary"]["files_analyzed"] == 1
    assert "errors" not in result


def test_unavailable_griffe_does_not_claim_analyzed_input(project: Path):
    target = project / "valid.py"
    target.write_text('"""Documented."""\n')
    with patch("docvet.mcp._GRIFFE_AVAILABLE", False):
        result = json.loads(docvet_check(str(target), ["griffe"]))
    assert result["summary"]["files_checked"] == 1
    assert result["summary"]["files_attempted"] == 1
    assert result["summary"]["files_analyzed"] == 0
    assert result["summary"]["files_failed"] == 0
    assert result["errors"]


@pytest.mark.parametrize("check", ["griffe", "freshness"])
@pytest.mark.parametrize(
    ("gated", "optout", "status", "exit_code"),
    [
        (True, False, "unavailable", 1),
        (False, False, "passed", 0),
        (True, True, "passed", 0),
    ],
)
def test_unavailable_checks_have_truthful_run_metadata(
    project: Path, check: str, gated: bool, optout: bool, status: str, exit_code: int
):
    (project / "pyproject.toml").write_text(
        "[tool.docvet]\n"
        f"fail-on = {json.dumps([check] if gated else [])}\n"
        f"fail-on-unavailable = {str(not optout).lower()}\n"
    )
    target = project / "valid.py"
    target.write_text('"""Documented."""\n')
    with (
        patch("docvet.mcp._GRIFFE_AVAILABLE", False),
        patch("docvet.mcp.subprocess.run", side_effect=FileNotFoundError),
    ):
        result = json.loads(docvet_check(str(target), [check]))
    run = result["run"]
    assert run["status"] == status
    assert run["exit_code"] == exit_code
    unavailable = run["unavailable_checks"]
    assert len(unavailable) == 1
    assert unavailable[0]["check"] == check
    assert unavailable[0]["reason"] == result["errors"][0]
    assert unavailable[0]["blocking"] is (gated and not optout)
    assert unavailable[0]["configured_gate"] is gated
    assert unavailable[0]["remedy"]
    if gated:
        assert "could not run" in run["exit_reason"]


@pytest.mark.parametrize("gated", [True, False])
def test_non_repository_freshness_is_unavailable_like_the_cli(
    project: Path, monkeypatch, gated: bool
):
    """With git installed, a tree outside any repository gates like the CLI."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(project.parent))
    (project / "pyproject.toml").write_text(
        f"[tool.docvet]\nfail-on = {json.dumps(['freshness'] if gated else [])}\n"
    )
    target = project / "valid.py"
    target.write_text('"""Documented."""\n')
    result = json.loads(docvet_check(str(target), ["freshness"]))
    run = result["run"]
    assert run["status"] == ("unavailable" if gated else "passed")
    assert run["exit_code"] == int(gated)
    assert [item["check"] for item in run["unavailable_checks"]] == ["freshness"]
    assert "not a git repository" in run["unavailable_checks"][0]["reason"]
    assert run["unavailable_checks"][0]["blocking"] is gated
    assert run["unavailable_checks"][0]["configured_gate"] is gated


def test_null_byte_target_is_structured_input_error():
    result = json.loads(docvet_check("x\x00.py", ["presence"]))
    assert result["run"]["status"] == "incomplete"
    assert result["run"]["exit_code"] == 1
    assert result["run"]["input_errors"][0]["kind"] == "input"
    assert result["summary"]["files_attempted"] == 1
    assert result["summary"]["files_analyzed"] == 0
    assert result["summary"]["files_failed"] == 1
    assert result["error"]


@pytest.mark.parametrize("check", ["griffe", "freshness"])
def test_empty_selection_succeeds_without_optional_prerequisites(
    project: Path, check: str
):
    with patch("docvet.mcp._GRIFFE_AVAILABLE", False):
        result = json.loads(docvet_check(str(project), ["presence", check]))
    assert result["run"]["status"] == "passed"
    assert result["run"]["exit_code"] == 0
    assert result["run"]["unavailable_checks"] == []
    assert result["summary"]["files_attempted"] == 0
    assert result["summary"]["files_analyzed"] == 0
    assert result["summary"]["files_failed"] == 0
    assert "presence_coverage" not in result
    assert "errors" not in result
