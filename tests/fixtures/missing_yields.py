"""Fixture: generator yields but docstring has no Yields section.

Examples:
    Used by the test suite to verify missing-yields detection::

        source = Path("tests/fixtures/missing_yields.py").read_text()

See Also:
    [`tests.fixtures`][]: Other test fixture modules.
"""

from __future__ import annotations

from collections.abc import Generator


def stream_items(items: list[str]) -> Generator[str, None, None]:
    """Stream items one at a time.

    Args:
        items: List of items to stream.
    """
    for item in items:
        yield item
