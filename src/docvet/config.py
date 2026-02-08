"""Configuration reader for ``[tool.docvet]`` in pyproject.toml."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Frozen dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FreshnessConfig:
    """Configuration for the freshness check."""

    drift_threshold: int = 30
    age_threshold: int = 90


@dataclass(frozen=True)
class EnrichmentConfig:
    """Configuration for the enrichment check."""

    require_examples: list[str] = field(
        default_factory=lambda: ["class", "protocol", "dataclass", "enum"]
    )
    require_raises: bool = True
    require_yields: bool = True
    require_warns: bool = True
    require_receives: bool = True
    require_other_parameters: bool = True
    require_typed_attributes: bool = True
    require_cross_references: bool = True
    prefer_fenced_code_blocks: bool = True


@dataclass(frozen=True)
class DocvetConfig:
    """Top-level docvet configuration."""

    src_root: str = "."
    package_name: str | None = None
    exclude: list[str] = field(default_factory=lambda: ["tests", "scripts"])
    fail_on: list[str] = field(default_factory=list)
    warn_on: list[str] = field(
        default_factory=lambda: [
            "freshness",
            "enrichment",
            "griffe",
            "coverage",
        ]
    )
    freshness: FreshnessConfig = field(default_factory=FreshnessConfig)
    enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)
    project_root: Path = field(default_factory=Path.cwd)


# ---------------------------------------------------------------------------
# Valid-key constants
# ---------------------------------------------------------------------------

_VALID_TOP_KEYS: frozenset[str] = frozenset(
    {
        "src-root",
        "package-name",
        "exclude",
        "fail-on",
        "warn-on",
        "freshness",
        "enrichment",
    }
)

_VALID_FRESHNESS_KEYS: frozenset[str] = frozenset({"drift-threshold", "age-threshold"})

_VALID_ENRICHMENT_KEYS: frozenset[str] = frozenset(
    {
        "require-examples",
        "require-raises",
        "require-yields",
        "require-warns",
        "require-receives",
        "require-other-parameters",
        "require-typed-attributes",
        "require-cross-references",
        "prefer-fenced-code-blocks",
    }
)

_VALID_CHECK_NAMES: frozenset[str] = frozenset(
    {"enrichment", "freshness", "coverage", "griffe"}
)


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
    for name in names:
        if name not in _VALID_CHECK_NAMES:
            valid_csv = ", ".join(sorted(_VALID_CHECK_NAMES))
            msg = (
                f"docvet: unknown check '{name}' in "
                f"{field_name}. Valid checks: {valid_csv}"
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

    Args:
        value: The value to check.
        expected: The expected Python type.
        key: Config key name for error messages.
        section: Section label for error messages.
    """
    if not isinstance(value, expected):
        actual = type(value).__name__
        msg = f"docvet: '{key}' in {section} must be {expected.__name__}, got {actual}"
        print(msg, file=sys.stderr)
        sys.exit(1)


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

    Args:
        data: Raw TOML dict for the enrichment section.

    Returns:
        A validated :class:`EnrichmentConfig`.
    """
    _validate_keys(data, _VALID_ENRICHMENT_KEYS, "[tool.docvet.enrichment]")
    section = "[tool.docvet.enrichment]"
    kwargs: dict[str, object] = {}
    for key, value in data.items():
        if key == "require-examples":
            _validate_type(value, list, key, section)
            for entry in value:  # type: ignore[union-attr]
                _validate_type(entry, str, key, section)
        else:
            _validate_type(value, bool, key, section)
        kwargs[_kebab_to_snake(key)] = value
    return EnrichmentConfig(**kwargs)  # type: ignore[arg-type]


def _parse_docvet_section(
    data: dict[str, object],
) -> dict[str, object]:
    """Validate and parse a non-empty ``[tool.docvet]`` dict.

    Args:
        data: Mutable copy of the raw TOML ``[tool.docvet]`` section.

    Returns:
        Processed dict ready for :class:`DocvetConfig` construction.
    """
    _validate_keys(data, _VALID_TOP_KEYS, "[tool.docvet]")

    converted: dict[str, object] = {_kebab_to_snake(k): v for k, v in data.items()}

    freshness_data = converted.pop("freshness", None)
    enrichment_data = converted.pop("enrichment", None)

    if freshness_data is not None:
        _validate_type(freshness_data, dict, "freshness", "[tool.docvet]")
        converted["freshness"] = _parse_freshness(freshness_data)  # type: ignore[arg-type]

    if enrichment_data is not None:
        _validate_type(enrichment_data, dict, "enrichment", "[tool.docvet]")
        converted["enrichment"] = _parse_enrichment(enrichment_data)  # type: ignore[arg-type]

    section = "[tool.docvet]"
    if "src_root" in converted:
        _validate_type(converted["src_root"], str, "src-root", section)
    if "package_name" in converted:
        _validate_type(converted["package_name"], str, "package-name", section)
    if "exclude" in converted:
        _validate_type(converted["exclude"], list, "exclude", section)
        for entry in converted["exclude"]:  # type: ignore[union-attr]
            _validate_type(entry, str, "exclude", section)
    if "fail_on" in converted:
        _validate_type(converted["fail_on"], list, "fail-on", section)
        for entry in converted["fail_on"]:  # type: ignore[union-attr]
            _validate_type(entry, str, "fail-on", section)
        _validate_check_names(converted["fail_on"], "fail-on")  # type: ignore[arg-type]
    if "warn_on" in converted:
        _validate_type(converted["warn_on"], list, "warn-on", section)
        for entry in converted["warn_on"]:  # type: ignore[union-attr]
            _validate_type(entry, str, "warn-on", section)
        _validate_check_names(converted["warn_on"], "warn-on")  # type: ignore[arg-type]

    return converted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_config(path: Path | None = None) -> DocvetConfig:
    """Load docvet configuration from ``pyproject.toml``.

    Args:
        path: Explicit path to a ``pyproject.toml``. When *None*,
            discovery walks up from CWD.

    Returns:
        A fully resolved :class:`DocvetConfig`.

    Raises:
        FileNotFoundError: If an explicit *path* does not exist.
    """
    if path is not None:
        if not path.is_file():
            raise FileNotFoundError(path)
        pyproject_path = path
        project_root = path.parent.resolve()
    else:
        pyproject_path = _find_pyproject()
        if pyproject_path is None:
            project_root = Path.cwd().resolve()
            parsed: dict[str, object] = {}
        else:
            project_root = pyproject_path.parent.resolve()

    if pyproject_path is not None:
        with open(pyproject_path, "rb") as f:
            toml_data = tomllib.load(f)
        data = toml_data.get("tool", {}).get("docvet", {})
        parsed = _parse_docvet_section(data) if data else {}

    configured_src = parsed.get("src_root")
    resolved_src_root = _resolve_src_root(
        project_root,
        configured_src if isinstance(configured_src, str) else None,
    )

    raw_fail = parsed.get("fail_on")
    fail_on: list[str] = (
        [str(x) for x in raw_fail] if isinstance(raw_fail, list) else []
    )
    raw_warn = parsed.get("warn_on")
    default_warn: list[str] = [
        "freshness",
        "enrichment",
        "griffe",
        "coverage",
    ]
    warn_on: list[str] = (
        [str(x) for x in raw_warn] if isinstance(raw_warn, list) else default_warn
    )
    fail_on_set = set(fail_on)
    final_warn_on: list[str] = [c for c in warn_on if c not in fail_on_set]

    raw_pkg = parsed.get("package_name")
    raw_exclude = parsed.get("exclude")
    exclude: list[str] = (
        [str(x) for x in raw_exclude]
        if isinstance(raw_exclude, list)
        else ["tests", "scripts"]
    )
    raw_freshness = parsed.get("freshness")
    raw_enrichment = parsed.get("enrichment")

    return DocvetConfig(
        src_root=resolved_src_root,
        package_name=raw_pkg if isinstance(raw_pkg, str) else None,
        exclude=exclude,
        fail_on=fail_on,
        warn_on=final_warn_on,
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
        project_root=project_root,
    )
