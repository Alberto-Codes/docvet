"""Tests for the prefer-fenced-code-blocks enrichment rule."""

from __future__ import annotations

import ast

import pytest

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _build_node_index,
    _check_prefer_fenced_code_blocks,
    _parse_sections,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_symbol_and_index(source: str):
    """Build a symbol + node_index + tree from inline source."""
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


# ---------------------------------------------------------------------------
# Direct-function tests (>>> doctest detection)
# ---------------------------------------------------------------------------


def test_fenced_blocks_when_doctest_format_returns_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()
        >>> print(foo)
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "prefer-fenced-code-blocks"
    assert result.category == "recommended"
    assert "doctest format" in result.message
    assert ">>>" in result.message


def test_fenced_blocks_when_fenced_code_returns_none():
    source = '''\
class Foo:
    """A class.

    Examples:
        ```python
        foo = Foo()
        print(foo)
        ```
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_fenced_blocks_when_no_examples_section_returns_none():
    source = '''\
class Foo:
    """A class."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_fenced_blocks_when_config_disabled_returns_no_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=False)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced_findings = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert fenced_findings == []


def test_fenced_blocks_orchestrator_fires_when_enabled():
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced_findings = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced_findings) == 1
    assert fenced_findings[0].symbol == "Foo"


def test_fenced_blocks_when_mixed_content_with_doctest_returns_finding():
    source = '''\
def foo():
    """Do something.

    Examples:
        Here's how to use it:

        >>> result = foo()
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "prefer-fenced-code-blocks"


def test_fenced_blocks_when_function_with_doctest_includes_kind_in_message():
    source = '''\
def foo():
    """Do something.

    Examples:
        >>> foo()
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert "function" in result.message


def test_fenced_blocks_when_doctest_inside_fenced_block_returns_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        ```python
        >>> foo = Foo()
        ```
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "prefer-fenced-code-blocks"


# ---------------------------------------------------------------------------
# Direct-function tests (:: rST indented block detection)
# ---------------------------------------------------------------------------


def test_fenced_blocks_when_rst_indented_block_returns_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        Typical usage::

            foo = Foo()
            print(foo)
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "prefer-fenced-code-blocks"
    assert result.category == "recommended"
    assert "::" in result.message
    assert "reStructuredText" in result.message


def test_fenced_blocks_when_rst_no_indented_follow_returns_none():
    source = '''\
class Foo:
    """A class.

    Examples:
        Not a code block::

        This is not indented more.
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_fenced_blocks_when_rst_trailing_whitespace_returns_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        Typical usage::   \n\n            foo = Foo()
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "prefer-fenced-code-blocks"
    assert "::" in result.message


def test_fenced_blocks_when_mixed_doctest_and_rst_direct_returns_doctest_finding():
    """Direct function still returns only the first match (doctest)."""
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()

        Another example::

            print(foo)
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert ">>>" in result.message
    assert "::" not in result.message


def test_fenced_blocks_when_module_rst_block_returns_finding():
    source = '''\
"""A module.

Examples:
    Typical usage::

        import foo
        foo.bar()
"""
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    symbol = [s for s in symbols if s.kind == "module"][0]
    assert symbol.docstring is not None
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "prefer-fenced-code-blocks"
    assert "module" in result.message
    assert "::" in result.message


def test_fenced_blocks_when_bare_double_colon_line_with_indent_returns_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        ::

            foo = Foo()
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_prefer_fenced_code_blocks(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "prefer-fenced-code-blocks"
    assert "::" in result.message


def test_fenced_blocks_when_rst_block_config_disabled_returns_no_finding():
    source = '''\
class Foo:
    """A class.

    Examples:
        Typical usage::

            foo = Foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=False)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced_findings = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert fenced_findings == []


def test_fenced_blocks_when_rst_block_orchestrator_fires_when_enabled():
    source = '''\
class Foo:
    """A class.

    Examples:
        Typical usage::

            foo = Foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced_findings = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced_findings) == 1
    assert fenced_findings[0].symbol == "Foo"


# ---------------------------------------------------------------------------
# Multi-finding tests (orchestrator-level — AC 1, 5, 7)
# ---------------------------------------------------------------------------


def test_orchestrator_mixed_doctest_and_rst_returns_two_findings():
    """AC 1: Both patterns → 2 findings with distinct messages."""
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()

        Another example::

            print(foo)
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced) == 2
    messages = {f.message for f in fenced}
    assert any(">>>" in m for m in messages)
    assert any("::" in m for m in messages)


def test_orchestrator_multiple_doctest_blocks_no_rst_returns_one_finding():
    """AC 5: Multiple >>> blocks, no :: → 1 finding (dedup per pattern type)."""
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()
        >>> print(foo)

        More examples:

        >>> bar = Foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced) == 1
    assert ">>>" in fenced[0].message


def test_orchestrator_multi_symbol_mixed_patterns_independent():
    """AC 7: Each symbol's findings are independent."""
    source = '''\
class Foo:
    """A class.

    Examples:
        >>> foo = Foo()

        Another::

            print(foo)
    """
    pass

class Bar:
    """Another class.

    Examples:
        >>> bar = Bar()
    """
    pass

class Baz:
    """Third class.

    Examples:
        Typical usage::

            baz = Baz()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    foo_findings = [f for f in fenced if f.symbol == "Foo"]
    bar_findings = [f for f in fenced if f.symbol == "Bar"]
    baz_findings = [f for f in fenced if f.symbol == "Baz"]

    assert len(foo_findings) == 2  # both >>> and ::
    assert len(bar_findings) == 1  # only >>>
    assert len(baz_findings) == 1  # only ::


def test_orchestrator_single_doctest_pattern_returns_one_finding():
    """AC 2: Only >>> → 1 finding (regression guard)."""
    source = '''\
def foo():
    """Do something.

    Examples:
        >>> foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced) == 1
    assert ">>>" in fenced[0].message


def test_orchestrator_single_rst_pattern_returns_one_finding():
    """AC 3: Only :: → 1 finding (regression guard)."""
    source = '''\
def foo():
    """Do something.

    Examples:
        Typical usage::

            foo()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced) == 1
    assert "::" in fenced[0].message


def test_orchestrator_no_patterns_returns_zero_findings():
    """AC 4: No >>> or :: → 0 findings (regression guard)."""
    source = '''\
def foo():
    """Do something.

    Examples:
        ```python
        foo()
        ```
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced) == 0


def test_orchestrator_doctest_inside_fenced_and_rst_outside_returns_two_findings():
    """AC edge case (Task 4.6): >>> inside fenced block AND :: outside."""
    source = '''\
class Foo:
    """A class.

    Examples:
        ```python
        >>> foo = Foo()
        ```

        Another example::

            print(foo)
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(prefer_fenced_code_blocks=True)

    findings = check_enrichment(source, tree, config, "test.py")

    fenced = [f for f in findings if f.rule == "prefer-fenced-code-blocks"]
    assert len(fenced) == 2
    messages = {f.message for f in fenced}
    assert any(">>>" in m for m in messages)
    assert any("::" in m for m in messages)
