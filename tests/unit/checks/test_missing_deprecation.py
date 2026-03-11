"""Tests for the missing-deprecation enrichment rule."""

from __future__ import annotations

import ast

import pytest

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _build_node_index,
    _check_missing_deprecation,
    _has_deprecated_decorator,
    _has_deprecation_warning_call,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

pytestmark = [pytest.mark.unit]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_symbol_and_index(source: str):
    """Build first function symbol, node_index and tree from inline source.

    Args:
        source: Python source code to parse.

    Returns:
        Tuple of (symbol, node_index, tree) where symbol is the first
        function or method found.
    """
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    func_symbols = [s for s in symbols if s.kind in ("function", "method")]
    if not func_symbols:
        func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.kind in ("function", "method"), (
        f"Expected function/method, got kind={symbol.kind!r}, name={symbol.name!r}"
    )
    assert symbol.docstring is not None
    return symbol, node_index, tree


def _make_outer_symbol_and_index(source: str):
    """Build the outermost function symbol and node_index from inline source.

    Picks the function symbol with the smallest line number so that
    nested-scope tests always target the outer function.

    Args:
        source: Python source code to parse.

    Returns:
        Tuple of (outer_symbol, node_index, tree).
    """
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    func_symbols = [s for s in symbols if s.kind in ("function", "method")]
    assert func_symbols, "No function symbols found"
    outer = min(func_symbols, key=lambda s: s.line)
    assert outer.docstring is not None
    return outer, node_index, tree


# ---------------------------------------------------------------------------
# AC 1 & 2: warnings.warn variants trigger finding
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "warning_class",
    ["DeprecationWarning", "PendingDeprecationWarning", "FutureWarning"],
)
def test_deprecation_warning_variants(warning_class: str) -> None:
    """AC 1 & 2: warnings.warn with any of the three deprecation categories emits a finding."""
    source = f'''\
import warnings

def old_api():
    """Do the old thing."""
    warnings.warn("Use new_api instead", {warning_class})
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "old_api"
    assert result.rule == "missing-deprecation"
    assert "deprecated" in result.message.lower()
    assert result.category == "required"


# ---------------------------------------------------------------------------
# AC 3: @deprecated decorator forms trigger finding
# ---------------------------------------------------------------------------


_DEPRECATED_FUNC_SOURCE = '''\
def old_api():
    """Do the old thing."""
    pass
'''


@pytest.mark.parametrize(
    "decorator_prefix",
    [
        pytest.param("@deprecated", id="name-form"),
        pytest.param("@typing_extensions.deprecated", id="attribute-form"),
        pytest.param('@deprecated("Use new_api instead.")', id="name-call-form"),
        pytest.param(
            '@typing_extensions.deprecated("Use new_api instead.")',
            id="attribute-call-form",
        ),
    ],
)
def test_deprecated_decorator(decorator_prefix: str) -> None:
    """AC 3: @deprecated and @*.deprecated decorators trigger finding (all call forms).

    Covers bare forms (third-party deprecated package) and call forms
    (PEP 702 / typing_extensions.deprecated — always requires message arg).
    """
    source = f"{decorator_prefix}\n{_DEPRECATED_FUNC_SOURCE}"

    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "old_api"
    assert result.rule == "missing-deprecation"
    assert result.category == "required"


# ---------------------------------------------------------------------------
# AC 4: "deprecated" anywhere in docstring passes
# ---------------------------------------------------------------------------


def test_deprecated_in_docstring_passes() -> None:
    """AC 4: 'deprecated' anywhere in docstring suppresses the finding."""
    source = '''\
import warnings

