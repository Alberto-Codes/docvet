"""Tests for the presence check module.

Tests check_presence detection of public symbols missing docstrings,
filtering logic for private/magic/init symbols, and per-file coverage
statistics.
"""

from __future__ import annotations

import pytest

from docvet.checks import Finding
from docvet.checks.presence import check_presence
from docvet.config import PresenceConfig

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# AC 1: Mixed documented/undocumented symbols
# ---------------------------------------------------------------------------


class TestCheckPresenceMixedSymbols:
    """Tests for mixed documented/undocumented detection (AC 1)."""

    def test_returns_finding_for_each_undocumented_symbol(self) -> None:
        source = '''\
"""Module docstring."""


def documented():
    """Has a docstring."""


def undocumented():
    pass


class Documented:
    """Has a docstring."""


class Undocumented:
    pass
'''
        findings, stats = check_presence(source, "app.py", PresenceConfig())

        assert len(findings) == 2
        rules = {f.symbol for f in findings}
        assert rules == {"undocumented", "Undocumented"}

    def test_finding_includes_file_line_symbol_rule_message(self) -> None:
        source = '''\
"""Module docstring."""


def missing():
    pass
'''
        findings, _ = check_presence(source, "app.py", PresenceConfig())

        assert len(findings) == 1
        f = findings[0]
        assert f.file == "app.py"
        assert f.line >= 1
        assert f.symbol == "missing"
        assert f.rule == "missing-docstring"
        assert f.message == "Public function has no docstring"
        assert f.category == "required"


# ---------------------------------------------------------------------------
# AC 2: Module-level missing docstring
# ---------------------------------------------------------------------------


class TestCheckPresenceModuleMissing:
    """Tests for module-level missing docstring (AC 2)."""

    def test_missing_module_docstring_returns_finding(self) -> None:
        source = """\
import os

def foo():
    \"\"\"Has one.\"\"\"
"""
        findings, _ = check_presence(source, "mod.py", PresenceConfig())

        module_findings = [f for f in findings if f.symbol == "mod"]
        assert len(module_findings) == 1
        assert module_findings[0].message == "Module 'mod' has no docstring"
        assert module_findings[0].line == 1

    def test_present_module_docstring_no_finding(self) -> None:
        source = '''\
"""Module docstring."""

import os
'''
        findings, _ = check_presence(source, "mod.py", PresenceConfig())

        module_findings = [f for f in findings if f.symbol == "mod"]
        assert module_findings == []


# ---------------------------------------------------------------------------
# AC 3: Class missing docstring
# ---------------------------------------------------------------------------


class TestCheckPresenceClassMissing:
    """Tests for class missing docstring (AC 3)."""

    def test_class_without_docstring_returns_finding(self) -> None:
        source = '''\
"""Module docstring."""


class NoDoc:
    pass
'''
        findings, _ = check_presence(source, "cls.py", PresenceConfig())

        assert len(findings) == 1
        assert findings[0].symbol == "NoDoc"
        assert findings[0].message == "Public class has no docstring"

    def test_class_with_docstring_no_finding(self) -> None:
        source = '''\
"""Module docstring."""


class WithDoc:
    """Has a docstring."""
'''
        findings, _ = check_presence(source, "cls.py", PresenceConfig())

        assert findings == []


# ---------------------------------------------------------------------------
# AC 4 & 5: ignore_init
# ---------------------------------------------------------------------------


class TestCheckPresenceIgnoreInit:
    """Tests for ignore_init config (AC 4, 5)."""

    def test_ignore_init_true_skips_init(self) -> None:
        source = '''\
"""Module docstring."""


class Foo:
    """Class doc."""

    def __init__(self):
        pass
'''
        config = PresenceConfig(ignore_init=True)
        findings, _ = check_presence(source, "a.py", config)

        assert findings == []

    def test_ignore_init_false_reports_init(self) -> None:
        source = '''\
"""Module docstring."""


class Foo:
    """Class doc."""

    def __init__(self):
        pass
'''
        config = PresenceConfig(ignore_init=False)
        findings, _ = check_presence(source, "a.py", config)

        assert len(findings) == 1
        assert findings[0].symbol == "__init__"
        assert findings[0].message == "Public method has no docstring"


