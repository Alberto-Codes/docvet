"""Unit tests for the freshness check module."""

from __future__ import annotations

import ast
import re
from typing import Literal
from unittest.mock import patch

from docvet.ast_utils import Symbol
from docvet.checks import Finding
from docvet.checks.freshness import (
    _HUNK_PATTERN,
    _build_finding,
    _classify_changed_lines,
    _compute_age,
    _compute_drift,
    _parse_blame_timestamps,
    _parse_diff_hunks,
    check_freshness_diff,
    check_freshness_drift,
)
from docvet.config import FreshnessConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_symbol(
    name: str = "foo",
    kind: Literal["function", "class", "method", "module"] = "function",
    line: int = 1,
) -> Symbol:
    """Create a minimal Symbol for testing _build_finding."""
    return Symbol(
        name=name,
        kind=kind,
        line=line,
        end_line=line + 5,
        definition_start=line,
        docstring='"""Docstring."""',
        docstring_range=(line + 1, line + 1),
        signature_range=(line, line) if kind != "class" else None,
        body_range=(line + 2, line + 5),
        parent=None,
    )


# ---------------------------------------------------------------------------
# _HUNK_PATTERN tests (AC 8)
# ---------------------------------------------------------------------------


class TestHunkPattern:
    """Tests for the _HUNK_PATTERN compiled regex."""

    def test_is_compiled_regex(self) -> None:
        assert isinstance(_HUNK_PATTERN, re.Pattern)

    def test_matches_standard_hunk_header(self) -> None:
        match = _HUNK_PATTERN.match("@@ -10,5 +12,8 @@")
        assert match is not None
        assert match.group(1) == "12"
        assert match.group(2) == "8"

    def test_matches_hunk_header_without_count(self) -> None:
        match = _HUNK_PATTERN.match("@@ -1 +1 @@")
        assert match is not None
        assert match.group(1) == "1"
        assert match.group(2) is None

    def test_matches_hunk_header_with_trailing_context(self) -> None:
        match = _HUNK_PATTERN.match("@@ -10,3 +10,5 @@ def foo():")
        assert match is not None
        assert match.group(1) == "10"
        assert match.group(2) == "5"

    def test_does_not_match_non_hunk_line(self) -> None:
        assert _HUNK_PATTERN.match("+    return 42") is None

    def test_does_not_match_diff_header(self) -> None:
        assert _HUNK_PATTERN.match("diff --git a/foo.py b/foo.py") is None


# ---------------------------------------------------------------------------
# _parse_diff_hunks tests (AC 1-6)
# ---------------------------------------------------------------------------


