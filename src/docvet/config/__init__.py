"""Configuration reader and formatter for ``[tool.docvet]`` in pyproject.toml.

Loads and validates the ``[tool.docvet]`` configuration table from
``pyproject.toml``. Supports ``extend-exclude`` for additive pattern
merging on top of defaults or an explicit ``exclude`` list, and
``docstring-style`` for switching between Google and Sphinx/RST
conventions. Uses composable validation helpers
(``_validate_string_list``, ``_resolve_fail_warn``) to keep individual
parsers focused. Exposes ``EnrichmentConfig``, ``FreshnessConfig``, and
``PresenceConfig`` dataclasses with sensible defaults for all check
modules. ``EnrichmentConfig`` fields include ``require_returns``,
``require_param_agreement``, ``require_deprecation_notice``,
``exclude_args_kwargs``, ``check_trivial_docstrings``,
``require_return_type``, ``require_init_params``, ``check_extra_raises``,
``check_extra_yields``, ``check_extra_returns``, and other rule toggles.
Validation keys in ``_VALID_ENRICHMENT_KEYS`` are kept alphabetically.
``PresenceConfig`` fields include
``check_overload_docstrings`` for the overload-has-docstring rule.
``user_set_keys`` tracks which enrichment toggles were explicitly
set by the user (for sphinx auto-disable logic).

Provides ``format_config_toml`` and ``format_config_json`` for rendering
the effective configuration with source annotations. Formatting logic
is delegated to the ``_formatting`` submodule.

Attributes:
    load_config: Load and validate ``[tool.docvet]`` from pyproject.toml.
    format_config_toml: Render effective config as TOML.
    format_config_json: Render effective config as JSON.

Examples:
    Load configuration from the project root:

    ```python
    from docvet.config import load_config

    config = load_config()
    enrichment = config.enrichment
    ```

See Also:
    [`docvet.cli`][]: CLI entry point that loads config on startup.
    [`docvet.checks`][]: Check functions that consume config objects.
"""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "DocvetConfig",
    "EnrichmentConfig",
    "FreshnessConfig",
    "PresenceConfig",
    "format_config_json",
    "format_config_toml",
    "get_user_keys",
    "load_config",
]

# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FreshnessConfig:
    """Configuration for the freshness check.

    Attributes:
        drift_threshold (int): Maximum days since last docstring update
            before flagging drift. Defaults to 30.
        age_threshold (int): Maximum days since initial docstring creation
            before flagging age. Defaults to 90.

    Examples:
        Use defaults (30-day drift, 90-day age):

        ```python
        cfg = FreshnessConfig()
        ```

        Tighten thresholds for a fast-moving codebase:

        ```python
        cfg = FreshnessConfig(drift_threshold=14, age_threshold=60)
        ```
    """

    drift_threshold: int = 30
    age_threshold: int = 90


