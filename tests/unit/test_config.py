"""Unit tests for the docvet config reader."""

from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path

import pytest

from docvet.config import (
    DocvetConfig,
    EnrichmentConfig,
    FreshnessConfig,
    _find_pyproject,
    _resolve_fail_warn,
    _validate_string_list,
    load_config,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def write_pyproject(tmp_path):
    def _write(content: str) -> Path:
        p = tmp_path / "pyproject.toml"
        p.write_text(content)
        return p

    return _write


# ---------------------------------------------------------------------------
# Dataclass defaults
# ---------------------------------------------------------------------------


def test_freshness_defaults_drift_threshold_is_30():
    cfg = FreshnessConfig()
    assert cfg.drift_threshold == 30


def test_freshness_defaults_age_threshold_is_90():
    cfg = FreshnessConfig()
    assert cfg.age_threshold == 90


def test_enrichment_defaults_require_examples_has_four_entries():
    cfg = EnrichmentConfig()
    assert cfg.require_examples == ["class", "protocol", "dataclass", "enum"]


def test_enrichment_defaults_require_raises_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_raises is True


def test_enrichment_defaults_require_yields_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_yields is True


def test_enrichment_defaults_require_warns_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_warns is True


def test_enrichment_defaults_require_receives_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_receives is True


def test_enrichment_defaults_require_other_parameters_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_other_parameters is True


def test_enrichment_defaults_require_typed_attributes_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_typed_attributes is True


def test_enrichment_defaults_require_cross_references_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_cross_references is True


def test_enrichment_defaults_prefer_fenced_code_blocks_is_true():
    cfg = EnrichmentConfig()
    assert cfg.prefer_fenced_code_blocks is True


def test_enrichment_defaults_require_attributes_is_true():
    cfg = EnrichmentConfig()
    assert cfg.require_attributes is True


def test_docvet_defaults_src_root_is_dot():
    cfg = DocvetConfig()
    assert cfg.src_root == "."


def test_docvet_defaults_package_name_is_none():
    cfg = DocvetConfig()
    assert cfg.package_name is None


def test_docvet_defaults_exclude_is_tests_scripts():
    cfg = DocvetConfig()
    assert cfg.exclude == ["tests", "scripts"]


def test_docvet_defaults_fail_on_is_empty():
    cfg = DocvetConfig()
    assert cfg.fail_on == []


def test_docvet_defaults_warn_on_has_all_checks():
    cfg = DocvetConfig()
    assert cfg.warn_on == [
        "freshness",
        "enrichment",
        "griffe",
        "coverage",
    ]


# ---------------------------------------------------------------------------
# Frozen enforcement
# ---------------------------------------------------------------------------


def test_freshness_when_mutated_raises_frozen_error():
    cfg = FreshnessConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.drift_threshold = 99  # type: ignore[misc]


def test_enrichment_when_mutated_raises_frozen_error():
    cfg = EnrichmentConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.require_raises = False  # type: ignore[misc]


def test_docvet_when_mutated_raises_frozen_error():
    cfg = DocvetConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.src_root = "lib"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Nested composition
# ---------------------------------------------------------------------------


def test_docvet_freshness_is_freshness_config():
    cfg = DocvetConfig()
    assert isinstance(cfg.freshness, FreshnessConfig)


def test_docvet_enrichment_is_enrichment_config():
    cfg = DocvetConfig()
    assert isinstance(cfg.enrichment, EnrichmentConfig)


# ---------------------------------------------------------------------------
# Discovery (_find_pyproject)
# ---------------------------------------------------------------------------


def test_find_pyproject_when_in_cwd_returns_path(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    assert _find_pyproject(start=tmp_path) == tmp_path / "pyproject.toml"


def test_find_pyproject_when_in_parent_walks_up(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    child = tmp_path / "subdir"
    child.mkdir()
    assert _find_pyproject(start=child) == tmp_path / "pyproject.toml"


def test_find_pyproject_when_missing_returns_none(tmp_path):
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    assert _find_pyproject(start=child) is None


def test_find_pyproject_when_git_boundary_stops(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    mid = tmp_path / "mid"
    mid.mkdir()
    (mid / ".git").mkdir()
    deep = mid / "deep"
    deep.mkdir()
    assert _find_pyproject(start=deep) is None


def test_find_pyproject_when_two_levels_returns_closest(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    child = tmp_path / "child"
    child.mkdir()
    (child / "pyproject.toml").write_text("")
    assert _find_pyproject(start=child) == child / "pyproject.toml"


def test_find_pyproject_when_git_and_toml_coexist_returns_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / ".git").mkdir()
    assert _find_pyproject(start=tmp_path) == tmp_path / "pyproject.toml"


def test_find_pyproject_when_oserror_returns_none(tmp_path, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "is_file", _boom)
    assert _find_pyproject(start=tmp_path) is None


def test_load_config_zero_config_with_src_dir_resolves_src(tmp_path, monkeypatch):
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.src_root == "src"


def test_load_config_zero_config_without_src_dir_resolves_dot(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    cfg = load_config()
    assert cfg.src_root == "."


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def test_load_config_full_config_populates_all_fields(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        """\
[tool.docvet]
src-root = "lib"
package-name = "mypkg"
exclude = ["vendor"]
fail-on = ["freshness"]
warn-on = ["enrichment"]

[tool.docvet.freshness]
drift-threshold = 10
age-threshold = 45

[tool.docvet.enrichment]
require-raises = false
require-attributes = false
require-examples = ["class"]
"""
    )
    cfg = load_config()
    assert cfg.src_root == "lib"
    assert cfg.package_name == "mypkg"
    assert cfg.exclude == ["vendor"]
    assert cfg.fail_on == ["freshness"]
    assert cfg.warn_on == ["enrichment"]
    assert cfg.freshness.drift_threshold == 10
    assert cfg.freshness.age_threshold == 45
    assert cfg.enrichment.require_raises is False
    assert cfg.enrichment.require_attributes is False
    assert cfg.enrichment.require_examples == ["class"]


def test_load_config_partial_config_uses_defaults(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nsrc-root = "lib"\n')
    cfg = load_config()
    assert cfg.src_root == "lib"
    assert cfg.fail_on == []
    assert cfg.freshness.drift_threshold == 30


def test_load_config_missing_section_returns_defaults(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.ruff]\nline-length = 88\n")
    cfg = load_config()
    assert cfg.fail_on == []
    assert cfg.warn_on == [
        "freshness",
        "enrichment",
        "griffe",
        "coverage",
    ]


def test_load_config_empty_file_returns_defaults(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("")
    cfg = load_config()
    assert cfg.fail_on == []


def test_load_config_nested_freshness_custom_thresholds(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        """\
[tool.docvet.freshness]
drift-threshold = 7
age-threshold = 14
"""
    )
    cfg = load_config()
    assert cfg.freshness.drift_threshold == 7
    assert cfg.freshness.age_threshold == 14


def test_load_config_nested_enrichment_flipped_booleans(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        """\
[tool.docvet.enrichment]
require-raises = false
require-yields = false
"""
    )
    cfg = load_config()
    assert cfg.enrichment.require_raises is False
    assert cfg.enrichment.require_yields is False
    assert cfg.enrichment.require_warns is True


def test_load_config_nested_enrichment_require_attributes_false(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        """\
[tool.docvet.enrichment]
require-attributes = false
"""
    )
    cfg = load_config()
    assert cfg.enrichment.require_attributes is False


def test_load_config_nested_enrichment_without_require_attributes_uses_default(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        """\
[tool.docvet.enrichment]
require-raises = false
"""
    )
    cfg = load_config()
    assert cfg.enrichment.require_attributes is True
    assert cfg.enrichment.require_raises is False


def test_load_config_explicit_path_uses_that_file(tmp_path):
    p = tmp_path / "custom.toml"
    p.write_text('[tool.docvet]\nsrc-root = "custom"\n')
    cfg = load_config(path=p)
    assert cfg.src_root == "custom"


def test_load_config_explicit_path_missing_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(path=tmp_path / "nonexistent.toml")


def test_load_config_src_root_auto_detect_with_src(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    write_pyproject("[tool.docvet]\n")
    cfg = load_config()
    assert cfg.src_root == "src"


def test_load_config_src_root_auto_detect_without_src(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\n")
    cfg = load_config()
    assert cfg.src_root == "."


def test_load_config_package_name_omitted_is_none(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\n")
    cfg = load_config()
    assert cfg.package_name is None


def test_load_config_package_name_set_is_preserved(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\npackage-name = "mypkg"\n')
    cfg = load_config()
    assert cfg.package_name == "mypkg"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_load_config_unknown_top_key_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\nbogus = true\n")
    with pytest.raises(SystemExit):
        load_config()
    assert "bogus" in capsys.readouterr().err


def test_load_config_unknown_freshness_key_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet.freshness]\nbad-key = 1\n")
    with pytest.raises(SystemExit):
        load_config()
    assert "bad-key" in capsys.readouterr().err


def test_load_config_unknown_enrichment_key_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet.enrichment]\nbad-key = true\n")
    with pytest.raises(SystemExit):
        load_config()
    assert "bad-key" in capsys.readouterr().err


def test_load_config_invalid_check_in_fail_on_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nfail-on = ["bogus"]\n')
    with pytest.raises(SystemExit):
        load_config()
    err = capsys.readouterr().err
    assert "bogus" in err
    assert "freshness" in err


def test_load_config_invalid_check_in_warn_on_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nwarn-on = ["nope"]\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "nope" in capsys.readouterr().err


def test_load_config_wrong_type_drift_threshold_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet.freshness]\ndrift-threshold = "thirty"\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "int" in capsys.readouterr().err


def test_load_config_bool_as_int_drift_threshold_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet.freshness]\ndrift-threshold = true\n")
    with pytest.raises(SystemExit):
        load_config()
    assert "int" in capsys.readouterr().err


def test_load_config_wrong_type_boolean_field_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet.enrichment]\nrequire-raises = "yes"\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "bool" in capsys.readouterr().err


def test_load_config_malformed_toml_raises_decode_error(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet\n")
    with pytest.raises(tomllib.TOMLDecodeError):
        load_config()


def test_load_config_wrong_type_exclude_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nexclude = "not-a-list"\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "list" in capsys.readouterr().err


def test_load_config_wrong_type_src_root_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\nsrc-root = 123\n")
    with pytest.raises(SystemExit):
        load_config()
    assert "str" in capsys.readouterr().err


def test_load_config_overlap_auto_subtracts_from_warn_on(
    tmp_path, monkeypatch, write_pyproject
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nfail-on = ["freshness"]\n')
    cfg = load_config()
    assert cfg.fail_on == ["freshness"]
    assert "freshness" not in cfg.warn_on


def test_load_config_multiple_unknown_keys_reported(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\nbogus1 = true\nbogus2 = false\n")
    with pytest.raises(SystemExit):
        load_config()
    err = capsys.readouterr().err
    assert "bogus1" in err
    assert "bogus2" in err


def test_load_config_non_dict_tool_section_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('tool = "not a table"\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "[tool]" in capsys.readouterr().err


def test_load_config_non_dict_docvet_section_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool]\ndocvet = "not a table"\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "[tool.docvet]" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# fail-on / warn-on overlap warning
# ---------------------------------------------------------------------------


def test_load_config_overlap_emits_stderr_warning(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        '[tool.docvet]\nfail-on = ["freshness"]\nwarn-on = ["freshness", "enrichment"]\n'
    )
    cfg = load_config()
    err = capsys.readouterr().err
    assert (
        "docvet: 'freshness' appears in both fail-on and warn-on; using fail-on" in err
    )
    assert cfg.fail_on == ["freshness"]
    assert "freshness" not in cfg.warn_on
    assert "enrichment" in cfg.warn_on


def test_load_config_no_overlap_emits_no_warning(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        '[tool.docvet]\nfail-on = ["freshness"]\nwarn-on = ["enrichment"]\n'
    )
    load_config()
    err = capsys.readouterr().err
    assert "appears in both" not in err


def test_load_config_overlap_multiple_checks_emits_warning_for_each(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        "[tool.docvet]\n"
        'fail-on = ["freshness", "coverage"]\n'
        'warn-on = ["freshness", "coverage", "enrichment"]\n'
    )
    cfg = load_config()
    err = capsys.readouterr().err
    assert (
        "docvet: 'freshness' appears in both fail-on and warn-on; using fail-on" in err
    )
    assert (
        "docvet: 'coverage' appears in both fail-on and warn-on; using fail-on" in err
    )
    assert "freshness" not in cfg.warn_on
    assert "coverage" not in cfg.warn_on
    assert "enrichment" in cfg.warn_on


def test_load_config_overlap_default_warn_on_no_warning(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nfail-on = ["freshness"]\n')
    cfg = load_config()
    err = capsys.readouterr().err
    assert "appears in both" not in err
    assert "freshness" not in cfg.warn_on


def test_load_config_fail_on_all_four_no_warn_on_zero_warnings(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        '[tool.docvet]\nfail-on = ["enrichment", "freshness", "coverage", "griffe"]\n'
    )
    cfg = load_config()
    err = capsys.readouterr().err
    assert "appears in both" not in err
    assert cfg.warn_on == []


def test_load_config_fail_on_partial_no_warn_on_zero_warnings(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nfail-on = ["enrichment"]\n')
    cfg = load_config()
    err = capsys.readouterr().err
    assert "appears in both" not in err
    assert cfg.warn_on == ["freshness", "griffe", "coverage"]


def test_load_config_both_explicit_overlap_warns_for_overlapping_only(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        "[tool.docvet]\n"
        'fail-on = ["enrichment"]\n'
        'warn-on = ["enrichment", "freshness"]\n'
    )
    cfg = load_config()
    err = capsys.readouterr().err
    assert (
        "docvet: 'enrichment' appears in both fail-on and warn-on; using fail-on" in err
    )
    assert err.count("appears in both") == 1
    assert cfg.fail_on == ["enrichment"]
    assert "enrichment" not in cfg.warn_on
    assert "freshness" in cfg.warn_on


def test_load_config_explicit_warn_on_no_fail_on_zero_warnings(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nwarn-on = ["enrichment", "freshness"]\n')
    cfg = load_config()
    err = capsys.readouterr().err
    assert "appears in both" not in err
    assert cfg.warn_on == ["enrichment", "freshness"]


# ---------------------------------------------------------------------------
# extend-exclude (Story 16.1)
# ---------------------------------------------------------------------------


def test_load_config_extend_exclude_appends_to_defaults(
    tmp_path, monkeypatch, write_pyproject
):
    """AC1: extend-exclude alone appends to defaults."""
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nextend-exclude = ["vendor"]\n')
    cfg = load_config()
    assert cfg.exclude == ["tests", "scripts", "vendor"]


def test_load_config_extend_exclude_multiple_values_appended(
    tmp_path, monkeypatch, write_pyproject
):
    """AC1 multi-value: all extend-exclude entries appended."""
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        '[tool.docvet]\nextend-exclude = ["vendor", "generated", "build"]\n'
    )
    cfg = load_config()
    assert cfg.exclude == ["tests", "scripts", "vendor", "generated", "build"]


def test_load_config_extend_exclude_empty_list_is_noop(
    tmp_path, monkeypatch, write_pyproject
):
    """Empty extend-exclude leaves defaults unchanged."""
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\nextend-exclude = []\n")
    cfg = load_config()
    assert cfg.exclude == ["tests", "scripts"]


def test_load_config_exclude_only_replaces_defaults(
    tmp_path, monkeypatch, write_pyproject
):
    """AC2: exclude alone replaces defaults (unchanged behavior)."""
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nexclude = ["vendor"]\n')
    cfg = load_config()
    assert cfg.exclude == ["vendor"]


def test_load_config_exclude_and_extend_exclude_compose(
    tmp_path, monkeypatch, write_pyproject
):
    """AC3: both keys compose."""
    monkeypatch.chdir(tmp_path)
    write_pyproject(
        '[tool.docvet]\nexclude = ["vendor"]\nextend-exclude = ["generated"]\n'
    )
    cfg = load_config()
    assert cfg.exclude == ["vendor", "generated"]


def test_load_config_neither_exclude_uses_defaults(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    """AC4: neither key uses defaults."""
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\n")
    cfg = load_config()
    assert cfg.exclude == ["tests", "scripts"]
    assert "appears in both" not in capsys.readouterr().err


def test_load_config_wrong_type_extend_exclude_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    """AC5: non-list type rejected."""
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nextend-exclude = "not-a-list"\n')
    with pytest.raises(SystemExit):
        load_config()
    err = capsys.readouterr().err
    assert "extend-exclude" in err
    assert "list" in err


def test_load_config_non_string_extend_exclude_entry_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    """AC6: non-string entry rejected."""
    monkeypatch.chdir(tmp_path)
    write_pyproject("[tool.docvet]\nextend-exclude = [123]\n")
    with pytest.raises(SystemExit):
        load_config()
    err = capsys.readouterr().err
    assert "extend-exclude" in err
    assert "str" in err


def test_load_config_unknown_key_extend_excludes_typo_exits(
    tmp_path, monkeypatch, write_pyproject, capsys
):
    """AC7: unknown key rejected (typo guard)."""
    monkeypatch.chdir(tmp_path)
    write_pyproject('[tool.docvet]\nextend-excludes = ["vendor"]\n')
    with pytest.raises(SystemExit):
        load_config()
    assert "extend-excludes" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# _validate_string_list
# ---------------------------------------------------------------------------


def test_validate_string_list_valid_list_passes():
    data: dict[str, object] = {"exclude": ["tests", "scripts"]}
    _validate_string_list(data, "exclude", "exclude")


def test_validate_string_list_non_list_exits(capsys):
    data: dict[str, object] = {"exclude": "not-a-list"}
    with pytest.raises(SystemExit):
        _validate_string_list(data, "exclude", "exclude")
    assert "list" in capsys.readouterr().err


def test_validate_string_list_non_string_entry_exits(capsys):
    data: dict[str, object] = {"exclude": [123]}
    with pytest.raises(SystemExit):
        _validate_string_list(data, "exclude", "exclude")
    assert "str" in capsys.readouterr().err


def test_validate_string_list_check_names_true_invalid_exits(capsys):
    data: dict[str, object] = {"fail_on": ["bogus"]}
    with pytest.raises(SystemExit):
        _validate_string_list(data, "fail_on", "fail-on", check_names=True)
    assert "bogus" in capsys.readouterr().err


def test_validate_string_list_check_names_false_skips_name_validation():
    data: dict[str, object] = {"exclude": ["anything-goes"]}
    _validate_string_list(data, "exclude", "exclude", check_names=False)


# ---------------------------------------------------------------------------
# _resolve_fail_warn
# ---------------------------------------------------------------------------


def test_resolve_fail_warn_both_from_parsed():
    parsed: dict[str, object] = {
        "fail_on": ["freshness"],
        "warn_on": ["enrichment"],
    }
    defaults = DocvetConfig()
    fail_on, warn_on = _resolve_fail_warn(parsed, defaults)
    assert fail_on == ["freshness"]
    assert warn_on == ["enrichment"]


def test_resolve_fail_warn_both_from_defaults():
    parsed: dict[str, object] = {}
    defaults = DocvetConfig()
    fail_on, warn_on = _resolve_fail_warn(parsed, defaults)
    assert fail_on == []
    assert warn_on == ["freshness", "enrichment", "griffe", "coverage"]


def test_resolve_fail_warn_overlap_explicit_warn_emits_warning(capsys):
    parsed: dict[str, object] = {
        "fail_on": ["freshness"],
        "warn_on": ["freshness", "enrichment"],
    }
    defaults = DocvetConfig()
    fail_on, warn_on = _resolve_fail_warn(parsed, defaults)
    err = capsys.readouterr().err
    assert "freshness" in err
    assert "appears in both" in err
    assert fail_on == ["freshness"]
    assert warn_on == ["enrichment"]


def test_resolve_fail_warn_default_warn_overlap_silent(capsys):
    parsed: dict[str, object] = {"fail_on": ["freshness"]}
    defaults = DocvetConfig()
    _resolve_fail_warn(parsed, defaults)
    err = capsys.readouterr().err
    assert "appears in both" not in err


def test_resolve_fail_warn_filtered_warn_excludes_fail_items():
    parsed: dict[str, object] = {
        "fail_on": ["freshness", "coverage"],
        "warn_on": ["freshness", "coverage", "enrichment"],
    }
    defaults = DocvetConfig()
    fail_on, warn_on = _resolve_fail_warn(parsed, defaults)
    assert fail_on == ["freshness", "coverage"]
    assert warn_on == ["enrichment"]
