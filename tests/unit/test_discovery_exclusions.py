"""Unit tests for discovery exclusion patterns."""

from __future__ import annotations

import pytest

from docvet.discovery import _is_excluded

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# _is_excluded tests
# ---------------------------------------------------------------------------


def test_is_excluded_when_component_matches_returns_true():
    assert _is_excluded("tests/unit/test_foo.py", ["tests"]) is True


def test_is_excluded_when_component_partial_match_returns_false():
    assert _is_excluded("src/docvet/test_utils.py", ["tests"]) is False


def test_is_excluded_when_filename_glob_matches_returns_true():
    assert _is_excluded("src/__pycache__/foo.pyc", ["*.pyc"]) is True


def test_is_excluded_when_path_pattern_matches_returns_true():
    assert _is_excluded("scripts/gen_docs.py", ["scripts/gen_*.py"]) is True


def test_is_excluded_when_path_pattern_wrong_root_returns_false():
    assert _is_excluded("other/scripts/gen_docs.py", ["scripts/gen_*.py"]) is False


def test_is_excluded_when_empty_exclude_returns_false():
    assert _is_excluded("src/docvet/cli.py", []) is False


# ---------------------------------------------------------------------------
# _is_excluded — trailing-slash patterns (AC #1)
# ---------------------------------------------------------------------------


def test_is_excluded_trailing_slash_matches_direct_child():
    """build/ matches build/output.py (direct child)."""
    assert _is_excluded("build/output.py", ["build/"]) is True


def test_is_excluded_trailing_slash_matches_nested_child():
    """build/ matches build/sub/deep.py (nested child)."""
    assert _is_excluded("build/sub/deep.py", ["build/"]) is True


def test_is_excluded_trailing_slash_matches_at_any_depth():
    """build/ matches src/build/mod.py (any depth)."""
    assert _is_excluded("src/build/mod.py", ["build/"]) is True


def test_is_excluded_trailing_slash_rejects_partial_dir_name():
    """build/ does NOT match rebuild/main.py (partial dir name)."""
    assert _is_excluded("rebuild/main.py", ["build/"]) is False


def test_is_excluded_trailing_slash_rejects_filename():
    """build/ does NOT match buildfile.py (filename, not directory)."""
    assert _is_excluded("buildfile.py", ["build/"]) is False


def test_is_excluded_path_trailing_slash_matches_rooted_prefix():
    """vendor/legacy/ matches vendor/legacy/old.py (rooted path prefix)."""
    assert _is_excluded("vendor/legacy/old.py", ["vendor/legacy/"]) is True


def test_is_excluded_path_trailing_slash_rejects_non_root():
    """vendor/legacy/ does NOT match src/vendor/legacy/old.py (not at root)."""
    assert _is_excluded("src/vendor/legacy/old.py", ["vendor/legacy/"]) is False


# ---------------------------------------------------------------------------
# _is_excluded — double-star patterns (AC #2)
# ---------------------------------------------------------------------------


def test_is_excluded_double_star_leading_matches_root_level():
    """**/test_*.py matches test_foo.py (root level, zero-segment)."""
    assert _is_excluded("test_foo.py", ["**/test_*.py"]) is True


def test_is_excluded_double_star_leading_matches_one_level():
    """**/test_*.py matches src/test_foo.py (one level)."""
    assert _is_excluded("src/test_foo.py", ["**/test_*.py"]) is True


def test_is_excluded_double_star_leading_matches_deep_nesting():
    """**/test_*.py matches a/b/c/test_bar.py (deep nesting)."""
    assert _is_excluded("a/b/c/test_bar.py", ["**/test_*.py"]) is True


def test_is_excluded_double_star_leading_rejects_non_match():
    """**/test_*.py does NOT match src/foo.py."""
    assert _is_excluded("src/foo.py", ["**/test_*.py"]) is False


def test_is_excluded_double_star_middle_matches_zero_segment():
    """src/**/test_*.py matches src/test_foo.py (zero-segment middle)."""
    assert _is_excluded("src/test_foo.py", ["src/**/test_*.py"]) is True


