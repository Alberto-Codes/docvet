"""Tests for the scaffold-incomplete enrichment rule."""

from __future__ import annotations

import ast
import textwrap

import pytest

from docvet.checks import Finding, check_enrichment
from docvet.config import EnrichmentConfig

pytestmark = pytest.mark.unit


def _check(source: str, *, config: EnrichmentConfig | None = None) -> list[Finding]:
    tree = ast.parse(source)
    cfg = config or EnrichmentConfig()
    return check_enrichment(source, tree, cfg, "test.py")


def _scaffold_findings(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.rule == "scaffold-incomplete"]


# ---------------------------------------------------------------------------
# Detection of TODO markers
# ---------------------------------------------------------------------------


class TestScaffoldDetection:
    """Detect [TODO: ...] markers in docstrings."""

    def test_detects_todo_in_raises_section(self):
        """TODO marker in Raises section produces scaffold finding."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate data.

                Raises:
                    ValueError: [TODO: describe when this is raised]
                """
                raise ValueError("bad")
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 1
        assert findings[0].rule == "scaffold-incomplete"
        assert findings[0].category == "scaffold"
        assert "Raises" in findings[0].message

    def test_detects_todo_in_returns_section(self):
        """TODO marker in Returns section detected."""
        source = textwrap.dedent('''\
            def get_name() -> str:
                """Get name.

                Returns:
                    str: [TODO: describe return value]
                """
                return "foo"
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 1
        assert "Returns" in findings[0].message

    def test_detects_multiple_todo_sections(self):
        """Multiple TODO sections consolidated into one finding per symbol."""
        source = textwrap.dedent('''\
            def process(data) -> str:
                """Process data.

                Args:
                    data: Input data.

                Returns:
                    str: [TODO: describe return value]

                Raises:
                    ValueError: [TODO: describe when this is raised]
                """
                if not data:
                    raise ValueError("bad")
                return str(data)
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 1
        assert "Returns" in findings[0].message
        assert "Raises" in findings[0].message


# ---------------------------------------------------------------------------
# No false positives
# ---------------------------------------------------------------------------


class TestNoFalsePositives:
    """No scaffold findings on real docstring content."""

    def test_no_finding_on_real_raises_content(self):
        """Real Raises content does not trigger scaffold finding."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate data.

                Raises:
                    ValueError: When the input data is empty or None.
                """
                raise ValueError("bad")
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 0

    def test_no_finding_on_function_without_todo(self):
        """Function with complete docstring produces no scaffold finding."""
        source = textwrap.dedent('''\
            def greet(name: str) -> str:
                """Greet a person by name.

                Args:
                    name: The person's name.

                Returns:
                    str: A greeting string.
                """
                return f"Hello, {name}"
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 0

    def test_no_finding_when_no_docstring(self):
        """Symbol without docstring produces no scaffold finding."""
        source = "def f():\n    pass\n"
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 0


# ---------------------------------------------------------------------------
# Config disable
# ---------------------------------------------------------------------------


class TestConfigDisable:
    """Scaffold-incomplete rule can be disabled via config."""

    def test_disabled_produces_no_findings(self):
        """Disabling scaffold_incomplete skips the rule."""
        source = textwrap.dedent('''\
            def f():
                """Do stuff.

                Raises:
                    ValueError: [TODO: describe when this is raised]
                """
                raise ValueError("x")
        ''')
        cfg = EnrichmentConfig(scaffold_incomplete=False)
        findings = _scaffold_findings(_check(source, config=cfg))
        assert len(findings) == 0

    def test_enabled_by_default(self):
        """Scaffold-incomplete is enabled by default."""
        cfg = EnrichmentConfig()
        assert cfg.scaffold_incomplete is True


# ---------------------------------------------------------------------------
# Message format
# ---------------------------------------------------------------------------


class TestMessageFormat:
    """Actionable message format with section names."""

    def test_message_contains_symbol_name(self):
        """Message includes the symbol name."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate data.

                Raises:
                    ValueError: [TODO: describe when this is raised]
                """
                raise ValueError("bad")
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 1
        assert "validate" in findings[0].message

    def test_message_contains_section_name(self):
        """Message includes the section name where TODO was found."""
        source = textwrap.dedent('''\
            class Foo:
                """A foo.

                Attributes:
                    x: [TODO: describe]

                Examples:
                    ```python
                    # [TODO: add example usage]
                    ```
                """
                x: int = 0
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 1
        assert "Attributes" in findings[0].message
        assert "Examples" in findings[0].message

    def test_generic_fallback_when_todo_before_any_section(self):
        """Generic fallback message when TODO appears before any section header."""
        source = textwrap.dedent('''\
            def f():
                """[TODO: describe] this function."""
                pass
        ''')
        findings = _scaffold_findings(_check(source))
        assert len(findings) == 1
        assert "scaffold placeholders" in findings[0].message
        assert "[TODO: ...]" in findings[0].message
