"""Tests for presence scoping of definitions nested inside functions.

Functions and classes whose ancestor chain contains a function (closures,
local helpers, local classes and their methods) are unreachable by import,
so check_presence excludes them from findings and coverage statistics.
Methods and classes nested only inside classes stay checked.
"""

from __future__ import annotations

import pytest

from docvet.checks import Finding
from docvet.checks.presence import PresenceStats, check_presence
from docvet.config import PresenceConfig

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Issue 456: Symbols nested inside a function scope are skipped
# ---------------------------------------------------------------------------


class TestCheckPresenceFunctionScopedSymbols:
    """Tests that defs/classes inside a function body are not checked."""

    def test_documented_outer_function_with_undocumented_closure(self) -> None:
        source = '''\
"""Module docstring."""


def timeline(card: str, as_json: bool) -> None:
    """Show a card timeline."""
    card_id = card

    def read(reader: object) -> list[dict[str, object]]:
        return [card_id]

    print(read, as_json)
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == []
        assert stats == PresenceStats(documented=2, total=2)

    def test_decorated_nested_def_and_local_class_skipped(self) -> None:
        source = '''\
"""Module docstring."""

import functools


def command(fn):
    """Register a command."""
    return fn


@command
def timeline(card):
    """Show a card timeline."""

    @functools.lru_cache
    def read(reader):
        return reader

    @command
    class Reader:
        def fetch(self):
            pass

    return read(card), Reader
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == []
        assert stats == PresenceStats(documented=3, total=3)

    def test_undocumented_outer_function_still_reported(self) -> None:
        source = '''\
"""Module docstring."""


def timeline(card):
    def read(reader):
        return reader

    return read(card)
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert len(findings) == 1
        assert findings[0] == Finding(
            file="a.py",
            line=4,
            symbol="timeline",
            rule="missing-docstring",
            message="Public function has no docstring",
            category="required",
        )
        assert stats == PresenceStats(documented=1, total=2)

    def test_async_outer_function_nested_def_skipped(self) -> None:
        source = '''\
"""Module docstring."""


async def outer():
    """Outer docstring."""

    async def inner_async():
        pass

    def inner_sync():
        pass
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == []
        assert stats == PresenceStats(documented=2, total=2)

    def test_class_nested_in_function_and_its_methods_skipped(self) -> None:
        source = '''\
"""Module docstring."""


def factory():
    """Build a local class."""

    class Local:
        def method(self):
            pass

        class Deeper:
            def deeper_method(self):
                pass

    return Local
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == []
        assert stats == PresenceStats(documented=2, total=2)

    def test_function_nested_in_method_skipped(self) -> None:
        source = '''\
"""Module docstring."""


class Service:
    """Service docstring."""

    def run(self):
        """Run the service."""

        def helper():
            pass

        return helper
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == []
        assert stats == PresenceStats(documented=3, total=3)

    def test_class_members_outside_functions_still_reported(self) -> None:
        source = '''\
"""Module docstring."""


class Outer:
    """Outer docstring."""

    def method(self):
        pass

    class Inner:
        def inner_method(self):
            pass
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert len(findings) == 3
        assert findings == [
            Finding(
                file="a.py",
                line=7,
                symbol="method",
                rule="missing-docstring",
                message="Public method has no docstring",
                category="required",
            ),
            Finding(
                file="a.py",
                line=10,
                symbol="Inner",
                rule="missing-docstring",
                message="Public class has no docstring",
                category="required",
            ),
            Finding(
                file="a.py",
                line=11,
                symbol="inner_method",
                rule="missing-docstring",
                message="Public method has no docstring",
                category="required",
            ),
        ]
        assert stats == PresenceStats(documented=2, total=5)

    def test_skipped_closures_excluded_from_denominator(self) -> None:
        source = '''\
"""Module docstring."""


def outer():
    def first():
        pass

    def second():
        pass
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == [
            Finding(
                file="a.py",
                line=4,
                symbol="outer",
                rule="missing-docstring",
                message="Public function has no docstring",
                category="required",
            )
        ]
        assert stats == PresenceStats(documented=1, total=2)
        assert stats.percentage == 50.0


# ---------------------------------------------------------------------------
# Issue 456: Overload stubs nested inside a function
# ---------------------------------------------------------------------------


_NESTED_OVERLOAD_SOURCE = '''\
"""Module docstring."""

from typing import overload


def outer():
    """Outer docstring."""

    @overload
    def parse(x: int) -> int:
        """Misplaced overload docstring."""

    @overload
    def parse(x: str) -> str: ...

    def parse(x):
        return x

    return parse
'''


class TestCheckPresenceNestedOverload:
    """Tests that nested overload stubs are skipped without hiding misplacement."""

    def test_nested_overload_flagged_when_check_enabled(self) -> None:
        findings, stats = check_presence(
            _NESTED_OVERLOAD_SOURCE, "a.py", PresenceConfig()
        )

        assert findings == [
            Finding(
                file="a.py",
                line=10,
                symbol="parse",
                rule="overload-has-docstring",
                message=(
                    "Overloaded function 'parse' should not have a docstring "
                    "— document the implementation instead"
                ),
                category="required",
            )
        ]
        assert stats == PresenceStats(documented=2, total=2)

    def test_nested_overload_skipped_when_check_disabled(self) -> None:
        findings, stats = check_presence(
            _NESTED_OVERLOAD_SOURCE,
            "a.py",
            PresenceConfig(check_overload_docstrings=False),
        )

        assert findings == []
        assert stats == PresenceStats(documented=2, total=2)