@dataclass(frozen=True)
class EnrichmentConfig:
    """Configuration for the enrichment check.

    Attributes:
        require_examples (list[str]): Symbol kinds that must have an
            ``Examples:`` section. Defaults to
            ``["class", "protocol", "dataclass", "enum"]``.
        require_raises (bool): Require ``Raises:`` sections. Defaults
            to ``True``.
        require_returns (bool): Require ``Returns:`` sections. Defaults
            to ``True``.
        require_yields (bool): Require ``Yields:`` sections. Defaults
            to ``True``.
        require_warns (bool): Require ``Warns:`` sections. Defaults
            to ``True``.
        require_receives (bool): Require ``Receives:`` sections.
            Defaults to ``True``.
        require_other_parameters (bool): Require ``Other Parameters:``
            sections. Defaults to ``True``.
        require_typed_attributes (bool): Require typed attribute format.
            Defaults to ``True``.
        require_cross_references (bool): Require ``See Also:`` in
            module docstrings. Defaults to ``True``.
        prefer_fenced_code_blocks (bool): Prefer fenced code blocks
            over indented blocks. Defaults to ``True``.
        require_attributes (bool): Require ``Attributes:`` sections.
            Defaults to ``True``.
        require_param_agreement (bool): Require parameter agreement
            between function signatures and ``Args:`` sections. Gates
            both ``missing-param-in-docstring`` and
            ``extra-param-in-docstring`` rules. Defaults to ``True``.
        require_deprecation_notice (bool): Require a deprecation notice
            in the docstring when the function uses deprecation patterns
            (``warnings.warn(..., DeprecationWarning)`` or
            ``@deprecated`` decorator). Defaults to ``True``.
        exclude_args_kwargs (bool): Exclude ``*args`` and ``**kwargs``
            from parameter agreement checks. Defaults to ``True``.
        check_trivial_docstrings (bool): Flag docstrings whose summary
            line trivially restates the symbol name without adding
            information. Defaults to ``True``.
        require_return_type (bool): Require return type documentation
            via either a typed ``Returns:`` entry or a ``->`` return
            annotation. Defaults to ``False`` (opt-in).
        require_init_params (bool): Require an ``Args:`` section
            documenting ``__init__`` parameters in either the class
            docstring or ``__init__`` docstring.
            Only fires on classes with an explicit ``__init__`` that
            takes parameters beyond ``self``. Defaults to ``False``
            (opt-in).
        check_extra_raises (bool): Flag documented exceptions not
            raised in the function body. Defaults to ``False``
            (opt-in) due to false positives on propagated exceptions
            from callees.
        check_extra_yields (bool): Flag ``Yields:`` sections when the
            function has no ``yield`` statement. Defaults to ``True``.
        check_extra_returns (bool): Flag ``Returns:`` sections when
            the function has no meaningful return. Defaults to
            ``True``.
        user_set_keys (frozenset[str]): Snake_case keys explicitly set
            by the user in ``[tool.docvet.enrichment]``. Populated during
            config parsing to distinguish user overrides from defaults.
            Used by sphinx auto-disable logic (Story 34.1).

    Examples:
        Use defaults (all rules enabled):

        ```python
        cfg = EnrichmentConfig()
        ```

        Disable yields checking for a project without generators:

        ```python
        cfg = EnrichmentConfig(require_yields=False)
        ```
    """

    require_examples: list[str] = field(
        default_factory=lambda: ["class", "protocol", "dataclass", "enum"]
    )
    require_raises: bool = True
    require_returns: bool = True
    require_yields: bool = True
    require_warns: bool = True
    require_receives: bool = True
    require_other_parameters: bool = True
    require_typed_attributes: bool = True
    require_cross_references: bool = True
    prefer_fenced_code_blocks: bool = True
    require_attributes: bool = True
    require_param_agreement: bool = True
    require_deprecation_notice: bool = True
    exclude_args_kwargs: bool = True
    check_trivial_docstrings: bool = True
    require_return_type: bool = False
    require_init_params: bool = False
    check_extra_raises: bool = False
    check_extra_yields: bool = True
    check_extra_returns: bool = True
    user_set_keys: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class PresenceConfig:
    """Configuration for the presence check.

    Attributes:
        enabled (bool): Whether the presence check is active.
            Defaults to ``True``.
        min_coverage (float): Minimum docstring coverage percentage
            (0.0–100.0). Enforced by the CLI layer (Story 28.2).
            Defaults to ``0.0`` (no threshold).
        ignore_init (bool): Skip ``__init__`` methods when checking
            for missing docstrings. Defaults to ``True``.
        ignore_magic (bool): Skip dunder methods (except
            ``__init__``) when checking for missing docstrings.
            Defaults to ``True``.
        ignore_private (bool): Skip single-underscore-prefixed
            symbols when checking for missing docstrings. Defaults
            to ``True``.
        check_overload_docstrings (bool): Flag ``@overload``-decorated
            functions that have docstrings. Defaults to ``True``.

    Examples:
        Use defaults (all ignore flags on, no threshold):

        ```python
        cfg = PresenceConfig()
        ```

        Require 95% coverage and check ``__init__`` methods:

        ```python
        cfg = PresenceConfig(min_coverage=95.0, ignore_init=False)
        ```
    """

    enabled: bool = True
    min_coverage: float = 0.0
    ignore_init: bool = True
    ignore_magic: bool = True
    ignore_private: bool = True
    check_overload_docstrings: bool = True


