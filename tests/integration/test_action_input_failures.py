"""Execute the Action's YAML shell against fixture reports and the real CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.name == "nt" or not shutil.which("bash") or not shutil.which("jq"),
        reason="The composite Action requires POSIX bash and jq",
    ),
]
ERROR = {"file": "bad.py", "kind": "parse", "message": "invalid syntax"}
FINDING = {
    "file": "good.py",
    "line": 1,
    "rule": "missing-docstring",
    "message": "Missing documentation",
    "category": "required",
    "severity": "high",
}


def report(
    *, errors=(), findings=(), status="incomplete", unavailable=(), legacy=False
):
    result = {
        "findings": list(findings),
        "summary": {
            "total": len(findings),
            "by_category": {
                "required": len(findings),
                "recommended": 0,
            },
            "files_checked": 1,
        },
    }
    if not legacy:
        result["run"] = {
            "status": status,
            "input_errors": list(errors),
            "unavailable_checks": list(unavailable),
        }
    return result


def run_action(tmp_path, checks, payload=None, code=1):
    action = yaml.safe_load((ROOT / "action.yml").read_text())
    step = next(s for s in action["runs"]["steps"] if s.get("id") == "run-docvet")
    script = (
        step["run"]
        .replace("${{ inputs.args }}", "")
        .replace("${{ inputs.checks }}", checks)
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / "docvet"
    if payload is None:
        # Run the checkout's CLI, not whatever release the runner installed.
        body = "from docvet.cli import app\napp()\n"
    else:
        (tmp_path / "report.json").write_text(json.dumps(payload))
        body = (
            "from pathlib import Path\n"
            "print(Path('report.json').read_text())\n"
            f"raise SystemExit({code})\n"
        )
    executable.write_text(f"#!{sys.executable}\n" + body)
    executable.chmod(0o755)
    output = tmp_path / "output"
    summary = tmp_path / "summary"
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", script],
        cwd=tmp_path,
        env=os.environ
        | {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
    return result, outputs, summary.read_text()


@pytest.mark.parametrize("checks", ["all", "presence,enrichment"])
@pytest.mark.parametrize("with_findings", [False, True])
def test_incomplete_reports_are_not_passing(tmp_path, checks, with_findings):
    result, outputs, summary = run_action(
        tmp_path,
        checks,
        report(errors=[ERROR], findings=[FINDING] if with_findings else []),
    )
    count = (2 if "," in checks else 1) if with_findings else 0
    assert result.returncode == 1
    assert outputs["total_findings"] == str(count)
    assert outputs["badge_color"] == "red"
    assert "analysis incomplete" in outputs["badge_message"]
    if count:
        assert f"{count} findings" in outputs["badge_message"]
    assert result.stdout.count("::error file=bad.py") == 1
    assert "Analysis incomplete" in summary
    assert "invalid syntax" in summary
    assert "All docstrings pass" not in summary


@pytest.mark.parametrize("blocking", [False, True])
def test_incomplete_preserves_availability_and_findings(tmp_path, blocking):
    unavailable = {
        "check": "griffe",
        "reason": "not installed",
        "remedy": "install extra",
        "configured_gate": True,
        "blocking": blocking,
    }
    result, outputs, summary = run_action(
        tmp_path,
        "presence,enrichment",
        report(errors=[ERROR], findings=[FINDING], unavailable=[unavailable]),
    )
    assert result.returncode == 1
    assert outputs["badge_color"] == "red"
    assert outputs["badge_message"] == "2 findings, analysis incomplete" + (
        ", gate unavailable" if blocking else ""
    )
    assert "not installed" in summary and "invalid syntax" in summary


@pytest.mark.parametrize("checks", ["all", "presence,enrichment"])
def test_incomplete_without_errors_still_fails(tmp_path, checks):
    result, outputs, summary = run_action(tmp_path, checks, report(), code=0)
    assert result.returncode == 1
    assert "::error::" in result.stdout
    assert outputs["badge_message"] == "analysis incomplete"
    assert "Analysis incomplete" in summary


def test_annotation_and_summary_escaping(tmp_path):
    error = {
        "file": "evil%,:\r\n::warning::x`|<b>.py",
        "kind": "parse",
        "message": "bad%\r\n::error::injected <script> & `|",
    }
    result, outputs, summary = run_action(
        tmp_path, "presence,enrichment", report(errors=[error])
    )
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("::error file=evil%25%2C%3A%0D%0A")
    assert "bad%25%0D%0A::error::injected" in lines[0]
    assert "<script>" not in summary and "<b>" not in summary
    assert "&lt;script&gt;" in summary and "&amp;" in summary
    assert outputs["badge_color"] == "red"


def test_input_errors_without_incomplete_status_still_fail(tmp_path):
    result, outputs, _ = run_action(
        tmp_path, "presence,enrichment", report(errors=[ERROR], status="passed"), code=0
    )
    assert result.returncode == 1
    assert outputs["badge_message"] == "analysis incomplete"
    assert result.stdout.count("::error file=bad.py") == 1


@pytest.mark.parametrize("blocking", [False, True])
def test_unavailable_without_input_errors_keeps_behavior(tmp_path, blocking):
    unavailable = {
        "check": "griffe",
        "reason": "not installed",
        "remedy": "install extra",
        "configured_gate": True,
        "blocking": blocking,
    }
    result, outputs, summary = run_action(
        tmp_path,
        "presence,enrichment",
        report(
            status="unavailable" if blocking else "passed", unavailable=[unavailable]
        ),
        code=int(blocking),
    )
    assert result.returncode == int(blocking)
    assert outputs["badge_message"] == ("gate unavailable" if blocking else "passing")
    assert outputs["badge_color"] == ("orange" if blocking else "brightgreen")
    assert "not installed" in summary


@pytest.mark.parametrize("checks", ["all", "presence,enrichment"])
@pytest.mark.parametrize(
    "legacy,findings", [(True, []), (True, [FINDING]), (False, [])]
)
def test_legacy_and_successful_reports_keep_behavior(
    tmp_path, checks, legacy, findings
):
    result, outputs, summary = run_action(
        tmp_path,
        checks,
        report(legacy=legacy, findings=findings, status="passed"),
        code=int(bool(findings)),
    )
    assert result.returncode == int(bool(findings))
    assert outputs["badge_color"] == ("red" if findings else "brightgreen")
    assert "analysis incomplete" not in outputs["badge_message"]
    if not findings:
        assert outputs["badge_message"] == "passing"
        assert "All docstrings pass" in summary


@pytest.mark.parametrize("checks", ["all", "presence,enrichment"])
@pytest.mark.parametrize("broken", [False, True])
def test_real_cli_failed_or_empty_input(tmp_path, checks, broken):
    (tmp_path / "pyproject.toml").write_text("[tool.docvet]\nfail-on=[]\n")
    if broken:
        (tmp_path / "bad.py").write_text("def broken(:\n")
    result, outputs, summary = run_action(tmp_path, checks)
    assert result.returncode == int(broken)
    assert outputs["badge_message"] == ("analysis incomplete" if broken else "passing")
    assert outputs["badge_color"] == ("red" if broken else "brightgreen")
    assert result.stdout.count("::error file=") == int(broken)
    assert ("Analysis incomplete" in summary) is broken
