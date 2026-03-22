"""Tests for reverse enrichment checks.

Covers ``extra-raises-in-docstring``, ``extra-yields-in-docstring``,
``extra-returns-in-docstring`` rules (story 35.3), including skip logic
for interface-documentation functions, scope-aware walking, exception
chaining, and shared config toggle gating.
"""

from __future__ import annotations

import ast
import textwrap

import pytest

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _build_node_index,
    _check_extra_raises_in_docstring,
    _check_extra_returns_in_docstring,
    _check_extra_yields_in_docstring,
    _parse_raises_entries,
    _parse_sections,
    _should_skip_reverse_check,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_active_style():
    """Reset module-level _active_style after each test."""
    import docvet.checks.enrichment as enrichment_mod

    yield
    enrichment_mod._active_style = "google"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_symbol_and_index(source: str):
    """Build a symbol + node_index + tree from inline source."""
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(textwrap.dedent(source))
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    func_symbols = [s for s in symbols if s.kind in ("function", "method")]
    if not func_symbols:
        func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


# ===========================================================================
# _parse_raises_entries tests (Task 7.10-7.12)
# ===========================================================================


class TestParseRaisesEntries:
    """Tests for the _parse_raises_entries helper."""

    def test_google_style_single_entry(self):
        """Google-style Raises section with one exception."""
        docstring = textwrap.dedent("""\
            Summary.

            Raises:
                ValueError: If input is invalid.
        """)
        result = _parse_raises_entries(docstring, style="google")
        assert result == {"ValueError"}

    def test_google_style_multiple_entries(self):
        """Google-style Raises section with multiple exceptions."""
        docstring = textwrap.dedent("""\
            Summary.

            Raises:
                ValueError: If input is invalid.
                TypeError: If wrong type.
                KeyError: If key missing.
        """)
        result = _parse_raises_entries(docstring, style="google")
        assert result == {"ValueError", "TypeError", "KeyError"}

    def test_google_style_continuation_lines_not_parsed(self):
        """Continuation lines must not be parsed as exception names."""
        docstring = textwrap.dedent("""\
            Summary.

            Raises:
                ValueError: If the input
                    is not valid and needs checking.
                TypeError: If wrong type.
        """)
        result = _parse_raises_entries(docstring, style="google")
        assert result == {"ValueError", "TypeError"}

    def test_google_style_no_raises_section(self):
        """No Raises section returns empty set."""
        docstring = "Summary.\n\nArgs:\n    x: A value.\n"
        result = _parse_raises_entries(docstring, style="google")
        assert result == set()

    def test_sphinx_style(self):
        """Sphinx :raises ExcType: pattern extraction."""
        docstring = textwrap.dedent("""\
            Summary.

            :raises ValueError: If input is invalid.
            :raises TypeError: If wrong type.
        """)
        result = _parse_raises_entries(docstring, style="sphinx")
        assert result == {"ValueError", "TypeError"}

    def test_sphinx_style_no_raises(self):
        """Sphinx docstring with no :raises: returns empty set."""
        docstring = ":param x: A value.\n:returns: Something.\n"
        result = _parse_raises_entries(docstring, style="sphinx")
        assert result == set()


# ===========================================================================
# extra-raises-in-docstring tests (Task 7.2-7.14)
# ===========================================================================


