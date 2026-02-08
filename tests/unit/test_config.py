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
