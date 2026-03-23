"""TOML and JSON formatting for docvet configuration display.

Renders the effective ``DocvetConfig`` as copy-paste-ready TOML or
structured JSON for the ``docvet config`` command. Pure functions —
only read config, no mutation.

See Also:
    [`docvet.config`][]: Configuration loading and dataclasses.

Examples:
    Format the current config as TOML:

    ```python
    from docvet.config import load_config, format_config_toml, get_user_keys

    cfg = load_config()
    print(format_config_toml(cfg, get_user_keys()))
    ```
"""

from __future__ import annotations

import dataclasses
import json

from . import DocvetConfig, _snake_to_kebab


def _fmt_toml_value(value: object) -> str:
    """Format a Python value as a TOML literal.

    Handles bool, str, int/float, and list types. List elements are
    formatted recursively to ensure consistent escaping.

    Args:
        value: The Python value to format.

    Returns:
        A TOML-compatible string representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        items = ", ".join(_fmt_toml_value(v) for v in value)
        return f"[{items}]"
    return str(value)


def _get_annotation(
    kebab_key: str,
    user_keys: dict[str, object],
    section_keys: dict[str, object] | None = None,
) -> str:
    """Return a source annotation comment for a config key.

    Args:
        kebab_key: The kebab-case key to annotate.
        user_keys: Top-level raw user config dict.
        section_keys: Nested section user keys, or *None* for
            top-level lookup.

    Returns:
        An inline TOML comment: ``"# (user)"`` or ``"# (default)"``.
    """
    if section_keys is not None:
        return "# (user)" if kebab_key in section_keys else "# (default)"
    return "# (user)" if kebab_key in user_keys else "# (default)"


def _get_section_user_keys(
    user_keys: dict[str, object],
    key: str,
) -> dict[str, object] | None:
    """Extract user-configured keys for a nested config section.

    Args:
        user_keys: Top-level raw user config dict.
        key: Section name (e.g., ``"freshness"``).

    Returns:
        A dict of user-set keys within the section, or *None*.
    """
    raw = user_keys.get(key)
    if isinstance(raw, dict):
        return {str(k): v for k, v in raw.items()}
    return None


def _format_toml_section(
    header: str,
    fields: list[tuple[str, str]],
    config_obj: object,
    user_keys: dict[str, object],
    section_keys: dict[str, object] | None,
) -> list[str]:
    """Render a TOML section with annotated key-value pairs.

    Args:
        header: TOML section header (e.g.,
            ``"[tool.docvet.freshness]"``).
        fields: List of ``(attr_name, kebab_key)`` pairs to render.
        config_obj: Config dataclass instance to read values from.
        user_keys: Top-level raw user config dict.
        section_keys: Nested section user keys for annotation.

    Returns:
        Lines for this section, starting with a blank separator.
    """
    lines = ["", header]
    for attr, kebab in fields:
        value = getattr(config_obj, attr)
        annotation = _get_annotation(kebab, user_keys, section_keys)
        lines.append(f"{kebab} = {_fmt_toml_value(value)}  {annotation}")
    return lines


def _convert_keys_to_kebab(d: dict[str, object]) -> dict[str, object]:
    """Recursively convert snake_case dict keys to kebab-case.

    Args:
        d: Dictionary with snake_case keys.

    Returns:
        New dictionary with all keys converted to kebab-case.
    """
    result: dict[str, object] = {}
    for k, v in d.items():
        kebab = _snake_to_kebab(k)
        if isinstance(v, dict):
            result[kebab] = _convert_keys_to_kebab(v)  # type: ignore[arg-type]
        else:
            result[kebab] = v
    return result


# ---------------------------------------------------------------------------
# Public formatters
# ---------------------------------------------------------------------------


def format_config_toml(
    config: DocvetConfig,
    user_keys: dict[str, object],
) -> str:
    """Format effective config as copy-paste-ready TOML.

    Renders the top-level ``[tool.docvet]`` keys (including
    ``docstring-style``) inline, then delegates each nested section
    (freshness, enrichment — including ``require-returns``,
    ``require-param-agreement``, ``require-deprecation-notice``,
    ``exclude-args-kwargs``, ``check-extra-raises``,
    ``check-extra-yields``, and ``check-extra-returns``, presence —
    including ``check-overload-docstrings``) to :func:`_format_toml_section`.
    Values are formatted via :func:`_fmt_toml_value` and annotated via
    :func:`_get_annotation`. Omits ``package-name`` when its value is
    ``None`` and ``project_root`` (runtime-only). When
    ``extend-exclude`` appears in *user_keys*, the merged ``exclude``
    list is annotated accordingly.

    Args:
        config: The effective :class:`DocvetConfig`.
        user_keys: Raw ``[tool.docvet]`` dict with kebab-case keys.

    Returns:
        A TOML-formatted string suitable for ``pyproject.toml``.
    """
    lines: list[str] = ["[tool.docvet]"]
    has_extend = "extend-exclude" in user_keys
    top_fields = [
        ("src_root", "src-root"),
        ("package_name", "package-name"),
        ("docstring_style", "docstring-style"),
        ("exclude", "exclude"),
        ("fail_on", "fail-on"),
        ("warn_on", "warn-on"),
    ]
    for attr, kebab in top_fields:
        value = getattr(config, attr)
        if attr == "package_name" and value is None:
            continue
        annotation = _get_annotation(kebab, user_keys)
        if attr == "exclude" and has_extend:
            annotation = "# (merged from exclude + extend-exclude)"
        lines.append(f"{kebab} = {_fmt_toml_value(value)}  {annotation}")

    lines.extend(
        _format_toml_section(
            "[tool.docvet.freshness]",
            [
                ("drift_threshold", "drift-threshold"),
                ("age_threshold", "age-threshold"),
            ],
            config.freshness,
            user_keys,
            _get_section_user_keys(user_keys, "freshness"),
        )
    )
    lines.extend(
        _format_toml_section(
            "[tool.docvet.enrichment]",
            [
                ("require_raises", "require-raises"),
                ("require_returns", "require-returns"),
                ("require_yields", "require-yields"),
                ("require_warns", "require-warns"),
                ("require_receives", "require-receives"),
                ("require_other_parameters", "require-other-parameters"),
                ("require_typed_attributes", "require-typed-attributes"),
                ("require_cross_references", "require-cross-references"),
                ("prefer_fenced_code_blocks", "prefer-fenced-code-blocks"),
                ("require_attributes", "require-attributes"),
                ("require_param_agreement", "require-param-agreement"),
                ("require_deprecation_notice", "require-deprecation-notice"),
                ("exclude_args_kwargs", "exclude-args-kwargs"),
                ("check_extra_raises", "check-extra-raises"),
                ("check_extra_yields", "check-extra-yields"),
                ("check_extra_returns", "check-extra-returns"),
                ("require_examples", "require-examples"),
            ],
            config.enrichment,
            user_keys,
            _get_section_user_keys(user_keys, "enrichment"),
        )
    )
    lines.extend(
        _format_toml_section(
            "[tool.docvet.presence]",
            [
                ("enabled", "enabled"),
                ("min_coverage", "min-coverage"),
                ("ignore_init", "ignore-init"),
                ("ignore_magic", "ignore-magic"),
                ("ignore_private", "ignore-private"),
                ("check_overload_docstrings", "check-overload-docstrings"),
            ],
            config.presence,
            user_keys,
            _get_section_user_keys(user_keys, "presence"),
        )
    )

    lines.append("")
    return "\n".join(lines)


def format_config_json(
    config: DocvetConfig,
    user_keys: dict[str, object],
) -> str:
    """Format effective config as a JSON string.

    Produces a JSON object with ``"config"`` (all effective values,
    kebab-case keys, ``project_root`` and ``user_set_keys`` excluded) and
    ``"user_configured"`` (list of dot-separated kebab-case paths for
    user-set keys). Key conversion is handled by
    :func:`_convert_keys_to_kebab`. Omits ``package-name`` when its
    value is ``None``.

    Args:
        config: The effective :class:`DocvetConfig`.
        user_keys: Raw ``[tool.docvet]`` dict with kebab-case keys.

    Returns:
        A pretty-printed JSON string.
    """
    raw = dataclasses.asdict(config)
    raw.pop("project_root", None)
    # Remove internal-only fields not meaningful in user-facing output.
    if "enrichment" in raw and isinstance(raw["enrichment"], dict):
        raw["enrichment"].pop("user_set_keys", None)
    converted = _convert_keys_to_kebab(raw)

    if converted.get("package-name") is None:
        converted.pop("package-name", None)

    user_configured: list[str] = []
    for key, value in user_keys.items():
        if key == "extend-exclude":
            continue
        if isinstance(value, dict):
            for sub_key in value:
                user_configured.append(f"{key}.{sub_key}")
        else:
            user_configured.append(key)

    output = {
        "config": converted,
        "user_configured": sorted(user_configured),
    }
    return json.dumps(output, indent=2)