class TestExtraRaisesInDocstring:
    """Tests for _check_extra_raises_in_docstring."""

    def test_documented_exception_not_raised_emits_finding(self):
        """AC 1: Raises ValueError documented but not raised -> finding."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            x = 1
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert isinstance(result, Finding)
        assert result.rule == "extra-raises-in-docstring"
        assert result.symbol == "foo"
        assert result.file == "test.py"
        assert result.line == symbol.line
        assert result.category == "recommended"
        assert "ValueError" in result.message

    def test_all_documented_exceptions_raised_no_finding(self):
        """AC 2: All documented exceptions raised -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            raise ValueError("bad")
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    @pytest.mark.parametrize(
        "source",
        [
            textwrap.dedent("""\
                def foo():
                    \"\"\"Summary.

                    Raises:
                        ValueError: If bad.
                    \"\"\"
                    def inner():
                        raise ValueError('bad')
            """),
            textwrap.dedent("""\
                def foo():
                    \"\"\"Summary.

                    Raises:
                        ValueError: If bad.
                    \"\"\"
                    async def inner():
                        raise ValueError('bad')
            """),
            textwrap.dedent("""\
                def foo():
                    \"\"\"Summary.

                    Raises:
                        ValueError: If bad.
                    \"\"\"
                    class Inner:
                        def m(self):
                            raise ValueError('bad')
            """),
        ],
        ids=["sync-func", "async-func", "nested-class"],
    )
    def test_nested_raise_not_counted(self, source):
        """AC 5: Nested raise not counted for outer function."""
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-raises-in-docstring"
        assert result.category == "recommended"
        assert "ValueError" in result.message

    def test_bare_reraise_not_matched(self):
        """AC 6: Bare raise (re-raise) does not match documented exceptions."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            try:
                pass
            except Exception:
                raise
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-raises-in-docstring"
        assert result.category == "recommended"
        assert "ValueError" in result.message

    def test_multiple_extra_exceptions(self):
        """Multiple extra exceptions listed in single finding."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
                TypeError: If wrong.
                KeyError: If missing.
            """
            raise ValueError("bad")
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-raises-in-docstring"
        assert result.category == "recommended"
        assert "KeyError" in result.message
        assert "TypeError" in result.message
        assert "ValueError" not in result.message

    def test_no_raises_section_no_finding(self):
        """No Raises section -> guard returns None."""
        source = '''\
        def foo():
            """Summary."""
            pass
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_config_disable_no_finding(self):
        """AC 8: require_raises=False skips both forward and reverse."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            pass
        '''
        symbol, node_index, tree = _make_symbol_and_index(source)
        config = EnrichmentConfig(require_raises=False)

        findings = check_enrichment(textwrap.dedent(source), tree, config, "test.py")

        assert not any(f.rule == "extra-raises-in-docstring" for f in findings)
        assert not any(f.rule == "missing-raises" for f in findings)

    def test_class_symbol_no_finding(self):
        """Class symbol -> guard returns None."""
        source = '''\
        class Foo:
            """Summary.

            Raises:
                ValueError: If bad.
            """
            pass
        '''
        from docvet.ast_utils import get_documented_symbols

        tree = ast.parse(textwrap.dedent(source))
        symbols = get_documented_symbols(tree)
        node_index = _build_node_index(tree)
        symbol = [s for s in symbols if s.kind == "class"][0]
        assert symbol.docstring is not None
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_exception_chaining_raise_from(self):
        """Raise X from Y: X in code_raises, not Y."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            try:
                pass
            except Exception as e:
                raise ValueError("bad") from e
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_partial_match_only_extra_flagged(self):
        """Raises: ValueError, TypeError but code only raises ValueError."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
                TypeError: If wrong.
            """
            raise ValueError("bad")
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-raises-in-docstring"
        assert result.category == "recommended"
        assert "TypeError" in result.message
        assert "ValueError" not in result.message


# ===========================================================================
# extra-yields-in-docstring tests (Task 7.15-7.19)
# ===========================================================================


class TestExtraYieldsInDocstring:
    """Tests for _check_extra_yields_in_docstring."""

    def test_yields_section_no_yield_emits_finding(self):
        """AC 3: Yields section but no yield -> finding."""
        source = '''\
        def foo():
            """Summary.

            Yields:
                int: Numbers.
            """
            x = 1
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_yields_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert isinstance(result, Finding)
        assert result.rule == "extra-yields-in-docstring"
        assert result.symbol == "foo"
        assert result.file == "test.py"
        assert result.line == symbol.line
        assert result.category == "recommended"

    def test_yields_section_with_yield_no_finding(self):
        """Yields section with yield in code -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Yields:
                int: Numbers.
            """
            yield 1
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_yields_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_yields_section_with_yield_from_no_finding(self):
        """Yields section with yield from in code -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Yields:
                int: Numbers.
            """
            yield from [1, 2, 3]
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_yields_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_nested_yield_not_counted(self):
        """AC 5: Nested yield not counted for outer function."""
        source = '''\
        def foo():
            """Summary.

            Yields:
                int: Numbers.
            """
            def inner():
                yield 1
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_yields_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-yields-in-docstring"
        assert result.category == "recommended"

    def test_no_yields_section_no_finding(self):
        """No Yields section -> guard returns None."""
        source = '''\
        def foo():
            """Summary."""
            pass
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_yields_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_config_disable_no_finding(self):
        """AC 8: require_yields=False skips reverse check."""
        source = '''\
        def foo():
            """Summary.

            Yields:
                int: Numbers.
            """
            pass
        '''
        symbol, node_index, tree = _make_symbol_and_index(source)
        config = EnrichmentConfig(require_yields=False)

        findings = check_enrichment(textwrap.dedent(source), tree, config, "test.py")

        assert not any(f.rule == "extra-yields-in-docstring" for f in findings)