# ---------------------------------------------------------------------------
# AC 6: ignore_magic
# ---------------------------------------------------------------------------


class TestCheckPresenceIgnoreMagic:
    """Tests for ignore_magic config (AC 6)."""

    def test_ignore_magic_true_skips_repr_and_str(self) -> None:
        source = '''\
"""Module docstring."""


class Foo:
    """Class doc."""

    def __repr__(self):
        return "Foo"

    def __str__(self):
        return "Foo"
'''
        config = PresenceConfig(ignore_magic=True)
        findings, _ = check_presence(source, "a.py", config)

        assert findings == []

    def test_ignore_magic_false_reports_repr_and_str(self) -> None:
        source = '''\
"""Module docstring."""


class Foo:
    """Class doc."""

    def __repr__(self):
        return "Foo"

    def __str__(self):
        return "Foo"
'''
        config = PresenceConfig(ignore_magic=False)
        findings, _ = check_presence(source, "a.py", config)

        assert len(findings) == 2
        symbols = {f.symbol for f in findings}
        assert symbols == {"__repr__", "__str__"}


# ---------------------------------------------------------------------------
# AC 7: ignore_private
# ---------------------------------------------------------------------------


class TestCheckPresenceIgnorePrivate:
    """Tests for ignore_private config (AC 7)."""

    def test_ignore_private_true_skips_private_function(self) -> None:
        source = '''\
"""Module docstring."""


def _helper():
    pass
'''
        config = PresenceConfig(ignore_private=True)
        findings, _ = check_presence(source, "a.py", config)

        assert findings == []

    def test_ignore_private_false_reports_private_function(self) -> None:
        source = '''\
"""Module docstring."""


def _helper():
    pass
'''
        config = PresenceConfig(ignore_private=False)
        findings, _ = check_presence(source, "a.py", config)

        assert len(findings) == 1
        assert findings[0].symbol == "_helper"


# ---------------------------------------------------------------------------
# AC 8: Nested symbols
# ---------------------------------------------------------------------------


class TestCheckPresenceNestedSymbols:
    """Tests for nested symbol detection (AC 8)."""

    def test_nested_method_inside_class_independently_reported(self) -> None:
        source = '''\
"""Module docstring."""


class Outer:
    """Outer docstring."""

    def method_one(self):
        pass

    def method_two(self):
        pass
'''
        findings, _ = check_presence(source, "a.py", PresenceConfig())

        assert len(findings) == 2
        symbols = {f.symbol for f in findings}
        assert symbols == {"method_one", "method_two"}

    def test_documented_method_not_reported(self) -> None:
        source = '''\
"""Module docstring."""


class Outer:
    """Outer docstring."""

    def documented(self):
        """Has docstring."""

    def undocumented(self):
        pass
'''
        findings, _ = check_presence(source, "a.py", PresenceConfig())

        assert len(findings) == 1
        assert findings[0].symbol == "undocumented"


# ---------------------------------------------------------------------------
# AC 9: Per-file stats
# ---------------------------------------------------------------------------


class TestCheckPresencePerFileStats:
    """Tests for per-file statistics (AC 9)."""

    def test_stats_reflect_documented_and_total(self) -> None:
        source = '''\
"""Module docstring."""


def one():
    """Doc."""


def two():
    """Doc."""


def three():
    pass


class Four:
    """Doc."""


class Five:
    pass


def six():
    """Doc."""


def seven():
    """Doc."""


def eight():
    """Doc."""
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        # module(d) + one(d) + two(d) + three(u) + four(d) + five(u) + six(d) + seven(d) + eight(d)
        assert stats.total == 9
        assert stats.documented == 7
        assert len(findings) == 2

    def test_stats_invariant_documented_plus_findings_equals_total(self) -> None:
        source = '''\
"""Module docstring."""


def a():
    pass


def b():
    """Doc."""


