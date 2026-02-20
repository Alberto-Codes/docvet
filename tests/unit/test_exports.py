"""Tests for __all__ exports across all docvet modules."""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.unit
class TestCheckSubmoduleExports:
    def test_enrichment_all_contains_check_enrichment(self):
        mod = importlib.import_module("docvet.checks.enrichment")
        assert hasattr(mod, "__all__")
        assert mod.__all__ == ["check_enrichment"]

    def test_freshness_all_contains_both_check_functions(self):
        mod = importlib.import_module("docvet.checks.freshness")
        assert hasattr(mod, "__all__")
        assert mod.__all__ == ["check_freshness_diff", "check_freshness_drift"]

    def test_griffe_compat_all_contains_check_griffe_compat(self):
        mod = importlib.import_module("docvet.checks.griffe_compat")
        assert hasattr(mod, "__all__")
        assert mod.__all__ == ["check_griffe_compat"]

    def test_coverage_all_contains_check_coverage(self):
        mod = importlib.import_module("docvet.checks.coverage")
        assert hasattr(mod, "__all__")
        assert mod.__all__ == ["check_coverage"]


@pytest.mark.unit
class TestChecksPackageReExports:
    def test_checks_all_contains_finding_and_all_check_functions(self):
        mod = importlib.import_module("docvet.checks")
        assert hasattr(mod, "__all__")
        expected = [
            "Finding",
            "check_coverage",
            "check_enrichment",
            "check_freshness_diff",
            "check_freshness_drift",
            "check_griffe_compat",
        ]
        assert sorted(mod.__all__) == expected
        assert len(mod.__all__) == 6

    def test_checks_package_exposes_check_functions_as_attributes(self):
        mod = importlib.import_module("docvet.checks")
        assert hasattr(mod, "check_coverage")
        assert hasattr(mod, "check_enrichment")
        assert hasattr(mod, "check_freshness_diff")
        assert hasattr(mod, "check_freshness_drift")
        assert hasattr(mod, "check_griffe_compat")
        assert callable(mod.check_coverage)
        assert callable(mod.check_enrichment)
        assert callable(mod.check_freshness_diff)
        assert callable(mod.check_freshness_drift)
        assert callable(mod.check_griffe_compat)


@pytest.mark.unit
class TestTopLevelExports:
    def test_docvet_all_contains_only_finding(self):
        mod = importlib.import_module("docvet")
        assert hasattr(mod, "__all__")
        assert mod.__all__ == ["Finding"]
        assert len(mod.__all__) == 1


@pytest.mark.unit
class TestConfigExports:
    def test_config_all_contains_public_types_and_load_config(self):
        mod = importlib.import_module("docvet.config")
        assert hasattr(mod, "__all__")
        expected = [
            "DocvetConfig",
            "EnrichmentConfig",
            "FreshnessConfig",
            "load_config",
        ]
        assert sorted(mod.__all__) == expected
        assert len(mod.__all__) == 4


@pytest.mark.unit
class TestInternalModulesExportNothing:
    @pytest.mark.parametrize(
        "module_path",
        [
            "docvet.ast_utils",
            "docvet.cli",
            "docvet.discovery",
            "docvet.reporting",
        ],
    )
    def test_internal_module_has_empty_all(self, module_path):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "__all__")
        assert mod.__all__ == []


_ALL_DOCVET_MODULES = [
    "docvet",
    "docvet.ast_utils",
    "docvet.checks",
    "docvet.checks.coverage",
    "docvet.checks.enrichment",
    "docvet.checks.freshness",
    "docvet.checks.griffe_compat",
    "docvet.cli",
    "docvet.config",
    "docvet.discovery",
    "docvet.reporting",
]


@pytest.mark.unit
class TestAllModulesHaveAll:
    @pytest.mark.parametrize("module_path", _ALL_DOCVET_MODULES)
    def test_module_defines_all(self, module_path):
        mod = importlib.import_module(module_path)
        assert hasattr(mod, "__all__"), f"{module_path} missing __all__"


@pytest.mark.unit
class TestAllEntriesAreResolvable:
    @pytest.mark.parametrize("module_path", _ALL_DOCVET_MODULES)
    def test_all_entries_are_resolvable(self, module_path):
        mod = importlib.import_module(module_path)
        for name in mod.__all__:
            assert hasattr(mod, name), (
                f"{module_path}.{name} in __all__ but not resolvable"
            )


@pytest.mark.unit
class TestNoPrivateNamesExported:
    @pytest.mark.parametrize("module_path", _ALL_DOCVET_MODULES)
    def test_no_underscore_prefixed_names_in_all(self, module_path):
        mod = importlib.import_module(module_path)
        private_names = [n for n in mod.__all__ if n.startswith("_")]
        assert private_names == [], (
            f"{module_path}.__all__ contains private names: {private_names}"
        )
