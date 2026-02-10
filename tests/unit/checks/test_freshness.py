"""Unit tests for the freshness check module."""

from __future__ import annotations

import re
from typing import Literal

from docvet.ast_utils import Symbol
from docvet.checks import Finding
from docvet.checks.freshness import _HUNK_PATTERN, _build_finding, _parse_diff_hunks

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
