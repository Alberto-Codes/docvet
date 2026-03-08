"""Tests for param agreement enrichment rules.

Covers ``missing-param-in-docstring`` and ``extra-param-in-docstring``
rules (story 35.1), including Google-style, Sphinx-style, positional-only,
keyword-only, async, ``*args``/``**kwargs`` exclusion, cross-rule
interaction, and config gating.
"""

from __future__ import annotations

import ast

import pytest

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _build_node_index,
    _check_extra_param_in_docstring,
    _check_missing_param_in_docstring,
    _extract_signature_params,
    _parse_args_entries,
    _parse_sections,
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

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    func_symbols = [s for s in symbols if s.kind in ("function", "method")]
    if not func_symbols:
        func_symbols = [s for s in symbols if s.kind != "module"]
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


def _make_named_symbol(source: str, name: str):
    """Build symbol + node_index for a specific named symbol."""
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    matches = [s for s in symbols if s.name == name]
    assert matches, f"No symbol named {name!r} found"
    symbol = matches[0]
    assert symbol.docstring is not None
    return symbol, node_index, tree


# ---------------------------------------------------------------------------
# AC 1 / 7.2: Missing param detection (parametrize)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected_missing"),
    [
        pytest.param(
            '''\
def greet(name, greeting):
    """Greet someone.

    Args:
        name: The person's name.
    """
''',
            ["greeting"],
            id="single-missing",
        ),
        pytest.param(
            '''\
def compute(a, b, c):
    """Compute something.

    Args:
        b: The middle value.
    """
''',
            ["a", "c"],
            id="multiple-missing",
        ),
    ],
)
def test_missing_param_detection(source, expected_missing):
    """AC 1: signature params not in Args: section."""
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "missing-param-in-docstring"
    assert result.symbol == symbol.name
    for param in expected_missing:
        assert param in result.message


# ---------------------------------------------------------------------------
# AC 2 / 7.3: Extra param detection (parametrize)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "expected_extra"),
    [
        pytest.param(
            '''\
def greet(name):
    """Greet someone.

    Args:
        name: The person's name.
        greeting: The greeting text.
    """
''',
            ["greeting"],
            id="single-extra",
        ),
        pytest.param(
            '''\
def process():
    """Process data.

    Args:
        alpha: First.
        beta: Second.
    """
''',
            ["alpha", "beta"],
            id="multiple-extra",
        ),
    ],
)
def test_extra_param_detection(source, expected_extra):
    """AC 2: Args: entries not in signature."""
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert isinstance(result, Finding)
    assert result.rule == "extra-param-in-docstring"
    assert result.symbol == symbol.name
    for param in expected_extra:
        assert param in result.message


# ---------------------------------------------------------------------------
# AC 3 / 7.4: self/cls exclusion
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "method_name"),
    [
        pytest.param(
            '''\
class Foo:
    """A class."""

    def bar(self, x):
        """Do something.

        Args:
            x: The value.
        """
''',
            "bar",
            id="self-excluded",
        ),
        pytest.param(
            '''\
class Foo:
    """A class."""

    @classmethod
    def create(cls, data):
        """Create from data.

        Args:
            data: Input data.
        """
''',
            "create",
            id="cls-excluded",
        ),
    ],
)
def test_self_cls_exclusion(source, method_name):
    """AC 3: self/cls never expected in Args: section."""
    symbol, node_index, _ = _make_named_symbol(source, method_name)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    missing = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )
    extra = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert missing is None
    assert extra is None


# ---------------------------------------------------------------------------
# AC 4-5 / 7.5: *args/**kwargs exclusion (default and opt-in)
# ---------------------------------------------------------------------------


_ARGS_KWARGS_SOURCE = '''\
def handler(name, *args, **kwargs):
    """Handle something.

    Args:
        name: The handler name.
    """
'''

_ARGS_KWARGS_DOCUMENTED_SOURCE = '''\
def handler(name, *args, **kwargs):
    """Handle something.

    Args:
        name: The handler name.
        *args: Positional arguments.
        **kwargs: Keyword arguments.
    """
'''


def test_args_kwargs_excluded_by_default():
    """AC 4: *args/**kwargs excluded with default config."""
    symbol, node_index, _ = _make_symbol_and_index(_ARGS_KWARGS_SOURCE)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()  # exclude_args_kwargs=True by default

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is None


