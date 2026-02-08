"""Tests for enrichment check infrastructure and rules."""

from __future__ import annotations

import ast
from pathlib import Path

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _SECTION_HEADERS,
    _build_node_index,
    _check_missing_raises,
    _parse_sections,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

# ---------------------------------------------------------------------------
# Section header constant tests
# ---------------------------------------------------------------------------


def test_section_headers_contains_all_ten_headers():
    expected = {
        "Args",
        "Returns",
        "Raises",
        "Yields",
        "Receives",
        "Warns",
        "Other Parameters",
        "Attributes",
        "Examples",
        "See Also",
    }
    assert _SECTION_HEADERS == expected


def test_section_headers_is_frozenset():
    assert isinstance(_SECTION_HEADERS, frozenset)


# ---------------------------------------------------------------------------
# Section parsing tests
# ---------------------------------------------------------------------------


def test_parse_sections_when_headers_present_returns_matching_set():
    docstring = """\
Summary line.

Args:
    x: A parameter.

Raises:
    ValueError: If x is negative.

Yields:
    int: The next value.
"""
    result = _parse_sections(docstring)
    assert result == {"Args", "Raises", "Yields"}


def test_parse_sections_when_varied_indentation_returns_headers():
    # Module-level docstring (no indent)
    module_doc = """\
Module summary.

Attributes:
    FOO: A constant.
"""
    assert "Attributes" in _parse_sections(module_doc)

    # Method-level docstring (8-space indent)
    method_doc = """\
Method summary.

        Raises:
            ValueError: Bad input.
"""
    assert "Raises" in _parse_sections(method_doc)


def test_parse_sections_when_no_headers_returns_empty_set():
    docstring = "Just a summary line with no sections."
    result = _parse_sections(docstring)
    assert result == set()


def test_parse_sections_when_malformed_missing_colon_returns_empty_set():
    docstring = """\
Summary.

    Raises
        ValueError: Bad input.
"""
    result = _parse_sections(docstring)
    assert result == set()


def test_parse_sections_when_empty_string_returns_empty_set():
    assert _parse_sections("") == set()


def test_parse_sections_when_all_headers_present_returns_all():
    docstring = """\
Summary.

Args:
Returns:
Raises:
Yields:
Receives:
Warns:
Other Parameters:
Attributes:
Examples:
See Also:
"""
    result = _parse_sections(docstring)
    assert result == _SECTION_HEADERS


def test_parse_sections_when_header_has_trailing_whitespace_returns_header():
    docstring = "Summary.\n\n    Raises:   \n"
    assert "Raises" in _parse_sections(docstring)


def test_parse_sections_when_header_has_inline_content_returns_empty_set():
    # Google-style headers must be standalone lines (colon + end of line).
    # "Raises: ValueError" on one line is not a valid section header.
    docstring = "    Raises: ValueError if bad input\n"
    assert _parse_sections(docstring) == set()


def test_parse_sections_when_header_inside_code_block_still_matches():
    # Known edge case: headers inside fenced code blocks are matched.
    # This produces a false negative at the rule level (safe direction, NFR5)
    # because the rule thinks a section exists when it's actually example code.
    docstring = """\
Summary.

Examples:
    ```python
    Raises:
        ValueError: example
    ```
"""
    result = _parse_sections(docstring)
    assert "Raises" in result
    assert "Examples" in result


# ---------------------------------------------------------------------------
# Node index tests
# ---------------------------------------------------------------------------


def test_build_node_index_when_functions_and_classes_maps_lines(parse_source):
    source = """\
def foo():
    pass

class Bar:
    def method(self):
        pass
"""
    tree = parse_source(source)
    index = _build_node_index(tree)

    assert 1 in index
    assert isinstance(index[1], ast.FunctionDef)

    assert 4 in index
    assert isinstance(index[4], ast.ClassDef)

    assert 5 in index
    assert isinstance(index[5], ast.FunctionDef)


def test_build_node_index_when_async_function_includes_async_node(parse_source):
    source = """\
async def fetch():
    pass
"""
    tree = parse_source(source)
    index = _build_node_index(tree)

    assert 1 in index
    assert isinstance(index[1], ast.AsyncFunctionDef)


def test_build_node_index_when_nested_functions_includes_inner(parse_source):
    source = """\
def outer():
    def inner():
        pass
"""
    tree = parse_source(source)
    index = _build_node_index(tree)

    assert 1 in index  # outer
    assert 2 in index  # inner


