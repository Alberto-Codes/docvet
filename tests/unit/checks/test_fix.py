"""Tests for the section scaffolding engine."""

from __future__ import annotations

import ast
import textwrap
from typing import Literal

import pytest

from docvet.checks import Finding
from docvet.checks.fix import scaffold_missing_sections

pytestmark = pytest.mark.unit

_Category = Literal["required", "recommended", "scaffold"]


def _finding(
    *,
    file: str = "test.py",
    line: int = 1,
    symbol: str = "func",
    rule: str = "missing-raises",
    message: str = "test message",
    category: _Category = "required",
) -> Finding:
    return Finding(
        file=file,
        line=line,
        symbol=symbol,
        rule=rule,
        message=message,
        category=category,
    )


def _scaffold(source: str, findings: list[Finding]) -> str:
    tree = ast.parse(source)
    return scaffold_missing_sections(source, tree, findings)


# ---------------------------------------------------------------------------
# Basic scaffolding (AC 1, 2, 4, 6)
# ---------------------------------------------------------------------------


class TestOnelinerExpansion:
    """AC 1: One-liner docstring expansion with sections."""

    def test_oneliner_raises(self):
        """One-liner expanded to multi-line with Raises section."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate input data."""
                if not data:
                    raise ValueError("empty")
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert "Raises:" in result
        assert "ValueError: [TODO: describe when this is raised]" in result
        assert '"""Validate input data.' in result
        ast.parse(result)  # valid Python

    def test_oneliner_multiple_sections(self):
        """One-liner expanded with multiple sections in canonical order."""
        source = textwrap.dedent('''\
            def process(data) -> str:
                """Process data."""
                if not data:
                    raise ValueError("bad")
                return str(data)
        ''')
        findings = [
            _finding(line=1, rule="missing-returns"),
            _finding(line=1, rule="missing-raises"),
        ]
        result = _scaffold(source, findings)
        ret_pos = result.index("Returns:")
        raises_pos = result.index("Raises:")
        assert ret_pos < raises_pos  # canonical order

    def test_oneliner_single_quotes(self):
        """One-liner with single quotes preserved."""
        source = "def f():\n    '''Summary.'''\n    pass\n"
        result = _scaffold(source, [_finding(line=1, rule="missing-examples")])
        assert "'''" in result
        assert "Examples:" in result
        ast.parse(result)