class TestParseDiffHunks:
    """Tests for _parse_diff_hunks."""

    def test_basic_hunk_expansion(self) -> None:
        """AC 1: Expands +start,count into line numbers."""
        diff = (
            "diff --git a/module.py b/module.py\n"
            "index abc1234..def5678 100644\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -10,3 +12,8 @@ def foo():\n"
            "     pass\n"
            "+    return 42\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == {12, 13, 14, 15, 16, 17, 18, 19}

    def test_multiple_hunks(self) -> None:
        """Multiple hunks in a single diff output."""
        diff = (
            "diff --git a/module.py b/module.py\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -1,2 +1,3 @@ first hunk\n"
            " context\n"
            "+added\n"
            "@@ -10,2 +11,2 @@ second hunk\n"
            " context\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == {1, 2, 3, 11, 12}

    def test_new_file_returns_empty_set(self) -> None:
        """AC 2: New files (--- /dev/null) return empty set."""
        diff = (
            "diff --git a/new_file.py b/new_file.py\n"
            "new file mode 100644\n"
            "index 0000000..abc1234\n"
            "--- /dev/null\n"
            "+++ b/new_file.py\n"
            "@@ -0,0 +1,5 @@\n"
            "+def hello():\n"
            '+    """Say hello."""\n'
            "+    pass\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == set()

    def test_binary_file_returns_empty_set(self) -> None:
        """AC 3: Binary files return empty set."""
        diff = (
            "diff --git a/image.png b/image.png\n"
            "Binary files a/image.png and b/image.png differ\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == set()

    def test_missing_count_defaults_to_one(self) -> None:
        """AC 4: Missing count defaults to 1."""
        diff = (
            "diff --git a/module.py b/module.py\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == {1}

    def test_empty_string_returns_empty_set(self) -> None:
        """AC 5: Empty string returns empty set."""
        assert _parse_diff_hunks("") == set()

    def test_whitespace_only_returns_empty_set(self) -> None:
        """Whitespace-only input returns empty set (no hunk headers to match)."""
        assert _parse_diff_hunks("  \n\n  ") == set()

    def test_rename_and_mode_change_lines_skipped(self) -> None:
        """AC 6: Rename and mode change lines are silently skipped."""
        diff = (
            "diff --git a/old.py b/new.py\n"
            "similarity index 95%\n"
            "rename from old.py\n"
            "rename to new.py\n"
            "old mode 100644\n"
            "new mode 100755\n"
            "--- a/old.py\n"
            "+++ b/new.py\n"
            "@@ -5,2 +5,3 @@ def bar():\n"
            "     pass\n"
            "+    return 1\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == {5, 6, 7}

    def test_count_zero_returns_no_lines(self) -> None:
        """Count of 0 (deletion hunk) produces no lines."""
        diff = (
            "diff --git a/module.py b/module.py\n"
            "--- a/module.py\n"
            "+++ b/module.py\n"
            "@@ -5,3 +5,0 @@\n"
        )
        result = _parse_diff_hunks(diff)
        assert result == set()

    def test_deleted_file_with_plus_dev_null(self) -> None:
        """Deleted file (+++ /dev/null) — hunk headers may appear but no new lines."""
        diff = (
            "diff --git a/old.py b/old.py\n"
            "deleted file mode 100644\n"
            "--- a/old.py\n"
            "+++ /dev/null\n"
            "@@ -1,3 +0,0 @@\n"
            "-def foo():\n"
            '-    """Removed."""\n'
            "-    pass\n"
        )
        result = _parse_diff_hunks(diff)
        # +0,0 means no lines in new version — range(0, 0) is empty
        assert result == set()

    def test_new_file_with_hunks_returns_empty(self) -> None:
        """New file with --- /dev/null followed by hunks still returns empty set."""
        diff = "--- /dev/null\n+++ b/brand_new.py\n@@ -0,0 +1,10 @@\n+line 1\n"
        result = _parse_diff_hunks(diff)
        assert result == set()


# ---------------------------------------------------------------------------
# _build_finding tests (AC 7)
# ---------------------------------------------------------------------------


class TestBuildFinding:
    """Tests for _build_finding shared helper."""

    def test_constructs_finding_with_correct_fields(self) -> None:
        """AC 7: Returns Finding with correct field mapping."""
        symbol = _make_symbol(name="do_work", kind="function", line=42)
        finding = _build_finding(
            file_path="src/app.py",
            symbol=symbol,
            rule="stale-signature",
            message="Function 'do_work' signature changed but docstring not updated",
            category="required",
        )
        assert isinstance(finding, Finding)
        assert finding.file == "src/app.py"
        assert finding.line == 42
        assert finding.symbol == "do_work"
        assert finding.rule == "stale-signature"
        assert (
            finding.message
            == "Function 'do_work' signature changed but docstring not updated"
        )
        assert finding.category == "required"

    def test_uses_symbol_line_and_name(self) -> None:
        """Finding.line comes from symbol.line, Finding.symbol from symbol.name."""
        symbol = _make_symbol(name="MyClass", kind="class", line=100)
        finding = _build_finding(
            file_path="src/models.py",
            symbol=symbol,
            rule="stale-body",
            message="Class 'MyClass' body changed but docstring not updated",
            category="recommended",
        )
        assert finding.line == 100
        assert finding.symbol == "MyClass"

    def test_recommended_category(self) -> None:
        """Supports recommended category."""
        symbol = _make_symbol()
        finding = _build_finding(
            file_path="src/util.py",
            symbol=symbol,
            rule="stale-import",
            message="Import changed",
            category="recommended",
        )
        assert finding.category == "recommended"


# ---------------------------------------------------------------------------
# _classify_changed_lines tests (AC 1-6)
# ---------------------------------------------------------------------------


def _make_function_symbol(
    name: str = "greet",
    line: int = 1,
    signature_range: tuple[int, int] = (1, 1),
    docstring_range: tuple[int, int] | None = (2, 2),
    body_range: tuple[int, int] = (3, 5),
    end_line: int = 5,
) -> Symbol:
    """Create a function Symbol with explicit range control for classification tests."""
    return Symbol(
        name=name,
        kind="function",
        line=line,
        end_line=end_line,
        definition_start=line,
        docstring='"""Docstring."""' if docstring_range is not None else None,
        docstring_range=docstring_range,
        signature_range=signature_range,
        body_range=body_range,
        parent=None,
    )


class TestClassifyChangedLines:
    def test_signature_change_returns_signature(self) -> None:
        # AC 1: changed lines in signature_range, no docstring change → "signature"
        sym = _make_function_symbol(
            signature_range=(1, 2),
            docstring_range=(3, 3),
            body_range=(4, 8),
        )
        result = _classify_changed_lines({1}, sym)
        assert result == "signature"

    def test_body_change_returns_body(self) -> None:
        # AC 2: changed lines in body_range, not signature, no docstring change → "body"
        sym = _make_function_symbol(
            signature_range=(1, 1),
            docstring_range=(2, 2),
            body_range=(3, 6),
        )
        result = _classify_changed_lines({4}, sym)
        assert result == "body"

    def test_import_change_returns_import(self) -> None:
        # AC 3: changed lines outside signature, docstring, body → "import"
        # Line 10 is within the symbol's total range (1-12) but outside named ranges
        sym = Symbol(
            name="greet",
            kind="function",
            line=5,
            end_line=12,
            definition_start=3,  # decorator at line 3
            docstring='"""Doc."""',
            docstring_range=(6, 6),
            signature_range=(5, 5),
            body_range=(7, 12),
            parent=None,
        )
        # Line 3 (decorator) is within definition_start..end_line but outside all named ranges
        result = _classify_changed_lines({3}, sym)
        assert result == "import"

    def test_docstring_and_signature_change_returns_none(self) -> None:
        # AC 4: changed lines in both signature and docstring → None (suppressed)
        sym = _make_function_symbol(
            signature_range=(1, 2),
            docstring_range=(3, 3),
            body_range=(4, 8),
        )
        result = _classify_changed_lines({1, 3}, sym)
        assert result is None

    def test_docstring_and_body_change_returns_none(self) -> None:
        # AC 5: changed lines in both body and docstring → None (suppressed)
        sym = _make_function_symbol(
            signature_range=(1, 1),
            docstring_range=(2, 2),
            body_range=(3, 6),
        )
        result = _classify_changed_lines({2, 4}, sym)
        assert result is None

    def test_class_symbol_body_change_returns_body(self) -> None:
        # AC 6: class (signature_range=None) with body change → "body", never "signature"
        sym = Symbol(
            name="Config",
            kind="class",
            line=1,
            end_line=10,
            definition_start=1,
            docstring='"""Config class."""',
            docstring_range=(2, 2),
            signature_range=None,
            body_range=(3, 10),
            parent=None,
        )
        result = _classify_changed_lines({5}, sym)
        assert result == "body"

    def test_module_symbol_body_change_returns_body(self) -> None:
        # AC 6: module (signature_range=None) with body change → "body"
        sym = Symbol(
            name="<module>",
            kind="module",
            line=1,
            end_line=20,
            definition_start=1,
            docstring='"""Module doc."""',
            docstring_range=(1, 1),
            signature_range=None,
            body_range=(2, 20),
            parent=None,
        )
        result = _classify_changed_lines({10}, sym)
        assert result == "body"

    def test_docstring_only_change_returns_none(self) -> None:
        # Docstring-only change → None (no finding needed)
        sym = _make_function_symbol(
            signature_range=(1, 1),
            docstring_range=(2, 3),
            body_range=(4, 8),
        )
        result = _classify_changed_lines({2}, sym)
        assert result is None

    def test_signature_and_body_change_no_docstring_returns_signature(self) -> None:
        # Signature + body changes (no docstring) → "signature" (highest severity wins)
        sym = _make_function_symbol(
            signature_range=(1, 2),
            docstring_range=(3, 3),
            body_range=(4, 8),
        )
        result = _classify_changed_lines({1, 5}, sym)
        assert result == "signature"


# ---------------------------------------------------------------------------
# check_freshness_diff tests (AC 7-16)
# ---------------------------------------------------------------------------

# Source: a simple module with one documented function.
# Line 1: def greet(name):
# Line 2:     """Say hello."""
# Line 3:     return f"Hello, {name}"
_SIMPLE_SOURCE = 'def greet(name):\n    """Say hello."""\n    return f"Hello, {name}"\n'

# Source: module with a function that has NO docstring.
# Line 1: def helper(x):
# Line 2:     return x + 1
_NO_DOC_SOURCE = "def helper(x):\n    return x + 1\n"

# Source: module with a decorated function (decorator line is outside all named ranges).
# Line 1: @deprecated
# Line 2: def greet(name):
# Line 3:     """Say hello."""
# Line 4:     return name
_DECORATED_SOURCE = (
    '@deprecated\ndef greet(name):\n    """Say hello."""\n    return name\n'
)

# Source: module with two functions, one signature change candidate.
# Line 1: import os
# Line 2:
# Line 3: def greet(name, greeting="Hi"):
# Line 4:     """Say hello."""
# Line 5:     return f"{greeting}, {name}"
# Line 6:
# Line 7: def farewell(name):
# Line 8:     """Say goodbye."""
# Line 9:     return f"Bye, {name}"
_TWO_FUNC_SOURCE = (
    "import os\n"
    "\n"
    'def greet(name, greeting="Hi"):\n'
    '    """Say hello."""\n'
    '    return f"{greeting}, {name}"\n'
    "\n"
    "def farewell(name):\n"
    '    """Say goodbye."""\n'
    '    return f"Bye, {name}"\n'
)


def _make_diff(start: int, count: int = 1) -> str:
    """Build a minimal unified diff with one hunk targeting given lines."""
    return (
        "diff --git a/test.py b/test.py\n"
        "--- a/test.py\n"
        "+++ b/test.py\n"
        f"@@ -1,1 +{start},{count} @@\n"
        "+changed\n"
    )


class TestCheckFreshnessDiff:
    def test_stale_signature_finding_produced(self) -> None:
        # AC 7: function signature changed, docstring not updated → stale-signature
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=1, count=1)  # line 1 = signature
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 1
        assert findings[0].rule == "stale-signature"
        assert findings[0].category == "required"

    def test_stale_body_finding_produced(self) -> None:
        # AC 8: method body changed, docstring not updated → stale-body
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=3, count=1)  # line 3 = body
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 1
        assert findings[0].rule == "stale-body"
        assert findings[0].category == "recommended"

    def test_import_change_skipped_for_undocumented_module(self) -> None:
        # FR54: import line maps to module symbol with no docstring → skipped
        source = _TWO_FUNC_SOURCE
        tree = ast.parse(source)
        diff = _make_diff(start=1, count=1)  # line 1 = import (module-level)
        findings = check_freshness_diff("test.py", diff, tree)
        # Module symbol has no docstring → docstring_range is None → skipped.
        assert len(findings) == 0

    def test_stale_import_with_module_docstring(self) -> None:
        # Module body change: import line falls in module body_range → stale-body
        source = (
            '"""Module doc."""\n'  # line 1: module docstring
            "import os\n"  # line 2: import (module body)
            "\n"  # line 3: blank
            "def greet(name):\n"  # line 4: function
            '    """Say hello."""\n'  # line 5: func docstring
            "    return name\n"  # line 6: func body
        )
        tree = ast.parse(source)
        diff = _make_diff(start=2, count=1)  # line 2 = import (module body)
        findings = check_freshness_diff("test.py", diff, tree)
        # Line 2 maps to module symbol (innermost for imports).
        # Module has docstring_range=(1,1), body_range=(2,...).
        # Classification: body change (line 2 in body_range) → stale-body for module.
        assert len(findings) == 1
        assert findings[0].rule == "stale-body"

    def test_stale_import_finding_for_decorator_change(self) -> None:
        # AC 9: decorator line changed (outside signature/body/docstring) → stale-import
        tree = ast.parse(_DECORATED_SOURCE)
        diff = _make_diff(start=1, count=1)  # line 1 = decorator
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 1
        assert findings[0].rule == "stale-import"
        assert findings[0].category == "recommended"

    def test_highest_severity_wins(self) -> None:
        # AC 10: signature + body changes (no docstring) → one stale-signature finding
        tree = ast.parse(_SIMPLE_SOURCE)
        # Diff must hit signature (line 1) and body (line 3) but NOT docstring (line 2).
        diff = (
            "diff --git a/test.py b/test.py\n"
            "--- a/test.py\n"
            "+++ b/test.py\n"
            "@@ -1,1 +1,1 @@\n"  # line 1 = signature
            "+changed\n"
            "@@ -3,1 +3,1 @@\n"  # line 3 = body
            "+changed\n"
        )
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 1
        assert findings[0].rule == "stale-signature"

    def test_no_docstring_symbol_skipped(self) -> None:
        # AC 11: symbol with no docstring → zero findings
        tree = ast.parse(_NO_DOC_SOURCE)
        diff = _make_diff(start=1, count=2)  # lines 1-2 = entire function
        findings = check_freshness_diff("test.py", diff, tree)
        # Function has no docstring → docstring_range is None → skipped
        # Module has no docstring either → also skipped
        assert len(findings) == 0

    def test_deleted_function_zero_findings(self) -> None:
        # AC 12: deleted function not in current AST → zero findings
        # Current source has only greet(); diff targets lines 10-15 (deleted function)
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=10, count=5)  # lines 10-14 don't exist in current AST
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 0

    def test_docstring_updated_zero_findings(self) -> None:
        # AC 14: all changed symbols have updated docstrings → empty list
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=1, count=2)  # lines 1-2 = signature + docstring
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 0

    def test_empty_diff_returns_empty_list(self) -> None:
        # AC 15: empty diff_output → empty list
        tree = ast.parse(_SIMPLE_SOURCE)
        findings = check_freshness_diff("test.py", "", tree)
        assert findings == []

    def test_deterministic_output(self) -> None:
        # AC 16: identical inputs → identical outputs
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=3, count=1)  # body change
        results = [check_freshness_diff("test.py", diff, tree) for _ in range(5)]
        for r in results[1:]:
            assert len(r) == len(results[0])
            for f1, f2 in zip(r, results[0]):
                assert f1.rule == f2.rule
                assert f1.line == f2.line
                assert f1.symbol == f2.symbol
                assert f1.message == f2.message

    def test_finding_message_format(self) -> None:
        # AC: message is "{Kind} '{name}' {change_type} changed but docstring not updated"
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=3, count=1)  # body change
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 1
        assert (
            findings[0].message
            == "Function 'greet' body changed but docstring not updated"
        )

    def test_finding_uses_symbol_line(self) -> None:
        # Finding.line should be symbol.line (def keyword), not the changed line number
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=3, count=1)  # changed line is 3, but def is on line 1
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 1
        assert findings[0].line == 1  # symbol.line, not the changed line

    def test_relocated_function_suppressed_when_docstring_in_diff(self) -> None:
        # AC 13: relocated function — all lines appear as changed in diff.
        # When a function moves, git shows all lines at the new location as added.
        # The docstring line is in the changed set → finding suppressed (no false positive).
        tree = ast.parse(_SIMPLE_SOURCE)
        diff = _make_diff(start=1, count=3)  # lines 1-3 = entire function
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 0

    def test_multiple_symbols_produce_multiple_findings(self) -> None:
        # Multiple symbols changed in one diff → one finding per affected symbol
        tree = ast.parse(_TWO_FUNC_SOURCE)
        # Hit greet signature (line 3) and farewell body (line 9)
        diff = (
            "diff --git a/test.py b/test.py\n"
            "--- a/test.py\n"
            "+++ b/test.py\n"
            "@@ -3,1 +3,1 @@\n"
            "+changed\n"
            "@@ -9,1 +9,1 @@\n"
            "+changed\n"
        )
        findings = check_freshness_diff("test.py", diff, tree)
        assert len(findings) == 2
        rules = {f.rule for f in findings}
        assert "stale-signature" in rules
        assert "stale-body" in rules