# ===========================================================================
# extra-returns-in-docstring tests (Task 7.20-7.25)
# ===========================================================================


class TestExtraReturnsInDocstring:
    """Tests for _check_extra_returns_in_docstring."""

    def test_returns_section_no_meaningful_return_emits_finding(self):
        """AC 4: Returns section but no meaningful return -> finding."""
        source = '''\
        def foo():
            """Summary.

            Returns:
                str: The result.
            """
            x = 1
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_returns_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert isinstance(result, Finding)
        assert result.rule == "extra-returns-in-docstring"
        assert result.symbol == "foo"
        assert result.file == "test.py"
        assert result.line == symbol.line
        assert result.category == "recommended"

    def test_returns_section_with_meaningful_return_no_finding(self):
        """Returns section with meaningful return -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Returns:
                str: The result.
            """
            return "hello"
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_returns_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_returns_section_only_bare_return_emits_finding(self):
        """AC 4: Returns section with only bare return/return None -> finding."""
        source = '''\
        def foo():
            """Summary.

            Returns:
                str: The result.
            """
            return None
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_returns_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-returns-in-docstring"
        assert result.category == "recommended"

    def test_nested_return_not_counted(self):
        """AC 5: Nested return not counted for outer function."""
        source = '''\
        def foo():
            """Summary.

            Returns:
                str: The result.
            """
            def inner():
                return "hello"
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_returns_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is not None
        assert result.rule == "extra-returns-in-docstring"
        assert result.category == "recommended"

    def test_no_returns_section_no_finding(self):
        """No Returns section -> guard returns None."""
        source = '''\
        def foo():
            """Summary."""
            pass
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_returns_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_config_disable_no_finding(self):
        """AC 8: require_returns=False skips reverse check."""
        source = '''\
        def foo():
            """Summary.

            Returns:
                str: The result.
            """
            pass
        '''
        symbol, node_index, tree = _make_symbol_and_index(source)
        config = EnrichmentConfig(require_returns=False)

        findings = check_enrichment(textwrap.dedent(source), tree, config, "test.py")

        assert not any(f.rule == "extra-returns-in-docstring" for f in findings)


# ===========================================================================
# Skip logic tests (Task 7.26-7.30)
# ===========================================================================