def c():
    pass
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert stats.documented + len(findings) == stats.total


# ---------------------------------------------------------------------------
# AC 10: All documented
# ---------------------------------------------------------------------------


class TestCheckPresenceAllDocumented:
    """Tests for all-documented case (AC 10)."""

    def test_all_documented_returns_zero_findings(self) -> None:
        source = '''\
"""Module docstring."""


def foo():
    """Foo doc."""


class Bar:
    """Bar doc."""
'''
        findings, stats = check_presence(source, "a.py", PresenceConfig())

        assert findings == []
        assert stats.documented == stats.total
        assert stats.total == 3


# ---------------------------------------------------------------------------
# AC 11: Empty file / imports only
# ---------------------------------------------------------------------------


class TestCheckPresenceEmptyFile:
    """Tests for empty file and import-only file (AC 11)."""

    def test_empty_file_returns_zero_findings(self) -> None:
        source = ""
        findings, stats = check_presence(source, "empty.py", PresenceConfig())

        assert findings == []
        assert stats.documented == 0
        assert stats.total == 0

    def test_imports_only_file_returns_module_finding(self) -> None:
        source = """\
import os
import sys
"""
        findings, stats = check_presence(source, "imports.py", PresenceConfig())

        # Module symbol exists but has no docstring
        module_findings = [f for f in findings if f.symbol == "imports"]
        assert len(module_findings) == 1
        assert module_findings[0].message == "Module 'imports' has no docstring"
        assert stats.total == 1
        assert stats.documented == 0


# ---------------------------------------------------------------------------
# AC 12: SyntaxError handling
# ---------------------------------------------------------------------------


class TestCheckPresenceSyntaxError:
    """Tests for SyntaxError handling (AC 12)."""

    def test_syntax_error_returns_empty_findings_and_zero_stats(self) -> None:
        source = "def broken(:\n    pass"
        findings, stats = check_presence(source, "bad.py", PresenceConfig())

        assert findings == []
        assert stats.documented == 0
        assert stats.total == 0


# ---------------------------------------------------------------------------
# Finding fields verification
# ---------------------------------------------------------------------------


class TestCheckPresenceFindingFields:
    """Tests for all 6 Finding fields (comprehensive verification)."""

    def test_finding_has_all_correct_fields(self) -> None:
        source = '''\
"""Module docstring."""


def target():
    pass
'''
        findings, _ = check_presence(source, "app.py", PresenceConfig())

        assert len(findings) == 1
        f = findings[0]
        assert isinstance(f, Finding)
        assert f.file == "app.py"
        assert f.line == 4
        assert f.symbol == "target"
        assert f.rule == "missing-docstring"
        assert f.message == "Public function has no docstring"
        assert f.category == "required"

    def test_class_finding_message_format(self) -> None:
        source = '''\
"""Module docstring."""


class Target:
    pass
'''
        findings, _ = check_presence(source, "app.py", PresenceConfig())

        assert len(findings) == 1
        assert findings[0].message == "Public class has no docstring"

    def test_method_finding_message_format(self) -> None:
        source = '''\
"""Module docstring."""


class Foo:
    """Doc."""

    def target(self):
        pass
'''
        findings, _ = check_presence(source, "app.py", PresenceConfig())

        assert len(findings) == 1
        assert findings[0].message == "Public method has no docstring"

    def test_module_finding_message_format(self) -> None:
        source = "x = 1\n"
        findings, _ = check_presence(source, "app.py", PresenceConfig())

        module_findings = [f for f in findings if f.symbol == "app"]
        assert len(module_findings) == 1
        assert module_findings[0].message == "Module 'app' has no docstring"


# ---------------------------------------------------------------------------
# Edge cases (dev-quality-checklist: proactive boundary tests)
# ---------------------------------------------------------------------------


