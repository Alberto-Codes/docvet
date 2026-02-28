"""LSP server for real-time docstring diagnostics.

Provides a pygls-based Language Server Protocol server that publishes
docstring quality diagnostics on ``textDocument/didOpen`` and
``textDocument/didSave`` events. The server runs enrichment, coverage,
and griffe compatibility checks on individual files, converting
:class:`~docvet.checks.Finding` objects to LSP ``Diagnostic`` instances
with appropriate severity, source, and documentation links. Internal
helpers thread the ``ls`` server instance explicitly for testability
rather than accessing the module-level ``server`` global.

Freshness checks are excluded because they require git context that is
not available in single-file LSP mode.

Attributes:
    DOCS_BASE_URL: Base URL for rule documentation pages.
    server: The pygls ``LanguageServer`` instance.

Examples:
    Start the server on stdio (typically invoked by an editor)::

        $ docvet lsp

    Install with the ``[lsp]`` extra::

        $ pip install docvet[lsp]

See Also:
    [`docvet.checks`][]: Check modules that produce Finding objects.
    [`docvet.config`][]: Configuration loaded on server startup.
    [`docvet.cli`][]: CLI entry point with the ``lsp`` subcommand.
"""

from __future__ import annotations

import ast
from pathlib import Path
from urllib.parse import unquote, urlparse

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from docvet.checks import Finding, check_coverage, check_enrichment, check_griffe_compat
from docvet.config import DocvetConfig, load_config

__all__ = ["start_server"]

DOCS_BASE_URL = "https://alberto-codes.github.io/docvet/rules"

_CATEGORY_TO_SEVERITY: dict[str, types.DiagnosticSeverity] = {
    "required": types.DiagnosticSeverity.Warning,
    "recommended": types.DiagnosticSeverity.Hint,
}

server = LanguageServer(
    name="docvet",
    version="1",
    text_document_sync_kind=types.TextDocumentSyncKind.Full,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finding_to_diagnostic(finding: Finding) -> types.Diagnostic:
    """Convert a Finding to an LSP Diagnostic.

    Maps Finding fields to Diagnostic fields: ``line`` to ``range``
    (1-based → 0-based), ``message`` to ``message``, ``rule`` to
    ``code``, and ``category`` to ``severity``. Sets ``source`` to
    ``"Docvet"`` and ``codeDescription.href`` to the rule documentation
    URL.

    Args:
        finding: The docvet finding to convert.

    Returns:
        An LSP Diagnostic ready for publishing.
    """
    line = max(finding.line - 1, 0)
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=line, character=0),
            end=types.Position(line=line, character=0),
        ),
        message=finding.message,
        severity=_CATEGORY_TO_SEVERITY.get(
            finding.category, types.DiagnosticSeverity.Warning
        ),
        source="Docvet",
        code=finding.rule,
        code_description=types.CodeDescription(
            href=f"{DOCS_BASE_URL}/{finding.rule}/",
        ),
    )


def _uri_to_path(uri: str) -> Path:
    """Convert a ``file://`` URI to a local ``Path``.

    Percent-decodes the URI path component (e.g., ``%20`` to space).

    Args:
        uri: A ``file://`` URI string.

    Returns:
        The corresponding local filesystem path.
    """
    parsed = urlparse(uri)
    return Path(unquote(parsed.path))


def _resolve_src_root(ls: LanguageServer, config: DocvetConfig) -> Path:
    """Resolve the source root from workspace folders or config.

    Uses the first LSP workspace folder if available, otherwise falls
    back to ``config.project_root``. Appends the configured
    ``src_root`` subdirectory.

    Args:
        ls: The language server instance.
        config: The loaded docvet configuration.

    Returns:
        The resolved source root path.
    """
    workspace_folders = ls.workspace.folders
    if workspace_folders:
        first_uri = next(iter(workspace_folders))
        base = _uri_to_path(first_uri)
    else:
        base = config.project_root
    return base / config.src_root


def _check_file(
    ls: LanguageServer,
    uri: str,
    source: str,
    config: DocvetConfig,
) -> list[types.Diagnostic]:
    """Run all applicable checks on a single file and return diagnostics.

    Parses the source into an AST, then runs enrichment, coverage, and
    griffe compatibility checks. Collects all findings and converts them
    to LSP diagnostics. Returns an empty list if the source has syntax
    errors or the file is not a Python file.

    Args:
        ls: The language server instance.
        uri: The document URI.
        source: The full document text.
        config: The loaded docvet configuration.

    Returns:
        A list of LSP Diagnostic objects for the file.
    """
    file_path = _uri_to_path(uri)
    if file_path.suffix != ".py":
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    findings: list[Finding] = []

    findings.extend(check_enrichment(source, tree, config.enrichment, str(file_path)))

    src_root = _resolve_src_root(ls, config)
    findings.extend(check_coverage(src_root, [file_path]))

    try:
        findings.extend(check_griffe_compat(src_root, [file_path]))
    except (ImportError, OSError):
        pass

    return [_finding_to_diagnostic(f) for f in findings]


def _publish_diagnostics(
    ls: LanguageServer,
    uri: str,
    source: str,
) -> None:
    """Run checks and publish diagnostics for a document.

    Shared helper called by both ``didOpen`` and ``didSave`` handlers.
    Loads config from the server object, runs checks, and publishes
    the resulting diagnostics.

    Args:
        ls: The language server instance.
        uri: The document URI.
        source: The full document text.
    """
    config: DocvetConfig = ls.docvet_config  # type: ignore[attr-defined]
    diagnostics = _check_file(ls, uri, source, config)
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(
            uri=uri,
            diagnostics=diagnostics,
        )
    )


# ---------------------------------------------------------------------------
# LSP event handlers
# ---------------------------------------------------------------------------


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: LanguageServer,
    params: types.DidOpenTextDocumentParams,
) -> None:
    """Handle ``textDocument/didOpen`` by publishing diagnostics.

    Args:
        ls: The language server instance.
        params: The open notification parameters.
    """
    _publish_diagnostics(ls, params.text_document.uri, params.text_document.text)


@server.feature(
    types.TEXT_DOCUMENT_DID_SAVE,
    types.SaveOptions(include_text=True),
)
def did_save(
    ls: LanguageServer,
    params: types.DidSaveTextDocumentParams,
) -> None:
    """Handle ``textDocument/didSave`` by re-publishing diagnostics.

    Falls back to the workspace document source when ``params.text`` is
    ``None`` (some clients ignore ``SaveOptions.include_text``).

    Args:
        ls: The language server instance.
        params: The save notification parameters.
    """
    source = params.text
    if source is None:
        doc = ls.workspace.get_text_document(params.text_document.uri)
        source = doc.source
    _publish_diagnostics(ls, params.text_document.uri, source)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def start_server() -> None:
    """Start the LSP server on stdio.

    Loads docvet configuration and attaches it to the server instance,
    then starts the pygls server in stdio mode.

    Examples:
        Typically invoked by the ``docvet lsp`` CLI command::

            from docvet.lsp import start_server

            start_server()
    """
    server.docvet_config = load_config()  # type: ignore[attr-defined]
    server.start_io()