class TestSkipReverseCheck:
    """Tests for _should_skip_reverse_check and skip behavior."""

    def test_abstractmethod_returns_skipped(self):
        """AC 11: @abstractmethod with Returns section -> no finding."""
        source = '''\
        import abc

        class Base(abc.ABC):
            @abc.abstractmethod
            def foo(self):
                """Summary.

                Returns:
                    str: The result.
                """
                ...
        '''
        from docvet.ast_utils import get_documented_symbols

        tree = ast.parse(textwrap.dedent(source))
        symbols = get_documented_symbols(tree)
        node_index = _build_node_index(tree)
        symbol = [s for s in symbols if s.name == "foo"][0]
        assert symbol.docstring is not None
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_returns_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_ellipsis_stub_yields_skipped(self):
        """AC 11: Stub body (...) with Yields section -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Yields:
                int: Numbers.
            """
            ...
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_yields_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_pass_stub_raises_skipped(self):
        """AC 11: Stub body (pass) with Raises section -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            pass
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    def test_raise_not_implemented_raises_skipped(self):
        """AC 11: raise NotImplementedError body with Raises -> no finding."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            raise NotImplementedError
        '''
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        result = _check_extra_raises_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert result is None

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            # abstractmethod
            (
                '''\
                import abc
                class C(abc.ABC):
                    @abc.abstractmethod
                    def foo(self):
                        """Summary."""
                        ...
                ''',
                True,
            ),
            # Ellipsis stub
            (
                '''\
                def foo():
                    """Summary."""
                    ...
                ''',
                True,
            ),
            # pass stub
            (
                '''\
                def foo():
                    """Summary."""
                    pass
                ''',
                True,
            ),
            # raise NotImplementedError stub
            (
                '''\
                def foo():
                    """Summary."""
                    raise NotImplementedError
                ''',
                True,
            ),
            # raise NotImplementedError("msg") stub
            (
                '''\
                def foo():
                    """Summary."""
                    raise NotImplementedError("not done")
                ''',
                True,
            ),
            # Normal function -> False
            (
                '''\
                def foo():
                    """Summary."""
                    return 42
                ''',
                False,
            ),
        ],
        ids=[
            "abstractmethod",
            "ellipsis",
            "pass",
            "raise-NIE",
            "raise-NIE-msg",
            "normal-func",
        ],
    )
    def test_should_skip_reverse_check_directly(self, source, expected):
        """Test _should_skip_reverse_check helper directly."""
        from docvet.ast_utils import get_documented_symbols

        tree = ast.parse(textwrap.dedent(source))
        symbols = get_documented_symbols(tree)
        node_index = _build_node_index(tree)
        target = [s for s in symbols if s.kind in ("function", "method")][0]
        node = node_index.get(target.line)
        assert node is not None

        result = _should_skip_reverse_check(node)

        assert result is expected


# ===========================================================================
# Category and cross-rule tests (Task 7.31-7.34)
# ===========================================================================


class TestCategoryAndCrossRule:
    """Tests for category=recommended and cross-rule interactions."""

    def test_all_three_rules_emit_recommended_category(self):
        """AC 7: All three reverse rules use category='recommended'."""
        # extra-raises
        source_raises = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            x = 1
        '''
        s, ni, _ = _make_symbol_and_index(source_raises)
        r = _check_extra_raises_in_docstring(
            s, _parse_sections(s.docstring), ni, EnrichmentConfig(), "t.py"
        )
        assert r is not None
        assert r.category == "recommended"

        # extra-yields
        source_yields = '''\
        def bar():
            """Summary.

            Yields:
                int: Numbers.
            """
            x = 1
        '''
        s, ni, _ = _make_symbol_and_index(source_yields)
        r = _check_extra_yields_in_docstring(
            s, _parse_sections(s.docstring), ni, EnrichmentConfig(), "t.py"
        )
        assert r is not None
        assert r.category == "recommended"

        # extra-returns
        source_returns = '''\
        def baz():
            """Summary.

            Returns:
                str: Result.
            """
            x = 1
        '''
        s, ni, _ = _make_symbol_and_index(source_returns)
        r = _check_extra_returns_in_docstring(
            s, _parse_sections(s.docstring), ni, EnrichmentConfig(), "t.py"
        )
        assert r is not None
        assert r.category == "recommended"

    def test_cross_rule_extra_raises_and_missing_yields(self):
        """Extra raises and forward missing-yields fire independently."""
        source = '''\
        def foo():
            """Summary.

            Raises:
                ValueError: If bad.
            """
            yield 1
        '''
        symbol, node_index, tree = _make_symbol_and_index(source)
        config = EnrichmentConfig()

        findings = check_enrichment(textwrap.dedent(source), tree, config, "test.py")

        rules = {f.rule for f in findings}
        assert "extra-raises-in-docstring" in rules
        assert "missing-yields" in rules

    def test_overload_symbol_no_finding(self):
        """Enrichment skips @overload symbols — no reverse findings."""
        source = '''\
        from typing import overload

        @overload
        def foo(x: int) -> int:
            """Summary.

            Returns:
                int: The value.
            """
            ...
        '''
        symbol, node_index, tree = _make_symbol_and_index(source)
        config = EnrichmentConfig()

        findings = check_enrichment(textwrap.dedent(source), tree, config, "test.py")

        assert not any(f.rule == "extra-returns-in-docstring" for f in findings)