# ---------------------------------------------------------------------------
# Blame output test constants
# ---------------------------------------------------------------------------

_BLAME_SINGLE_ENTRY = """\
1234567890123456789012345678901234567890 1 1 1
author Test Author
author-mail <test@example.com>
author-time 1707500000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 1707500000
committer-tz +0000
summary Initial commit
filename test.py
\tdef greet(name):
"""

_BLAME_MULTI_ENTRY = """\
1234567890123456789012345678901234567890 1 1 1
author Test Author
author-mail <test@example.com>
author-time 1707500000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 1707500000
committer-tz +0000
summary Initial commit
filename test.py
\tdef greet(name):
abcdef7890123456789012345678901234567890 2 2 1
author Another Author
author-mail <another@example.com>
author-time 1707600000
author-tz +0000
committer Another Author
committer-mail <another@example.com>
committer-time 1707600000
committer-tz +0000
summary Add docstring
filename test.py
\t    \"\"\"Say hello.\"\"\"
fedcba9876543210fedcba9876543210fedcba98 3 3 1
author Test Author
author-mail <test@example.com>
author-time 1707700000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 1707700000
committer-tz +0000
summary Add return
filename test.py
\t    return f"Hello, {name}"
"""


# ---------------------------------------------------------------------------
# _parse_blame_timestamps tests (AC 1-8)
# ---------------------------------------------------------------------------


