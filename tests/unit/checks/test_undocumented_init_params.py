"""Tests for the undocumented-init-params enrichment rule."""

from __future__ import annotations

import ast
import textwrap

import pytest

from docvet.checks.enrichment import (
    _build_node_index,
    _check_undocumented_init_params,
    _parse_sections,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_class_symbol_and_index(source: str):
    """Build a class symbol + node_index from inline source.

    Returns the first class symbol, its parsed sections, and the
    node_index.
    """
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(textwrap.dedent(source))
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbols = [s for s in symbols if s.kind == "class"]
    assert class_symbols, "No class symbol found in source"
    symbol = class_symbols[0]
    assert symbol.docstring is not None
    sections = _parse_sections(symbol.docstring)
    return symbol, sections, node_index


# ---------------------------------------------------------------------------
# AC 1: Undocumented params -> finding
# ---------------------------------------------------------------------------


def test_undocumented_init_params_emits_finding():
    """AC 1: Class with __init__ params and no Args section anywhere."""
    source = '''\
    class Server:
        """A network server."""

        def __init__(self, host, port):
            self.host = host
            self.port = port
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "server.py"
    )
    assert finding is not None
    assert finding.file == "server.py"
    assert finding.line == symbol.line
    assert finding.symbol == "Server"
    assert finding.rule == "undocumented-init-params"
    assert "host" in finding.message
    assert "port" in finding.message
    assert finding.category == "required"


# ---------------------------------------------------------------------------
# AC 2: Class docstring has Args -> no finding
# ---------------------------------------------------------------------------


def test_class_docstring_has_args_no_finding():
    """AC 2: Args section in class docstring satisfies check (FR24)."""
    source = '''\
    class Server:
        """A network server.

        Args:
            host: The hostname.
            port: The port number.
        """

        def __init__(self, host, port):
            self.host = host
            self.port = port
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "server.py"
    )
    assert finding is None


# ---------------------------------------------------------------------------
# AC 3: __init__ docstring has Args -> no finding
# ---------------------------------------------------------------------------


def test_init_docstring_has_args_no_finding():
    """AC 3: Args section in __init__ docstring satisfies check (FR24)."""
    source = '''\
    class Server:
        """A network server."""

        def __init__(self, host, port):
            """Initialize the server.

            Args:
                host: The hostname.
                port: The port number.
            """
            self.host = host
            self.port = port
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "server.py"
    )
    assert finding is None


# ---------------------------------------------------------------------------
# AC 4: No params beyond self -> no finding
# ---------------------------------------------------------------------------


def test_no_params_beyond_self_no_finding():
    """AC 4: __init__(self) with no extra params produces no finding."""
    source = '''\
    class Singleton:
        """A singleton pattern."""

        def __init__(self):
            self.value = 42
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "singleton.py"
    )
    assert finding is None


# ---------------------------------------------------------------------------
# AC 5: No __init__ defined -> no finding
# ---------------------------------------------------------------------------


def test_no_init_method_no_finding():
    """AC 5: Class with no __init__ produces no finding."""
    source = '''\
    class Empty:
        """An empty class."""

        pass
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "empty.py"
    )
    assert finding is None


@pytest.mark.parametrize(
    "decorator, base",
    [
        ("@dataclass", ""),
        ("", "(NamedTuple)"),
        ("", "(TypedDict)"),
    ],
    ids=["dataclass", "namedtuple", "typeddict"],
)
def test_structural_types_no_init_no_finding(decorator, base):
    """AC 5 variant: Structural types without explicit __init__ are skipped.

    Auto-generated __init__ is not in the source AST, so
    _find_init_method returns None.
    """
    imports = ""
    if decorator == "@dataclass":
        imports = "from dataclasses import dataclass\n"
    elif base == "(NamedTuple)":
        imports = "from typing import NamedTuple\n"
    elif base == "(TypedDict)":
        imports = "from typing import TypedDict\n"

    source = f"""\
{imports}{decorator}
class MyType{base}:
    \"\"\"A structural type.\"\"\"

    x: int
    y: str
"""
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(textwrap.dedent(source))
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbols = [s for s in symbols if s.kind == "class"]
    assert class_symbols, f"No class symbol for {decorator or base}"
    symbol = class_symbols[0]
    if symbol.docstring is None:
        return  # No docstring -> rule won't fire anyway
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "types.py"
    )
    assert finding is None


# ---------------------------------------------------------------------------
# AC 6: Only *args/**kwargs with exclude -> no finding
# ---------------------------------------------------------------------------


def test_only_args_kwargs_excluded_no_finding():
    """AC 6: __init__(self, *args, **kwargs) with exclude produces no finding."""
    source = '''\
    class Proxy:
        """A pass-through proxy."""

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True, exclude_args_kwargs=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "proxy.py"
    )
    assert finding is None


