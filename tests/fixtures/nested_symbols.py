"""Fixture: nested symbols for comprehensive AST extraction tests."""

from __future__ import annotations


def top_level_function(x: int) -> int:
    """A top-level function.

    Args:
        x: Input value.

    Returns:
        The value doubled.
    """
    return x * 2


class OuterClass:
    """A class with methods and nested classes."""

    def __init__(self, value: int) -> None:
        """Initialize OuterClass.

        Args:
            value: The initial value.
        """
        self.value = value

    def regular_method(self) -> int:
        """Return the stored value."""
        return self.value

    @property
    def computed(self) -> int:
        """The computed property."""
        return self.value * 2

    @staticmethod
    def static_helper() -> str:
        """A static method helper."""
        return "static"

    @classmethod
    def from_string(cls, text: str) -> OuterClass:
        """Create from a string.

        Args:
            text: A numeric string.

        Returns:
            A new OuterClass instance.
        """
        return cls(int(text))

    class InnerClass:
        """A nested class inside OuterClass."""

        def inner_method(self) -> None:
            """Do nothing."""


async def async_function(n: int) -> list[int]:
    """An async top-level function.

    Args:
        n: Count of items.

    Returns:
        A list of integers.
    """
    return list(range(n))


def decorated_multiline(
    first: str,
    second: int,
    third: bool = False,
) -> str:
    """A function with a multi-line signature.

    Args:
        first: First argument.
        second: Second argument.
        third: Third argument.

    Returns:
        A formatted string.
    """
    return f"{first}-{second}-{third}"


def no_docstring_function():
    x = 1
    return x + 1