@dataclass(frozen=True)
class DocvetConfig:
    """Top-level docvet configuration.

    Attributes:
        src_root (str): Source directory relative to project root.
            Defaults to ``"."`` (auto-detects ``src/`` layout).
        package_name (str | None): Explicit package name override.
            Defaults to ``None`` (auto-detected).
        docstring_style (str): Docstring convention style. Either
            ``"google"`` (default) or ``"sphinx"`` (RST field-list
            syntax). Affects section detection, auto-disable rules,
            and griffe compatibility check behavior.
        exclude (list[str]): Directory names to exclude from checks.
            Defaults to ``["tests", "scripts"]``.
        fail_on (list[str]): Check names that cause exit code 1.
            Defaults to ``[]``.
        warn_on (list[str]): Check names reported without failing.
            Defaults to all five checks.
        freshness (FreshnessConfig): Freshness check settings.
        enrichment (EnrichmentConfig): Enrichment check settings.
        presence (PresenceConfig): Presence check settings.
        project_root (Path): Resolved project root directory.

    Examples:
        Load from ``pyproject.toml`` (typical usage):

        ```python
        from docvet.config import load_config

        cfg = load_config()
        ```

        Construct directly for programmatic use:

        ```python
        cfg = DocvetConfig(fail_on=["enrichment", "freshness"])
        ```
    """

    src_root: str = "."
    package_name: str | None = None
    docstring_style: str = "google"
    exclude: list[str] = field(default_factory=lambda: ["tests", "scripts"])
    fail_on: list[str] = field(default_factory=list)
    warn_on: list[str] = field(
        default_factory=lambda: [
            "presence",
            "freshness",
            "enrichment",
            "griffe",
            "coverage",
        ]
    )
    freshness: FreshnessConfig = field(default_factory=FreshnessConfig)
    enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)
    presence: PresenceConfig = field(default_factory=PresenceConfig)
    project_root: Path = field(default_factory=Path.cwd)


# ---------------------------------------------------------------------------
# Valid-key constants
# ---------------------------------------------------------------------------

_VALID_TOP_KEYS: frozenset[str] = frozenset(
    {
        "docstring-style",
        "src-root",
        "package-name",
        "exclude",
        "extend-exclude",
        "fail-on",
        "warn-on",
        "freshness",
        "enrichment",
        "presence",
    }
)

_VALID_DOCSTRING_STYLES: frozenset[str] = frozenset({"google", "sphinx"})

_VALID_FRESHNESS_KEYS: frozenset[str] = frozenset({"drift-threshold", "age-threshold"})

_VALID_ENRICHMENT_KEYS: frozenset[str] = frozenset(
    {
        "check-extra-raises",
        "check-extra-returns",
        "check-extra-yields",
        "check-trivial-docstrings",
        "exclude-args-kwargs",
        "prefer-fenced-code-blocks",
        "require-attributes",
        "require-cross-references",
        "require-deprecation-notice",
        "require-examples",
        "require-init-params",
        "require-other-parameters",
        "require-param-agreement",
        "require-raises",
        "require-receives",
        "require-return-type",
        "require-returns",
        "require-typed-attributes",
        "require-warns",
        "require-yields",
    }
)

_VALID_CHECK_NAMES: frozenset[str] = frozenset(
    {"enrichment", "freshness", "coverage", "griffe", "presence"}
)

_VALID_PRESENCE_KEYS: frozenset[str] = frozenset(
    {
        "check-overload-docstrings",
        "enabled",
        "ignore-init",
        "ignore-magic",
        "ignore-private",
        "min-coverage",
    }
)

_TOOL_SECTION = "[tool.docvet]"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _kebab_to_snake(key: str) -> str:
    """Convert a TOML kebab-case key to Python snake_case.

    Args:
        key: The kebab-case key string.

    Returns:
        The snake_case equivalent.
    """
    return key.replace("-", "_")


def _snake_to_kebab(key: str) -> str:
    """Convert a Python snake_case key to TOML kebab-case.

    Args:
        key: The snake_case key string.

    Returns:
        The kebab-case equivalent.
    """
    return key.replace("_", "-")