class TestCheckPresenceEdgeCases:
    """Edge case tests for _should_skip boundary conditions."""

    def test_single_underscore_init_not_treated_as_magic(self) -> None:
        """__init without trailing __ is private, not magic or init."""
        source = '''\
"""Module docstring."""


def __init():
    pass
'''
        # ignore_private=True, ignore_magic=True, ignore_init=True
        config = PresenceConfig()
        findings, _ = check_presence(source, "a.py", config)

        # __init starts with _ so it's private → skipped by ignore_private
        assert findings == []

    def test_triple_underscore_is_private(self) -> None:
        """___triple is private (starts with _), not magic."""
        source = '''\
"""Module docstring."""


def ___triple():
    pass
'''
        config = PresenceConfig(ignore_private=True)
        findings, _ = check_presence(source, "a.py", config)

        assert findings == []

    def test_public_method_inside_private_class_still_checked(self) -> None:
        """Parent visibility doesn't gate child checking."""
        source = '''\
"""Module docstring."""


class _Private:
    """Private class doc."""

    def public_method(self):
        pass
'''
        config = PresenceConfig(ignore_private=True)
        findings, _ = check_presence(source, "a.py", config)

        # _Private is skipped (private), but public_method is checked
        assert len(findings) == 1
        assert findings[0].symbol == "public_method"

    def test_file_with_shebang_line_and_no_docstring(self) -> None:
        """Module with shebang but no docstring."""
        source = """\
#!/usr/bin/env python
import os
"""
        findings, _ = check_presence(source, "script.py", PresenceConfig())

        module_findings = [f for f in findings if f.symbol == "script"]
        assert len(module_findings) == 1

    def test_file_with_coding_pragma_and_no_docstring(self) -> None:
        """Module with coding pragma but no docstring."""
        source = """\
# -*- coding: utf-8 -*-
import os
"""
        findings, _ = check_presence(source, "legacy.py", PresenceConfig())

        module_findings = [f for f in findings if f.symbol == "legacy"]
        assert len(module_findings) == 1

    def test_stats_consistency_across_mixed_file(self) -> None:
        """Documented + len(findings) == total for all cases."""
        source = '''\
"""Module docstring."""


def a():
    """Doc."""


def _private():
    pass


def b():
    pass


class C:
    """Doc."""

    def __init__(self):
        pass

    def __repr__(self):
        return ""

    def method(self):
        pass
'''
        config = PresenceConfig()
        findings, stats = check_presence(source, "a.py", config)

        # Skipped: _private (private), __init__ (init), __repr__ (magic)
        # Checked: <module>(d), a(d), b(u), C(d), method(u)
        assert stats.total == 5
        assert stats.documented == 3
        assert len(findings) == 2
        assert stats.documented + len(findings) == stats.total


class TestNoDoubleCounting:
    """Regression guard: enrichment skips undocumented symbols (AC 3)."""

    def test_enrichment_produces_zero_findings_for_undocumented_symbols(self):
        """10.20: Both check_presence and check_enrichment on the same source.

        Verify that check_enrichment produces zero findings for symbols
        that have no docstring (enrichment skips `symbol.docstring is None`
        at enrichment.py:1354). This is a unit-level test, NOT a CLI mock.
        """
        import ast

        from docvet.checks.enrichment import check_enrichment
        from docvet.config import EnrichmentConfig

        source = '''\
def documented_func():
    """Has a docstring."""
    pass

def undocumented_func():
    pass

class UndocumentedClass:
    pass
'''
        tree = ast.parse(source)
        config = PresenceConfig()
        enrichment_config = EnrichmentConfig()

        # Presence: should find the undocumented symbols
        presence_findings, stats = check_presence(source, "test.py", config)
        undocumented_symbols = {f.symbol for f in presence_findings}
        assert "undocumented_func" in undocumented_symbols
        assert "UndocumentedClass" in undocumented_symbols

        # Enrichment: must produce zero findings for those undocumented symbols
        enrichment_findings = check_enrichment(
            source, tree, enrichment_config, "test.py"
        )
        enrichment_symbols = {f.symbol for f in enrichment_findings}
        for sym in undocumented_symbols:
            assert sym not in enrichment_symbols, (
                f"Enrichment should not flag undocumented symbol '{sym}'"
            )
