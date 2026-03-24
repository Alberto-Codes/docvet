"""Rule catalog for the docvet MCP server.

Static catalog of all 32 docvet rules with descriptions, categories,
fix guidance, and examples. Used by the ``docvet_rules`` MCP tool
to provide rule discovery for AI agents.

Attributes:
    _RULE_CATALOG: Complete list of rule entries across all 5 checks.
    _RULE_TO_CHECK: Mapping from rule name to owning check module.

See Also:
    [`docvet.mcp`][]: MCP server and tool handlers.

Examples:
    Look up which check owns a rule:

    ```python
    from docvet.mcp._catalog import _RULE_TO_CHECK

    check = _RULE_TO_CHECK["missing-raises"]  # "enrichment"
    ```
"""

from __future__ import annotations

from typing import TypedDict


class RuleCatalogEntry(TypedDict):
    """A single entry in the docvet rule catalog.

    Attributes:
        name (str): The rule identifier (e.g. ``missing-raises``).
        check (str): The check module that owns this rule.
        description (str): Human-readable description of what the rule detects.
        category (str): Severity category (``required``, ``recommended``,
            or ``scaffold``).
        guidance (str): Prescriptive fix guidance for the rule.
        fix_example (str | None): Optional code example showing the fix.
    """

    name: str
    check: str
    description: str
    category: str
    guidance: str
    fix_example: str | None


