"""Tests for the missing-return-type enrichment rule."""

from __future__ import annotations

import ast

import pytest

from docvet.checks import Finding
from docvet.checks.enrichment import (
    _RETURNS_TYPE_PATTERN,
    _build_node_index,
    _check_missing_return_type,
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


# ---------------------------------------------------------------------------
# AC 1: Untyped Returns + no annotation -> finding
# ---------------------------------------------------------------------------


def test_untyped_returns_no_annotation_emits_finding():
    """AC 1: Returns with no type and no -> annotation."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The computed result.
    """
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert isinstance(result, Finding)
    assert result.file == "test.py"
    assert result.line == symbol.line
    assert result.symbol == "compute"
    assert result.rule == "missing-return-type"
    assert result.category == "recommended"
    assert "compute" in result.message
    assert "Returns" in result.message or "return" in result.message


# ---------------------------------------------------------------------------
# AC 2: Typed Returns entry -> no finding
# ---------------------------------------------------------------------------


def test_typed_returns_entry_no_finding():
    """AC 2: Returns with type (e.g., dict: The result.)."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        dict: The computed result mapping.
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 3: Untyped Returns + annotation -> no finding (FR20)
# ---------------------------------------------------------------------------


def test_annotation_satisfies_check_no_finding():
    """AC 3: No type in Returns but -> dict annotation satisfies (FR20)."""
    source = '''\
def compute(x) -> dict:
    """Compute a result.

    Returns:
        The computed result mapping.
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 4: Skip conditions (__init__, __del__, @property, @cached_property)
# ---------------------------------------------------------------------------


def test_init_method_skip_no_finding():
    """AC 4: __init__ excluded from check."""
    source = '''\
class Foo:
    """A class."""

    def __init__(self):
        """Initialize.

        Returns:
            The initialized instance.
        """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_del_method_skip_no_finding():
    """AC 4: __del__ excluded from check."""
    source = '''\
class Foo:
    """A class."""

    def __del__(self):
        """Clean up.

        Returns:
            The cleanup status.
        """
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_property_method_skip_no_finding():
    """AC 4: @property excluded from check."""
    source = '''\
class Foo:
    """A class."""

    @property
    def name(self):
        """The user name.

        Returns:
            The name string.
        """
        return self._name
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_cached_property_skip_no_finding():
    """AC 4: @cached_property excluded from check."""
    source = '''\
import functools

class Foo:
    """A class."""

    @functools.cached_property
    def total(self):
        """The total count.

        Returns:
            The computed total.
        """
        return sum(self._items)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# AC 5 & 6: Config gating
# ---------------------------------------------------------------------------


def test_config_enabled_emits_finding():
    """AC 5: require_return_type=True activates the rule."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The computed result.
    """
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-return-type"


def test_config_default_false_skips_via_dispatch():
    """AC 6: Default require_return_type=False means dispatch skips rule."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The computed result.
    """
    return x * 2
'''
    config = EnrichmentConfig()
    assert config.require_return_type is False

    tree = ast.parse(source)
    findings = check_enrichment(source, tree, config, "test.py")

    assert not any(f.rule == "missing-return-type" for f in findings)


# ---------------------------------------------------------------------------
# AC 7: _RETURNS_TYPE_PATTERN regex tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("    dict: The result.", True),
        ("    list[str]: The items.", True),
        ("    str | None: The name.", True),
        ("    Optional[int]: The count.", True),
        ("    None: Always returns None.", True),
        ("    Callable[[int], str]: The transformer.", True),
        ("    tuple[str, ...]: The items.", True),
        ("    _PrivateType: Internal result.", True),
        ("    The result mapping.", False),
        ("    A list of items.", False),
        ("    123: not a type.", False),
    ],
    ids=[
        "dict",
        "list_generic",
        "union_pipe",
        "optional",
        "none_type",
        "callable",
        "tuple_ellipsis",
        "private_type",
        "untyped_description",
        "article_start",
        "digit_start",
    ],
)
def test_returns_type_pattern(line: str, expected: bool):
    """AC 7: Regex matches typed entries and rejects descriptions."""
    assert bool(_RETURNS_TYPE_PATTERN.match(line)) is expected


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_no_returns_section_no_finding():
    """Function without Returns section -> not applicable."""
    source = '''\
def greet(name):
    """Greet the user.

    Args:
        name: The user name.
    """
    print(f"Hello {name}")
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_async_function_untyped_returns_emits_finding():
    """Async function with untyped Returns and no annotation -> finding."""
    source = '''\
async def fetch(url):
    """Fetch data from URL.

    Returns:
        The response data.
    """
    return await get(url)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-return-type"


def test_class_symbol_no_finding():
    """Class symbol -> rule only applies to functions/methods."""
    source = '''\
class Foo:
    """A class.

    Returns:
        Something unusual in a class docstring.
    """
'''
    from docvet.ast_utils import get_documented_symbols

    tree = ast.parse(source)
    symbols = get_documented_symbols(tree)
    node_index = _build_node_index(tree)
    class_symbols = [s for s in symbols if s.kind == "class"]
    symbol = class_symbols[0]
    assert symbol.docstring is not None
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_complex_annotation_satisfies_check():
    """Complex return type annotation -> dict[str, list[int]] satisfies."""
    source = '''\
def compute(x) -> dict[str, list[int]]:
    """Compute a result.

    Returns:
        The computed result mapping.
    """
    return {"result": [x * 2]}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# Sphinx-style tests
# ---------------------------------------------------------------------------


def test_sphinx_rtype_satisfies_check():
    """AC 17: Sphinx :rtype: presence satisfies check."""
    source = '''\
def compute(x):
    """Compute a result.

    :returns: The computed result.
    :rtype: dict
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring, style="sphinx")
    config = EnrichmentConfig(require_return_type=True)

    # Simulate sphinx mode by setting the module variable
    import docvet.checks.enrichment as enr

    old_style = enr._active_style
    enr._active_style = "sphinx"
    try:
        result = _check_missing_return_type(
            symbol, sections, node_index, config, "test.py"
        )
    finally:
        enr._active_style = old_style

    assert result is None


def test_sphinx_returns_without_rtype_emits_finding():
    """AC 18: Sphinx :returns: without :rtype: and no annotation -> finding."""
    source = '''\
def compute(x):
    """Compute a result.

    :returns: The computed result.
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring, style="sphinx")
    config = EnrichmentConfig(require_return_type=True)

    import docvet.checks.enrichment as enr

    old_style = enr._active_style
    enr._active_style = "sphinx"
    try:
        result = _check_missing_return_type(
            symbol, sections, node_index, config, "test.py"
        )
    finally:
        enr._active_style = old_style

    assert result is not None
    assert result.rule == "missing-return-type"


# ---------------------------------------------------------------------------
# Party-mode consensus edge cases (Q2, Q5, Q6)
# ---------------------------------------------------------------------------


def test_numpy_returns_section_no_finding():
    """Q2: NumPy underline format -> no finding (can't parse, don't FP)."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns
    -------
    result : dict
        The computed result mapping.
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_none_typed_entry_no_finding():
    """Q5: None: is a valid typed entry."""
    source = '''\
def reset():
    """Reset the state.

    Returns:
        None: Always returns None after reset.
    """
    return None
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_none_annotation_satisfies_check():
    """Q5: -> None annotation satisfies FR20."""
    source = '''\
def reset() -> None:
    """Reset the state.

    Returns:
        Nothing meaningful after reset.
    """
    return None
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_multiline_untyped_description_emits_finding():
    """Q6-A: Multi-line description with no type on first line -> finding."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The result mapping containing
        user data and metadata.
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is not None
    assert result.rule == "missing-return-type"


def test_empty_line_before_typed_entry_no_finding():
    """Q6-B: Blank line then typed entry -> first non-empty line has type."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:

        dict: The computed result mapping.
    """
    return {"result": x * 2}
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_multiple_typed_entries_first_typed_no_finding():
    """Q6-C: Multiple Returns entries, first typed -> no finding."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        str: The name.
        int: The age.
    """
    return "Alice", 30
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


def test_empty_returns_section_no_finding():
    """Q6-D: Returns section with only whitespace -> no finding (safe)."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
    """
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    assert result is None


# ---------------------------------------------------------------------------
# Assertion strength (AC 26)
# ---------------------------------------------------------------------------


def test_all_finding_fields_populated():
    """Verify all 6 Finding fields on primary finding test."""
    source = '''\
def fetch(url):
    """Fetch data.

    Returns:
        The response data from the server.
    """
    return get(url)
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "api.py")

    assert result is not None
    assert result.file == "api.py"
    assert result.line == symbol.line
    assert result.symbol == "fetch"
    assert result.rule == "missing-return-type"
    assert result.category == "recommended"
    assert "fetch" in result.message


# ---------------------------------------------------------------------------
# Cross-rule interaction (AC 27)
# ---------------------------------------------------------------------------


def test_missing_returns_does_not_trigger_missing_return_type():
    """Mutual exclusion: no Returns section -> only missing-returns fires."""
    source = '''\
def compute(x):
    """Compute a result."""
    return x * 2
'''
    symbol, node_index, _ = _make_symbol_and_index(source)
    sections = _parse_sections(symbol.docstring)
    config = EnrichmentConfig(require_return_type=True)

    result = _check_missing_return_type(symbol, sections, node_index, config, "test.py")

    # missing-return-type should NOT fire when there's no Returns section
    assert result is None


# ---------------------------------------------------------------------------
# Integration test (AC 28)
# ---------------------------------------------------------------------------


def test_dispatch_wiring_via_check_enrichment():
    """Integration: check_enrichment with require_return_type=True."""
    source = '''\
def compute(x):
    """Compute a result.

    Returns:
        The computed result.
    """
    return x * 2
'''
    config = EnrichmentConfig(require_return_type=True)
    tree = ast.parse(source)

    findings = check_enrichment(source, tree, config, "test.py")

    return_type_findings = [f for f in findings if f.rule == "missing-return-type"]
    assert len(return_type_findings) == 1
    assert return_type_findings[0].symbol == "compute"
