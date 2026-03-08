"""Tests for NumPy-style section recognition in the enrichment check.

Covers AC1-AC6 of Story 34.3: NumPy section headers, underline format
detection, boundary detection in ``_extract_section_content()``, and
regression tests for existing Google-style sections.
"""

from __future__ import annotations

import pytest

from docvet.checks.enrichment import (
    _SECTION_HEADERS,
    _extract_section_content,
    _parse_sections,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# AC6: _SECTION_HEADERS frozenset assertions
# ---------------------------------------------------------------------------


class TestSectionHeadersFrozenset:
    """Tests for _SECTION_HEADERS membership and size (AC: 6)."""

    def test_section_headers_has_exactly_15_entries(self) -> None:
        """_SECTION_HEADERS contains exactly 15 entries after NumPy additions."""
        assert len(_SECTION_HEADERS) == 15

    @pytest.mark.parametrize(
        "header",
        ["Notes", "References", "Warnings", "Extended Summary", "Methods"],
    )
    def test_section_headers_contains_new_entries(self, header: str) -> None:
        """_SECTION_HEADERS contains all 5 new NumPy section names."""
        assert header in _SECTION_HEADERS


# ---------------------------------------------------------------------------
# AC1: New section headers recognized in Google colon format
# ---------------------------------------------------------------------------


class TestNewSectionHeadersGoogleColon:
    """Tests for new headers recognized via Google colon format (AC: 1)."""

    def test_notes_colon_recognized(self) -> None:
        """Notes: header recognized by _parse_sections()."""
        docstring = "Summary.\n\nNotes:\n    Some notes here."
        assert "Notes" in _parse_sections(docstring)

    def test_references_colon_recognized(self) -> None:
        """References: header recognized by _parse_sections()."""
        docstring = "Summary.\n\nReferences:\n    Some refs."
        assert "References" in _parse_sections(docstring)

    def test_warnings_colon_recognized(self) -> None:
        """Warnings: header recognized by _parse_sections()."""
        docstring = "Summary.\n\nWarnings:\n    Be careful."
        assert "Warnings" in _parse_sections(docstring)

    def test_extended_summary_colon_recognized(self) -> None:
        """Extended Summary: header recognized by _parse_sections()."""
        docstring = "Summary.\n\nExtended Summary:\n    More details."
        assert "Extended Summary" in _parse_sections(docstring)

    def test_methods_colon_recognized(self) -> None:
        """Methods: header recognized by _parse_sections()."""
        docstring = "Summary.\n\nMethods:\n    do_thing()."
        assert "Methods" in _parse_sections(docstring)


# ---------------------------------------------------------------------------
# AC2: NumPy underline format detection
# ---------------------------------------------------------------------------


class TestNumpyUnderlineFormat:
    """Tests for NumPy underline format detection (AC: 2)."""

    def test_args_underline_recognized(self) -> None:
        """Args with dash underline recognized via NumPy underline format."""
        docstring = "Summary.\n\nArgs\n----\n    x: An int.\n"
        assert "Args" in _parse_sections(docstring)

    def test_returns_underline_recognized(self) -> None:
        """Returns with dash underline recognized via NumPy underline format."""
        docstring = "Summary.\n\nReturns\n-------\n    int: The result.\n"
        assert "Returns" in _parse_sections(docstring)

    def test_notes_underline_recognized(self) -> None:
        """Notes with dash underline recognized via NumPy underline format."""
        docstring = "Summary.\n\nNotes\n-----\n    Some notes.\n"
        assert "Notes" in _parse_sections(docstring)

    def test_raises_underline_recognized(self) -> None:
        """Raises with dash underline recognized via NumPy underline format."""
        docstring = "Summary.\n\nRaises\n------\n    ValueError: Bad input.\n"
        assert "Raises" in _parse_sections(docstring)

    def test_examples_underline_with_equals_recognized(self) -> None:
        """Examples with equals underline recognized via NumPy underline format."""
        docstring = "Summary.\n\nExamples\n========\n    >>> 1 + 1\n"
        assert "Examples" in _parse_sections(docstring)

    def test_arbitrary_text_with_dashes_not_recognized(self) -> None:
        """Arbitrary text followed by dashes is NOT a section (AC: 2 negative)."""
        docstring = "Summary.\n\nSome random text\n----------------\n    Content.\n"
        sections = _parse_sections(docstring)
        assert "Some random text" not in sections

    def test_underline_fewer_than_3_dashes_not_recognized(self) -> None:
        """Underline with fewer than 3 dashes is NOT recognized (AC: 2 negative)."""
        docstring = "Summary.\n\nReturns\n--\n    int: The result.\n"
        # Only colon format should work, not 2-dash underline
        assert "Returns" not in _parse_sections(docstring)

    def test_blank_line_between_header_and_underline_not_recognized(self) -> None:
        """Header with blank line before underline is NOT recognized (AC: 2 negative)."""
        docstring = "Summary.\n\nReturns\n\n-------\n    int: The result.\n"
        assert "Returns" not in _parse_sections(docstring)

    def test_no_blank_line_between_header_and_underline_recognized(self) -> None:
        """Header immediately followed by underline IS recognized (AC: 2 positive)."""
        docstring = "Summary.\n\nReturns\n-------\n    int: The result.\n"
        assert "Returns" in _parse_sections(docstring)

    def test_mixed_google_and_numpy_in_same_docstring(self) -> None:
        """Mixed Google colon and NumPy underline detected in same docstring."""
        docstring = (
            "Summary.\n\n"
            "Args:\n    x: An int.\n\n"
            "Returns\n-------\n    int: The result.\n"
        )
        sections = _parse_sections(docstring)
        assert "Args" in sections
        assert "Returns" in sections


# ---------------------------------------------------------------------------
# AC3: Boundary detection — no content bleed
# ---------------------------------------------------------------------------


class TestBoundaryDetection:
    """Tests for section boundary detection preventing content bleed (AC: 3)."""

    def test_notes_colon_does_not_bleed_into_returns(self) -> None:
        """Notes: content does not bleed into Returns: section."""
        docstring = (
            "Summary.\n\nNotes:\n    Important note.\n\nReturns:\n    int: The value.\n"
        )
        content = _extract_section_content(docstring, "Returns")
        assert content is not None
        assert "Important note" not in content
        assert "int" in content

    def test_numpy_notes_boundary_stops_colon_returns_extraction(self) -> None:
        """Colon-format Returns extraction stops at NumPy Notes boundary."""
        docstring = (
            "Summary.\n\n"
            "Returns:\n    int: The value.\n\n"
            "Notes\n-----\n    Important note.\n"
        )
        content = _extract_section_content(docstring, "Returns")
        assert content is not None
        assert "Important note" not in content
        assert "int" in content

    def test_mixed_boundary_numpy_before_colon(self) -> None:
        """NumPy-underlined section correctly terminates preceding colon section."""
        docstring = (
            "Summary.\n\nArgs:\n    x: An argument.\n\nNotes\n-----\n    A note.\n"
        )
        content = _extract_section_content(docstring, "Args")
        assert content is not None
        assert "A note" not in content
        assert "x: An argument" in content


# ---------------------------------------------------------------------------
# AC4: Regression tests — existing Google-style unchanged
# ---------------------------------------------------------------------------


class TestGoogleStyleRegression:
    """Tests for existing Google-style behavior unchanged (AC: 4)."""

    def test_args_colon_still_recognized(self) -> None:
        """Args: still recognized after NumPy additions."""
        docstring = "Summary.\n\nArgs:\n    x: An int.\n"
        assert "Args" in _parse_sections(docstring)

    def test_returns_colon_still_recognized(self) -> None:
        """Returns: still recognized after NumPy additions."""
        docstring = "Summary.\n\nReturns:\n    int: The value.\n"
        assert "Returns" in _parse_sections(docstring)

    def test_raises_colon_still_recognized(self) -> None:
        """Raises: still recognized after NumPy additions."""
        docstring = "Summary.\n\nRaises:\n    ValueError: Bad input.\n"
        assert "Raises" in _parse_sections(docstring)

    def test_extract_section_content_unchanged_for_google(self) -> None:
        """_extract_section_content() works identically for Google format."""
        docstring = (
            "Summary.\n\nArgs:\n    x: An int.\n\nReturns:\n    int: The result.\n"
        )
        content = _extract_section_content(docstring, "Args")
        assert content is not None
        assert "x: An int" in content
        assert "int: The result" not in content