def _validate_keys(
    data: dict[str, object],
    valid_keys: frozenset[str],
    section: str,
) -> None:
    """Validate that all keys in *data* are recognised.

    Args:
        data: Parsed TOML section dictionary.
        valid_keys: Set of allowed key names (kebab-case).
        section: Human-readable section label for error messages.
    """
    unknown = sorted(k for k in data if k not in valid_keys)
    if unknown:
        keys_csv = ", ".join(unknown)
        valid_csv = ", ".join(sorted(valid_keys))
        msg = (
            f"docvet: unknown config keys in {section}: "
            f"{keys_csv}. Valid keys: {valid_csv}"
        )
        print(msg, file=sys.stderr)
        sys.exit(1)


def _validate_check_names(names: list[str], field_name: str) -> None:
    """Validate that every entry is a known check name.

    Args:
        names: List of check name strings to validate.
        field_name: Config field name for error messages.
    """
    invalid = sorted(n for n in names if n not in _VALID_CHECK_NAMES)
    if invalid:
        names_csv = ", ".join(invalid)
        valid_csv = ", ".join(sorted(_VALID_CHECK_NAMES))
        msg = (
            f"docvet: unknown checks in {field_name}: "
            f"{names_csv}. Valid checks: {valid_csv}"
        )
        print(msg, file=sys.stderr)
        sys.exit(1)


def _validate_type(
    value: object,
    expected: type,
    key: str,
    section: str,
) -> None:
    """Type-check a single config value.

    Rejects ``bool`` when *expected* is ``int`` (since ``bool`` is a
    subclass of ``int`` in Python). Used directly for scalar fields
    and composed by :func:`_validate_string_list` for list entries.

    Args:
        value: The value to check.
        expected: The expected Python type.
        key: Config key name for error messages.
        section: Section label for error messages.
    """
    # bool is a subclass of int — reject bools when expecting int.
    if expected is int and isinstance(value, bool):
        msg = f"docvet: '{key}' in {section} must be int, got bool"
        print(msg, file=sys.stderr)
        sys.exit(1)
    if not isinstance(value, expected):
        actual = type(value).__name__
        msg = f"docvet: '{key}' in {section} must be {expected.__name__}, got {actual}"
        print(msg, file=sys.stderr)
        sys.exit(1)


def _validate_string_list(
    data: dict[str, object],
    key: str,
    section: str,
    *,
    check_names: bool = False,
) -> None:
    """Validate that ``data[key]`` is a list of strings.

    Checks that the value is a ``list``, that every entry is a ``str``,
    and optionally that each string is a recognised check name.

    Args:
        data: Parsed config dictionary containing *key*.
        key: The snake_case key to validate inside *data*.
        section: Human-readable TOML section label (kebab-case) used in
            error messages passed to :func:`_validate_type`.
        check_names: When ``True``, additionally validate entries
            against :data:`_VALID_CHECK_NAMES` via
            :func:`_validate_check_names`.
    """
    _validate_type(data[key], list, section, _TOOL_SECTION)
    for entry in data[key]:  # type: ignore[union-attr]
        _validate_type(entry, str, section, _TOOL_SECTION)
    if check_names:
        _validate_check_names(data[key], section)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _find_pyproject(start: Path | None = None) -> Path | None:
    """Walk up from *start* to find the nearest ``pyproject.toml``.

    Args:
        start: Directory to begin searching from. Defaults to CWD.

    Returns:
        Path to the discovered file, or *None* if not found.
    """
    path = (start or Path.cwd()).resolve()
    try:
        while True:
            candidate = path / "pyproject.toml"
            if candidate.is_file():
                return candidate
            if (path / ".git").exists():
                return None
            parent = path.parent
            if parent == path:
                return None
            path = parent
    except OSError:
        return None


def _resolve_src_root(
    project_root: Path,
    configured: str | None,
) -> str:
    """Resolve the source root, applying the ``src/`` heuristic.

    Args:
        project_root: Directory containing the discovered pyproject.toml.
        configured: Explicitly configured ``src-root``, or *None*.

    Returns:
        The resolved source root string.
    """
    if configured is not None:
        return configured
    if (project_root / "src").is_dir():
        return "src"
    return "."


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------