def old_api():
    """This function is deprecated. Use new_api instead."""
    warnings.warn("Use new_api instead", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_deprecated_case_insensitive_passes() -> None:
    """AC 4: 'Deprecated' (capital D) also suppresses the finding (case-insensitive)."""
    source = '''\
import warnings

def old_api():
    """Deprecated: Use new_api instead."""
    warnings.warn("Use new_api instead", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 5: No deprecation pattern -> no finding
# ---------------------------------------------------------------------------


def test_no_deprecation_pattern_no_finding() -> None:
    """AC 5: function with no deprecation pattern produces no finding."""
    source = '''\
def active_api(x):
    """Compute and return x squared."""
    return x ** 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 6: Nested scope — outer function not flagged
# ---------------------------------------------------------------------------


def test_nested_function_not_flagged() -> None:
    """AC 6: warnings.warn inside a nested def does not flag the outer function."""
    source = '''\
import warnings

def outer():
    """Outer function that is not deprecated."""
    def inner():
        warnings.warn("inner is deprecated", DeprecationWarning)
    inner()
'''
    outer, node_index, _ = _make_outer_symbol_and_index(source)
    assert outer.name == "outer"
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(outer, sections, node_index, config, "test.py")

    assert result is None


def test_nested_class_method_not_flagged() -> None:
    """AC 6: warnings.warn inside a nested class method does not flag the outer function."""
    source = '''\
import warnings

def outer():
    """Outer function that is not deprecated."""
    class Inner:
        def method(self):
            """Inner method."""
            warnings.warn("method is deprecated", DeprecationWarning)
    return Inner()
'''
    outer, node_index, _ = _make_outer_symbol_and_index(source)
    assert outer.name == "outer"
    sections = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(outer, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 7: Config disable skips rule (orchestrator-level)
# ---------------------------------------------------------------------------


def test_config_disable_skips_rule() -> None:
    """AC 7: require_deprecation_notice=False skips the rule via orchestrator."""
    source = '''\
import warnings

def old_api():
    """Do the old thing."""
    warnings.warn("Use new_api instead", DeprecationWarning)
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_deprecation_notice=False)

    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-deprecation" for f in findings)


# ---------------------------------------------------------------------------
# AC 6b: class symbol -> no finding (guard: only FunctionDef/AsyncFunctionDef)
# ---------------------------------------------------------------------------


def test_class_symbol_no_finding() -> None:
    """Class symbol is not a function/method — guard returns None."""
    source = '''\
import warnings

class OldClass:
    """An old class that will be deprecated."""

    def method(self):
        """A method."""
        warnings.warn("OldClass is deprecated", DeprecationWarning)
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = next(s for s in symbols if s.kind == "class")
    assert class_symbol.docstring is not None
    sections: set[str] = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert result is None


# ---------------------------------------------------------------------------
# AC 1 (async): async def with deprecation warning triggers finding
# ---------------------------------------------------------------------------


def test_async_function_with_deprecation_emits_finding() -> None:
    """AsyncFunctionDef is covered — async def triggers finding."""
    source = '''\
import warnings

async def old_async_api():
    """Fetch data asynchronously."""
    warnings.warn("Use new_async_api instead", DeprecationWarning)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    assert symbol.name == "old_async_api"
    sections: set[str] = set()
    config = EnrichmentConfig()

    result = _check_missing_deprecation(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "old_async_api"
    assert result.rule == "missing-deprecation"
    assert result.category == "required"


# ---------------------------------------------------------------------------
# AC 8 (cross-rule): Both missing-raises and missing-deprecation fire together
# ---------------------------------------------------------------------------


def test_cross_rule_deprecation_and_missing_raises() -> None:
    """Task 6.14 (cross-rule): both missing-raises and missing-deprecation fire together."""
    source = '''\
import warnings

def old_api(x):
    """Do the old thing."""
    warnings.warn("Use new_api instead", DeprecationWarning)
    if x < 0:
        raise ValueError("x must be non-negative")
    return x
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    rules = {f.rule for f in findings}
    assert "missing-deprecation" in rules
    assert "missing-raises" in rules


# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------


def test_has_deprecation_warning_call_detects_warnings_warn() -> None:
    """Helper: _has_deprecation_warning_call detects warnings.warn at top scope."""
    source = '''\
import warnings

def f():
    """A function."""
    warnings.warn("msg", DeprecationWarning)
'''
    tree = ast.parse(source)
    func_node = tree.body[1]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecation_warning_call(func_node) is True


def test_has_deprecation_warning_call_skips_nested_def() -> None:
    """Helper: _has_deprecation_warning_call skips nested FunctionDef."""
    source = '''\
import warnings

def outer():
    """Outer."""
    def inner():
        warnings.warn("msg", DeprecationWarning)
'''
    tree = ast.parse(source)
    func_node = tree.body[1]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecation_warning_call(func_node) is False


def test_has_deprecation_warning_call_rejects_bare_warn() -> None:
    """Helper: bare warn() (not warnings.warn) is not matched."""
    source = '''\
def f():
    """A function."""
    warn("msg", DeprecationWarning)
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecation_warning_call(func_node) is False


def test_has_deprecated_decorator_name_form() -> None:
    """Helper: @deprecated (Name form) detected."""
    source = '''\
@deprecated
def f():
    """A function."""
    pass
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecated_decorator(func_node) is True


def test_has_deprecated_decorator_attribute_form() -> None:
    """Helper: @typing_extensions.deprecated (Attribute form) detected."""
    source = '''\
@typing_extensions.deprecated
def f():
    """A function."""
    pass
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecated_decorator(func_node) is True


def test_has_deprecated_decorator_name_call_form() -> None:
    """Helper: @deprecated("msg") call form (PEP 702 standard) detected."""
    source = '''\
@deprecated("Use new_api instead.")
def f():
    """A function."""
    pass
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecated_decorator(func_node) is True


def test_has_deprecated_decorator_attribute_call_form() -> None:
    """Helper: @typing_extensions.deprecated("msg") call form (PEP 702) detected."""
    source = '''\
@typing_extensions.deprecated("Use new_api instead.")
def f():
    """A function."""
    pass
'''
    tree = ast.parse(source)
    func_node = tree.body[0]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecated_decorator(func_node) is True


def test_has_deprecated_decorator_unrelated_decorator_not_matched() -> None:
    """Helper: @staticmethod is not matched as a deprecated decorator."""
    source = '''\
class Foo:
    """Foo."""

    @staticmethod
    def f():
        """A function."""
        pass
'''
    tree = ast.parse(source)
    class_node = tree.body[0]
    assert isinstance(class_node, ast.ClassDef)
    # body[0] is the class docstring Expr; body[1] is the FunctionDef
    func_node = next(n for n in class_node.body if isinstance(n, ast.FunctionDef))
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecated_decorator(func_node) is False


def test_keyword_category_arg_detected() -> None:
    """warnings.warn(msg, category=DeprecationWarning) form is detected."""
    source = '''\
import warnings

def f():
    """A function."""
    warnings.warn("msg", category=DeprecationWarning)
'''
    tree = ast.parse(source)
    func_node = tree.body[1]
    assert isinstance(func_node, ast.FunctionDef)

    assert _has_deprecation_warning_call(func_node) is True
