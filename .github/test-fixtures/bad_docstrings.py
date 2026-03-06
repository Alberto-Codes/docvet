"""Test fixture with known docstring issues for CI action verification."""


def raises_without_docs(value: int) -> str:
    """Convert value to string."""
    if value < 0:
        raise ValueError("negative")
    return str(value)


class UndocumentedAttrs:
    """A class with undocumented attributes."""

    def __init__(self) -> None:
        self.name = "test"
        self.value = 42