class TestParseBlameTimestamps:
    """Tests for _parse_blame_timestamps."""

    def test_single_entry_returns_line_timestamp_mapping(self) -> None:
        """AC 1, 2, 3: Single blame entry returns {line_num: timestamp}."""
        result = _parse_blame_timestamps(_BLAME_SINGLE_ENTRY)
        assert result == {1: 1707500000}

    def test_multiple_entries_returns_complete_mapping(self) -> None:
        """AC 1: Multiple entries produce complete dict[int, int] mapping."""
        result = _parse_blame_timestamps(_BLAME_MULTI_ENTRY)
        assert result == {1: 1707500000, 2: 1707600000, 3: 1707700000}

    def test_empty_string_returns_empty_dict(self) -> None:
        """AC 5: Empty string returns empty dict."""
        assert _parse_blame_timestamps("") == {}

    def test_whitespace_only_returns_empty_dict(self) -> None:
        """Whitespace-only input returns empty dict."""
        assert _parse_blame_timestamps("   \n\n   ") == {}

    def test_header_fields_silently_skipped(self) -> None:
        """AC 4: Only line numbers and timestamps extracted, not author names etc."""
        result = _parse_blame_timestamps(_BLAME_SINGLE_ENTRY)
        # Should only have line 1 with its timestamp — no extra keys
        assert len(result) == 1
        assert 1 in result
        # Timestamp should be the author-time value, not any other numeric field
        assert result[1] == 1707500000

    def test_boundary_commit_parses_normally(self) -> None:
        """AC 6: Boundary commit (normal 40-char SHA) parses — author-time still present."""
        # In --line-porcelain, boundary commits still have 40-char SHA and author-time
        blame = """\
1234567890123456789012345678901234567890 1 1 1
author Boundary Author
author-mail <boundary@example.com>
author-time 1600000000
author-tz +0000
committer Boundary Author
committer-mail <boundary@example.com>
committer-time 1600000000
committer-tz +0000
summary boundary commit
boundary
filename module.py
\timport os
"""
        result = _parse_blame_timestamps(blame)
        assert result == {1: 1600000000}

    def test_uncommitted_changes_zero_sha_parses_normally(self) -> None:
        """AC 7: Zero SHA (uncommitted changes) parses normally."""
        blame = """\
0000000000000000000000000000000000000000 1 1 1
author Not Committed Yet
author-mail <not.committed.yet>
author-time 1710000000
author-tz +0000
committer Not Committed Yet
committer-mail <not.committed.yet>
committer-time 1710000000
committer-tz +0000
summary Not Yet Committed
filename working.py
\tprint("hello")
"""
        result = _parse_blame_timestamps(blame)
        assert result == {1: 1710000000}

    def test_corrupted_data_silently_skipped(self) -> None:
        """AC 8: Non-blame lines interspersed with valid blocks are skipped."""
        blame = """\
THIS IS CORRUPTED DATA
some random line
1234567890123456789012345678901234567890 1 5 1
author Test Author
author-mail <test@example.com>
author-time 1707500000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 1707500000
committer-tz +0000
summary Commit
filename test.py
\tvalid line
MORE CORRUPTED DATA
"""
        result = _parse_blame_timestamps(blame)
        assert result == {5: 1707500000}

    def test_block_missing_author_time_skipped(self) -> None:
        """Blame block without author-time produces no entry."""
        blame = """\
1234567890123456789012345678901234567890 1 1 1
author Test Author
author-mail <test@example.com>
committer Test Author
committer-mail <test@example.com>
committer-time 1707500000
committer-tz +0000
summary Commit
filename test.py
\tdef greet(name):
"""
        result = _parse_blame_timestamps(blame)
        # No author-time → current_timestamp remains None → no entry emitted
        assert result == {}

    def test_block_missing_content_line_skipped(self) -> None:
        """Truncated block (no tab-prefixed content line) produces no entry."""
        blame = """\
1234567890123456789012345678901234567890 1 1 1
author Test Author
author-mail <test@example.com>
author-time 1707500000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 1707500000
committer-tz +0000
summary Commit
filename test.py"""
        result = _parse_blame_timestamps(blame)
        # No tab-prefixed content line → entry never emitted
        assert result == {}

    def test_sha_line_with_only_two_fields_skipped(self) -> None:
        """Malformed SHA line with only 2 fields is silently skipped."""
        blame = """\
1234567890123456789012345678901234567890 1
author-time 1707500000
\tsome content
"""
        result = _parse_blame_timestamps(blame)
        # SHA line rejected (< 3 parts) → current_line never set → no entry
        assert result == {}

    def test_sha_line_with_non_numeric_third_field_skipped(self) -> None:
        """SHA-like line with non-numeric third field is silently handled."""
        blame = """\
1234567890123456789012345678901234567890 1 notanumber 1
author-time 1707500000
\tsome content
"""
        result = _parse_blame_timestamps(blame)
        # int("notanumber") raises ValueError → current_line set to None → no entry
        assert result == {}

    def test_valid_blocks_among_corrupted_data(self) -> None:
        """Valid blocks are parsed even when surrounded by corrupted data."""
        blame = """\
GARBAGE LINE
1234567890123456789012345678901234567890 1 3 1
author Test
author-mail <t@e.com>
author-time 1700000000
author-tz +0000
committer Test
committer-mail <t@e.com>
committer-time 1700000000
committer-tz +0000
summary First
filename test.py
\tline three
ANOTHER GARBAGE LINE
abcdef7890123456789012345678901234567890 2 7 1
author Test
author-mail <t@e.com>
author-time 1800000000
author-tz +0000
committer Test
committer-mail <t@e.com>
committer-time 1800000000
committer-tz +0000
summary Second
filename test.py
\tline seven
"""
        result = _parse_blame_timestamps(blame)
        assert result == {3: 1700000000, 7: 1800000000}

    def test_truncated_block_followed_by_valid_block(self) -> None:
        """Truncated first block (no content line) is discarded when next SHA appears."""
        blame = """\
1234567890123456789012345678901234567890 1 1 1
author-time 1000000000
abcdef7890123456789012345678901234567890 1 2 1
author Test Author
author-mail <test@example.com>
author-time 2000000000
author-tz +0000
committer Test Author
committer-mail <test@example.com>
committer-time 2000000000
committer-tz +0000
summary Second commit
filename test.py
\tcontent line
"""
        result = _parse_blame_timestamps(blame)
        # First block has no tab-prefixed content line before second SHA → discarded
        assert result == {2: 2000000000}

    def test_author_time_non_numeric_value_skipped(self) -> None:
        """author-time with non-numeric value triggers ValueError and is skipped."""
        blame = """\
1234567890123456789012345678901234567890 1 1 1
author-time notanumber
\tcontent line
"""
        result = _parse_blame_timestamps(blame)
        # int("notanumber") raises ValueError → timestamp stays None → no entry
        assert result == {}

    def test_author_time_missing_value_skipped(self) -> None:
        """author-time with trailing space but no value triggers IndexError and is skipped."""
        blame = """\
1234567890123456789012345678901234567890 1 1 1
author-time\x20
\tcontent line
"""
        result = _parse_blame_timestamps(blame)
        # "author-time ".split() → ["author-time"], [1] raises IndexError → skipped
        assert result == {}