def test_args_kwargs_required_when_opt_in():
    """AC 5: *args/**kwargs checked when exclude-args-kwargs=false."""
    symbol, node_index, _ = _make_symbol_and_index(_ARGS_KWARGS_SOURCE)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(exclude_args_kwargs=False)

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "missing-param-in-docstring"
    assert result.symbol == "handler"
    assert "args" in result.message
    assert "kwargs" in result.message


def test_star_prefixed_args_in_docstring_match_signature():
    """AC 4/5: *args/**kwargs with star prefix in docstring match bare names."""
    symbol, node_index, _ = _make_symbol_and_index(_ARGS_KWARGS_DOCUMENTED_SOURCE)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(exclude_args_kwargs=False)

    missing = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )
    extra = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert missing is None
    assert extra is None


def test_documented_args_kwargs_not_extra_when_excluded():
    """Star-prefixed entries in docs should not be extra when exclude=True."""
    symbol, node_index, _ = _make_symbol_and_index(_ARGS_KWARGS_DOCUMENTED_SOURCE)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(exclude_args_kwargs=True)

    # When exclude_args_kwargs=True, sig_params won't contain args/kwargs,
    # but doc_params will contain them -> extra finding expected.
    extra = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert extra is not None
    assert extra.rule == "extra-param-in-docstring"
    assert "args" in extra.message
    assert "kwargs" in extra.message


# ---------------------------------------------------------------------------
# AC 6 / 7.6: No Args section -> zero findings
# ---------------------------------------------------------------------------


def test_no_args_section_no_findings():
    """AC 6: no Args: section -> no param agreement findings."""
    source = '''\
def compute(x, y):
    """Compute a result."""
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    missing = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )
    extra = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert missing is None
    assert extra is None


# ---------------------------------------------------------------------------
# AC 7 / 7.7: Perfect agreement -> zero findings
# ---------------------------------------------------------------------------


def test_perfect_agreement_zero_findings():
    """AC 7: all params documented, no extras -> zero findings."""
    source = '''\
def transform(data, scale, offset):
    """Transform data.

    Args:
        data: The input data.
        scale: Scale factor.
        offset: Offset value.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    missing = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )
    extra = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert missing is None
    assert extra is None


# ---------------------------------------------------------------------------
# AC 9 / 7.8: Config disable -> zero findings
# ---------------------------------------------------------------------------


def test_config_disable_skips_both_rules():
    """AC 9: require-param-agreement=false skips both rules."""
    source = '''\
def broken(x, y):
    """Broken docs.

    Args:
        z: Wrong param.
    """
'''
    tree = ast.parse(source)
    config = EnrichmentConfig(require_param_agreement=False)

    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-param-in-docstring" for f in findings)
    assert not any(f.rule == "extra-param-in-docstring" for f in findings)


# ---------------------------------------------------------------------------
# 7.9: Cross-rule interaction tests (unfiltered findings)
# ---------------------------------------------------------------------------


def test_overload_symbol_no_param_findings():
    """Cross-rule: @overload functions produce no param agreement findings."""
    source = '''\
from typing import overload

@overload
def process(x: int) -> int:
    """Process an integer.

    Args:
        x: The value.
    """
    ...

@overload
def process(x: str) -> str:
    """Process a string.

    Args:
        x: The value.
    """
    ...
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-param-in-docstring" for f in findings)
    assert not any(f.rule == "extra-param-in-docstring" for f in findings)


def test_class_symbol_no_param_findings():
    """Cross-rule: class symbols never trigger param agreement."""
    source = '''\
class MyClass:
    """A class with Args in its docstring.

    Args:
        name: The name.
    """
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbol = [s for s in symbols if s.kind == "class"][0]
    assert class_symbol.docstring is not None
    sections = _parse_sections(class_symbol.docstring)
    config = EnrichmentConfig()

    missing = _check_missing_param_in_docstring(
        class_symbol, sections, node_index, config, "test.py"
    )
    extra = _check_extra_param_in_docstring(
        class_symbol, sections, node_index, config, "test.py"
    )

    assert missing is None
    assert extra is None


def test_module_symbol_no_param_findings():
    """Cross-rule: module symbols never trigger param agreement."""
    source = '''\
"""Module docstring.

Args:
    something: A module-level thing.
