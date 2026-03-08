"""Tests for the missing-returns enrichment rule."""

from __future__ import annotations

import ast

import pytest

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _build_node_index,
    _check_missing_returns,
    _is_stub_function,
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
    # Prefer function/method symbols so tests target callable objects
    # rather than enclosing classes when both are documented.
    func_symbols = [s for s in symbols if s.kind in ("function", "method")]
    if not func_symbols:
        func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


# ---------------------------------------------------------------------------
# AC 1: Function with return <expr> and no Returns section -> finding
# ---------------------------------------------------------------------------


def test_function_with_return_value_and_no_returns_section_emits_finding():
    """AC 1: return <expr> without Returns: section."""
    source = '''\
def compute(x):
    """Compute a result."""
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "compute"
    assert result.rule == "missing-returns"
    assert result.category == "required"
    assert "compute" in result.message
    assert "Returns" in result.message


# ---------------------------------------------------------------------------
# AC 2: Bare return or return None -> no finding
# ---------------------------------------------------------------------------


def test_function_with_bare_return_only_no_finding():
    """AC 2: bare return is control flow, not meaningful."""
    source = '''\
def early_exit(x):
    """Exit early if needed."""
    if x < 0:
        return
    print(x)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_function_with_return_none_only_no_finding():
    """AC 2: return None is not meaningful."""
    source = '''\
def do_nothing():
    """Do nothing special."""
    return None
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 3: Mix of return value and bare return -> finding
# ---------------------------------------------------------------------------


def test_function_with_mixed_returns_emits_finding():
    """AC 3: at least one meaningful return triggers finding."""
    source = '''\
def maybe_compute(x):
    """Maybe compute a result."""
    if x < 0:
        return
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-returns"


# ---------------------------------------------------------------------------
# AC 4: @property, __init__, dunder methods -> no finding
# ---------------------------------------------------------------------------


def test_property_method_no_finding():
    """AC 4: @property skipped."""
    source = '''\
class Foo:
    """A class."""

    @property
    def name(self):
        """The name."""
        return self._name
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_init_method_no_finding():
    """AC 4: __init__ skipped (dunder)."""
    source = '''\