def test_build_node_index_when_module_only_returns_empty_dict(parse_source):
    source = '"""Module docstring."""\n\nFOO = 42\n'
    tree = parse_source(source)
    index = _build_node_index(tree)

    assert index == {}


def test_build_node_index_get_returns_none_for_module_symbol(parse_source):
    # AC#7: module-level symbol (line 1) with no corresponding AST node.
    # A module docstring starts at line 1 but is not a FunctionDef/ClassDef,
    # so node_index.get(1) must return None.
    source = '"""Module docstring."""\n\nx = 42\n'
    tree = parse_source(source)
    index = _build_node_index(tree)

    assert index.get(1) is None


def test_build_node_index_get_returns_none_for_arbitrary_missing_line(parse_source):
    source = "def foo():\n    pass\n"
    tree = parse_source(source)
    index = _build_node_index(tree)

    assert index.get(99) is None


# ---------------------------------------------------------------------------
# _check_missing_raises tests
# ---------------------------------------------------------------------------


def _make_symbol_and_index(source: str):
    """Helper to build a symbol + node_index + sections from inline source."""
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    # Return the first non-module symbol (the function)
    func_symbols = [s for s in symbols if s.kind != "module"]
    return func_symbols[0], node_index, tree


def test_missing_raises_when_function_raises_without_section_returns_finding():
    source = '''\
def foo():
    """Do something."""
    raise ValueError("bad")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-raises"
    assert result.category == "required"
    assert result.symbol == "foo"
    assert "ValueError" in result.message


def test_missing_raises_when_raises_section_present_returns_none():
    source = '''\
def foo():
    """Do something.

    Raises:
        ValueError: If bad.
    """
    raise ValueError("bad")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_raises_when_no_raise_statements_returns_none():
    source = '''\
def foo():
    """Do something."""
    return 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_raises_when_raise_without_exception_returns_finding():
    source = '''\
def foo():
    """Do something."""
    try:
        pass
    except Exception:
        raise
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert "(re-raise)" in result.message


def test_missing_raises_when_multiple_exceptions_lists_all_in_message():
    source = '''\
def foo():
    """Do something."""
    if True:
        raise ValueError("bad")
    raise TypeError("wrong")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert "TypeError" in result.message
    assert "ValueError" in result.message


def test_missing_raises_when_node_index_missing_returns_none():
    # Module symbol — node_index won't have it
    source = '''\
"""Module docstring."""

FOO = 42
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    module_symbol = [s for s in symbols if s.kind == "module"][0]
    assert module_symbol.docstring is not None
    sections = _parse_sections(module_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(
        module_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# check_enrichment orchestrator tests
# ---------------------------------------------------------------------------


def test_check_enrichment_when_no_docstring_skips_symbol():
    source = """\
def foo():
    raise ValueError("bad")
"""
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    # foo has no docstring — should be skipped (AC #4)
    assert findings == []


def test_check_enrichment_when_raises_disabled_returns_no_finding():
    source = '''\
def foo():
    """Do something."""
    raise ValueError("bad")
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_raises=False)

    findings = check_enrichment(source, tree, config, "test.py")

    missing_raises = [f for f in findings if f.rule == "missing-raises"]
    assert missing_raises == []


def test_check_enrichment_when_complete_module_returns_empty():
    source = Path("tests/fixtures/complete_module.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(
        source, tree, config, "tests/fixtures/complete_module.py"
    )

    assert findings == []


def test_check_enrichment_when_missing_raises_fixture_returns_finding():
    source = Path("tests/fixtures/missing_raises.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(
        source, tree, config, "tests/fixtures/missing_raises.py"
    )

    assert len(findings) == 1
    assert findings[0].rule == "missing-raises"
    assert findings[0].symbol == "validate_input"


def test_check_enrichment_returns_list_of_findings():
    source = '''\
def foo():
    """Do something."""
    raise ValueError("bad")

def bar():
    """Do other thing."""
    raise TypeError("wrong")
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    assert isinstance(findings, list)
    assert len(findings) == 2
    assert all(isinstance(f, Finding) for f in findings)


def test_check_enrichment_when_all_rules_disabled_returns_empty():
    source = '''\
def foo():
    """Do something."""
    raise ValueError("bad")
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_raises=False)

    findings = check_enrichment(source, tree, config, "test.py")

    assert findings == []