# ---------------------------------------------------------------------------
# Drift mode test constants
# ---------------------------------------------------------------------------

# Source with documented func (lines 4-6), undocumented func (9-10), stub (13-14)
_DRIFT_SOURCE = """\
\"\"\"Module docstring.\"\"\"


def documented_func(x):
    \"\"\"Func docstring.\"\"\"
    return x + 1


def undocumented_func(x):
    return x + 1


def stub_func():
    \"\"\"Only a docstring, no real body.\"\"\"
"""

_DAY = 86400
_BASE_TS = 1696118400  # 2023-10-01 00:00:00 UTC


def _build_blame(*entries: tuple[int, int]) -> str:
    sha = "a" * 40
    blocks: list[str] = []
    for line_num, ts in entries:
        blocks.append(
            f"{sha} 1 {line_num} 1\n"
            f"author Test\n"
            f"author-mail <t@e.com>\n"
            f"author-time {ts}\n"
            f"author-tz +0000\n"
            f"committer Test\n"
            f"committer-mail <t@e.com>\n"
            f"committer-time {ts}\n"
            f"committer-tz +0000\n"
            f"summary Commit\n"
            f"filename test.py\n"
            f"\tline content\n"
        )
    return "".join(blocks)


# ---------------------------------------------------------------------------
# _compute_drift tests (AC 1, 4, 8)
# ---------------------------------------------------------------------------