class Foo:
    """A class."""

    def __init__(self):
        """Init the instance."""
        return None
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    # Find __init__ symbol
    init_symbol = [s for s in symbols if s.name == "__init__"][0]
    assert init_symbol.docstring is not None
    sections = _parse_sections(init_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(
        init_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_dunder_repr_no_finding():
    """AC 4: __repr__ skipped (dunder)."""
    source = '''\
class Foo:
    """A class."""

    def __repr__(self):
        """String representation."""
        return f"Foo()"
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    repr_symbol = [s for s in symbols if s.name == "__repr__"][0]
    assert repr_symbol.docstring is not None
    sections = _parse_sections(repr_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(
        repr_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_dunder_len_no_finding():
    """AC 4: __len__ skipped (dunder)."""
    source = '''\
class Foo:
    """A class."""

    def __len__(self):
        """Return count."""
        return 42
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    len_symbol = [s for s in symbols if s.name == "__len__"][0]
    assert len_symbol.docstring is not None
    sections = _parse_sections(len_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(len_symbol, sections, node_index, config, "test.py")

    assert result is None


def test_dunder_bool_no_finding():
    """AC 4: __bool__ skipped (dunder)."""
    source = '''\
class Foo:
    """A class."""

    def __bool__(self):
        """Check truthiness."""
        return True
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    bool_symbol = [s for s in symbols if s.name == "__bool__"][0]
    assert bool_symbol.docstring is not None
    sections = _parse_sections(bool_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(
        bool_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# AC 5: return <expr> inside nested function/class -> no finding for outer
# ---------------------------------------------------------------------------


def test_return_in_nested_function_no_finding_for_outer():
    """AC 5: scope-aware walk — nested def stops traversal."""
    source = '''\
def outer():
    """Outer function."""
    def inner():
        return 42
    inner()
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_return_in_nested_class_no_finding_for_outer():
    """AC 5: scope-aware walk — nested class stops traversal."""
    source = '''\
def outer():
    """Outer function."""
    class Inner:
        def method(self):
            return 42
    Inner()
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 6: Function with Returns: section present -> no finding
# ---------------------------------------------------------------------------


def test_function_with_returns_section_present_no_finding():
    """AC 6: Returns: section satisfies the check."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The doubled value.
    """
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 7: require-returns = false -> rule skipped (orchestrator-level)
# ---------------------------------------------------------------------------


def test_require_returns_false_config_skips_rule():
    """AC 7: config gating via orchestrator."""
    source = '''\
def compute(x):
    """Compute a result."""
    return x * 2
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_returns=False)

    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-returns" for f in findings)


# ---------------------------------------------------------------------------
# AC 9: Function with no docstring -> no finding
# ---------------------------------------------------------------------------


def test_function_without_docstring_no_finding():
    """AC 9: enrichment only runs on documented symbols (orchestrator)."""
    source = """\
def compute(x):
    return x * 2
"""
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-returns" for f in findings)


# ---------------------------------------------------------------------------
# AC 11: @abstractmethod -> no finding
# ---------------------------------------------------------------------------


def test_abstractmethod_with_return_no_finding():
    """AC 11: abstract methods define interface contracts."""
    source = '''\
from abc import abstractmethod

class Base:
    """A base class."""

    @abstractmethod
    def compute(self):
        """Compute a result."""
        return 0
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    compute_symbol = [s for s in symbols if s.name == "compute"][0]
    assert compute_symbol.docstring is not None
    sections = _parse_sections(compute_symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(
        compute_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# AC 12: Stub functions -> no finding
# ---------------------------------------------------------------------------


def test_stub_function_with_pass_no_finding():
    """AC 12: stub with pass body."""
    source = '''\
def placeholder() -> int:
    """A placeholder function."""
    pass
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_stub_function_with_ellipsis_no_finding():
    """AC 12: stub with Ellipsis body."""
    source = '''\
def placeholder() -> int:
    """A placeholder function."""
    ...
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_stub_function_with_raise_not_implemented_no_finding():
    """AC 12: stub with raise NotImplementedError."""
    source = '''\
def placeholder() -> int:
    """A placeholder function."""
    raise NotImplementedError
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# Additional edge cases
# ---------------------------------------------------------------------------


def test_class_symbol_no_finding():
    """Class symbol is not a function/method — skip."""
    source = '''\
class Foo:
    """A class with a class body return."""
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

    result = _check_missing_returns(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_async_function_with_return_value_emits_finding():
    """Async function with return value and no Returns: section."""
    source = '''\
async def fetch(url):
    """Fetch a URL."""
    return await something(url)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-returns"
    assert result.symbol == "fetch"


def test_function_with_returns_section_and_return_value_zero_findings():
    """Negative: Returns section present AND return value — zero findings."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The doubled value.
    """
    return x * 2
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-returns" for f in findings)


def test_overload_function_with_return_no_finding():
    """Defensive skip: @overload functions should not trigger missing-returns."""
    source = '''\
from typing import overload

@overload
def process(x: int) -> int:
    """Process an integer."""
    ...

@overload
def process(x: str) -> str:
    """Process a string."""
    ...
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    config = EnrichmentConfig()

    for sym in symbols:
        if sym.name == "process" and sym.docstring:
            sections = _parse_sections(sym.docstring)
            result = _check_missing_returns(
                sym, sections, node_index, config, "test.py"
            )
            assert result is None


def test_cached_property_no_finding():
    """AC 4: @cached_property skipped like @property."""
    source = '''\
class Foo:
    """A class."""

    @cached_property
    def name(self):
        """The name."""
        return self._name
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_returns(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# Direct _is_stub_function helper tests (M2 review finding)
# ---------------------------------------------------------------------------


def test_is_stub_function_pass():
    """Direct test: pass-only body is a stub."""
    tree = ast.parse("def f():\n    pass\n")
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True


def test_is_stub_function_ellipsis():
    """Direct test: Ellipsis-only body is a stub."""
    tree = ast.parse("def f():\n    ...\n")
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True


def test_is_stub_function_raise_not_implemented():
    """Direct test: raise NotImplementedError body is a stub."""
    tree = ast.parse("def f():\n    raise NotImplementedError\n")
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True


def test_is_stub_function_raise_not_implemented_with_args():
    """Direct test: raise NotImplementedError('msg') body is a stub."""
    tree = ast.parse("def f():\n    raise NotImplementedError('not done')\n")
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True


def test_is_stub_function_multi_statement_not_stub():
    """Direct test: multi-statement body is NOT a stub."""
    tree = ast.parse("def f():\n    x = 1\n    return x\n")
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is False


def test_is_stub_function_documented_stub_with_pass():
    """Direct test: documented stub (docstring + pass) is a stub."""
    tree = ast.parse('def f():\n    """A placeholder."""\n    pass\n')
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True


def test_is_stub_function_documented_stub_with_ellipsis():
    """Direct test: documented stub (docstring + ...) is a stub."""
    tree = ast.parse('def f():\n    """A placeholder."""\n    ...\n')
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True


def test_is_stub_function_documented_stub_with_raise():
    """Direct test: documented stub (docstring + raise) is a stub."""
    tree = ast.parse(
        'def f():\n    """A placeholder."""\n    raise NotImplementedError\n'
    )
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)
    assert _is_stub_function(func_node) is True
