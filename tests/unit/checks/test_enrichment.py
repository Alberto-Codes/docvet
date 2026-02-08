"""Tests for enrichment check infrastructure and rules."""

from __future__ import annotations

import ast

from docvet.checks.enrichment import (
    _SECTION_HEADERS,
    _build_node_index,
    _parse_sections,
)

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


def test_build_node_index_get_returns_none_for_missing_line(parse_source):
    source = "def foo():\n    pass\n"
    tree = parse_source(source)
    index = _build_node_index(tree)

    # Line 99 doesn't exist — .get() returns None
    assert index.get(99) is None
    # Module-level symbol line (typically line 1 for module docstring, but
    # if a function starts at line 1 it would be there)
    # Test the pattern: get with a line that has no node
    assert index.get(2) is None