class TestComputeDrift:
    def test_drift_exceeds_threshold(self) -> None:
        assert _compute_drift([_BASE_TS + 73 * _DAY], [_BASE_TS], threshold=30) is True

    def test_drift_within_threshold(self) -> None:
        assert _compute_drift([_BASE_TS + 10 * _DAY], [_BASE_TS], threshold=30) is False

    def test_exact_boundary_returns_false(self) -> None:
        # AC 4: strict > comparison — exact boundary does NOT trigger
        assert _compute_drift([_BASE_TS + 30 * _DAY], [_BASE_TS], threshold=30) is False

    def test_empty_code_timestamps_returns_false(self) -> None:
        assert _compute_drift([], [_BASE_TS], threshold=30) is False

    def test_empty_doc_timestamps_returns_false(self) -> None:
        assert _compute_drift([_BASE_TS], [], threshold=30) is False


# ---------------------------------------------------------------------------
# _compute_age tests (AC 2, 5, 7)
# ---------------------------------------------------------------------------


class TestComputeAge:
    def test_age_exceeds_threshold(self) -> None:
        assert _compute_age([_BASE_TS], now=_BASE_TS + 147 * _DAY, threshold=90) is True

    def test_age_within_threshold(self) -> None:
        assert _compute_age([_BASE_TS], now=_BASE_TS + 60 * _DAY, threshold=90) is False

    def test_exact_boundary_returns_false(self) -> None:
        # AC 5: strict > comparison — exact boundary does NOT trigger
        assert _compute_age([_BASE_TS], now=_BASE_TS + 90 * _DAY, threshold=90) is False

    def test_empty_doc_timestamps_returns_false(self) -> None:
        assert _compute_age([], now=_BASE_TS + 200 * _DAY, threshold=90) is False


