"""Observable CLI contracts for failed input and Python source encodings."""

import json
import subprocess

import pytest
from typer.testing import CliRunner

from docvet.cli import app

pytestmark = pytest.mark.unit
runner = CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Create an isolated git project with no finding gates and a coverage floor."""
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.docvet]\nfail-on = []\n[tool.docvet.presence]\nmin-coverage = 100\n"
    )
    return tmp_path


@pytest.mark.parametrize(
    "command", ["check", "presence", "enrichment", "freshness", "fix"]
)
@pytest.mark.parametrize(
    "payload,kind", [(b"def broken(:\n", "parse"), (b"\xff\n", "decode")]
)
def test_failed_source_is_incomplete_json(project, command, payload, kind):
    """Unexamined input never passes, even with no finding gates."""
    path = project / "bad.py"
    path.write_bytes(payload)
    result = runner.invoke(app, ["--format", "json", command, str(path)])
    assert result.exit_code == 1, result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == "incomplete"
    assert len(data["run"]["input_errors"]) == 1
    assert data["run"]["input_errors"][0]["kind"] == kind
    assert data["summary"]["files_attempted"] == 1
    assert data["summary"]["files_analyzed"] == 0
    assert data["summary"]["files_failed"] == 1
    if command in {"check", "presence"}:
        assert data["presence_coverage"]["percentage"] is None
        assert data["presence_coverage"]["complete"] is False
        assert data["presence_coverage"]["passed"] is False


@pytest.mark.parametrize("option", [[], ["--quiet"], ["--verbose"], ["--summary"]])
def test_mixed_scope_reports_observed_coverage(project, option):
    """Mixed inputs report subset coverage without claiming completeness."""
    good = project / "good.py"
    good.write_text('"""Documented module."""\n')
    bad = project / "bad.py"
    bad.write_text("def broken(:\n")
    result = runner.invoke(
        app, ["--format", "json", *option, "check", str(good), str(bad)]
    )
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["summary"]["files_checked"] == 2
    assert data["summary"]["files_analyzed"] == 1
    assert data["presence_coverage"] == {
        "documented": 1,
        "total": 1,
        "percentage": 100.0,
        "threshold": 100.0,
        "passed": False,
        "complete": False,
    }
    assert result.stderr.count(": parse:") == 1
    assert "passes" not in result.stderr


def test_empty_selection_is_json_without_coverage(project):
    """A legitimate empty selection is distinct from failed inputs."""
    result = runner.invoke(app, ["--format", "json", "check", "--all"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["run"]["status"] == "passed"
    assert data["summary"]["files_attempted"] == 0
    assert "presence_coverage" not in data


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize(
    "encoding,cookie,bom",
    [
        ("utf-8", "", b""),
        ("utf-8", "", b"\xef\xbb\xbf"),
        ("latin-1", "# coding: latin-1\n", b""),
        ("latin-1", "#!/usr/bin/env python\n# -*- coding: latin-1 -*-\n", b""),
    ],
    ids=["utf8", "bom", "cookie-first", "cookie-second"],
)
def test_fix_preserves_encoding_newlines_and_dry_run_json(
    project, newline, encoding, cookie, bom
):
    """Fixes preserve source representation and dry-run output is valid JSON."""
    source = (
        cookie + '"""Café module."""\ndef f():\n    """Do café work."""\n'
        '    raise ValueError("café")\n# untouched café\n'
    ).replace("\n", newline)
    path = project / "encoded.py"
    original = bom + source.encode(encoding)
    path.write_bytes(original)
    dry = runner.invoke(app, ["--format", "json", "fix", "--dry-run", str(path)])
    assert dry.exit_code == 0, dry.output
    data = json.loads(dry.stdout)
    assert data["run"]["status"] == "passed"
    assert data["diffs"]
    assert path.read_bytes() == original
    actual = runner.invoke(app, ["--format", "json", "fix", str(path)])
    assert actual.exit_code == 0, actual.output
    modified = path.read_bytes()
    assert modified.startswith(bom + cookie.replace("\n", newline).encode(encoding))
    assert b"Raises:" in modified
    assert modified.endswith(f"# untouched café{newline}".encode(encoding))
    stripped = modified.replace(newline.encode(encoding), b"")
    assert b"\r" not in stripped and b"\n" not in stripped


def test_fix_keeps_offsets_past_non_newline_separators(project):
    """A Latin-1 NEL byte before the symbol does not shift the scaffold."""
    source = (
        "# coding: latin-1\r\n# page\x85break caf\xe9\r\ndef f(x):\r\n"
        '    """Do.\r\n\r\n    Args:\r\n        x: V.\r\n    """\r\n'
        '    raise ValueError("x")\r\n'
    )
    path = project / "nel.py"
    original = source.encode("latin-1")
    path.write_bytes(original)
    result = runner.invoke(app, ["--format", "json", "fix", str(path)])
    assert result.exit_code == 0, result.output
    modified = path.read_bytes()
    head, tail = original.split(b'    """\r\n    raise', 1)
    raises = b"\r\n    Raises:\r\n        ValueError: [TODO: describe when this is raised]\r\n"
    assert modified.startswith(head + raises)
    assert modified.endswith(b'    """\r\n    raise' + tail)
    assert modified.count(b"\x85") == 1
    assert b"\n" not in modified.replace(b"\r\n", b"")


