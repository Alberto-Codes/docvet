"""Tests for missing-deprecation enrichment rule.

Covers ``missing-deprecation`` rule (story 35.2), including
``warnings.warn(..., DeprecationWarning)`` positional and keyword forms,
``PendingDeprecationWarning``, ``FutureWarning``, ``@deprecated`` decorator
(PEP 702 ``ast.Call`` form), scope-aware nested function isolation,
docstring notice escape hatch, config gating, and cross-rule interaction
with ``missing-warns``.
"""

from __future__ import annotations

import ast

import pytest

from docvet.checks.enrichment import (
    _build_node_index,
    _check_missing_deprecation,
    _has_deprecated_decorator,
    _is_deprecation_warn_call,
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
    func_symbols = [s for s in symbols if s.kind in ("function", "method")]
    if not func_symbols:
        func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


_DEFAULT_CONFIG = EnrichmentConfig()
_DISABLED_CONFIG = EnrichmentConfig(require_deprecation_notice=False)


# ---------------------------------------------------------------------------
# _is_deprecation_warn_call tests
# ---------------------------------------------------------------------------


class TestIsDeprecationWarnCall:
    """Tests for the _is_deprecation_warn_call helper."""

    @pytest.mark.parametrize(
        "source,expected",
        [
            # Positional DeprecationWarning
            (
                "import warnings\nwarnings.warn('x', DeprecationWarning)",
                True,
            ),
            # Positional PendingDeprecationWarning
            (
                "import warnings\nwarnings.warn('x', PendingDeprecationWarning)",
                True,
            ),
            # Positional FutureWarning
            (
                "import warnings\nwarnings.warn('x', FutureWarning)",
                True,
            ),
            # Keyword category=DeprecationWarning
            (
                "import warnings\nwarnings.warn('x', category=DeprecationWarning)",
                True,
            ),
            # No explicit category — defaults to UserWarning, not matched
            (
                "import warnings\nwarnings.warn('x')",
                False,
            ),
            # Explicit UserWarning — not a deprecation category
            (
                "import warnings\nwarnings.warn('x', UserWarning)",
                False,
            ),
            # Bare warn() with DeprecationWarning
            (
                "from warnings import warn\nwarn('x', DeprecationWarning)",
                True,
            ),
        ],
        ids=[
            "positional-DeprecationWarning",
            "positional-PendingDeprecationWarning",
            "positional-FutureWarning",
            "keyword-category",
            "no-category-UserWarning-default",
            "explicit-UserWarning",
            "bare-warn-DeprecationWarning",
        ],
    )
    def test_deprecation_warn_call_variants(self, source: str, expected: bool):
        """Verify _is_deprecation_warn_call matches correct patterns."""
        tree = ast.parse(source)
        # Find the Call node in the tree
        call_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_node = node
                break
        assert call_node is not None
        assert _is_deprecation_warn_call(call_node) is expected

    def test_non_warn_call_returns_false(self):
        """Non-warn calls are never matched."""
        tree = ast.parse("print('hello')")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                assert _is_deprecation_warn_call(node) is False


# ---------------------------------------------------------------------------
# _has_deprecated_decorator tests
# ---------------------------------------------------------------------------


class TestHasDeprecatedDecorator:
    """Tests for the _has_deprecated_decorator helper (PEP 702 ast.Call form)."""

    def test_bare_deprecated_with_arg(self):
        """@deprecated('reason') — ast.Call(func=Name) form."""
        source = '@deprecated("Use new_func")\ndef foo():\n    """Doc."""\n    pass'
        tree = ast.parse(source)
        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef)
        assert _has_deprecated_decorator(func_node) is True

    def test_typing_extensions_qualified(self):
        """@typing_extensions.deprecated('reason') — ast.Call(func=Attribute)."""
        source = (
            '@typing_extensions.deprecated("Use new_func")\n'
            'def foo():\n    """Doc."""\n    pass'
        )
        tree = ast.parse(source)
        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef)
        assert _has_deprecated_decorator(func_node) is True

    def test_warnings_qualified(self):
        """@warnings.deprecated('reason') — ast.Call(func=Attribute)."""
        source = (
            '@warnings.deprecated("Use new_func")\ndef foo():\n    """Doc."""\n    pass'
        )
        tree = ast.parse(source)
        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef)
        assert _has_deprecated_decorator(func_node) is True

    def test_no_decorator(self):
        """Function with no decorators returns False."""
        source = 'def foo():\n    """Doc."""\n    pass'
        tree = ast.parse(source)
        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef)
        assert _has_deprecated_decorator(func_node) is False

    def test_non_deprecated_call_decorator(self):
        """@functools.lru_cache(maxsize=128) does not match."""
        source = (
            '@functools.lru_cache(maxsize=128)\ndef foo():\n    """Doc."""\n    pass'
        )
        tree = ast.parse(source)
        func_node = tree.body[0]
        assert isinstance(func_node, ast.FunctionDef)
        assert _has_deprecated_decorator(func_node) is False


