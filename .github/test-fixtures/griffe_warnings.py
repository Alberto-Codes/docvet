"""Test fixture whose docstring fault only the griffe check can see.

The ``phantom`` entry below documents a parameter the signature does not
have. Griffe's Google-style parser warns about it while loading the
module, which docvet reports as ``griffe-unknown-param``. No other check
inspects a docstring against its signature this way, so a finding here
proves the griffe check actually ran rather than being skipped.
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