class TestMultilineInsertion:
    """AC 2: Multi-line docstring insertion preserving existing content."""

    def test_existing_args_preserved_adds_raises(self):
        """Existing Args preserved byte-for-byte when Raises is added."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate input.

                Args:
                    data: The input data.
                """
                if not data:
                    raise ValueError("empty")
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert "Args:\n        data: The input data.\n" in result
        assert "Raises:" in result
        assert "ValueError:" in result
        ast.parse(result)

    def test_multiple_existing_sections_preserved(self):
        """Multiple existing sections preserved, new section inserted."""
        source = textwrap.dedent('''\
            def process(data):
                """Process data.

                Args:
                    data: Input.

                Returns:
                    str: Result.
                """
                if not data:
                    raise ValueError("bad")
                return str(data)
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert "Args:" in result
        assert "Returns:" in result
        assert "Raises:" in result
        ast.parse(result)


class TestClassAttributes:
    """AC 3: Dataclass/NamedTuple/TypedDict Attributes scaffolding."""

    def test_dataclass_attributes(self):
        """Dataclass fields extracted and listed in Attributes section."""
        source = textwrap.dedent('''\
            from dataclasses import dataclass

            @dataclass
            class Config:
                """Configuration settings."""
                host: str
                port: int
        ''')
        result = _scaffold(
            source, [_finding(line=4, symbol="Config", rule="missing-attributes")]
        )
        assert "Attributes:" in result
        assert "host: [TODO: describe]" in result
        assert "port: [TODO: describe]" in result

    def test_namedtuple_attributes(self):
        """NamedTuple fields extracted."""
        source = textwrap.dedent('''\
            from typing import NamedTuple

            class Point(NamedTuple):
                """A 2D point."""
                x: float
                y: float
        ''')
        result = _scaffold(
            source, [_finding(line=3, symbol="Point", rule="missing-attributes")]
        )
        assert "x: [TODO: describe]" in result
        assert "y: [TODO: describe]" in result


class TestGeneratorSections:
    """AC 4: Generator Yields and Receives scaffolding."""

    def test_yields_and_receives(self):
        """Both Yields and Receives scaffolded with generic placeholders."""
        source = textwrap.dedent('''\
            def gen():
                """Generate items."""
                val = yield 1
        ''')
        findings = [
            _finding(line=1, rule="missing-yields"),
            _finding(line=1, rule="missing-receives"),
        ]
        result = _scaffold(source, findings)
        assert "Yields:" in result
        assert "Receives:" in result
        y_pos = result.index("Yields:")
        r_pos = result.index("Receives:")
        assert y_pos < r_pos  # canonical order


class TestExamplesSection:
    """AC 5: Examples section with doctest-style placeholder."""

    def test_examples_fenced_code_placeholder(self):
        """Examples section uses doctest-style placeholder."""
        source = textwrap.dedent('''\
            class Foo:
                """A foo class."""
                pass
        ''')
        result = _scaffold(
            source, [_finding(line=1, symbol="Foo", rule="missing-examples")]
        )
        assert "Examples:" in result
        assert ">>> # [TODO: add example usage]" in result


# ---------------------------------------------------------------------------
# Determinism and idempotency (AC 6, 7)
# ---------------------------------------------------------------------------


class TestDeterminism:
    """AC 6: Same input = same output."""

    def test_deterministic_output(self):
        """Running scaffold twice produces identical results."""
        source = textwrap.dedent('''\
            def f():
                """Do stuff."""
                raise ValueError("x")
        ''')
        findings = [_finding(line=1, rule="missing-raises")]
        result1 = _scaffold(source, findings)
        result2 = _scaffold(source, findings)
        assert result1 == result2


class TestIdempotency:
    """AC 7: Scaffold is idempotent — second run produces no changes."""

    def test_second_run_no_changes(self):
        """Running scaffold on already-scaffolded source makes no changes."""
        source = textwrap.dedent('''\
            def f():
                """Do stuff."""
                raise ValueError("x")
        ''')
        findings = [_finding(line=1, rule="missing-raises")]
        first = _scaffold(source, findings)
        # Re-parse the scaffolded source and run again
        tree2 = ast.parse(first)
        second = scaffold_missing_sections(first, tree2, findings)
        assert first == second

    def test_existing_section_not_duplicated(self):
        """Section already present in docstring is not duplicated."""
        source = textwrap.dedent('''\
            def f():
                """Do stuff.

                Raises:
                    ValueError: When bad.
                """
                raise ValueError("x")
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert result == source  # no changes


# ---------------------------------------------------------------------------
# Mixed symbols (AC 8)
# ---------------------------------------------------------------------------


class TestMixedSymbols:
    """AC 8: Only incomplete symbols modified."""

    def test_complete_symbol_untouched(self):
        """Complete symbol's docstring is not modified."""
        source = textwrap.dedent('''\
            def complete():
                """Complete function.

                Raises:
                    ValueError: When bad.
                """
                raise ValueError("x")

            def incomplete():
                """Incomplete function."""
                raise TypeError("y")
        ''')
        findings = [_finding(line=9, symbol="incomplete", rule="missing-raises")]
        result = _scaffold(source, findings)
        # complete() unchanged
        assert "Complete function." in result
        assert result.count("Raises:") == 2  # one existing + one scaffolded
        # incomplete() scaffolded
        assert "TypeError:" in result


# ---------------------------------------------------------------------------
# Section-specific enrichment (AST re-extraction)
# ---------------------------------------------------------------------------


class TestSectionSpecificEnrichment:
    """Section-specific placeholders from AST re-extraction."""

    def test_raises_with_multiple_exceptions(self):
        """Multiple raised exceptions listed individually."""
        source = textwrap.dedent('''\
            def validate(data):
                """Validate data."""
                if not data:
                    raise ValueError("empty")
                if not isinstance(data, dict):
                    raise TypeError("not dict")
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert "ValueError: [TODO: describe when this is raised]" in result
        assert "TypeError: [TODO: describe when this is raised]" in result

    def test_returns_with_annotation(self):
        """Return type from annotation used in placeholder."""
        source = textwrap.dedent('''\
            def get_name() -> str:
                """Get the name."""
                return "foo"
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-returns")])
        assert "str: [TODO: describe return value]" in result

    def test_returns_without_annotation(self):
        """Generic placeholder when no return annotation."""
        source = textwrap.dedent('''\
            def get_name():
                """Get the name."""
                return "foo"
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-returns")])
        assert "[TODO: describe return value]" in result
        assert "str:" not in result


# ---------------------------------------------------------------------------
# Edge cases from POC (spike section 2.3)
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases validated by the POC."""

    def test_empty_findings_returns_source(self):
        """Empty findings list returns source unchanged."""
        source = "def f():\n    '''Summary.'''\n    pass\n"
        assert _scaffold(source, []) == source

    def test_no_actionable_findings(self):
        """Findings with non-scaffold rules return source unchanged."""
        source = "def f():\n    '''Summary.'''\n    pass\n"
        findings = [_finding(line=1, rule="trivial-docstring")]
        assert _scaffold(source, findings) == source

    def test_nested_class_method(self):
        """Nested method in class gets correct indentation."""
        source = textwrap.dedent('''\
            class Outer:
                """Outer class."""

                def method(self):
                    """Do something."""
                    raise ValueError("x")
        ''')
        result = _scaffold(
            source, [_finding(line=4, symbol="method", rule="missing-raises")]
        )
        assert "Raises:" in result
        ast.parse(result)

    def test_async_function(self):
        """Async function handled correctly."""
        source = textwrap.dedent('''\
            async def fetch(url):
                """Fetch data."""
                raise ConnectionError("failed")
        ''')
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert "ConnectionError:" in result
        ast.parse(result)

    def test_decorated_function(self):
        """Decorated function scaffolded correctly."""
        source = textwrap.dedent('''\
            @staticmethod
            def process():
                """Process data."""
                raise RuntimeError("boom")
        ''')
        result = _scaffold(source, [_finding(line=2, rule="missing-raises")])
        assert "RuntimeError:" in result
        ast.parse(result)

    def test_raw_docstring(self):
        """Raw docstring prefix preserved."""
        source = 'def f():\n    r"""Raw summary."""\n    raise ValueError("x")\n'
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert 'r"""' in result
        assert "Raises:" in result
        ast.parse(result)

    def test_tab_indentation(self):
        """Tab-indented code handled correctly."""
        source = 'def f():\n\t"""Summary."""\n\traise ValueError(\'x\')\n'
        result = _scaffold(source, [_finding(line=1, rule="missing-raises")])
        assert "Raises:" in result
        ast.parse(result)

    def test_module_level_docstring_untouched(self):
        """Module-level docstring is not modified when function is targeted."""
        source = textwrap.dedent('''\
            """Module docstring."""

            def f():
                """Function docstring."""
                raise ValueError("x")
        ''')
        result = _scaffold(source, [_finding(line=3, rule="missing-raises")])
        assert result.startswith('"""Module docstring."""')
        assert "Raises:" in result
        ast.parse(result)

    def test_multiple_symbols_reverse_order(self):
        """Multiple symbols processed in reverse order preserving line numbers."""
        source = textwrap.dedent('''\
            def first():
                """First function."""
                raise ValueError("a")

            def second():
                """Second function."""
                raise TypeError("b")
        ''')
        findings = [
            _finding(line=1, symbol="first", rule="missing-raises"),
            _finding(line=5, symbol="second", rule="missing-raises"),
        ]
        result = _scaffold(source, findings)
        assert result.count("Raises:") == 2
        assert "ValueError:" in result
        assert "TypeError:" in result
        ast.parse(result)

    def test_dataclass_with_decorator(self):
        """Dataclass with @dataclass decorator scaffolded correctly."""
        source = textwrap.dedent('''\
            from dataclasses import dataclass

            @dataclass
            class Settings:
                """Application settings."""
                debug: bool
                port: int
                host: str
        ''')
        result = _scaffold(
            source,
            [_finding(line=4, symbol="Settings", rule="missing-attributes")],
        )
        assert "debug: [TODO: describe]" in result
        assert "port: [TODO: describe]" in result
        assert "host: [TODO: describe]" in result
        ast.parse(result)