# ---------------------------------------------------------------------------
# _check_missing_deprecation tests
# ---------------------------------------------------------------------------


class TestCheckMissingDeprecation:
    """Tests for the main _check_missing_deprecation check function."""

    # -- AC 1: warnings.warn(..., DeprecationWarning) without notice --

    def test_warn_deprecation_warning_emits_finding(self):
        """AC 1: DeprecationWarning in warn call without notice → finding."""
        source = (
            "import warnings\n"
            "def foo():\n"
            '    """Do something."""\n'
            "    warnings.warn('old', DeprecationWarning)\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.symbol == "foo"
        assert finding.rule == "missing-deprecation"
        assert "deprecation" in finding.message.lower()
        assert finding.category == "required"

    # -- AC 2: PendingDeprecationWarning and FutureWarning --

    @pytest.mark.parametrize(
        "category",
        ["PendingDeprecationWarning", "FutureWarning"],
        ids=["PendingDeprecationWarning", "FutureWarning"],
    )
    def test_other_deprecation_categories(self, category: str):
        """AC 2: PendingDeprecationWarning and FutureWarning → finding."""
        source = (
            "import warnings\n"
            "def foo():\n"
            '    """Do something."""\n'
            f"    warnings.warn('old', {category})\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.rule == "missing-deprecation"
        assert finding.symbol == "foo"
        assert finding.category == "required"

    # -- AC 3: @deprecated decorator --

    def test_deprecated_decorator_emits_finding(self):
        """AC 3: @deprecated('reason') without notice → finding."""
        source = (
            '@deprecated("Use new_func")\n'
            "def foo():\n"
            '    """Do something."""\n'
            "    pass\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.rule == "missing-deprecation"
        assert finding.symbol == "foo"
        assert "@deprecated" in finding.message
        assert finding.category == "required"

    def test_typing_extensions_deprecated_emits_finding(self):
        """AC 3: @typing_extensions.deprecated('reason') → finding."""
        source = (
            '@typing_extensions.deprecated("Use new_func")\n'
            "def foo():\n"
            '    """Do something."""\n'
            "    pass\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.rule == "missing-deprecation"
        assert finding.symbol == "foo"

    def test_warnings_deprecated_emits_finding(self):
        """AC 3: @warnings.deprecated('reason') → finding."""
        source = (
            '@warnings.deprecated("Use new_func")\n'
            "def foo():\n"
            '    """Do something."""\n'
            "    pass\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.rule == "missing-deprecation"

    # -- AC 4: "deprecated" in docstring → no finding --

    @pytest.mark.parametrize(
        "docstring",
        [
            "Deprecated: use new_func instead.",
            "This function is DEPRECATED.",
            ".. deprecated:: 2.0\n    Use new_func instead.",
            "Returns something. Note: deprecated since v1.",
        ],
        ids=["google-style", "uppercase", "sphinx-directive", "inline-mention"],
    )
    def test_deprecated_in_docstring_no_finding(self, docstring: str):
        """AC 4: 'deprecated' anywhere in docstring → no finding."""
        source = (
            "import warnings\n"
            f"def foo():\n"
            f'    """{docstring}"""\n'
            "    warnings.warn('old', DeprecationWarning)\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is None

    # -- AC 5: No deprecation patterns → no finding --

    def test_no_deprecation_patterns_no_finding(self):
        """AC 5: Function with no deprecation patterns → no finding."""
        source = 'def foo():\n    """Do something."""\n    return 42\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is None

    # -- AC 6: Nested function scope isolation --

    @pytest.mark.parametrize(
        "nested_def",
        [
            "    def inner():\n        warnings.warn('old', DeprecationWarning)\n",
            "    async def inner():\n"
            "        warnings.warn('old', DeprecationWarning)\n",
            "    class Inner:\n"
            "        def method(self):\n"
            "            warnings.warn('old', DeprecationWarning)\n",
        ],
        ids=["sync-function", "async-function", "nested-class"],
    )
    def test_nested_scope_boundary_isolation(self, nested_def: str):
        """AC 6: Deprecation warn in nested scope → no finding for outer."""
        source = (
            "import warnings\n"
            "def outer():\n"
            '    """Outer doc."""\n'
            f"{nested_def}"
            "    return 1\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is None

    # -- AC 7: Config disable --

    def test_config_disable_no_finding(self):
        """AC 7: require-deprecation-notice = false → rule skipped via orchestrator."""
        source = (
            "import warnings\n"
            "def foo():\n"
            '    """Do something."""\n'
            "    warnings.warn('old', DeprecationWarning)\n"
        )
        symbol, node_index, tree = _make_symbol_and_index(source)
        # With config disabled, orchestrator skips the rule.
        findings = check_enrichment(source, tree, _DISABLED_CONFIG, "test.py")
        deprecation_findings = [f for f in findings if f.rule == "missing-deprecation"]
        assert len(deprecation_findings) == 0

    # -- Additional edge cases --

    def test_class_symbol_no_finding(self):
        """Class symbols are guarded — no finding."""
        source = 'class Foo:\n    """A class."""\n    pass\n'
        from docvet.ast_utils import get_documented_symbols

        tree = ast.parse(source)
        symbols = get_documented_symbols(tree)
        node_index = _build_node_index(tree)
        class_symbol = [s for s in symbols if s.kind == "class"][0]
        assert class_symbol.docstring is not None
        sections = _parse_sections(class_symbol.docstring)
        finding = _check_missing_deprecation(
            class_symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is None

    def test_keyword_category_arg(self):
        """Keyword category=DeprecationWarning form → finding."""
        source = (
            "import warnings\n"
            "def foo():\n"
            '    """Do something."""\n'
            "    warnings.warn('old', category=DeprecationWarning)\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.rule == "missing-deprecation"

    def test_bare_warn_with_deprecation(self):
        """Bare warn() after from-import with DeprecationWarning → finding."""
        source = (
            "from warnings import warn\n"
            "def foo():\n"
            '    """Do something."""\n'
            "    warn('old', DeprecationWarning)\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is not None
        assert finding.rule == "missing-deprecation"

    def test_warn_no_category_no_finding(self):
        """warnings.warn('msg') with no explicit category → no finding."""
        source = (
            "import warnings\n"
            "def foo():\n"
            '    """Do something."""\n'
            "    warnings.warn('something happened')\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        finding = _check_missing_deprecation(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert finding is None


# ---------------------------------------------------------------------------
# Cross-rule interaction tests
# ---------------------------------------------------------------------------


class TestCrossRuleInteraction:
    """Verify interaction with existing rules via unfiltered findings."""

    def test_deprecation_and_missing_warns_both_emit(self):
        """Cross-rule: warn(DeprecationWarning) without Warns section.

        Both missing-warns and missing-deprecation should fire —
        they detect different concerns.
        """
        source = (
            "import warnings\n"
            "def foo():\n"
            '    """Do something."""\n'
            "    warnings.warn('old', DeprecationWarning)\n"
        )
        tree = ast.parse(source)
        findings = check_enrichment(source, tree, _DEFAULT_CONFIG, "test.py")
        rules = {f.rule for f in findings}
        assert "missing-warns" in rules
        assert "missing-deprecation" in rules

    def test_overload_symbol_no_findings(self):
        """@overload symbols are skipped by enrichment — no findings."""
        source = (
            "from typing import overload\n"
            "@overload\n"
            "def foo(x: int) -> int:\n"
            '    """Overload."""\n'
            "    ...\n"
        )
        tree = ast.parse(source)
        findings = check_enrichment(source, tree, _DEFAULT_CONFIG, "test.py")
        # Enrichment skips overloads entirely — no rules fire.
        deprecation_findings = [f for f in findings if f.rule == "missing-deprecation"]
        assert len(deprecation_findings) == 0
