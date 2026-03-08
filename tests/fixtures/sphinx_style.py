"""Sphinx/RST-style fixture file for testing sphinx mode.

A sample module using Sphinx/RST field-list syntax in docstrings.
This file is used to verify sphinx mode produces correct findings.

.. seealso::
   :py:mod:`tests.fixtures`
"""

from __future__ import annotations


def complete_function(name: str, count: int) -> str:
    """Process the given input completely.

    :param name: The name to process.
    :type name: str
    :param count: Number of repetitions.
    :type count: int
    :returns: The processed result string.
    :rtype: str
    :raises ValueError: If name is empty.

    >>> complete_function("hello", 2)
    'hellohello'
    """
    if not name:
        raise ValueError("name cannot be empty")
    return name * count


def missing_raises(value: int) -> None:
    """Validate the given value.

    :param value: The value to validate.
    """
    if value < 0:
        raise ValueError("value must be non-negative")


class SphinxClass:
    """A class with Sphinx-style docstrings.

    :ivar name: The instance name.
    :cvar count: The class-level counter.
    """

    count: int = 0

    def __init__(self, name: str) -> None:
        """Initialize the instance.

        :param name: The instance name.
        """
        self.name = name