def _parse_freshness(data: dict[str, object]) -> FreshnessConfig:
    """Parse and validate ``[tool.docvet.freshness]``.

    Args:
        data: Raw TOML dict for the freshness section.

    Returns:
        A validated :class:`FreshnessConfig`.
    """
    _validate_keys(data, _VALID_FRESHNESS_KEYS, "[tool.docvet.freshness]")
    section = "[tool.docvet.freshness]"
    kwargs: dict[str, object] = {}
    for key, value in data.items():
        _validate_type(value, int, key, section)
        kwargs[_kebab_to_snake(key)] = value
    return FreshnessConfig(**kwargs)  # type: ignore[arg-type]


def _parse_enrichment(data: dict[str, object]) -> EnrichmentConfig:
    """Parse and validate ``[tool.docvet.enrichment]``.

    Tracks which keys the user explicitly set (before defaults are
    applied) via ``user_set_keys`` on the returned config. This allows
    sphinx auto-disable logic to distinguish user overrides from defaults.

    Args:
        data: Raw TOML dict for the enrichment section.

    Returns:
        A validated :class:`EnrichmentConfig`.
    """
    _validate_keys(data, _VALID_ENRICHMENT_KEYS, "[tool.docvet.enrichment]")
    section = "[tool.docvet.enrichment]"
    # Record user-set keys BEFORE applying defaults (Story 34.1, NFR5).
    raw_user_keys = frozenset(_kebab_to_snake(k) for k in data)
    kwargs: dict[str, object] = {}
    for key, value in data.items():
        if key == "require-examples":
            _validate_type(value, list, key, section)
            for entry in value:  # type: ignore[union-attr]
                _validate_type(entry, str, key, section)
        else:
            _validate_type(value, bool, key, section)
        kwargs[_kebab_to_snake(key)] = value
    kwargs["user_set_keys"] = raw_user_keys
    return EnrichmentConfig(**kwargs)  # type: ignore[arg-type]


def _parse_presence(data: dict[str, object]) -> PresenceConfig:
    """Parse and validate ``[tool.docvet.presence]``.

    Args:
        data: Raw TOML dict for the presence section.

    Returns:
        A validated :class:`PresenceConfig`.
    """
    _validate_keys(data, _VALID_PRESENCE_KEYS, "[tool.docvet.presence]")
    section = "[tool.docvet.presence]"
    kwargs: dict[str, object] = {}
    for key, value in data.items():
        if key == "min-coverage":
            if isinstance(value, bool):
                msg = f"docvet: 'min-coverage' in {section} must be float, got bool"
                print(msg, file=sys.stderr)
                sys.exit(1)
            if isinstance(value, int | float):
                kwargs[_kebab_to_snake(key)] = float(value)
            else:
                actual = type(value).__name__
                msg = f"docvet: 'min-coverage' in {section} must be float, got {actual}"
                print(msg, file=sys.stderr)
                sys.exit(1)
        else:
            _validate_type(value, bool, key, section)
            kwargs[_kebab_to_snake(key)] = value
    return PresenceConfig(**kwargs)  # type: ignore[arg-type]


