"""Tests for enrichment check infrastructure and rules."""

from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _SECTION_HEADERS,
    _build_node_index,
    _check_missing_attributes,
    _check_missing_examples,
    _check_missing_other_parameters,
    _check_missing_raises,
    _check_missing_receives,
    _check_missing_warns,
    _check_missing_yields,
    _has_self_assignments,
    _is_dataclass,
    _is_enum,
    _is_init_module,
    _is_namedtuple,
    _is_protocol,
    _is_typeddict,
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
    """Helper to build a symbol + node_index + tree from inline source."""
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    # Return the first non-module symbol (the function)
    func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


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


def test_missing_raises_when_bare_name_raise_returns_finding():
    # raise ValueError (no parentheses) — ast.Name branch
    source = '''\
def foo():
    """Do something."""
    raise ValueError
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert "ValueError" in result.message


def test_missing_raises_when_attribute_call_raise_returns_finding():
    # raise errors.CustomError("msg") — ast.Call(func=ast.Attribute) branch
    source = '''\
def foo():
    """Do something."""
    raise errors.CustomError("bad")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert "CustomError" in result.message


def test_missing_raises_when_bare_attribute_raise_returns_finding():
    # raise errors.CustomError (no parentheses) — ast.Attribute branch
    source = '''\
def foo():
    """Do something."""
    raise errors.CustomError
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert "CustomError" in result.message


def test_missing_raises_when_nested_function_raises_returns_none():
    # Raises inside nested functions should NOT be attributed to outer
    source = '''\
def outer():
    """Outer function."""
    def inner():
        raise ValueError("inner")
    return inner()
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_raises_when_outer_and_nested_raise_reports_only_outer():
    # Only outer's raises should be reported, not nested function's
    source = '''\
def outer():
    """Outer function."""
    raise TypeError("outer")
    def inner():
        raise ValueError("inner")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert "TypeError" in result.message
    assert "ValueError" not in result.message


def test_missing_raises_when_class_symbol_returns_none():
    # Class symbols should be skipped — missing-raises targets functions only
    source = '''\