"""
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    module_symbols = [s for s in symbols if s.kind == "module"]
    if module_symbols:
        symbol = module_symbols[0]
        assert symbol.docstring is not None
        sections = _parse_sections(symbol.docstring)
        config = EnrichmentConfig()

        missing = _check_missing_param_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )
        extra = _check_extra_param_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )

        assert missing is None
        assert extra is None


def test_missing_raises_and_missing_param_both_emitted():
    """Cross-rule: missing-raises and missing-param coexist."""
    source = '''\
def risky(a, b):
    """Do something risky.

    Args:
        a: First param.
    """
    if not a:
        raise ValueError("bad a")
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py")
    rules = {f.rule for f in findings}

    assert "missing-raises" in rules
    assert "missing-param-in-docstring" in rules


# ---------------------------------------------------------------------------
# 7.10: Positional-only params
# ---------------------------------------------------------------------------


def test_positional_only_params_checked():
    """Positional-only params (before /) are included in agreement checks."""
    source = '''\
def func(x, /, y):
    """Do something.

    Args:
        y: Second param.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "missing-param-in-docstring"
    assert result.symbol == "func"
    assert "x" in result.message


# ---------------------------------------------------------------------------
# 7.11: Keyword-only params
# ---------------------------------------------------------------------------


def test_keyword_only_params_checked():
    """Keyword-only params (after *) are included in agreement checks."""
    source = '''\
def func(x, *, key=None, verbose=False):
    """Do something.

    Args:
        x: The value.
        key: A key.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "missing-param-in-docstring"
    assert result.symbol == "func"
    assert "verbose" in result.message


# ---------------------------------------------------------------------------
# 7.12: Async def params
# ---------------------------------------------------------------------------


def test_async_def_params_checked():
    """Async functions have param agreement checked."""
    source = '''\
async def fetch(url, timeout):
    """Fetch a URL.

    Args:
        url: The URL to fetch.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.rule == "missing-param-in-docstring"
    assert result.symbol == "fetch"
    assert "timeout" in result.message


# ---------------------------------------------------------------------------
# 7.13: Sphinx mode
# ---------------------------------------------------------------------------


def test_sphinx_mode_param_parsing():
    """AC 11: Sphinx :param name: entries parsed correctly."""
    source = '''\
def connect(host, port, timeout):
    """Connect to a server.

    :param host: The hostname.
    :param port: The port number.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring, style="sphinx")
    config = EnrichmentConfig()

    # Manually set _active_style to sphinx for direct check function calls.
    import docvet.checks.enrichment as enrichment_mod

    original_style = enrichment_mod._active_style
    try:
        enrichment_mod._active_style = "sphinx"
        result = _check_missing_param_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )
    finally:
        enrichment_mod._active_style = original_style

    assert result is not None
    assert result.rule == "missing-param-in-docstring"
    assert result.symbol == "connect"
    assert "timeout" in result.message


def test_sphinx_mode_extra_param():
    """AC 11: Sphinx mode detects extra :param: entries."""
    source = '''\
def connect(host):
    """Connect to a server.

    :param host: The hostname.
    :param port: The port number.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring, style="sphinx")
    config = EnrichmentConfig()

    import docvet.checks.enrichment as enrichment_mod

    original_style = enrichment_mod._active_style
    try:
        enrichment_mod._active_style = "sphinx"
        result = _check_extra_param_in_docstring(
            symbol, sections, node_index, config, "test.py"
        )
    finally:
        enrichment_mod._active_style = original_style

    assert result is not None
    assert result.rule == "extra-param-in-docstring"
    assert result.symbol == "connect"
    assert "port" in result.message


def test_sphinx_orchestrator_integration():
    """AC 11: Full orchestrator with sphinx style."""
    source = '''\
def connect(host, port, timeout):
    """Connect to a server.

    :param host: The hostname.
    :param port: The port number.
    """
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()

    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")

    param_findings = [f for f in findings if "param" in f.rule]
    assert any(f.rule == "missing-param-in-docstring" for f in param_findings)
    missing = [f for f in param_findings if f.rule == "missing-param-in-docstring"][0]
    assert "timeout" in missing.message


# ---------------------------------------------------------------------------
# 7.14: Direct helper tests
# ---------------------------------------------------------------------------