def test_args_kwargs_not_excluded_emits_finding():
    """AC 6 inverse: *args/**kwargs included when exclude disabled."""
    source = '''\
    class Proxy:
        """A pass-through proxy."""

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True, exclude_args_kwargs=False)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "proxy.py"
    )
    assert finding is not None
    assert "*args" in finding.message
    assert "**kwargs" in finding.message


# ---------------------------------------------------------------------------
# AC 7: Config disabled -> skipped
# ---------------------------------------------------------------------------


def test_config_default_false_skips_via_dispatch():
    """AC 7: Default require_init_params=False skips the rule in dispatch."""
    source = '''\
    class Server:
        """A server."""

        def __init__(self, host):
            self.host = host
    '''
    tree = ast.parse(textwrap.dedent(source))
    config = EnrichmentConfig()  # Default: require_init_params=False
    findings = check_enrichment(source, tree, config, "server.py")
    init_findings = [f for f in findings if f.rule == "undocumented-init-params"]
    assert len(init_findings) == 0


# ---------------------------------------------------------------------------
# AC 9: Sphinx :param satisfies check
# ---------------------------------------------------------------------------


def test_sphinx_param_in_class_docstring_no_finding():
    """AC 9: Sphinx :param directives map to Args via _SPHINX_SECTION_MAP."""
    source = '''\
    class Server:
        """:param host: The hostname.
        :param port: The port number.
        """

        def __init__(self, host, port):
            self.host = host
            self.port = port
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    # Sphinx mode: _parse_sections maps :param -> "Args"
    sphinx_sections = _parse_sections(symbol.docstring, style="sphinx")
    config = EnrichmentConfig(require_init_params=True)
    # We need to simulate sphinx mode for _active_style
    import docvet.checks.enrichment as _mod

    old_style = _mod._active_style
    _mod._active_style = "sphinx"
    try:
        finding = _check_undocumented_init_params(
            symbol, sphinx_sections, node_index, config, "server.py"
        )
    finally:
        _mod._active_style = old_style
    assert finding is None


def test_sphinx_param_in_init_docstring_no_finding():
    """AC 9 variant: Sphinx :param in __init__ docstring satisfies check."""
    source = '''\
    class Server:
        """A network server."""

        def __init__(self, host, port):
            """:param host: The hostname.
            :param port: The port number.
            """
            self.host = host
            self.port = port
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    import docvet.checks.enrichment as _mod

    old_style = _mod._active_style
    _mod._active_style = "sphinx"
    try:
        finding = _check_undocumented_init_params(
            symbol, sections, node_index, config, "server.py"
        )
    finally:
        _mod._active_style = old_style
    assert finding is None


# ---------------------------------------------------------------------------
# Edge cases & guard clauses
# ---------------------------------------------------------------------------


def test_non_class_symbol_no_finding():
    """Guard: function symbol is not a class, rule skips."""
    source = '''\
    def helper(x):
        """A helper function.

        Args:
            x: The input.
        """
        return x
    '''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(textwrap.dedent(source))
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    func_symbols = [s for s in symbols if s.kind == "function"]
    assert func_symbols
    symbol = func_symbols[0]
    assert symbol.docstring is not None
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "helper.py"
    )
    assert finding is None


def test_mixed_regular_and_args_kwargs_finding():
    """Mixed regular + *args with exclude: finding for regular params only."""
    source = '''\
    class Handler:
        """A handler."""

        def __init__(self, name, *args, **kwargs):
            self.name = name
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True, exclude_args_kwargs=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "handler.py"
    )
    assert finding is not None
    assert "name" in finding.message
    assert "*args" not in finding.message
    assert "**kwargs" not in finding.message


def test_kwonly_params_emits_finding():
    """Keyword-only params after * are detected."""
    source = '''\
    class Config:
        """A config object."""

        def __init__(self, *, debug, verbose):
            self.debug = debug
            self.verbose = verbose
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "config.py"
    )
    assert finding is not None
    assert "debug" in finding.message
    assert "verbose" in finding.message


def test_posonly_params_emits_finding():
    """Positional-only params (before /) are detected."""
    source = '''\
    class Coord:
        """A coordinate."""

        def __init__(self, x, y, /):
            self.x = x
            self.y = y
    '''
    symbol, sections, node_index = _make_class_symbol_and_index(source)
    config = EnrichmentConfig(require_init_params=True)
    finding = _check_undocumented_init_params(
        symbol, sections, node_index, config, "coord.py"
    )
    assert finding is not None
    assert "x" in finding.message
    assert "y" in finding.message


# ---------------------------------------------------------------------------
# Cross-rule non-interference
# ---------------------------------------------------------------------------


def test_cross_rule_no_interference():
    """Enabling require_init_params alongside other rules doesn't conflict.

    Verifies that undocumented-init-params findings are distinct from
    missing-attributes and missing-param-in-docstring findings.
    """
    source = '''\
    class Server:
        """A server."""

        def __init__(self, host, port):
            self.host = host
            self.port = port
    '''
    tree = ast.parse(textwrap.dedent(source))
    config = EnrichmentConfig(
        require_init_params=True,
        require_param_agreement=True,
        require_attributes=True,
    )
    findings = check_enrichment(source, tree, config, "server.py")
    init_findings = [f for f in findings if f.rule == "undocumented-init-params"]
    assert len(init_findings) == 1
    # Other rules may also fire (missing-attributes), but no duplication
    # with undocumented-init-params.
    rules = [f.rule for f in findings]
    assert rules.count("undocumented-init-params") == 1


def test_args_section_present_no_init_finding():
    """When class has Args section, undocumented-init-params doesn't fire.

    missing-param-in-docstring may fire for individual params, but that's
    a separate rule.
    """
    source = '''\
    class Server:
        """A server.

        Args:
            host: The hostname.
        """

        def __init__(self, host, port):
            self.host = host
            self.port = port
    '''
    tree = ast.parse(textwrap.dedent(source))
    config = EnrichmentConfig(
        require_init_params=True,
        require_param_agreement=True,
    )
    findings = check_enrichment(source, tree, config, "server.py")
    init_findings = [f for f in findings if f.rule == "undocumented-init-params"]
    assert len(init_findings) == 0