# ---------------------------------------------------------------------------
# check_freshness_drift tests (AC 1-15)
# ---------------------------------------------------------------------------


class TestCheckFreshnessDrift:
    def test_stale_drift_finding_produced(self) -> None:
        # AC 1: code 73 days newer than docstring → stale-drift
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 73 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 73 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 73 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) == 1
        assert drift_findings[0].symbol == "documented_func"

    def test_stale_age_finding_produced(self) -> None:
        # AC 2: docstring 147 days old → stale-age
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS),
            (5, _BASE_TS),
            (6, _BASE_TS),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
        )
        age_findings = [f for f in findings if f.rule == "stale-age"]
        func_age = [f for f in age_findings if f.symbol == "documented_func"]
        assert len(func_age) == 1

    def test_both_drift_and_age_on_same_symbol(self) -> None:
        # AC 3: same symbol triggers both stale-drift and stale-age
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 73 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 73 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
        )
        func_findings = [f for f in findings if f.symbol == "documented_func"]
        rules = {f.rule for f in func_findings}
        assert "stale-drift" in rules
        assert "stale-age" in rules
        assert len(func_findings) == 2

    def test_exact_drift_boundary_produces_no_finding(self) -> None:
        # AC 4: code_max - doc_max == threshold * 86400 → no stale-drift
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 30 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 30 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 30 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) == 0

    def test_exact_age_boundary_produces_no_finding(self) -> None:
        # AC 5: now - doc_max == threshold * 86400 → no stale-age
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS),
            (5, _BASE_TS),
            (6, _BASE_TS),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 90 * _DAY
        )
        age_findings = [f for f in findings if f.rule == "stale-age"]
        assert len(age_findings) == 0

    def test_no_docstring_symbol_skipped(self) -> None:
        # AC 6: symbol with docstring_range=None → zero findings
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (9, _BASE_TS),
            (10, _BASE_TS + 73 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
        )
        undoc = [f for f in findings if f.symbol == "undocumented_func"]
        assert len(undoc) == 0

    def test_stub_symbol_age_can_fire_drift_cannot(self) -> None:
        # AC 7: stub with only docstring line → stale-age can fire, stale-drift cannot
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame((14, _BASE_TS))
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
        )
        stub_findings = [f for f in findings if f.symbol == "stub_func"]
        rules = {f.rule for f in stub_findings}
        assert "stale-drift" not in rules
        assert "stale-age" in rules

    def test_within_threshold_produces_zero_findings(self) -> None:
        # AC 8: within both thresholds → zero findings
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 5 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 5 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 10 * _DAY
        )
        func_findings = [f for f in findings if f.symbol == "documented_func"]
        assert len(func_findings) == 0

    def test_default_thresholds_applied(self) -> None:
        # AC 9: default drift_threshold=30, age_threshold=90
        config = FreshnessConfig()
        assert config.drift_threshold == 30
        assert config.age_threshold == 90
        tree = ast.parse(_DRIFT_SOURCE)
        blame = _build_blame(
            (4, _BASE_TS + 31 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 31 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 31 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) >= 1

    def test_custom_drift_threshold(self) -> None:
        # AC 10: drift_threshold=7, code 10 days newer → stale-drift
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig(drift_threshold=7)
        blame = _build_blame(
            (4, _BASE_TS + 10 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 10 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 10 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) >= 1

    def test_custom_age_threshold(self) -> None:
        # AC 11: age_threshold=180, docstring 100 days old → no stale-age
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig(age_threshold=180)
        blame = _build_blame(
            (4, _BASE_TS),
            (5, _BASE_TS),
            (6, _BASE_TS),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 100 * _DAY
        )
        age_findings = [f for f in findings if f.rule == "stale-age"]
        assert len(age_findings) == 0

    def test_explicit_now_parameter_used(self) -> None:
        # AC 12: explicit now is used for age calculation
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS),
            (5, _BASE_TS),
            (6, _BASE_TS),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 91 * _DAY
        )
        age_findings = [f for f in findings if f.rule == "stale-age"]
        assert len(age_findings) >= 1
        assert "(91 days)" in age_findings[0].message

    def test_default_now_uses_time_time(self) -> None:
        # AC 13: no now parameter → defaults to time.time()
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        fake_now = _BASE_TS + 200 * _DAY
        blame = _build_blame(
            (4, _BASE_TS),
            (5, _BASE_TS),
            (6, _BASE_TS),
        )
        with patch("docvet.checks.freshness.time") as mock_time:
            mock_time.time.return_value = float(fake_now)
            findings = check_freshness_drift("test.py", blame, tree, config)
        age_findings = [f for f in findings if f.rule == "stale-age"]
        assert len(age_findings) >= 1
        assert "(200 days)" in age_findings[0].message

    def test_empty_blame_output_returns_empty_list(self) -> None:
        # AC 14: empty blame_output → []
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        assert check_freshness_drift("test.py", "", tree, config, now=_BASE_TS) == []

    def test_deterministic_output(self) -> None:
        # AC 15: identical inputs → identical output
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 73 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 73 * _DAY),
        )
        results = [
            check_freshness_drift(
                "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
            )
            for _ in range(5)
        ]
        for r in results[1:]:
            assert len(r) == len(results[0])
            for f1, f2 in zip(r, results[0]):
                assert f1.rule == f2.rule
                assert f1.line == f2.line
                assert f1.symbol == f2.symbol
                assert f1.message == f2.message

    def test_finding_message_format_drift(self) -> None:
        # Message contains expected dates and day count
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 73 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 73 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 73 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) == 1
        msg = drift_findings[0].message
        assert "Function 'documented_func'" in msg
        assert "code modified 2023-12-13" in msg
        assert "docstring last modified 2023-10-01" in msg
        assert "(73 days drift)" in msg

    def test_finding_fields_correct(self) -> None:
        # Verify rule, category, file, line, symbol
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 73 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 73 * _DAY),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 73 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) == 1
        f = drift_findings[0]
        assert f.rule == "stale-drift"
        assert f.category == "recommended"
        assert f.file == "test.py"
        assert f.line == 4
        assert f.symbol == "documented_func"

    def test_lines_not_mapping_to_symbol_skipped(self) -> None:
        # Line outside any symbol range → silently skipped
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame((100, _BASE_TS))
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
        )
        assert len(findings) == 0

    def test_identical_timestamps_no_drift(self) -> None:
        # All timestamps identical → code == docstring → no stale-drift
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS),
            (5, _BASE_TS),
            (6, _BASE_TS),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 10 * _DAY
        )
        drift_findings = [f for f in findings if f.rule == "stale-drift"]
        assert len(drift_findings) == 0

    def test_findings_sorted_by_line_number(self) -> None:
        # Multiple symbols → findings sorted by line
        tree = ast.parse(_DRIFT_SOURCE)
        config = FreshnessConfig()
        blame = _build_blame(
            (4, _BASE_TS + 73 * _DAY),
            (5, _BASE_TS),
            (6, _BASE_TS + 73 * _DAY),
            (14, _BASE_TS),
        )
        findings = check_freshness_drift(
            "test.py", blame, tree, config, now=_BASE_TS + 147 * _DAY
        )
        assert len(findings) >= 2
        lines = [f.line for f in findings]
        assert lines == sorted(lines)
