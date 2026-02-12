"""Module with known-bad docstrings for griffe compatibility testing."""


def untyped_params(x, y, z):
    """Process three values without type annotations.

    Args:
        x: First value.
        y: Second value.
        z: Third value.
    """


def phantom_param(real_param: str) -> None:
    """Do something with parameters.

    Args:
        real_param: A real parameter.
        ghost_param: This parameter does not exist in the signature.
    """


def bad_format(x: int, y: str) -> None:  # noqa: D417
    """Process values with malformed parameter entries.

    Args:
        x - First value uses dash instead of colon.
        y - Second value also uses dash.
    """


def well_documented(name: str, count: int) -> str:
    """Format a greeting message.

    Args:
        name: The person's name.
        count: Number of greetings.

    Returns:
        A formatted greeting string.
    """
    return f"Hello {name}! " * count
