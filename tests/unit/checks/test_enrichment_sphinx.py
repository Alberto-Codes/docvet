"""Tests for Sphinx/RST docstring style support in enrichment checks."""

from __future__ import annotations

import ast

import pytest

from docvet.checks.enrichment import (
    _SPHINX_SECTION_MAP,
    _parse_sections,
    check_enrichment,
)
from docvet.config import EnrichmentConfig

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Sphinx section map tests
# ---------------------------------------------------------------------------


def test_sphinx_section_map_param_maps_to_args():
    assert _SPHINX_SECTION_MAP[":param"] == "Args"


def test_sphinx_section_map_type_maps_to_args():
    assert _SPHINX_SECTION_MAP[":type"] == "Args"


def test_sphinx_section_map_returns_maps_to_returns():
    assert _SPHINX_SECTION_MAP[":returns:"] == "Returns"


def test_sphinx_section_map_return_maps_to_returns():
    assert _SPHINX_SECTION_MAP[":return:"] == "Returns"


def test_sphinx_section_map_rtype_maps_to_returns():
    assert _SPHINX_SECTION_MAP[":rtype:"] == "Returns"


def test_sphinx_section_map_raises_maps_to_raises():
    assert _SPHINX_SECTION_MAP[":raises"] == "Raises"


def test_sphinx_section_map_ivar_maps_to_attributes():
    assert _SPHINX_SECTION_MAP[":ivar"] == "Attributes"


def test_sphinx_section_map_cvar_maps_to_attributes():
    assert _SPHINX_SECTION_MAP[":cvar"] == "Attributes"


def test_sphinx_section_map_seealso_maps_to_see_also():
    assert _SPHINX_SECTION_MAP[".. seealso::"] == "See Also"


def test_sphinx_section_map_doctest_maps_to_examples():
    assert _SPHINX_SECTION_MAP[">>>"] == "Examples"


def test_sphinx_section_map_double_colon_maps_to_examples():
    assert _SPHINX_SECTION_MAP["::"] == "Examples"


def test_sphinx_section_map_code_block_maps_to_examples():
    assert _SPHINX_SECTION_MAP[".. code-block::"] == "Examples"


# ---------------------------------------------------------------------------
# _parse_sections sphinx mode tests
# ---------------------------------------------------------------------------


def test_parse_sections_sphinx_param_detected():
    docstring = """\
    Summary line.

    :param name: The name parameter.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Args" in sections


def test_parse_sections_sphinx_type_detected():
    docstring = """\
    Summary line.

    :type name: str
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Args" in sections


def test_parse_sections_sphinx_returns_detected():
    docstring = """\
    Summary line.

    :returns: The result value.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Returns" in sections


def test_parse_sections_sphinx_return_detected():
    docstring = """\
    Summary line.

    :return: The result value.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Returns" in sections


def test_parse_sections_sphinx_rtype_detected():
    docstring = """\
    Summary line.

    :rtype: int
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Returns" in sections


def test_parse_sections_sphinx_raises_detected():
    docstring = """\
    Summary line.

    :raises ValueError: If input is invalid.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Raises" in sections


def test_parse_sections_sphinx_ivar_detected():
    docstring = """\
    Summary line.

    :ivar name: The instance name.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Attributes" in sections


def test_parse_sections_sphinx_cvar_detected():
    docstring = """\
    Summary line.

    :cvar count: The class counter.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Attributes" in sections


def test_parse_sections_sphinx_seealso_detected():
    docstring = """\
    Summary line.

    .. seealso::
       :py:func:`other_func`
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "See Also" in sections


def test_parse_sections_sphinx_doctest_detected():
    docstring = """\
    Summary line.

    >>> print("hello")
    hello
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Examples" in sections


def test_parse_sections_sphinx_double_colon_detected():
    docstring = """\
    Summary line.

    Example usage::

        foo()
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Examples" in sections


def test_parse_sections_sphinx_code_block_detected():
    docstring = """\
    Summary line.

    .. code-block:: python

        foo()
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert "Examples" in sections


