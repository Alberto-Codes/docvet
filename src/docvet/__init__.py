"""Docstring quality vetting for Python projects.

Provides a six-layer docstring quality model, implementing layers 3-6
(completeness, accuracy, rendering, and visibility). Use the ``docvet``
CLI command or import check functions programmatically.

Attributes:
    Finding: Re-exported from ``docvet.checks`` for convenience.

Examples:
    Run all checks on changed files::

        $ docvet check

    Run all checks on the entire codebase::

        $ docvet check --all

See Also:
    [`docvet.checks`][]: Check modules and the Finding dataclass.
    [`docvet.cli`][]: CLI entry point and subcommands.
"""

from __future__ import annotations

from docvet.checks import Finding

__all__ = ["Finding"]
