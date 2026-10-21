"""Unit tests for the core rule catalog and its MCP-free import path.

Tests cover:
- ``import docvet.cli`` does not import the MCP SDK
- Suppression rule validation works on a base install (no ``mcp`` extra)
- ``docvet.mcp`` re-exports the core catalog objects

See Also:
    [`docvet.rules`][]: Rule catalog shared by the CLI and MCP server.
    [`docvet.cli._suppression`][]: Suppression parsing and validation.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.unit

_BLOCK_MCP = textwrap.dedent("""\
    import sys

    # Simulate a base install: the mcp SDK cannot be imported.
    sys.modules["mcp"] = None
    sys.modules["mcp.server"] = None
    sys.modules["mcp.server.fastmcp"] = None
    """)


def _run_python(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


class TestCliImportIsMcpFree:
    def test_import_docvet_cli_does_not_import_mcp(self) -> None:
        result = _run_python(
            "import docvet.cli, sys\n"
            "assert 'mcp' not in sys.modules, 'mcp imported by docvet.cli'\n"
            "assert 'docvet.mcp' not in sys.modules, 'docvet.mcp imported'\n"
        )

        assert result.returncode == 0, result.stderr


class TestSuppressionWithoutMcpExtra:
    def test_invalid_rule_warning_fires_without_mcp_extra(self) -> None:
        script = _BLOCK_MCP + textwrap.dedent("""\
            from docvet.cli import _suppression

            assert _suppression.KNOWN_RULES, "KNOWN_RULES is empty"
            assert "missing-raises" in _suppression.KNOWN_RULES
            source = "def foo():  # docvet: ignore[not-a-rule]\\n    pass\\n"
            smap = _suppression.parse_suppression_directives(source, "test.py")
            # Unknown rules are warned about but still recorded.
            assert smap.line_directives[1] == {"not-a-rule"}, smap.line_directives
            """)

        result = _run_python(script)

        assert result.returncode == 0, result.stderr
        assert "warning: test.py:1: unknown rule 'not-a-rule'" in result.stderr

    def test_known_rule_produces_no_warning_without_mcp_extra(self) -> None:
        script = _BLOCK_MCP + textwrap.dedent("""\
            from docvet.cli._suppression import parse_suppression_directives

            source = "def foo():  # docvet: ignore[missing-raises]\\n    pass\\n"
            parse_suppression_directives(source, "test.py")
            """)

        result = _run_python(script)

        assert result.returncode == 0, result.stderr
        assert "unknown rule" not in result.stderr


class TestRuleCatalog:
    def test_rule_to_check_covers_every_catalog_entry(self) -> None:
        from docvet.rules import _RULE_CATALOG, _RULE_TO_CHECK

        assert len(_RULE_TO_CHECK) == len(_RULE_CATALOG)
        assert all(_RULE_TO_CHECK[r["name"]] == r["check"] for r in _RULE_CATALOG)

    def test_mcp_reexports_the_core_catalog(self) -> None:
        pytest.importorskip("mcp")
        import docvet.mcp
        import docvet.rules

        assert docvet.mcp._RULE_CATALOG is docvet.rules._RULE_CATALOG
        assert docvet.mcp._RULE_TO_CHECK is docvet.rules._RULE_TO_CHECK
        assert docvet.mcp.RuleCatalogEntry is docvet.rules.RuleCatalogEntry