def test_is_excluded_double_star_middle_matches_one_segment():
    """src/**/test_*.py matches src/a/test_foo.py (one-segment middle)."""
    assert _is_excluded("src/a/test_foo.py", ["src/**/test_*.py"]) is True


def test_is_excluded_double_star_middle_rejects_wrong_prefix():
    """src/**/test_*.py does NOT match other/test_foo.py (wrong prefix)."""
    assert _is_excluded("other/test_foo.py", ["src/**/test_*.py"]) is False


def test_is_excluded_double_star_trailing_matches_direct():
    """build/** matches build/out.py (trailing ** direct)."""
    assert _is_excluded("build/out.py", ["build/**"]) is True


def test_is_excluded_double_star_trailing_matches_nested():
    """build/** matches build/sub/out.py (trailing ** nested)."""
    assert _is_excluded("build/sub/out.py", ["build/**"]) is True


# ---------------------------------------------------------------------------
# _is_excluded — backward compatibility regression (AC #3)
# ---------------------------------------------------------------------------


def test_is_excluded_backward_compat_component_match():
    """Existing component-level pattern still works (regression)."""
    assert _is_excluded("tests/unit/test_foo.py", ["tests"]) is True
    assert _is_excluded("src/docvet/test_utils.py", ["tests"]) is False


def test_is_excluded_backward_compat_glob_match():
    """Existing filename glob still works (regression)."""
    assert _is_excluded("src/__pycache__/foo.pyc", ["*.pyc"]) is True
    assert _is_excluded("src/foo.py", ["*.pyc"]) is False


def test_is_excluded_backward_compat_path_pattern():
    """Existing path-level pattern still works (regression)."""
    assert _is_excluded("scripts/gen_docs.py", ["scripts/gen_*.py"]) is True
    assert _is_excluded("other/scripts/gen_docs.py", ["scripts/gen_*.py"]) is False


# ---------------------------------------------------------------------------
# _is_excluded — mixed patterns (AC #4)
# ---------------------------------------------------------------------------


def test_is_excluded_mixed_patterns_all_types():
    """Multiple pattern types in a single exclude list all work."""
    exclude = ["tests", "build/", "**/conftest.py"]
    # Component match
    assert _is_excluded("tests/unit/test_foo.py", exclude) is True
    # Trailing-slash match
    assert _is_excluded("build/output.py", exclude) is True
    # Double-star match
    assert _is_excluded("src/conftest.py", exclude) is True
    assert _is_excluded("conftest.py", exclude) is True
    # None match
    assert _is_excluded("src/docvet/cli.py", exclude) is False


def test_is_excluded_bare_double_star_matches_everything():
    """Pattern ** matches any path (degenerate case)."""
    assert _is_excluded("src/docvet/cli.py", ["**"]) is True
    assert _is_excluded("foo.py", ["**"]) is True


def test_is_excluded_trailing_slash_with_double_star_does_not_match():
    """Patterns combining trailing-slash and ** route to trailing-slash branch."""
    # build/**/ → dirname "build/**" contains "/" → rooted prefix check → no match
    assert _is_excluded("build/out.py", ["build/**/"]) is False
    # **/ → dirname "**" has no "/" → component check → no path segment equals "**"
    assert _is_excluded("src/foo.py", ["**/"]) is False


def test_is_excluded_mixed_simple_and_advanced_from_extend_exclude():
    """Patterns from both exclude and extend-exclude evaluate correctly."""
    # Simulates merged list from config (exclude + extend-exclude)
    merged = ["*.pyc", "build/", "**/test_*.py", "scripts/gen_*.py"]
    assert _is_excluded("src/__pycache__/foo.pyc", merged) is True
    assert _is_excluded("build/out.py", merged) is True
    assert _is_excluded("a/b/test_foo.py", merged) is True
    assert _is_excluded("scripts/gen_docs.py", merged) is True
    assert _is_excluded("src/docvet/cli.py", merged) is False