def test_read_failure_is_json_and_diagnostic_once(project, monkeypatch):
    """A read error survives multiple check consumers without duplicate notices."""
    from pathlib import Path

    path = project / "unreadable.py"
    path.write_text('"""Module."""\n')
    original_read = Path.read_bytes

    def fail_selected(self):
        if self == path:
            raise PermissionError("permission denied for regression")
        return original_read(self)

    monkeypatch.setattr(Path, "read_bytes", fail_selected)
    result = runner.invoke(app, ["--format", "json", "check", str(path)])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["run"]["input_errors"][0]["kind"] == "read"
    assert result.stderr.count(": read:") == 1


@pytest.mark.parametrize("candidate", ["missing.py", "directory.py", "notes.txt"])
def test_invalid_explicit_targets_in_json_output_file(project, candidate):
    """Invalid explicit targets remain machine readable with --output."""
    (project / "directory.py").mkdir()
    (project / "notes.txt").write_text("notes")
    output = project / "result.json"
    result = runner.invoke(
        app,
        ["--format", "json", "--output", str(output), "check", "--files", candidate],
    )
    assert result.exit_code == 1
    assert result.stdout == ""
    data = json.loads(output.read_text())
    assert data["run"]["status"] == "incomplete"
    assert data["run"]["input_errors"][0]["kind"] == "input"
    assert data["summary"]["files_attempted"] == 1


def test_coverage_only_does_not_parse_source(project):
    """Package visibility analysis does not claim a source parsing failure."""
    path = project / "bad.py"
    path.write_bytes(b"def broken(:\n")
    result = runner.invoke(app, ["--format", "json", "coverage", str(path)])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["run"]["input_errors"] == []
    assert data["summary"]["files_analyzed"] == 1


def test_latin1_suppression_uses_decoded_source(project):
    """Declared encoding also governs suppression parsing."""
    path = project / "suppressed.py"
    path.write_bytes(
        "# coding: latin-1\n# café\n# docvet: ignore-file[missing-raises]\n"
        'def f():\n    """Work."""\n    raise ValueError("café")\n'.encode("latin-1")
    )
    result = runner.invoke(app, ["--format", "json", "enrichment", str(path)])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert not any(f["rule"] == "missing-raises" for f in data["findings"])
    assert any(f["rule"] == "missing-raises" for f in data["suppressed"])


def test_failed_replacement_encoding_leaves_original_intact(project, monkeypatch):
    """Unrepresentable scaffold output becomes a controlled write failure."""
    path = project / "ascii.py"
    original = b'# coding: ascii\ndef f():\n    """Work."""\n    raise ValueError()\n'
    path.write_bytes(original)
    monkeypatch.setattr(
        "docvet.checks.fix.scaffold_missing_sections",
        lambda source, tree, findings: source + "# café\n",
    )
    result = runner.invoke(app, ["--format", "json", "fix", str(path)])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["run"]["input_errors"][0]["kind"] == "write"
    assert path.read_bytes() == original


def test_fix_suppression_uses_updated_line_positions(project):
    """Scaffolding earlier docstrings moves later suppression directives."""
    path = project / "shifted.py"
    path.write_text(
        '"""Module."""\n'
        'def first():\n    """First."""\n    raise ValueError()\n\n'
        "def second():  # docvet: ignore[scaffold-incomplete]\n"
        '    """Second."""\n    raise ValueError()\n'
    )
    result = runner.invoke(app, ["--format", "json", "fix", str(path)])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert any(f["symbol"] == "first" for f in data["findings"])
    assert not any(f["symbol"] == "second" for f in data["findings"])
    assert any(f["symbol"] == "second" for f in data["suppressed"])


@pytest.mark.parametrize("command", ["coverage", "check"])
def test_ignore_file_suppresses_missing_init(project, command):
    """Coverage findings keep their inline suppression contract."""
    (project / "pyproject.toml").write_text(
        '[tool.docvet]\nfail-on = ["coverage"]\nsrc-root = "."\n'
    )
    package = project / "pkg" / "sub"
    package.mkdir(parents=True)
    (project / "pkg" / "__init__.py").write_text('"""Package."""\n')
    (package / "mod.py").write_text(
        '# docvet: ignore-file[missing-init]\n"""Module."""\n'
    )
    result = runner.invoke(app, ["--format", "json", command, "--all"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == "passed"
    assert data["run"]["input_errors"] == []
    assert not any(f["rule"] == "missing-init" for f in data["findings"])
    assert [f["rule"] for f in data["suppressed"]] == ["missing-init"]


def test_coverage_only_suppression_reads_unparseable_source(project):
    """Structural suppression needs decoded comments, not a valid parse."""
    (project / "pyproject.toml").write_text(
        '[tool.docvet]\nfail-on = ["coverage"]\nsrc-root = "."\n'
    )
    package = project / "pkg"
    package.mkdir()
    (package / "broken.py").write_text(
        "# docvet: ignore-file[missing-init]\ndef broken(:\n"
    )
    result = runner.invoke(app, ["--format", "json", "coverage", "--all"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data["run"]["input_errors"] == []
    assert data["summary"]["files_analyzed"] == 1
    assert data["findings"] == []
    assert [f["rule"] for f in data["suppressed"]] == ["missing-init"]


def test_fix_terminal_reports_incomplete_counts(project):
    """Terminal fix output carries the same attempted/failed counts as JSON."""
    good = project / "good.py"
    good.write_text('def f():\n    """Work."""\n    raise ValueError()\n')
    bad = project / "bad.py"
    bad.write_text("def broken(:\n")
    result = runner.invoke(app, ["fix", "--dry-run", str(bad), str(good)])
    assert result.exit_code == 1
    assert "2 files attempted, 1 analyzed, 1 failed" in result.stderr
    assert "Would fix" not in result.stderr
    assert "+++ b/" in result.stdout