_RULE_CATALOG: list[RuleCatalogEntry] = [
    {
        "name": "missing-docstring",
        "check": "presence",
        "description": "Public symbol lacks a docstring.",
        "category": "required",
        "guidance": (
            "Add a Google-style docstring with a one-line summary ending in a"
            " period, followed by a detailed description."
        ),
        "fix_example": '"""One-line summary.\n\nDetailed description.\n"""',
    },
    {
        "name": "overload-has-docstring",
        "check": "presence",
        "description": (
            "@overload-decorated function has a docstring — document the"
            " implementation instead."
        ),
        "category": "required",
        "guidance": (
            "Remove the docstring from the @overload-decorated function and"
            " document the implementation function instead."
        ),
        "fix_example": (
            "@overload\ndef connect(address: str) -> TCPConnection: ...\n\n"
            "def connect(address):\n"
            '    """Connect to a server.\n\n'
            "    Args:\n"
            '        address: Hostname string or (host, port) tuple.\n    """'
        ),
    },
    {
        "name": "missing-raises",
        "check": "enrichment",
        "description": "Function raises an exception not documented in Raises section.",
        "category": "required",
        "guidance": (
            "Add a Raises: section listing each exception type and the"
            " condition that triggers it."
        ),
        "fix_example": "Raises:\n    ValueError: If the input is negative.",
    },
    {
        "name": "missing-returns",
        "check": "enrichment",
        "description": "Function returns a value but has no Returns section.",
        "category": "required",
        "guidance": (
            "Add a Returns: section describing the type and meaning of the"
            " return value."
        ),
        "fix_example": "Returns:\n    The parsed configuration as a dictionary.",
    },
    {
        "name": "missing-yields",
        "check": "enrichment",
        "description": "Generator function lacks a Yields section.",
        "category": "required",
        "guidance": (
            "Add a Yields: section describing what values the generator produces."
        ),
        "fix_example": (
            "Yields:\n    Row data as a dictionary with column names as keys."
        ),
    },
    {
        "name": "missing-receives",
        "check": "enrichment",
        "description": "Generator function using send() lacks a Receives section.",
        "category": "required",
        "guidance": (
            "Add a Receives: section documenting values accepted via .send()."
        ),
        "fix_example": ("Receives:\n    Numeric value to add to the running total."),
    },
    {
        "name": "missing-warns",
        "check": "enrichment",
        "description": "Function issues warnings not documented in Warns section.",
        "category": "required",
        "guidance": (
            "Add a Warns: section listing each warning category and the condition."
        ),
        "fix_example": ("Warns:\n    UserWarning: If timeout is less than 5 seconds."),
    },
    {
        "name": "missing-deprecation",
        "check": "enrichment",
        "description": (
            "Function uses deprecation patterns (warnings.warn with"
            " DeprecationWarning or @deprecated decorator) but has no"
            " deprecation notice in docstring."
        ),
        "category": "required",
        "guidance": (
            "Add the word 'deprecated' somewhere in the docstring"
            " (case-insensitive). Common formats: Google-style"
            " 'Deprecated:' section, Sphinx '.. deprecated::' directive,"
            " or inline mention."
        ),
        "fix_example": (
            "Deprecated:\n    Use :func:`new_func` instead. Will be removed in v3.0."
        ),
    },
    {
        "name": "missing-other-parameters",
        "check": "enrichment",
        "description": "Function has *args or **kwargs not documented in Other Parameters.",
        "category": "required",
        "guidance": (
            "Add an Other Parameters: section documenting *args and/or **kwargs."
        ),
        "fix_example": (
            "Other Parameters:\n    **kwargs: Arbitrary keyword arguments"
            " passed to the\n        underlying handler."
        ),
    },
    {
        "name": "missing-attributes",
        "check": "enrichment",
        "description": "Class or module has undocumented public attributes.",
        "category": "required",
        "guidance": (
            "Add an Attributes: section listing all public instance attributes"
            " with types and descriptions."
        ),
        "fix_example": (
            "Attributes:\n    name (str): The user's display name.\n"
            "    email (str): The user's email address."
        ),
    },
    {
        "name": "missing-typed-attributes",
        "check": "enrichment",
        "description": "Attributes section uses untyped style instead of typed.",
        "category": "recommended",
        "guidance": "Use typed attribute format: name (type): description.",
        "fix_example": (
            "Attributes:\n    host (str): The server hostname.\n"
            "    port (int): The server port number."
        ),
    },
    {
        "name": "missing-examples",
        "check": "enrichment",
        "description": "Public symbol lacks an Examples section.",
        "category": "recommended",
        "guidance": (
            "Add an Examples: section with a brief description followed by a"
            " fenced code block using ```python."
        ),
        "fix_example": (
            "Examples:\n    Create a widget with default settings:\n\n"
            "    ```python\n    widget = Widget()\n"
            "    assert widget.is_active\n    ```"
        ),
    },
    {
        "name": "missing-cross-references",
        "check": "enrichment",
        "description": (
            "Module missing See Also section, or existing See Also entries"
            " lack cross-reference link syntax."
        ),
        "category": "recommended",
        "guidance": (
            "Add a See Also: section using mkdocstrings cross-reference"
            " syntax: [`fully.qualified.Name`][]. Each entry uses"
            " bracket-backtick-bracket format for linkable references."
        ),
        "fix_example": (
            "See Also:\n    [`mypackage.Config`][]: Application"
            " configuration.\n    [`mypackage.utils`][]: Utility functions."
        ),
    },
    {
        "name": "prefer-fenced-code-blocks",
        "check": "enrichment",
        "description": "Docstring uses indented code blocks instead of fenced.",
        "category": "recommended",
        "guidance": (
            "Replace >>> doctest or :: reST indented code blocks with fenced"
            " ```python blocks."
        ),
        "fix_example": (
            "Examples:\n    Run the check:\n\n    ```python\n"
            "    result = check(data)\n    ```"
        ),
    },
    {
        "name": "stale-signature",
        "check": "freshness",
        "description": "Function signature changed without docstring update.",
        "category": "required",
        "guidance": (
            "Update the docstring Args, Returns, and Raises sections to match"
            " the changed function signature."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-body",
        "check": "freshness",
        "description": "Function body changed without docstring update.",
        "category": "recommended",
        "guidance": (
            "Review and update the docstring description and sections to"
            " reflect the changed function behavior."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-import",
        "check": "freshness",
        "description": "Import changed near symbol without docstring update.",
        "category": "recommended",
        "guidance": (
            "Review the docstring for references to changed imports and update"
            " accordingly."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-drift",
        "check": "freshness",
        "description": "Docstring has not been updated since significant code changes.",
        "category": "recommended",
        "guidance": (
            "Review and refresh the docstring to reflect cumulative code"
            " changes since the last docstring edit."
        ),
        "fix_example": None,
    },
    {
        "name": "stale-age",
        "check": "freshness",
        "description": "Docstring has not been updated for an extended period.",
        "category": "recommended",
        "guidance": (
            "Review and confirm the docstring still accurately describes the"
            " symbol's current behavior."
        ),
        "fix_example": None,
    },
    {
        "name": "missing-init",
        "check": "coverage",
        "description": "Directory with Python files lacks __init__.py for mkdocs discovery.",
        "category": "required",
        "guidance": (
            "Create an __init__.py file with a module docstring in the directory."
        ),
        "fix_example": None,
    },
    {
        "name": "missing-param-in-docstring",
        "check": "enrichment",
        "description": "Function signature parameter not documented in Args section.",
        "category": "required",
        "guidance": (
            "Add the missing parameter to the Args: section with a type"
            " annotation and description."
        ),
        "fix_example": "Args:\n    name (str): The user's display name.",
    },
    {
        "name": "extra-param-in-docstring",
        "check": "enrichment",
        "description": "Args section documents a parameter not in the function signature.",
        "category": "required",
        "guidance": (
            "Remove the stale parameter entry from the Args: section, or"
            " rename it to match the current signature."
        ),
        "fix_example": (
            "Args:\n    name (str): The user's display name.\n"
            "    # Remove entries for parameters no longer in the signature."
        ),
    },
    {
        "name": "griffe-unknown-param",
        "check": "griffe",
        "description": "Griffe reports a parameter not matching the function signature.",
        "category": "required",
        "guidance": (
            "Remove or rename the documented parameter in the Args: section to"
            " match the actual function signature."
        ),
        "fix_example": "Args:\n    name (str): The user's display name.",
    },
    {
        "name": "griffe-missing-type",
        "check": "griffe",
        "description": "Griffe reports a missing type annotation in docstring.",
        "category": "recommended",
        "guidance": (
            "Add parenthesized type annotations to parameter entries:"
            " name (type): description."
        ),
        "fix_example": "Args:\n    name (str): The user's display name.",
    },
    {
        "name": "griffe-format-warning",
        "check": "griffe",
        "description": "Griffe reports a formatting issue in the docstring.",
        "category": "recommended",
        "guidance": (
            "Fix docstring formatting: ensure proper indentation (4 spaces),"
            " correct section headers, and valid Google-style syntax."
        ),
        "fix_example": "Args:\n    data (dict): The input data to process.",
    },
    {
        "name": "extra-raises-in-docstring",
        "check": "enrichment",
        "description": (
            "Docstring documents exceptions not raised in the function body."
        ),
        "category": "recommended",
        "guidance": (
            "This rule is opt-in (check-extra-raises = true) because"
            " documenting propagated exceptions from callees is common"
            " and correct. If the exception is genuinely stale, remove"
            " it from the Raises: section."
        ),
        "fix_example": "Raises:\n    ValueError: If the input is invalid.",
    },
    {
        "name": "extra-yields-in-docstring",
        "check": "enrichment",
        "description": (
            "Docstring has a Yields: section but the function does not yield."
        ),
        "category": "recommended",
        "guidance": (
            "Remove the Yields: section or convert the function to a"
            " generator. If refactored from a generator, replace Yields:"
            " with Returns:."
        ),
        "fix_example": "Returns:\n    A list of processed items.",
    },
    {
        "name": "extra-returns-in-docstring",
        "check": "enrichment",
        "description": (
            "Docstring has a Returns: section but the function does not return a value."
        ),
        "category": "recommended",
        "guidance": (
            "Remove the Returns: section if the function has no meaningful"
            " return value, or add the missing return statement."
        ),
        "fix_example": ('def save(data: dict) -> None:\n    """Save data to disk."""'),
    },
    {
        "name": "trivial-docstring",
        "check": "enrichment",
        "description": (
            "Docstring summary line restates the symbol name without"
            " adding information."
        ),
        "category": "recommended",
        "guidance": (
            "Replace the summary line with a description that adds"
            " information beyond what the name already communicates,"
            " such as behavior, constraints, or return value."
        ),
        "fix_example": (
            'def get_user():\n    """Fetch the active user from the'
            ' session cache by their ID."""'
        ),
    },
    {
        "name": "missing-return-type",
        "check": "enrichment",
        "description": (
            "Returns section has no type and function has no return annotation."
        ),
        "category": "recommended",
        "guidance": (
            "Add a type to the Returns entry (e.g., 'int: The count.')"
            " or add a -> return annotation to the function signature."
        ),
        "fix_example": "Returns:\n    int: The computed value.",
    },
    {
        "name": "undocumented-init-params",
        "check": "enrichment",
        "description": (
            "Class __init__ takes parameters but neither class nor"
            " __init__ docstring has an Args section."
        ),
        "category": "required",
        "guidance": (
            "Add an Args: section to either the class docstring or"
            " the __init__ docstring listing all constructor parameters"
            " with descriptions."
        ),
        "fix_example": (
            "Args:\n    host (str): The server hostname.\n"
            "    port (int): The server port number."
        ),
    },
    {
        "name": "scaffold-incomplete",
        "check": "enrichment",
        "description": (
            "Scaffolded placeholder section still contains TODO marker"
            " and needs to be filled in by the developer."
        ),
        "category": "scaffold",
        "guidance": (
            "Replace the TODO placeholder in the scaffolded section with"
            " actual documentation content."
        ),
        "fix_example": "Raises:\n    ValueError: If the input is negative.",
    },
]

_RULE_TO_CHECK: dict[str, str] = {r["name"]: r["check"] for r in _RULE_CATALOG}
