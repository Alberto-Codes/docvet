"""Tests for the trivial-docstring enrichment rule.

Covers name decomposition (snake_case, CamelCase, acronyms, digits),
summary word extraction (stop word filtering), the trivial-docstring
check function (subset detection, property skip, config gating), and
cross-rule interaction (story 35.4).
"""

from __future__ import annotations

import ast

import pytest

from docvet.checks.enrichment import (
    _build_node_index,
    _check_trivial_docstring,
    _decompose_name,
    _extract_summary_words,
    _parse_sections,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_symbol_and_index(source: str, *, kind: str | None = None):
    """Build a symbol + node_index from inline source.

    Args:
        source: Python source code string.
        kind: If given, select the first symbol matching this kind.
            If None, select the first non-module symbol.

    Returns:
        Tuple of (symbol, node_index, tree).
    """
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    if kind:
        candidates = [s for s in symbols if s.kind == kind]
    else:
        candidates = [s for s in symbols if s.kind != "module"]
    symbol = candidates[0]
    return symbol, node_index, tree


_DEFAULT_CONFIG = EnrichmentConfig()
_DISABLED_CONFIG = EnrichmentConfig(check_trivial_docstrings=False)


# ---------------------------------------------------------------------------
# _decompose_name tests
# ---------------------------------------------------------------------------


class TestDecomposeName:
    """Tests for the _decompose_name helper (AC: 6, 7)."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("snake_case_name", {"snake", "case", "name"}),
            ("get_user", {"get", "user"}),
            ("CamelCaseName", {"camel", "case", "name"}),
            ("UserManager", {"user", "manager"}),
            ("HTTPSConnection", {"https", "connection"}),
            ("HTMLParser", {"html", "parser"}),
            ("XMLHTTPRequest", {"xmlhttp", "request"}),
            ("Base64Encoder", {"base64", "encoder"}),
            ("_private_func", {"private", "func"}),
            ("__dunder__", {"dunder"}),
            ("__private", {"private"}),
            ("_", set()),
            ("___", set()),
            ("", set()),
            ("x", {"x"}),
            ("getUser", {"get", "user"}),
        ],
        ids=[
            "snake_case",
            "snake_two_words",
            "camel_case",
            "camel_two_words",
            "acronym_https",
            "acronym_html",
            "multi_acronym",
            "digits_attached",
            "leading_underscore",
            "dunder",
            "double_leading",
            "single_underscore",
            "triple_underscore",
            "empty_string",
            "single_char",
            "lower_camel",
        ],
    )
    def test_decompose_name(self, name: str, expected: set[str]):
        """Verify word decomposition for various name patterns."""
        assert _decompose_name(name) == expected


# ---------------------------------------------------------------------------
# _extract_summary_words tests
# ---------------------------------------------------------------------------


class TestExtractSummaryWords:
    """Tests for the _extract_summary_words helper (AC: 5)."""

    @pytest.mark.parametrize(
        ("docstring", "expected"),
        [
            ("The user manager.", {"user", "manager"}),
            ("A simple and easy to use parser.", {"simple", "easy", "use", "parser"}),
            ("Get user.", {"get", "user"}),
            ("The.", set()),
            ("", set()),
            ("Process the data.", {"process", "data"}),
            (
                "Fetch a user from the database by their ID.",
                {"fetch", "user", "database", "their", "id"},
            ),
        ],
        ids=[
            "articles_filtered",
            "multiple_stop_words",
            "no_stop_words",
            "only_stop_words",
            "empty_string",
            "mixed_stop_words",
            "meaningful_sentence",
        ],
    )
    def test_extract_summary_words(self, docstring: str, expected: set[str]):
        """Verify stop word filtering and tokenisation."""
        assert _extract_summary_words(docstring) == expected


# ---------------------------------------------------------------------------
# Core detection tests
# ---------------------------------------------------------------------------


class TestTrivialDocstringDetection:
    """Tests for the _check_trivial_docstring rule (AC: 1-4)."""

    def test_snake_case_exact_match_emits_finding(self):
        """AC1: get_user + 'Get user.' is trivial."""
        source = 'def get_user():\n    """Get user."""\n    return 1\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.file == "test.py"
        assert result.line == symbol.line
        assert result.symbol == "get_user"
        assert result.rule == "trivial-docstring"
        assert result.category == "recommended"
        assert "restates the name" in result.message

    def test_camel_case_class_trivial_emits_finding(self):
        """AC2: UserManager class + 'User manager.' is trivial."""
        source = 'class UserManager:\n    """User manager."""\n'
        symbol, node_index, _ = _make_symbol_and_index(source, kind="class")
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.rule == "trivial-docstring"
        assert result.category == "recommended"

    def test_stop_words_filtered_subset_emits_finding(self):
        """AC3: 'Process the data.' after stop words is subset of process_data."""
        source = 'def process_data():\n    """Process the data."""\n    pass\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.rule == "trivial-docstring"

    def test_meaningful_docstring_no_finding(self):
        """AC4: 'Fetch a user from the database by their ID.' is not trivial."""
        source = (
            "def get_user():\n"
            '    """Fetch a user from the database by their ID."""\n'
            "    return 1\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None


# ---------------------------------------------------------------------------
# Guard clause tests
# ---------------------------------------------------------------------------


class TestTrivialDocstringGuards:
    """Tests for guard clauses that prevent false positives."""

    def test_no_docstring_no_finding(self):
        """Function without docstring produces no finding."""
        source = "def get_user():\n    return 1\n"
        tree = ast.parse(source)
        from docvet.ast_utils import get_documented_symbols

        symbols = get_documented_symbols(tree)
        node_index = _build_node_index(tree)
        func_symbols = [s for s in symbols if s.kind == "function"]
        assert len(func_symbols) == 1
        symbol = func_symbols[0]
        assert symbol.docstring is None
        result = _check_trivial_docstring(
            symbol, set(), node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None

    def test_single_char_name_still_trivial(self):
        """Single-char name x with docstring 'X.' is trivial — subset match."""
        source = 'def x():\n    """X."""\n    pass\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None

    def test_all_stop_words_docstring_no_finding(self):
        """Docstring that is all stop words produces no finding."""
        source = 'def process():\n    """The."""\n    pass\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


class TestTrivialDocstringEdgeCases:
    """Edge cases for subset detection."""

    def test_partial_subset_extra_word_no_finding(self):
        """Summary with word not in name is not a subset."""
        source = 'def validate_input():\n    """Validate input data."""\n    pass\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None

    def test_superset_docstring_no_finding(self):
        """Summary has more words than name — not a subset."""
        source = 'def process():\n    """Process data."""\n    pass\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None

    def test_module_symbol_trivial_finding(self):
        """Module symbol with trivial docstring emits finding."""
        source = '"""Module."""\n\nx = 1\n'
        tree = ast.parse(source)
        from docvet.ast_utils import get_documented_symbols

        symbols = get_documented_symbols(tree)
        node_index = _build_node_index(tree)
        mod_symbol = [s for s in symbols if s.kind == "module"][0]
        assert mod_symbol.docstring is not None
        sections = _parse_sections(mod_symbol.docstring)
        result = _check_trivial_docstring(
            mod_symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.rule == "trivial-docstring"
        assert result.symbol == "test"  # module_display_name("test.py")

    def test_method_symbol_trivial_finding(self):
        """Method on a class with trivial docstring emits finding."""
        source = (
            "class Foo:\n"
            '    """Foo class."""\n'
            "    def get_data(self):\n"
            '        """Get data."""\n'
            "        return 1\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source, kind="method")
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.rule == "trivial-docstring"

    def test_overloaded_function_trivial_fires(self):
        """Implementation function behind @overload stubs still fires trivial-docstring."""
        source = (
            "from typing import overload\n"
            "@overload\n"
            "def get_user(id: int) -> str: ...\n"
            "@overload\n"
            "def get_user(id: str) -> str: ...\n"
            "def get_user(id):\n"
            '    """Get user."""\n'
            "    return str(id)\n"
        )
        tree = ast.parse(source)
        findings = check_enrichment(source, tree, _DEFAULT_CONFIG, "test.py")
        trivial = [f for f in findings if f.rule == "trivial-docstring"]
        assert len(trivial) == 1

    def test_backtick_content_adds_information(self):
        """Docstring with backtick content has extra words — not trivial."""
        source = 'def get_user():\n    """Get `User` model instance."""\n    return 1\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None

    def test_multiline_trivial_first_line(self):
        """Multi-line docstring with trivial first line still flags."""
        source = (
            "def get_user():\n"
            '    """Get user.\n'
            "\n"
            "    Fetches the active user from the session cache.\n"
            '    """\n'
            "    return 1\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.rule == "trivial-docstring"


# ---------------------------------------------------------------------------
# Property skip tests (AC: 10)
# ---------------------------------------------------------------------------


class TestPropertySkip:
    """Tests for @property/@cached_property skip logic (AC: 10)."""

    def test_property_skip_no_finding(self):
        """AC10: @property method restating name is not flagged."""
        source = (
            "class Foo:\n"
            '    """Foo class."""\n'
            "    @property\n"
            "    def user_name(self):\n"
            '        """The user name."""\n'
            "        return self._name\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source, kind="method")
        assert symbol.name == "user_name"
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None

    def test_cached_property_skip_no_finding(self):
        """AC10: @cached_property method restating name is not flagged."""
        source = (
            "from functools import cached_property\n"
            "class Foo:\n"
            '    """Foo class."""\n'
            "    @cached_property\n"
            "    def total_count(self):\n"
            '        """Total count."""\n'
            "        return 42\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source, kind="method")
        assert symbol.name == "total_count"
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is None

    def test_non_property_method_emits_finding(self):
        """Regular method restating name IS flagged (no property decorator)."""
        source = (
            "class Foo:\n"
            '    """Foo class."""\n'
            "    def user_name(self):\n"
            '        """User name."""\n'
            "        return self._name\n"
        )
        symbol, node_index, _ = _make_symbol_and_index(source, kind="method")
        assert symbol.name == "user_name"
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.rule == "trivial-docstring"
        assert result.category == "recommended"


# ---------------------------------------------------------------------------
# Config tests (AC: 8)
# ---------------------------------------------------------------------------


class TestTrivialDocstringConfig:
    """Tests for config gating."""

    def test_config_disable_no_finding(self):
        """AC8: check_trivial_docstrings=False skips the rule entirely."""
        source = 'def get_user():\n    """Get user."""\n    return 1\n'
        tree = ast.parse(source)
        findings = check_enrichment(source, tree, _DISABLED_CONFIG, "test.py")
        trivial = [f for f in findings if f.rule == "trivial-docstring"]
        assert len(trivial) == 0


# ---------------------------------------------------------------------------
# Category and assertion tests
# ---------------------------------------------------------------------------


class TestTrivialDocstringCategory:
    """Tests for finding category and field completeness."""

    def test_finding_category_recommended(self):
        """AC7 (implicit): trivial-docstring uses recommended category."""
        source = 'def get_user():\n    """Get user."""\n    return 1\n'
        symbol, node_index, _ = _make_symbol_and_index(source)
        sections = _parse_sections(symbol.docstring)
        result = _check_trivial_docstring(
            symbol, sections, node_index, _DEFAULT_CONFIG, "test.py"
        )
        assert result is not None
        assert result.category == "recommended"


# ---------------------------------------------------------------------------
# Cross-rule interaction test
# ---------------------------------------------------------------------------


class TestCrossRuleInteraction:
    """Tests for cross-rule interaction with existing enrichment rules."""

    def test_trivial_and_missing_raises_both_fire(self):
        """Trivial docstring + missing-raises fire independently."""
        source = (
            'def get_user():\n    """Get user."""\n    raise ValueError("not found")\n'
        )
        tree = ast.parse(source)
        findings = check_enrichment(source, tree, _DEFAULT_CONFIG, "test.py")
        rules = {f.rule for f in findings}
        assert "trivial-docstring" in rules
        assert "missing-raises" in rules