def _parse_docvet_section(
    data: dict[str, object],
) -> dict[str, object]:
    """Validate and parse a non-empty ``[tool.docvet]`` dict.

    Converts kebab-case keys to snake_case, validates types for all
    top-level keys, and delegates nested sections (``freshness``,
    ``enrichment``, ``presence``) to their respective parsers.
    Validates ``docstring-style`` against ``_VALID_DOCSTRING_STYLES``.
    List-of-string fields (``exclude``, ``extend-exclude``,
    ``fail-on``, ``warn-on``) are validated via
    :func:`_validate_string_list`.

    Args:
        data: Mutable copy of the raw TOML ``[tool.docvet]`` section.

    Returns:
        Processed dict ready for :class:`DocvetConfig` construction.
    """
    _validate_keys(data, _VALID_TOP_KEYS, _TOOL_SECTION)

    converted: dict[str, object] = {_kebab_to_snake(k): v for k, v in data.items()}

    freshness_data = converted.pop("freshness", None)
    enrichment_data = converted.pop("enrichment", None)
    presence_data = converted.pop("presence", None)

    if freshness_data is not None:
        _validate_type(freshness_data, dict, "freshness", _TOOL_SECTION)
        converted["freshness"] = _parse_freshness(freshness_data)  # type: ignore[arg-type]

    if enrichment_data is not None:
        _validate_type(enrichment_data, dict, "enrichment", _TOOL_SECTION)
        converted["enrichment"] = _parse_enrichment(enrichment_data)  # type: ignore[arg-type]

    if presence_data is not None:
        _validate_type(presence_data, dict, "presence", _TOOL_SECTION)
        converted["presence"] = _parse_presence(presence_data)  # type: ignore[arg-type]

    if "docstring_style" in converted:
        _validate_type(
            converted["docstring_style"], str, "docstring-style", _TOOL_SECTION
        )
        style = converted["docstring_style"]
        if style not in _VALID_DOCSTRING_STYLES:
            valid_csv = ", ".join(sorted(_VALID_DOCSTRING_STYLES))
            msg = (
                f"docvet: invalid docstring-style '{style}' in {_TOOL_SECTION}. "
                f"Valid options: {valid_csv}"
            )
            print(msg, file=sys.stderr)
            sys.exit(1)
    if "src_root" in converted:
        _validate_type(converted["src_root"], str, "src-root", _TOOL_SECTION)
    if "package_name" in converted:
        _validate_type(converted["package_name"], str, "package-name", _TOOL_SECTION)
    if "exclude" in converted:
        _validate_string_list(converted, "exclude", "exclude")
    if "extend_exclude" in converted:
        _validate_string_list(converted, "extend_exclude", "extend-exclude")
    if "fail_on" in converted:
        _validate_string_list(converted, "fail_on", "fail-on", check_names=True)
    if "warn_on" in converted:
        _validate_string_list(converted, "warn_on", "warn-on", check_names=True)

    return converted


# ---------------------------------------------------------------------------
# Load helpers
# ---------------------------------------------------------------------------


def _read_docvet_toml(pyproject_path: Path) -> dict[str, object]:
    """Read ``pyproject.toml`` and return the raw ``[tool.docvet]`` dict.

    Args:
        pyproject_path: Path to the ``pyproject.toml`` file.

    Returns:
        The raw TOML dict for ``[tool.docvet]``, or an empty dict when
        the section is absent.
    """
    with open(pyproject_path, "rb") as f:
        toml_data = tomllib.load(f)
    tool_section = toml_data.get("tool")
    if tool_section is None:
        return {}
    if not isinstance(tool_section, dict):
        print(
            "docvet: [tool] in pyproject.toml must be a table",
            file=sys.stderr,
        )
        sys.exit(1)
    docvet_section = tool_section.get("docvet")
    if docvet_section is None:
        return {}
    if not isinstance(docvet_section, dict):
        print(
            "docvet: [tool.docvet] in pyproject.toml must be a table",
            file=sys.stderr,
        )
        sys.exit(1)
    return docvet_section


def _find_pyproject_path(path: Path | None) -> Path | None:
    """Resolve an explicit or discovered ``pyproject.toml`` path.

    When *path* is given, validates it exists; otherwise falls back
    to :func:`_find_pyproject` for upward directory traversal.

    Args:
        path: Explicit path provided by the caller, or *None* for
            automatic discovery.

    Returns:
        Resolved path to ``pyproject.toml``, or *None* when discovery
        finds nothing.

    Raises:
        FileNotFoundError: If an explicit *path* does not exist.
    """
    if path is not None:
        if not path.is_file():
            raise FileNotFoundError(path)
        return path
    return _find_pyproject()


