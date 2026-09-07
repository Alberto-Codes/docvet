"""Test fixture that makes the griffe check report a required finding.

The ``phantom`` entry below documents a parameter the signature does not
have. Griffe's Google-style parser warns about it while loading the
module, which docvet reports as ``griffe-unknown-param`` (required).

This fault is not griffe's alone: the enrichment check independently
reports ``extra-param-in-docstring`` on the same function. So a finding
here does not by itself prove griffe ran. The ``test-griffe`` job in
``.github/workflows/test-action.yml`` gets that proof from its
``checks: "griffe"`` input, which runs the griffe subcommand on its own.
"""


def documented_phantom_parameter(actual: int) -> str:
    """Render a value as text.

    Args:
        actual: The value to render.
        phantom: A parameter that does not exist in the signature.

    Returns:
        The value rendered as text.
    """
    return str(actual)