class Foo:
    """A class that raises in class body."""
    raise RuntimeError("class-level")
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.docstring is not None
    sections = _parse_sections(class_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_raises(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


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


def test_check_enrichment_when_active_rules_disabled_returns_empty():
    source = '''\
import warnings

@dataclass
class MyData:
    """A data class."""
    x: int

class PlainClass:
    """A plain class."""
    def __init__(self):
        self.x = 1

def foo(**kwargs):
    """Do something."""
    raise ValueError("bad")
    value = yield 42
    warnings.warn("deprecated", DeprecationWarning)
'''
    tree = ast.parse(source)
    # Dynamically disable all boolean toggles so this test doesn't break
    # when new rules are added to EnrichmentConfig.
    config = EnrichmentConfig(
        **{
            f.name: False
            for f in dataclasses.fields(EnrichmentConfig)
            if f.default is True
        },
        require_examples=[],
    )

    findings = check_enrichment(source, tree, config, "__init__.py")

    assert findings == []


# ---------------------------------------------------------------------------
# _check_missing_yields tests
# ---------------------------------------------------------------------------


def test_missing_yields_when_generator_yields_without_section_returns_finding():
    source = '''\
def gen():
    """Generate values."""
    yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-yields"
    assert result.category == "required"
    assert result.symbol == "gen"
    assert "yields" in result.message.lower()


def test_missing_yields_when_yields_section_present_returns_none():
    source = '''\
def gen():
    """Generate values.

    Yields:
        int: The next value.
    """
    yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_yields_when_no_yield_statements_returns_none():
    source = '''\
def foo():
    """Do something."""
    return 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_yields_when_yield_from_without_section_returns_finding():
    source = '''\
def gen():
    """Delegate to sub-generator."""
    yield from range(10)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-yields"


def test_missing_yields_when_node_index_missing_returns_none():
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

    result = _check_missing_yields(
        module_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_yields_when_class_symbol_returns_none():
    source = '''\
class Foo:
    """A class with yield in body."""
    x = (i for i in range(10))
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.docstring is not None
    sections = _parse_sections(class_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_yields_when_nested_generator_yields_returns_none():
    source = '''\
def outer():
    """Outer function."""
    def inner():
        yield 42
    return list(inner())
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_yields_when_async_generator_yields_returns_finding():
    source = '''\
async def gen():
    """Async generate values."""
    yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_yields(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-yields"
    assert result.symbol == "gen"


# ---------------------------------------------------------------------------
# _check_missing_receives tests
# ---------------------------------------------------------------------------


def test_missing_receives_when_send_pattern_without_section_returns_finding():
    source = '''\
def gen():
    """Generate and receive values."""
    value = yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-receives"
    assert result.category == "required"
    assert result.symbol == "gen"
    assert "send pattern" in result.message


def test_missing_receives_when_receives_section_present_returns_none():
    source = '''\
def gen():
    """Generate and receive values.

    Receives:
        int: The sent value.
    """
    value = yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_receives_when_no_send_pattern_returns_none():
    source = '''\
def foo():
    """Do something."""
    return 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_receives_when_plain_yield_no_assignment_returns_none():
    source = '''\
def gen():
    """Generate values."""
    yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_receives_when_annotated_assign_yield_returns_finding():
    source = '''\
def gen():
    """Generate and receive values."""
    value: int = yield 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-receives"


def test_missing_receives_when_nested_send_pattern_returns_none():
    source = '''\
def outer():
    """Outer function."""
    def inner():
        value = yield 42
    return inner()
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_receives_when_node_index_missing_returns_none():
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

    result = _check_missing_receives(
        module_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_receives_when_class_symbol_returns_none():
    source = '''\
class Foo:
    """A class."""
    pass
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.docstring is not None
    sections = _parse_sections(class_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_receives(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# check_enrichment orchestrator tests (yields/receives)
# ---------------------------------------------------------------------------


def test_check_enrichment_when_yields_disabled_returns_no_finding():
    source = '''\
def gen():
    """Generate values."""
    yield 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_yields=False)

    findings = check_enrichment(source, tree, config, "test.py")

    missing_yields = [f for f in findings if f.rule == "missing-yields"]
    assert missing_yields == []


def test_check_enrichment_when_receives_disabled_returns_no_finding():
    source = '''\
def gen():
    """Generate and receive values."""
    value = yield 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_receives=False)

    findings = check_enrichment(source, tree, config, "test.py")

    missing_receives = [f for f in findings if f.rule == "missing-receives"]
    assert missing_receives == []


def test_check_enrichment_when_missing_yields_fixture_returns_finding():
    source = Path("tests/fixtures/missing_yields.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(
        source, tree, config, "tests/fixtures/missing_yields.py"
    )

    yields_findings = [f for f in findings if f.rule == "missing-yields"]
    assert len(yields_findings) == 1
    assert yields_findings[0].symbol == "stream_items"


def test_check_enrichment_when_complete_module_still_returns_empty():
    source = Path("tests/fixtures/complete_module.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(
        source, tree, config, "tests/fixtures/complete_module.py"
    )

    assert findings == []


# ---------------------------------------------------------------------------
# _check_missing_warns tests
# ---------------------------------------------------------------------------


def test_missing_warns_when_function_calls_warn_without_section_returns_finding():
    source = '''\
import warnings

def foo():
    """Do something."""
    warnings.warn("deprecated", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-warns"
    assert result.category == "required"
    assert result.symbol == "foo"
    assert "warnings.warn()" in result.message


def test_missing_warns_when_warns_section_present_returns_none():
    source = '''\
import warnings

def foo():
    """Do something.

    Warns:
        DeprecationWarning: If deprecated.
    """
    warnings.warn("deprecated", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_warns_when_no_warn_calls_returns_none():
    source = '''\
def foo():
    """Do something."""
    return 42
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_warns_when_qualified_warnings_warn_returns_finding():
    source = '''\
import warnings

def foo():
    """Do something."""
    warnings.warn("something bad", UserWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-warns"


def test_missing_warns_when_bare_warn_import_returns_finding():
    source = '''\
from warnings import warn

def foo():
    """Do something."""
    warn("deprecated", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-warns"


def test_missing_warns_when_node_index_missing_returns_none():
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

    result = _check_missing_warns(
        module_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_warns_when_class_symbol_returns_none():
    source = '''\
class Foo:
    """A class."""
    pass
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.docstring is not None
    sections = _parse_sections(class_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(class_symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_warns_when_nested_warn_call_returns_none():
    source = '''\
import warnings

def outer():
    """Outer function."""
    def inner():
        warnings.warn("inner", DeprecationWarning)
    return inner()
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_warns_when_unrelated_function_call_returns_none():
    source = '''\
import logging

def foo():
    """Do something."""
    logging.warn("something")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_warns_when_bare_warn_is_user_defined_still_returns_finding():
    # Known tradeoff: bare warn() is assumed to be from warnings import.
    # A user-defined warn() function will trigger a false positive.
    # This is accepted per architecture spec — Pattern 2 matches any bare
    # warn() call because in well-structured code, bare warn() comes from
    # `from warnings import warn`.
    source = '''\
def warn(msg):
    print(msg)

def foo():
    """Do something."""
    warn("oops")
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    foo_symbol = [s for s in symbols if s.name == "foo"][0]
    assert foo_symbol.docstring is not None
    sections = _parse_sections(foo_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(foo_symbol, sections, node_index, config, "test.py")

    # Returns a finding (false positive) — documented as accepted behavior.
    assert result is not None
    assert result.rule == "missing-warns"


def test_missing_warns_when_nested_class_warn_call_returns_none():
    # Warn calls inside nested classes should NOT be attributed to outer function.
    source = '''\
import warnings

def outer():
    """Outer function."""
    class Inner:
        def method(self):
            warnings.warn("inner", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_warns(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# _check_missing_other_parameters tests
# ---------------------------------------------------------------------------


def test_missing_other_parameters_when_kwargs_without_section_returns_finding():
    source = '''\
def foo(**kwargs):
    """Do something."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_other_parameters(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-other-parameters"
    assert result.category == "recommended"
    assert result.symbol == "foo"
    assert "**kwargs" in result.message


def test_missing_other_parameters_when_section_present_returns_none():
    source = '''\
def foo(**kwargs):
    """Do something.

    Other Parameters:
        verbose: If True, print debug info.
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_other_parameters(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_other_parameters_when_custom_kwarg_name_uses_actual_name():
    source = '''\
def foo(**options):
    """Do something."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_other_parameters(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert "**options" in result.message


def test_missing_other_parameters_when_no_kwargs_returns_none():
    source = '''\
def foo(x, y):
    """Do something."""
    return x + y
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_other_parameters(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_other_parameters_when_node_index_missing_returns_none():
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

    result = _check_missing_other_parameters(
        module_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_other_parameters_when_async_function_with_kwargs_returns_finding():
    source = '''\
async def foo(**kwargs):
    """Do something."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_other_parameters(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "missing-other-parameters"
    assert result.symbol == "foo"


def test_missing_other_parameters_when_class_symbol_returns_none():
    source = '''\
class Foo:
    """A class."""
    pass
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.docstring is not None
    sections = _parse_sections(class_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_other_parameters(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# check_enrichment orchestrator tests (warns/other-parameters)
# ---------------------------------------------------------------------------


def test_check_enrichment_when_warns_enabled_returns_finding():
    source = '''\
import warnings

def foo():
    """Do something."""
    warnings.warn("deprecated", DeprecationWarning)
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    missing_warns = [f for f in findings if f.rule == "missing-warns"]
    assert len(missing_warns) == 1
    assert missing_warns[0].symbol == "foo"


def test_check_enrichment_when_other_parameters_enabled_returns_finding():
    source = '''\
def foo(**kwargs):
    """Do something."""
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    missing_other = [f for f in findings if f.rule == "missing-other-parameters"]
    assert len(missing_other) == 1
    assert missing_other[0].symbol == "foo"


def test_check_enrichment_when_warns_disabled_returns_no_finding():
    source = '''\
import warnings

def foo():
    """Do something."""
    warnings.warn("deprecated", DeprecationWarning)
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_warns=False)

    findings = check_enrichment(source, tree, config, "test.py")

    missing_warns = [f for f in findings if f.rule == "missing-warns"]
    assert missing_warns == []


def test_check_enrichment_when_other_parameters_disabled_returns_no_finding():
    source = '''\
def foo(**kwargs):
    """Do something."""
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_other_parameters=False)

    findings = check_enrichment(source, tree, config, "test.py")

    missing_other = [f for f in findings if f.rule == "missing-other-parameters"]
    assert missing_other == []


# ---------------------------------------------------------------------------
# _is_dataclass helper tests
# ---------------------------------------------------------------------------


def test_is_dataclass_when_simple_decorator_returns_true():
    node = ast.parse("@dataclass\nclass Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_dataclass(node) is True


def test_is_dataclass_when_qualified_decorator_returns_true():
    node = ast.parse("@dataclasses.dataclass\nclass Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_dataclass(node) is True


def test_is_dataclass_when_call_decorator_returns_true():
    node = ast.parse("@dataclass(frozen=True)\nclass Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_dataclass(node) is True


def test_is_dataclass_when_qualified_call_decorator_returns_true():
    node = ast.parse("@dataclasses.dataclass(frozen=True)\nclass Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_dataclass(node) is True


def test_is_dataclass_when_no_decorator_returns_false():
    node = ast.parse("class Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_dataclass(node) is False


def test_is_dataclass_when_other_decorator_returns_false():
    node = ast.parse("@other_decorator\nclass Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_dataclass(node) is False


# ---------------------------------------------------------------------------
# _is_namedtuple helper tests
# ---------------------------------------------------------------------------


def test_is_namedtuple_when_simple_base_returns_true():
    node = ast.parse("class Foo(NamedTuple): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_namedtuple(node) is True


def test_is_namedtuple_when_qualified_base_returns_true():
    node = ast.parse("class Foo(typing.NamedTuple): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_namedtuple(node) is True


def test_is_namedtuple_when_no_base_returns_false():
    node = ast.parse("class Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_namedtuple(node) is False


def test_is_namedtuple_when_other_base_returns_false():
    node = ast.parse("class Foo(SomethingElse): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_namedtuple(node) is False


# ---------------------------------------------------------------------------
# _is_typeddict helper tests
# ---------------------------------------------------------------------------


def test_is_typeddict_when_simple_base_returns_true():
    node = ast.parse("class Foo(TypedDict): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_typeddict(node) is True


def test_is_typeddict_when_qualified_base_returns_true():
    node = ast.parse("class Foo(typing.TypedDict): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_typeddict(node) is True


def test_is_typeddict_when_no_base_returns_false():
    node = ast.parse("class Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_typeddict(node) is False


# ---------------------------------------------------------------------------
# _check_missing_attributes tests
# ---------------------------------------------------------------------------


def test_missing_attributes_when_dataclass_without_section_returns_finding():
    source = '''\
@dataclass
class Foo:
    """A data class."""
    x: int
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-attributes"
    assert result.category == "required"
    assert result.symbol == "Foo"
    assert "Dataclass" in result.message
    assert "Foo" in result.message


def test_missing_attributes_when_qualified_dataclass_returns_finding():
    source = '''\
@dataclasses.dataclass
class Foo:
    """A data class."""
    x: int
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert "Dataclass" in result.message


def test_missing_attributes_when_dataclass_call_returns_finding():
    source = '''\
@dataclass(frozen=True)
class Foo:
    """A frozen data class."""
    x: int
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert "Dataclass" in result.message


def test_missing_attributes_when_namedtuple_without_section_returns_finding():
    source = '''\
class Point(NamedTuple):
    """A point in 2D space."""
    x: int
    y: int
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert result.category == "required"
    assert "NamedTuple" in result.message
    assert "Point" in result.message


def test_missing_attributes_when_qualified_namedtuple_returns_finding():
    source = '''\
class Point(typing.NamedTuple):
    """A point in 2D space."""
    x: int
    y: int
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert "NamedTuple" in result.message


def test_missing_attributes_when_typeddict_without_section_returns_finding():
    source = '''\
class Options(TypedDict):
    """Configuration options."""
    verbose: bool
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert result.category == "required"
    assert "TypedDict" in result.message
    assert "Options" in result.message


def test_missing_attributes_when_attributes_section_present_returns_none():
    source = '''\
@dataclass
class Foo:
    """A data class.

    Attributes:
        x: An integer value.
    """
    x: int
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_attributes_when_node_index_missing_returns_none():
    source = '''\
@dataclass
class Foo:
    """A data class."""
    x: int
'''
    symbol, _, _ = _make_symbol_and_index(source)
    assert symbol.kind == "class"
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()
    empty_node_index = _build_node_index(ast.parse(""))

    result = _check_missing_attributes(
        symbol, sections, empty_node_index, config, "test.py"
    )

    assert result is None


def test_missing_attributes_when_function_symbol_returns_none():
    source = '''\
def foo():
    """A function."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_attributes_when_plain_class_returns_none():
    source = '''\
class Foo:
    """A plain class without dataclass/NamedTuple/TypedDict."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# check_enrichment orchestrator tests (attributes)
# ---------------------------------------------------------------------------


def test_check_enrichment_when_attributes_disabled_returns_no_finding():
    source = '''\
@dataclass
class Foo:
    """A data class."""
    x: int
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_attributes=False)

    findings = check_enrichment(source, tree, config, "test.py")

    missing_attrs = [f for f in findings if f.rule == "missing-attributes"]
    assert missing_attrs == []


def test_check_enrichment_when_dataclass_no_docstring_returns_no_finding():
    source = """\
@dataclass
class Foo:
    x: int
"""
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    missing_attrs = [f for f in findings if f.rule == "missing-attributes"]
    assert missing_attrs == []


def test_check_enrichment_when_complete_module_with_dataclass_returns_empty():
    source = Path("tests/fixtures/complete_module.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(
        source, tree, config, "tests/fixtures/complete_module.py"
    )

    assert findings == []


# ---------------------------------------------------------------------------
# _has_self_assignments helper tests
# ---------------------------------------------------------------------------


def test_has_self_assignments_when_init_with_simple_assign_returns_true():
    node = ast.parse("class Foo:\n def __init__(self):\n  self.x = 1").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is True


def test_has_self_assignments_when_init_with_annotated_assign_returns_true():
    node = ast.parse("class Foo:\n def __init__(self):\n  self.x: int = 0").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is True


def test_has_self_assignments_when_no_init_returns_false():
    node = ast.parse("class Foo:\n pass").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is False


def test_has_self_assignments_when_init_without_self_assigns_returns_false():
    node = ast.parse("class Foo:\n def __init__(self):\n  pass").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is False


def test_has_self_assignments_when_nested_function_self_assigns_returns_false():
    source = """\
class Foo:
    def __init__(self):
        def helper():
            self.x = 1
"""
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is False


def test_has_self_assignments_when_init_assigns_local_var_returns_false():
    node = ast.parse("class Foo:\n def __init__(self):\n  x = 1").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is False


def test_has_self_assignments_when_init_assigns_cls_attribute_returns_false():
    node = ast.parse("class Foo:\n def __init__(self):\n  cls.x = 1").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is False


def test_has_self_assignments_when_nested_class_self_assigns_returns_false():
    source = """\
class Foo:
    def __init__(self):
        class Inner:
            self.x = 1
"""
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is False


def test_has_self_assignments_when_async_init_with_self_assigns_returns_true():
    source = """\
class Foo:
    async def __init__(self):
        self.x = 1
"""
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    assert _has_self_assignments(node) is True


# ---------------------------------------------------------------------------
# _is_init_module helper tests
# ---------------------------------------------------------------------------


def test_is_init_module_when_init_py_returns_true():
    assert _is_init_module("__init__.py") is True


def test_is_init_module_when_nested_init_py_returns_true():
    assert _is_init_module("src/pkg/__init__.py") is True


def test_is_init_module_when_regular_py_returns_false():
    assert _is_init_module("module.py") is False


def test_is_init_module_when_similar_name_returns_false():
    assert _is_init_module("not__init__.py") is False


def test_is_init_module_when_windows_backslash_path_returns_true():
    assert _is_init_module("src\\pkg\\__init__.py") is True


# ---------------------------------------------------------------------------
# _check_missing_attributes tests (branches 4-5: plain class, init module)
# ---------------------------------------------------------------------------


def test_missing_attributes_when_plain_class_with_self_assigns_returns_finding():
    source = '''\
class Foo:
    """A plain class."""
    def __init__(self):
        self.x = 1
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-attributes"
    assert result.category == "required"
    assert "Class" in result.message
    assert "Foo" in result.message


def test_missing_attributes_when_plain_class_with_annotated_self_assigns_returns_finding():
    source = '''\
class Foo:
    """A plain class."""
    def __init__(self):
        self.x: int = 0
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert "Class" in result.message


def test_missing_attributes_when_plain_class_no_self_assigns_returns_none():
    source = '''\
class Foo:
    """A plain class."""
    def __init__(self):
        pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_attributes_when_init_module_without_section_returns_finding():
    source = '''\
"""Package docstring."""

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

    result = _check_missing_attributes(
        module_symbol, sections, node_index, config, "__init__.py"
    )

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-attributes"
    assert result.category == "required"
    assert "Module" in result.message


def test_missing_attributes_when_init_module_with_section_returns_none():
    source = '''\
"""Package docstring.

Attributes:
    FOO: A constant.
"""

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

    result = _check_missing_attributes(
        module_symbol, sections, node_index, config, "__init__.py"
    )

    assert result is None


def test_missing_attributes_when_regular_module_returns_none():
    source = '''\
"""Regular module docstring."""

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

    result = _check_missing_attributes(
        module_symbol, sections, node_index, config, "regular.py"
    )

    assert result is None


def test_missing_attributes_when_dataclass_wins_over_plain_class_returns_dataclass_finding():
    source = '''\
@dataclass
class Foo:
    """A data class with init."""
    x: int
    def __init__(self):
        self.y = 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-attributes"
    assert "Dataclass" in result.message


def test_missing_attributes_when_nested_self_assigns_in_init_returns_none():
    source = '''\
class Foo:
    """A plain class."""
    def __init__(self):
        def helper():
            self.x = 1
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_attributes(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_attributes_when_module_symbol_kind_accepted():
    source = '''\
"""Package docstring."""

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

    # Module symbol kind should no longer be rejected — it's accepted
    # but only fires for __init__.py files
    result = _check_missing_attributes(
        module_symbol, sections, node_index, config, "__init__.py"
    )

    # Should return a finding (module kind is now accepted and this is __init__.py)
    assert result is not None
    assert result.rule == "missing-attributes"


# ---------------------------------------------------------------------------
# check_enrichment orchestrator tests (plain class + init module)
# ---------------------------------------------------------------------------


def test_check_enrichment_when_plain_class_detected_returns_finding():
    source = '''\
class Foo:
    """A plain class."""
    def __init__(self):
        self.x = 1
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    missing_attrs = [f for f in findings if f.rule == "missing-attributes"]
    assert len(missing_attrs) == 1
    assert "Class" in missing_attrs[0].message
    assert "Foo" in missing_attrs[0].message


def test_check_enrichment_when_init_module_detected_returns_finding():
    source = '''\
"""Package docstring."""

FOO = 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "__init__.py")

    missing_attrs = [f for f in findings if f.rule == "missing-attributes"]
    assert len(missing_attrs) == 1
    assert "Module" in missing_attrs[0].message


def test_check_enrichment_when_complete_module_with_plain_class_returns_empty():
    source = Path("tests/fixtures/complete_module.py").read_text()
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(
        source, tree, config, "tests/fixtures/complete_module.py"
    )

    assert findings == []


# ---------------------------------------------------------------------------
# _is_protocol helper tests
# ---------------------------------------------------------------------------


def test_is_protocol_when_simple_base_returns_true():
    node = ast.parse("class Foo(Protocol): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_protocol(node) is True


def test_is_protocol_when_qualified_base_returns_true():
    node = ast.parse("class Foo(typing.Protocol): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_protocol(node) is True


def test_is_protocol_when_no_base_returns_false():
    node = ast.parse("class Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_protocol(node) is False


def test_is_protocol_when_other_base_returns_false():
    node = ast.parse("class Foo(SomethingElse): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_protocol(node) is False


def test_is_protocol_when_multiple_bases_with_protocol_returns_true():
    node = ast.parse("class Foo(Protocol, ABC): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_protocol(node) is True


def test_is_protocol_when_runtime_checkable_decorated_returns_true():
    source = "@runtime_checkable\nclass Foo(Protocol): ..."
    node = ast.parse(source).body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_protocol(node) is True


# ---------------------------------------------------------------------------
# _is_enum helper tests
# ---------------------------------------------------------------------------


def test_is_enum_when_simple_enum_base_returns_true():
    node = ast.parse("class Color(Enum): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_qualified_enum_base_returns_true():
    node = ast.parse("class Color(enum.Enum): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_int_enum_returns_true():
    node = ast.parse("class Status(IntEnum): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_str_enum_returns_true():
    node = ast.parse("class Mode(StrEnum): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_flag_returns_true():
    node = ast.parse("class Perm(Flag): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_int_flag_returns_true():
    node = ast.parse("class Perm(IntFlag): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_qualified_str_enum_returns_true():
    node = ast.parse("class Mode(enum.StrEnum): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_mixin_base_with_enum_returns_true():
    node = ast.parse("class Color(str, Enum): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is True


def test_is_enum_when_no_base_returns_false():
    node = ast.parse("class Foo: ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is False


def test_is_enum_when_other_base_returns_false():
    node = ast.parse("class Foo(SomethingElse): ...").body[0]
    assert isinstance(node, ast.ClassDef)
    assert _is_enum(node) is False


# ---------------------------------------------------------------------------
# _check_missing_examples tests
# ---------------------------------------------------------------------------


def test_missing_examples_when_class_without_section_returns_finding():
    source = '''\
class Parser:
    """Parse input data."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-examples"
    assert result.category == "recommended"
    assert result.symbol == "Parser"
    assert "Class" in result.message
    assert "Parser" in result.message
    assert "Examples" in result.message


def test_missing_examples_when_protocol_without_section_returns_finding():
    source = '''\
class Handler(Protocol):
    """Handle requests."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["protocol"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-examples"
    assert "Protocol" in result.message
    assert "Handler" in result.message


def test_missing_examples_when_dataclass_without_section_returns_finding():
    source = '''\
@dataclass
class Config:
    """Application configuration."""
    debug: bool
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["dataclass"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-examples"
    assert "Dataclass" in result.message
    assert "Config" in result.message


def test_missing_examples_when_enum_without_section_returns_finding():
    source = '''\
class Color(Enum):
    """Available colors."""
    RED = 1
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["enum"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-examples"
    assert "Enum" in result.message
    assert "Color" in result.message


def test_missing_examples_when_examples_section_present_returns_none():
    source = '''\
class Parser:
    """Parse input data.

    Examples:
        >>> p = Parser()
    """
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_examples_when_class_not_in_config_list_returns_none():
    source = '''\
class Parser:
    """Parse input data."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["dataclass"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_examples_when_function_symbol_returns_none():
    source = '''\
def foo():
    """Do something."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_missing_examples_when_method_symbol_returns_none():
    source = '''\
class Foo:
    """A class."""
    def bar(self):
        """Do something."""
        pass
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    method_symbol = [s for s in symbols if s.kind == "method"][0]
    assert method_symbol.docstring is not None
    sections = _parse_sections(method_symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )

    result = _check_missing_examples(
        method_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_missing_examples_when_init_module_without_section_returns_finding():
    source = '''\
"""Package docstring."""

FOO = 42
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    module_symbol = [s for s in symbols if s.kind == "module"][0]
    assert module_symbol.docstring is not None
    sections = _parse_sections(module_symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )

    result = _check_missing_examples(
        module_symbol, sections, node_index, config, "__init__.py"
    )

    assert result is not None
    assert result.rule == "missing-examples"
    assert "Module" in result.message


def test_missing_examples_when_non_init_module_returns_none():
    source = '''\
"""Regular module docstring."""

FOO = 42
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    module_symbol = [s for s in symbols if s.kind == "module"][0]
    assert module_symbol.docstring is not None
    sections = _parse_sections(module_symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )

    result = _check_missing_examples(
        module_symbol, sections, node_index, config, "regular.py"
    )

    assert result is None


def test_missing_examples_when_node_index_missing_returns_none():
    source = '''\
class Foo:
    """A class."""
    pass
'''
    symbol, _, _ = _make_symbol_and_index(source)
    assert symbol.kind == "class"
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["class"],
    )
    empty_node_index = _build_node_index(ast.parse(""))

    result = _check_missing_examples(
        symbol, sections, empty_node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# check_enrichment orchestrator tests (missing-examples)
# ---------------------------------------------------------------------------


def test_check_enrichment_when_examples_enabled_class_returns_finding():
    source = '''\
class Parser:
    """Parse input data."""
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert len(missing_examples) == 1
    assert missing_examples[0].symbol == "Parser"


def test_check_enrichment_when_examples_empty_list_returns_no_finding():
    source = '''\
class Parser:
    """Parse input data."""
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=[])

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_check_enrichment_when_examples_enabled_init_module_returns_finding():
    source = '''\
"""Package docstring."""

FOO = 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "__init__.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert len(missing_examples) == 1
    assert "Module" in missing_examples[0].message


# ---------------------------------------------------------------------------
# Edge case and regression tests (missing-examples)
# ---------------------------------------------------------------------------


def test_missing_examples_when_class_has_examples_section_returns_none():
    source = '''\
class Parser:
    """Parse input data.

    Examples:
        >>> p = Parser()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_undocumented_symbol_returns_none():
    source = """\
class Parser:
    pass
"""
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_empty_require_list_returns_none():
    source = '''\
class Parser:
    """Parse input data."""
    pass

@dataclass
class Config:
    """Application config."""
    debug: bool

class Color(Enum):
    """Colors."""
    RED = 1
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=[])

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_type_not_in_list_returns_none():
    source = '''\
class Parser:
    """Parse input data."""
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["dataclass"])

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_init_module_has_examples_section_returns_none():
    source = '''\
"""Package docstring.

Examples:
    >>> import pkg
"""

FOO = 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "__init__.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_non_init_module_no_finding():
    source = '''\
"""Regular module docstring."""

FOO = 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "regular.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_namedtuple_does_not_trigger():
    source = '''\
class Point(NamedTuple):
    """A point in 2D space."""
    x: int
    y: int
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(
        require_examples=["class", "protocol", "dataclass", "enum"]
    )

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_typeddict_does_not_trigger():
    source = '''\
class Options(TypedDict):
    """Configuration options."""
    verbose: bool
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(
        require_examples=["class", "protocol", "dataclass", "enum"]
    )

    findings = check_enrichment(source, tree, config, "test.py")

    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    assert missing_examples == []


def test_missing_examples_when_nested_class_inside_function_triggers_on_inner_class():
    source = '''\
def factory():
    """Create a parser.

    Returns:
        A new parser instance.
    """
    class Parser:
        """Inner parser."""
        pass
    return Parser()
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_examples=["class"])

    findings = check_enrichment(source, tree, config, "test.py")

    # The inner class IS documented and IS a class, so it DOES get checked.
    # However, it's not excluded by the rule — nested classes with docstrings
    # are valid symbols returned by get_documented_symbols.
    # The function itself won't trigger because functions aren't in the config.
    missing_examples = [f for f in findings if f.rule == "missing-examples"]
    # Parser class has a docstring and kind="class", so it triggers
    assert len(missing_examples) == 1
    assert missing_examples[0].symbol == "Parser"


def test_missing_examples_when_protocol_with_abc_classifies_as_protocol():
    source = '''\
class Handler(Protocol, ABC):
    """Handle requests."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["protocol"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-examples"
    assert "Protocol" in result.message


def test_missing_examples_when_str_enum_mixin_classifies_as_enum():
    source = '''\
class Color(str, Enum):
    """Available colors."""
    RED = "red"
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(
        require_raises=False,
        require_yields=False,
        require_warns=False,
        require_receives=False,
        require_other_parameters=False,
        require_attributes=False,
        require_examples=["enum"],
    )

    result = _check_missing_examples(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-examples"
    assert "Enum" in result.message