def _resolve_fail_warn(
    parsed: dict[str, object],
    defaults: DocvetConfig,
) -> tuple[list[str], list[str]]:
    """Resolve ``fail-on`` and ``warn-on`` lists from parsed config.

    Extracts both lists from *parsed* with fallback to *defaults*.
    Detects overlap and emits a stderr warning per overlapping check
    (only when ``warn-on`` was explicitly set). Filters ``warn-on``
    to exclude items already present in ``fail-on``.

    Args:
        parsed: Validated config dict (snake_case keys).
        defaults: Default :class:`DocvetConfig` for fallback values.

    Returns:
        A ``(fail_on, warn_on)`` tuple ready for
        :class:`DocvetConfig` construction.
    """
    raw_fail = parsed.get("fail_on")
    fail_on: list[str] = (
        [str(x) for x in raw_fail]
        if isinstance(raw_fail, list)
        else list(defaults.fail_on)
    )
    raw_warn = parsed.get("warn_on")
    warn_on: list[str] = (
        [str(x) for x in raw_warn]
        if isinstance(raw_warn, list)
        else list(defaults.warn_on)
    )
    fail_on_set = set(fail_on)
    if "warn_on" in parsed:
        for check in warn_on:
            if check in fail_on_set:
                print(
                    f"docvet: '{check}' appears in both fail-on and warn-on; using fail-on",
                    file=sys.stderr,
                )
    return fail_on, [c for c in warn_on if c not in fail_on_set]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_user_keys(
    path: Path | None = None,
) -> tuple[dict[str, object], Path | None]:
    """Return the raw ``[tool.docvet]`` dict and the pyproject.toml path.

    Exposes the user's configuration as-is (kebab-case keys, no
    validation or parsing) so callers can distinguish user-set values
    from defaults.

    Args:
        path: Explicit path to a ``pyproject.toml``. When *None*,
            discovery walks up from CWD.

    Returns:
        A tuple of ``(raw_dict, pyproject_path)``. *raw_dict* is the
        ``[tool.docvet]`` table (empty dict if absent). *pyproject_path*
        is the resolved path, or *None* when no file was found.
    """
    pyproject_path = _find_pyproject_path(path)
    if pyproject_path is None:
        return {}, None
    return _read_docvet_toml(pyproject_path), pyproject_path


from ._formatting import format_config_json, format_config_toml  # noqa: E402


def load_config(path: Path | None = None) -> DocvetConfig:
    """Load docvet configuration from ``pyproject.toml``.

    Merges ``extend-exclude`` patterns on top of the resolved base
    exclude list (explicit ``exclude`` or defaults) before constructing
    the final :class:`DocvetConfig`. Reads ``docstring-style`` and
    passes it through to the config. Delegates ``fail-on``/``warn-on``
    resolution (including overlap detection and filtering) to
    :func:`_resolve_fail_warn`. Nested ``presence`` section is parsed
    via :func:`_parse_presence`.

    Args:
        path: Explicit path to a ``pyproject.toml``. When *None*,
            discovery walks up from CWD.

    Returns:
        A fully resolved :class:`DocvetConfig`.
    """
    pyproject_path = _find_pyproject_path(path)
    if pyproject_path is not None:
        project_root = pyproject_path.parent.resolve()
        data = _read_docvet_toml(pyproject_path)
        parsed: dict[str, object] = _parse_docvet_section(data) if data else {}
    else:
        project_root = Path.cwd().resolve()
        parsed = {}

    # Use dataclass defaults as single source of truth for omitted keys.
    defaults = DocvetConfig()

    configured_src = parsed.get("src_root")
    resolved_src_root = _resolve_src_root(
        project_root,
        configured_src if isinstance(configured_src, str) else None,
    )

    fail_on, warn_on = _resolve_fail_warn(parsed, defaults)

    raw_pkg = parsed.get("package_name")
    raw_style = parsed.get("docstring_style")
    raw_exclude = parsed.get("exclude")
    raw_extend_exclude = parsed.get("extend_exclude")
    raw_freshness = parsed.get("freshness")
    raw_enrichment = parsed.get("enrichment")
    raw_presence = parsed.get("presence")

    base_exclude: list[str] = (
        [str(x) for x in raw_exclude]
        if isinstance(raw_exclude, list)
        else list(defaults.exclude)
    )
    if isinstance(raw_extend_exclude, list):
        base_exclude = base_exclude + [str(x) for x in raw_extend_exclude]

    return DocvetConfig(
        src_root=resolved_src_root,
        package_name=raw_pkg if isinstance(raw_pkg, str) else None,
        docstring_style=raw_style if isinstance(raw_style, str) else "google",
        exclude=base_exclude,
        fail_on=fail_on,
        warn_on=warn_on,
        freshness=(
            raw_freshness
            if isinstance(raw_freshness, FreshnessConfig)
            else FreshnessConfig()
        ),
        enrichment=(
            raw_enrichment
            if isinstance(raw_enrichment, EnrichmentConfig)
            else EnrichmentConfig()
        ),
        presence=(
            raw_presence
            if isinstance(raw_presence, PresenceConfig)
            else PresenceConfig()
        ),
        project_root=project_root,
    )