def test_parse_sections_sphinx_multiple_sections():
    docstring = """\
    Summary line.

    :param x: The input value.
    :returns: The output value.
    :raises ValueError: If x is invalid.

    >>> print(42)
    42
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert sections == {"Args", "Returns", "Raises", "Examples"}


def test_parse_sections_sphinx_empty_docstring():
    sections = _parse_sections("Summary only.", style="sphinx")
    assert sections == set()


def test_parse_sections_sphinx_no_recognized_patterns():
    docstring = """\
    Summary line.

    This is a description with no RST patterns.
    """
    sections = _parse_sections(docstring, style="sphinx")
    assert sections == set()


# ---------------------------------------------------------------------------
# Google mode unchanged (regression)
# ---------------------------------------------------------------------------


def test_parse_sections_google_mode_unchanged():
    docstring = """\
    Summary line.

    Args:
        x: The input value.

    Returns:
        The output value.
    """
    sections = _parse_sections(docstring, style="google")
    assert sections == {"Args", "Returns"}


def test_parse_sections_default_style_is_google():
    docstring = """\
    Summary line.

    Args:
        x: The input value.
    """
    sections = _parse_sections(docstring)
    assert "Args" in sections


def test_parse_sections_google_mode_ignores_sphinx_patterns():
    docstring = """\
    Summary line.

    :param x: The input value.
    """
    sections = _parse_sections(docstring, style="google")
    assert sections == set()


# ---------------------------------------------------------------------------
# Auto-disable rules in sphinx mode (Task 3)
# ---------------------------------------------------------------------------

_GENERATOR_SOURCE = '''\
def gen():
    """Generate values.

    Yields:
        int: The next value.
    """
    yield 42
'''


def test_check_enrichment_sphinx_auto_disables_yields_rule():
    source = '''\
def gen():
    """Generate values."""
    yield 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")
    assert not any(f.rule == "missing-yields" for f in findings)


def test_check_enrichment_sphinx_auto_disables_receives_rule():
    source = '''\
def gen():
    """Receive values."""
    x = yield
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")
    assert not any(f.rule == "missing-receives" for f in findings)


def test_check_enrichment_sphinx_auto_disables_warns_rule():
    source = '''\
import warnings

def func():
    """Do something."""
    warnings.warn("oops")
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")
    assert not any(f.rule == "missing-warns" for f in findings)


def test_check_enrichment_sphinx_auto_disables_fenced_code_blocks_rule():
    source = '''\
def func():
    """Do something.

    Examples:
        >>> func()
    """
    pass
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    # In sphinx mode, prefer-fenced-code-blocks should be auto-disabled.
    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")
    assert not any(f.rule == "prefer-fenced-code-blocks" for f in findings)


def test_check_enrichment_sphinx_explicit_override_beats_auto_disable():
    source = '''\
def gen():
    """Generate values."""
    yield 42
'''
    tree = ast.parse(source)
    # User explicitly enabled require_yields — should override auto-disable.
    config = EnrichmentConfig(user_set_keys=frozenset({"require_yields"}))
    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")
    assert any(f.rule == "missing-yields" for f in findings)


def test_check_enrichment_google_mode_no_auto_disable():
    source = '''\
def gen():
    """Generate values."""
    yield 42
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "test.py", style="google")
    assert any(f.rule == "missing-yields" for f in findings)


def test_check_enrichment_sphinx_raises_rule_not_auto_disabled():
    source = '''\
def func():
    """Do something."""
    raise ValueError("bad")
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    # require_raises is NOT in auto-disable set, so it should still fire.
    findings = check_enrichment(source, tree, config, "test.py", style="sphinx")
    assert any(f.rule == "missing-raises" for f in findings)


def test_enrichment_config_user_set_keys_default_is_empty():
    config = EnrichmentConfig()
    assert config.user_set_keys == frozenset()


def test_enrichment_config_user_set_keys_populated():
    config = EnrichmentConfig(
        require_yields=False,
        user_set_keys=frozenset({"require_yields"}),
    )
    assert "require_yields" in config.user_set_keys


# ---------------------------------------------------------------------------
# Sphinx cross-reference roles (Task 4, AC5)
# ---------------------------------------------------------------------------


def test_check_enrichment_sphinx_role_satisfies_cross_ref_check():
    source = '''\
"""Module docstring.

Uses :py:class:`SomeClass` for processing.
"""
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "mod.py", style="sphinx")
    assert not any(f.rule == "missing-cross-references" for f in findings)


def test_check_enrichment_sphinx_py_func_role_satisfies_cross_ref():
    source = '''\
"""Module docstring.

See :py:func:`other_func` for details.
"""
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "mod.py", style="sphinx")
    assert not any(f.rule == "missing-cross-references" for f in findings)


def test_check_enrichment_sphinx_no_roles_still_flags_missing_cross_ref():
    source = '''\
"""Module docstring without any cross-references."""
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "mod.py", style="sphinx")
    assert any(f.rule == "missing-cross-references" for f in findings)


def test_check_enrichment_google_mode_backtick_refs_still_work():
    source = '''\
"""Module docstring.

See Also:
    [`other_module`][]: Related module.
"""
'''
    tree = ast.parse(source)
    config = EnrichmentConfig()
    findings = check_enrichment(source, tree, config, "mod.py", style="google")
    assert not any(f.rule == "missing-cross-references" for f in findings)