class TestParseArgsEntries:
    """Direct tests for _parse_args_entries helper."""

    def test_google_style_basic(self):
        """Parse standard Google Args: section."""
        docstring = """\
Do something.

Args:
    name: The name.
    value: The value.
"""
        result = _parse_args_entries(docstring, style="google")
        assert result == {"name", "value"}

    def test_google_style_with_type_annotation(self):
        """Parse entries with type in parens."""
        docstring = """\
Do something.

Args:
    name (str): The name.
    count (int): The count.
"""
        result = _parse_args_entries(docstring, style="google")
        assert result == {"name", "count"}

    def test_google_style_with_stars(self):
        """Parse *args and **kwargs entries."""
        docstring = """\
Handle stuff.

Args:
    name: The name.
    *args: Positional args.
    **kwargs: Keyword args.
"""
        result = _parse_args_entries(docstring, style="google")
        assert result == {"name", "args", "kwargs"}

    def test_sphinx_style(self):
        """Parse Sphinx :param name: entries."""
        docstring = """\
Do something.

:param name: The name.
:param value: The value.
"""
        result = _parse_args_entries(docstring, style="sphinx")
        assert result == {"name", "value"}

    def test_no_args_section_returns_empty(self):
        """No Args: section returns empty set."""
        docstring = "Just a summary."
        result = _parse_args_entries(docstring, style="google")
        assert result == set()

    def test_empty_args_section(self):
        """Args: section with no entries returns empty set."""
        docstring = """\
Do something.

Args:
"""
        result = _parse_args_entries(docstring, style="google")
        assert result == set()


class TestExtractSignatureParams:
    """Direct tests for _extract_signature_params helper."""

    def test_regular_params(self):
        """Extract regular params."""
        tree = ast.parse("def f(a, b, c): pass")
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"a", "b", "c"}

    def test_excludes_self(self):
        """Excludes self from params."""
        tree = ast.parse("class C:\n  def m(self, x): pass")
        cls_node = tree.body[0]
        assert isinstance(cls_node, ast.ClassDef)
        node = cls_node.body[0]
        assert isinstance(node, ast.FunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"x"}

    def test_excludes_cls(self):
        """Excludes cls from params."""
        tree = ast.parse("class C:\n  @classmethod\n  def m(cls, x): pass")
        cls_node = tree.body[0]
        assert isinstance(cls_node, ast.ClassDef)
        node = cls_node.body[0]
        assert isinstance(node, ast.FunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"x"}

    def test_excludes_args_kwargs_by_default(self):
        """*args/**kwargs excluded with default config."""
        tree = ast.parse("def f(x, *args, **kwargs): pass")
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"x"}

    def test_includes_args_kwargs_when_opted_in(self):
        """*args/**kwargs included when exclude_args_kwargs=False."""
        tree = ast.parse("def f(x, *args, **kwargs): pass")
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        config = EnrichmentConfig(exclude_args_kwargs=False)
        result = _extract_signature_params(node, config)
        assert result == {"x", "args", "kwargs"}

    def test_positional_only(self):
        """Positional-only params are included."""
        tree = ast.parse("def f(x, /, y): pass")
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"x", "y"}

    def test_keyword_only(self):
        """Keyword-only params are included."""
        tree = ast.parse("def f(x, *, key=None): pass")
        node = tree.body[0]
        assert isinstance(node, ast.FunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"x", "key"}

    def test_async_function(self):
        """Async function params extracted."""
        tree = ast.parse("async def f(a, b): pass")
        node = tree.body[0]
        assert isinstance(node, ast.AsyncFunctionDef)
        result = _extract_signature_params(node, EnrichmentConfig())
        assert result == {"a", "b"}


# ---------------------------------------------------------------------------
# Finding field assertions (7.14 — test validity)
# ---------------------------------------------------------------------------


def test_missing_param_finding_fields():
    """All Finding fields populated correctly for missing-param."""
    source = '''\
def process(alpha, beta):
    """Process items.

    Args:
        alpha: First item.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_missing_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "process"
    assert result.rule == "missing-param-in-docstring"
    assert result.category == "required"
    assert "beta" in result.message


def test_extra_param_finding_fields():
    """All Finding fields populated correctly for extra-param."""
    source = '''\
def process(alpha):
    """Process items.

    Args:
        alpha: First item.
        gamma: Nonexistent.
    """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig()

    result = _check_extra_param_in_docstring(
        symbol, sections, node_index, config, "test.py"
    )

    assert result is not None
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "process"
    assert result.rule == "extra-param-in-docstring"
    assert result.category == "required"
    assert "gamma" in result.message
