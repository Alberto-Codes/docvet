"""CLI regression coverage for suppression across Python line endings."""

import json

import pytest
from typer.testing import CliRunner

from docvet.cli import app

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize(
    "command,source,rule,line,suppressed",
    [
        (
            "presence",
            b'"""Module."""\ndef f(): # docvet: ignore[missing-docstring]\n    pass\n',
            "missing-docstring",
            2,
            True,
        ),
        (
            "presence",
            b'"""Module."""\n# docvet: ignore-file[missing-docstring]\ndef f():\n    pass\n',
            "missing-docstring",
            3,
            True,
        ),
        (
            "presence",
            b'"""Module."""\ndef f():\n    pass # docvet: ignore[missing-docstring]\n',
            "missing-docstring",
            2,
            False,
        ),
        (
            "coverage",
            b'"""Module."""\n# docvet: ignore-file[missing-init]\nx = 1\n',
            "missing-init",
            1,
            True,
        ),
        (
            "coverage",
            b'"""Module."""\n # docvet: ignore[missing-init]',
            "missing-init",
            1,
            False,
        ),
        (
            "coverage",
            b'"""Module.""" # docvet: ignore[missing-init]\nx = 1\n',
            "missing-init",
            1,
            True,
        ),
    ],
    ids=[
        "presence-inline",
        "presence-file",
        "presence-other-line",
        "coverage-file",
        "coverage-other-line",
        "coverage-inline",
    ],
)
def test_directives_keep_line_scope_and_source_bytes(
    tmp_path, monkeypatch, newline, command, source, rule, line, suppressed
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.docvet]\nsrc-root = "."\nfail-on = ["presence", "coverage"]\n'
    )
    package = tmp_path / "pkg"
    package.mkdir()
    path = package / "module.py"
    original = source.replace(b"\n", newline)
    path.write_bytes(original)

    result = CliRunner().invoke(app, ["--format", "json", command, str(path)])

    assert result.exit_code == (0 if suppressed else 1), result.output
    data = json.loads(result.stdout)
    assert data["run"]["status"] == ("passed" if suppressed else "findings")
    assert data["run"]["input_errors"] == []
    selected = data["suppressed" if suppressed else "findings"]
    assert [(finding["rule"], finding["line"]) for finding in selected] == [
        (rule, line)
    ]
    assert data["findings" if suppressed else "suppressed"] == []
    assert path.read_bytes() == original
