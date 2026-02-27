"""Tests for the Finding dataclass."""

from __future__ import annotations

import pytest

from docvet.checks import Finding


def test_finding_can_be_constructed_with_all_fields():
    """Test that Finding can be constructed with all 6 required fields."""
    finding = Finding(
        file="src/example.py",
        line=42,
        symbol="validate_input",
        rule="missing-raises",
        message="Function 'validate_input' raises ValueError but has no Raises: section",
        category="required",
    )

    assert finding.file == "src/example.py"
    assert finding.line == 42
    assert finding.symbol == "validate_input"
    assert finding.rule == "missing-raises"
    expected_message = (
        "Function 'validate_input' raises ValueError but has no Raises: section"
    )
    assert finding.message == expected_message
    assert finding.category == "required"


def test_finding_is_frozen_raises_on_mutation():
    """Test that Finding is frozen and raises FrozenInstanceError on mutation attempts."""
    from dataclasses import FrozenInstanceError

    finding = Finding(
        file="src/example.py",
        line=10,
        symbol="my_function",
        rule="missing-yields",
        message="Generator function missing Yields section",
        category="required",
    )

    with pytest.raises(FrozenInstanceError):
        finding.rule = "different-rule"  # type: ignore[misc]


def test_finding_is_hashable():
    """Test that Finding instances are hashable and can be added to sets/dicts."""
    finding1 = Finding(
        file="src/example.py",
        line=5,
        symbol="process_data",
        rule="missing-warns",
        message="Function calls warnings.warn but has no Warns: section",
        category="required",
    )
    finding2 = Finding(
        file="src/another.py",
        line=20,
        symbol="DataClass",
        rule="missing-attributes",
        message="Dataclass has 3 fields but has no Attributes: section",
        category="required",
    )

    # Should be able to add to set
    findings_set = {finding1, finding2}
    assert len(findings_set) == 2
    assert finding1 in findings_set
    assert finding2 in findings_set

    # Should be able to use as dict key
    findings_dict = {finding1: "first", finding2: "second"}
    assert findings_dict[finding1] == "first"
    assert findings_dict[finding2] == "second"


def test_finding_equality_works_correctly():
    """Test that Finding instances with same values are equal."""
    finding1 = Finding(
        file="src/test.py",
        line=100,
        symbol="test_func",
        rule="missing-examples",
        message="Class lacks Examples section",
        category="recommended",
    )
    finding2 = Finding(
        file="src/test.py",
        line=100,
        symbol="test_func",
        rule="missing-examples",
        message="Class lacks Examples section",
        category="recommended",
    )
    finding3 = Finding(
        file="src/test.py",
        line=100,
        symbol="test_func",
        rule="missing-examples",
        message="Different message",
        category="recommended",
    )

    # Identical findings should be equal
    assert finding1 == finding2
    assert hash(finding1) == hash(finding2)

    # Different findings should not be equal
    assert finding1 != finding3
    assert hash(finding1) != hash(finding3)


def test_finding_exports_finding_class():
    """Test that __all__ includes Finding class."""
    from docvet import checks

    assert hasattr(checks, "__all__")
    assert "Finding" in checks.__all__
    assert "Finding" in dir(checks)


def test_finding_normalizes_backslash_paths_to_forward_slashes():
    """Test that Finding normalizes backslash path separators to forward slashes."""
    finding = Finding(
        file="src\\docvet\\checks\\enrichment.py",
        line=1,
        symbol="test",
        rule="missing-raises",
        message="test message",
        category="required",
    )
    assert finding.file == "src/docvet/checks/enrichment.py"


def test_finding_normalizes_mixed_separator_paths():
    """Test that Finding normalizes paths with mixed forward and backslash separators."""
    finding = Finding(
        file="src/docvet\\checks/enrichment.py",
        line=1,
        symbol="test",
        rule="missing-raises",
        message="test message",
        category="required",
    )
    assert finding.file == "src/docvet/checks/enrichment.py"


def test_finding_preserves_forward_slash_paths():
    """Test that Finding preserves paths already using forward slashes."""
    finding = Finding(
        file="src/docvet/checks/enrichment.py",
        line=1,
        symbol="test",
        rule="missing-raises",
        message="test message",
        category="required",
    )
    assert finding.file == "src/docvet/checks/enrichment.py"


def test_finding_rejects_empty_file():
    """Test that Finding raises ValueError for empty file path."""
    with pytest.raises(ValueError, match="file must be non-empty"):
        Finding(
            file="",
            line=1,
            symbol="test",
            rule="missing-raises",
            message="test message",
            category="required",
        )


def test_finding_rejects_negative_line():
    """Test that Finding raises ValueError for negative line numbers."""
    with pytest.raises(ValueError, match="line must be >= 1"):
        Finding(
            file="test.py",
            line=-1,
            symbol="test",
            rule="missing-raises",
            message="test message",
            category="required",
        )


def test_finding_rejects_zero_line():
    """Test that Finding raises ValueError for zero line number."""
    with pytest.raises(ValueError, match="line must be >= 1"):
        Finding(
            file="test.py",
            line=0,
            symbol="test",
            rule="missing-raises",
            message="test message",
            category="required",
        )


def test_finding_rejects_empty_symbol():
    """Test that Finding raises ValueError for empty symbol."""
    with pytest.raises(ValueError, match="symbol must be non-empty"):
        Finding(
            file="test.py",
            line=1,
            symbol="",
            rule="missing-raises",
            message="test message",
            category="required",
        )


def test_finding_rejects_empty_rule():
    """Test that Finding raises ValueError for empty rule."""
    with pytest.raises(ValueError, match="rule must be non-empty"):
        Finding(
            file="test.py",
            line=1,
            symbol="test",
            rule="",
            message="test message",
            category="required",
        )


def test_finding_rejects_empty_message():
    """Test that Finding raises ValueError for empty message."""
    with pytest.raises(ValueError, match="message must be non-empty"):
        Finding(
            file="test.py",
            line=1,
            symbol="test",
            rule="missing-raises",
            message="",
            category="required",
        )


def test_finding_rejects_invalid_category():
    """Test that Finding raises ValueError for invalid category values."""
    with pytest.raises(
        ValueError, match='category must be "required" or "recommended"'
    ):
        Finding(
            file="test.py",
            line=1,
            symbol="test",
            rule="missing-raises",
            message="test message",
            category="invalid",  # type: ignore[arg-type]
        )
