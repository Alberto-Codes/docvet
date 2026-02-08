"""Fixture: generator yields but docstring has no Yields section."""

from __future__ import annotations

from collections.abc import Generator


def stream_items(items: list[str]) -> Generator[str, None, None]:
    """Stream items one at a time.

    Args:
        items: List of items to stream.
    """
    for item in items:
        yield item
