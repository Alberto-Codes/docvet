"""Unit tests for the docvet LSP server module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pygls = pytest.importorskip("pygls")

from lsprotocol import types  # noqa: E402

from docvet.checks import Finding  # noqa: E402
from docvet.config import DocvetConfig  # noqa: E402
from docvet.lsp import (  # noqa: E402
    DOCS_BASE_URL,
    _check_file,
    _finding_to_diagnostic,
    _publish_diagnostics,
    _uri_to_path,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config() -> DocvetConfig:
    """Minimal DocvetConfig for testing."""
    return DocvetConfig(
        project_root=Path("/fake/project"),
        src_root="src",
    )


@pytest.fixture()
def sample_finding() -> Finding:
    """A representative required-category finding."""
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
    """A recommended-category finding."""
    return Finding(
        file="app.py",
        line=5,
        symbol="bar",
        rule="missing-examples",
        message="Docstring missing Examples section.",
        category="recommended",
    )


@pytest.fixture()
def mock_server(config: DocvetConfig) -> MagicMock:
    """A mocked LanguageServer with docvet_config attached."""
    ls = MagicMock()
    ls.docvet_config = config
    ls.workspace.folders = {}
    return ls


# ---------------------------------------------------------------------------
# Task 4: Finding → Diagnostic conversion
# ---------------------------------------------------------------------------


class TestFindingToDiagnostic:
    """Tests for _finding_to_diagnostic."""

    def test_required_category_maps_to_warning(self, sample_finding: Finding) -> None:
        diag = _finding_to_diagnostic(sample_finding)
        assert diag.severity == types.DiagnosticSeverity.Warning

    def test_recommended_category_maps_to_hint(
        self, recommended_finding: Finding
    ) -> None:
        diag = _finding_to_diagnostic(recommended_finding)
        assert diag.severity == types.DiagnosticSeverity.Hint

    def test_all_six_fields_mapped(self, sample_finding: Finding) -> None:
        diag = _finding_to_diagnostic(sample_finding)
        assert diag.message == "Docstring missing Raises section for ValueError."
        assert diag.code == "missing-raises"
        assert diag.source == "Docvet"
        assert diag.severity == types.DiagnosticSeverity.Warning
        assert diag.range.start.line == 9
        assert diag.code_description is not None
        assert diag.code_description.href == f"{DOCS_BASE_URL}/missing-raises/"

    def test_line_number_offset_one_based_to_zero_based(
        self, sample_finding: Finding
    ) -> None:
        diag = _finding_to_diagnostic(sample_finding)
        assert diag.range.start.line == 9
        assert diag.range.end.line == 9
        assert diag.range.start.character == 0
        assert diag.range.end.character == 0

    def test_line_one_maps_to_zero(self) -> None:
        finding = Finding("f.py", 1, "s", "rule", "msg", "required")
        diag = _finding_to_diagnostic(finding)
        assert diag.range.start.line == 0

    def test_source_is_capitalized_docvet(self, sample_finding: Finding) -> None:
        diag = _finding_to_diagnostic(sample_finding)
        assert diag.source == "Docvet"

    def test_code_description_href_links_to_rule_page(
        self, sample_finding: Finding
    ) -> None:
        diag = _finding_to_diagnostic(sample_finding)
        assert diag.code_description is not None
        assert diag.code_description.href == (
            "https://alberto-codes.github.io/docvet/rules/missing-raises/"
        )

    def test_code_description_href_for_different_rule(self) -> None:
        finding = Finding("f.py", 1, "s", "stale-drift", "msg", "recommended")
        diag = _finding_to_diagnostic(finding)
        assert diag.code_description is not None
        assert diag.code_description.href == (
            "https://alberto-codes.github.io/docvet/rules/stale-drift/"
        )


# ---------------------------------------------------------------------------
# Task 5: _check_file orchestrator
# ---------------------------------------------------------------------------


class TestCheckFile:
    """Tests for _check_file orchestrator."""

    def test_enrichment_findings_included(self, config: DocvetConfig) -> None:
        source = 'def foo():\n    """Summary."""\n    raise ValueError("x")\n'
        uri = "file:///fake/project/src/app.py"
        with (
            patch("docvet.lsp.check_enrichment") as mock_enrich,
            patch("docvet.lsp.check_coverage", return_value=[]),
            patch("docvet.lsp.check_griffe_compat", return_value=[]),
            patch("docvet.lsp.server") as mock_srv,
        ):
            mock_srv.workspace.folders = {}
            finding = Finding("app.py", 2, "foo", "missing-raises", "msg", "required")
            mock_enrich.return_value = [finding]
            result = _check_file(uri, source, config)
        assert len(result) == 1
        assert result[0].code == "missing-raises"

    def test_griffe_findings_included(self, config: DocvetConfig) -> None:
        source = "def foo():\n    pass\n"
        uri = "file:///fake/project/src/app.py"
        with (
            patch("docvet.lsp.check_enrichment", return_value=[]),
            patch("docvet.lsp.check_coverage", return_value=[]),
            patch("docvet.lsp.check_griffe_compat") as mock_griffe,
            patch("docvet.lsp.server") as mock_srv,
        ):
            mock_srv.workspace.folders = {}
            finding = Finding(
                "app.py", 1, "foo", "griffe-unknown-param", "msg", "recommended"
            )
            mock_griffe.return_value = [finding]
            result = _check_file(uri, source, config)
        assert len(result) == 1
        assert result[0].code == "griffe-unknown-param"

    def test_griffe_returns_empty_when_exception(self, config: DocvetConfig) -> None:
        source = "def foo():\n    pass\n"
        uri = "file:///fake/project/src/app.py"
        with (
            patch("docvet.lsp.check_enrichment", return_value=[]),
            patch("docvet.lsp.check_coverage", return_value=[]),
            patch(
                "docvet.lsp.check_griffe_compat",
                side_effect=ImportError("no griffe"),
            ),
            patch("docvet.lsp.server") as mock_srv,
        ):
            mock_srv.workspace.folders = {}
            result = _check_file(uri, source, config)
        assert result == []

    def test_coverage_findings_included(self, config: DocvetConfig) -> None:
        source = "x = 1\n"
        uri = "file:///fake/project/src/app.py"
        with (
            patch("docvet.lsp.check_enrichment", return_value=[]),
            patch("docvet.lsp.check_coverage") as mock_cov,
            patch("docvet.lsp.check_griffe_compat", return_value=[]),
            patch("docvet.lsp.server") as mock_srv,
        ):
            mock_srv.workspace.folders = {}
            finding = Finding("src/pkg", 1, "pkg", "missing-init", "msg", "required")
            mock_cov.return_value = [finding]
            result = _check_file(uri, source, config)
        assert len(result) == 1
        assert result[0].code == "missing-init"

    def test_no_findings_returns_empty(self, config: DocvetConfig) -> None:
        source = "x = 1\n"
        uri = "file:///fake/project/src/app.py"
        with (
            patch("docvet.lsp.check_enrichment", return_value=[]),
            patch("docvet.lsp.check_coverage", return_value=[]),
            patch("docvet.lsp.check_griffe_compat", return_value=[]),
            patch("docvet.lsp.server") as mock_srv,
        ):
            mock_srv.workspace.folders = {}
            result = _check_file(uri, source, config)
        assert result == []

    def test_syntax_error_returns_empty(self, config: DocvetConfig) -> None:
        source = "def foo(\n"
        uri = "file:///fake/project/src/app.py"
        result = _check_file(uri, source, config)
        assert result == []

    def test_non_python_file_returns_empty(self, config: DocvetConfig) -> None:
        uri = "file:///fake/project/README.md"
        result = _check_file(uri, "# Title", config)
        assert result == []


# ---------------------------------------------------------------------------
# Task 6: LSP event handlers and CLI command
# ---------------------------------------------------------------------------


class TestDidOpen:
    """Tests for the didOpen handler."""

    def test_publishes_diagnostics(self, mock_server: MagicMock) -> None:
        params = types.DidOpenTextDocumentParams(
            text_document=types.TextDocumentItem(
                uri="file:///fake/project/src/app.py",
                language_id="python",
                version=1,
                text="x = 1\n",
            )
        )
        with (
            patch("docvet.lsp._check_file", return_value=[]) as mock_check,
        ):
            _publish_diagnostics(
                mock_server,
                params.text_document.uri,
                params.text_document.text,
            )
        mock_check.assert_called_once_with(
            "file:///fake/project/src/app.py",
            "x = 1\n",
            mock_server.docvet_config,
        )
        mock_server.text_document_publish_diagnostics.assert_called_once()


class TestDidSave:
    """Tests for the didSave handler."""

    def test_publishes_diagnostics_with_text(self, mock_server: MagicMock) -> None:
        params = types.DidSaveTextDocumentParams(
            text_document=types.TextDocumentIdentifier(
                uri="file:///fake/project/src/app.py",
            ),
            text="x = 1\n",
        )
        assert params.text is not None
        with patch("docvet.lsp._check_file", return_value=[]):
            _publish_diagnostics(
                mock_server,
                params.text_document.uri,
                params.text,
            )
        mock_server.text_document_publish_diagnostics.assert_called_once()

    def test_falls_back_to_workspace_doc_when_text_none(
        self, mock_server: MagicMock
    ) -> None:
        mock_doc = MagicMock()
        mock_doc.source = "fallback_source\n"
        mock_server.workspace.get_text_document.return_value = mock_doc

        uri = "file:///fake/project/src/app.py"

        # Simulate the didSave handler fallback logic
        source = None
        if source is None:
            doc = mock_server.workspace.get_text_document(uri)
            source = doc.source

        with patch("docvet.lsp._check_file", return_value=[]) as mock_check:
            _publish_diagnostics(mock_server, uri, source)

        mock_check.assert_called_once_with(
            uri, "fallback_source\n", mock_server.docvet_config
        )

    def test_non_python_publishes_empty(self, mock_server: MagicMock) -> None:
        uri = "file:///fake/project/README.md"
        with patch("docvet.lsp._check_file", return_value=[]) as mock_check:
            _publish_diagnostics(mock_server, uri, "# Title")
        mock_check.assert_called_once()
        call_args = mock_server.text_document_publish_diagnostics.call_args
        params = call_args[0][0]
        assert params.diagnostics == []


class TestCliLspCommand:
    """Tests for the docvet lsp CLI command."""

    def test_lsp_help_succeeds(self) -> None:
        from typer.testing import CliRunner

        from docvet.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["lsp", "--help"])
        assert result.exit_code == 0
        assert "LSP server" in result.output

    def test_graceful_error_when_pygls_missing(self) -> None:
        from typer.testing import CliRunner

        from docvet.cli import app

        runner = CliRunner()
        with patch.dict("sys.modules", {"docvet.lsp": None}):
            result = runner.invoke(app, ["lsp"])
        assert result.exit_code == 1
        assert "pygls" in result.output


# ---------------------------------------------------------------------------
# URI conversion
# ---------------------------------------------------------------------------


class TestUriToPath:
    """Tests for _uri_to_path."""

    def test_simple_file_uri(self) -> None:
        result = _uri_to_path("file:///home/user/project/app.py")
        assert result == Path("/home/user/project/app.py")

    def test_uri_with_encoded_spaces(self) -> None:
        result = _uri_to_path("file:///home/user/my%20project/app.py")
        assert result == Path("/home/user/my project/app.py")
