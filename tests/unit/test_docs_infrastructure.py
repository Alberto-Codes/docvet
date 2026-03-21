"""Tests for documentation infrastructure integrity.

Validates that docs/rules.yml, rule page files, and mkdocs.yml nav
entries are consistent and structurally sound. Catches silent
corruption (typos, missing fields, orphaned entries) that
``mkdocs build --strict`` cannot detect.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RULES_PATH = _REPO_ROOT / "docs" / "rules.yml"
_DOCS_DIR = _REPO_ROOT / "docs" / "site"
_MKDOCS_PATH = _REPO_ROOT / "mkdocs.yml"

_REQUIRED_FIELDS = {
    "id",
    "name",
    "check",
    "category",
    "applies_to",
    "summary",
    "since",
    "fix",
}
_VALID_CHECKS = {"presence", "enrichment", "freshness", "coverage", "griffe"}
_VALID_CATEGORIES = {"required", "recommended"}

_EXPECTED_RULE_COUNT = 28


def _load_rules() -> list[dict]:
    """Load and return the rules list from docs/rules.yml."""
    return yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Class 1: Rules YAML Schema Validation
# ---------------------------------------------------------------------------


class TestRulesYamlSchema:
    """Validates docs/rules.yml structure and field constraints."""

    def test_rules_file_exists(self) -> None:
        """The rule metadata file exists at the expected path."""
        assert _RULES_PATH.exists(), f"Missing {_RULES_PATH}"

    def test_rules_file_is_valid_yaml_list(self) -> None:
        """The file parses as a YAML list of rule definitions."""
        rules = _load_rules()
        assert isinstance(rules, list), "Expected a YAML list of rule definitions"

    def test_rule_count(self) -> None:
        """Exactly the expected number of rules are defined.

        Hardcoded to catch accidental deletion. Update this count
        when adding a new rule.
        """
        rules = _load_rules()
        assert len(rules) == _EXPECTED_RULE_COUNT, (
            f"Expected {_EXPECTED_RULE_COUNT} rules, got {len(rules)}. "
            "Update _EXPECTED_RULE_COUNT if you added a new rule."
        )

    def test_all_required_fields_present(self) -> None:
        """Every rule entry has all 8 required fields."""
        rules = _load_rules()
        for rule in rules:
            missing = _REQUIRED_FIELDS - set(rule.keys())
            assert not missing, (
                f"Rule '{rule.get('id', '???')}' missing fields: {missing}"
            )

    def test_no_duplicate_ids(self) -> None:
        """No two rules share the same id (duplicates cause ambiguous lookups)."""
        rules = _load_rules()
        ids = [r["id"] for r in rules]
        duplicates = [rid for rid in ids if ids.count(rid) > 1]
        assert not duplicates, f"Duplicate rule ids: {set(duplicates)}"

    def test_check_field_values(self) -> None:
        """Every rule's check field is a valid check name.

        Invalid values create dead breadcrumb back-links in rendered
        rule pages (../checks/{check}.md).
        """
        rules = _load_rules()
        for rule in rules:
            assert rule["check"] in _VALID_CHECKS, (
                f"Rule '{rule['id']}' has invalid check '{rule['check']}'. "
                f"Valid: {_VALID_CHECKS}"
            )

    def test_category_field_values(self) -> None:
        """Every rule's category is 'required' or 'recommended'."""
        rules = _load_rules()
        for rule in rules:
            assert rule["category"] in _VALID_CATEGORIES, (
                f"Rule '{rule['id']}' has invalid category '{rule['category']}'. "
                f"Valid: {_VALID_CATEGORIES}"
            )

    def test_since_field_is_version_string(self) -> None:
        """Every rule's since field looks like a version number."""
        rules = _load_rules()
        for rule in rules:
            assert re.match(r"^\d+\.\d+\.\d+$", rule["since"]), (
                f"Rule '{rule['id']}' has invalid since '{rule['since']}'. "
                "Expected format: X.Y.Z"
            )

    def test_fix_field_is_nonempty(self) -> None:
        """Every rule has non-empty fix guidance."""
        rules = _load_rules()
        for rule in rules:
            assert rule["fix"] and rule["fix"].strip(), (
                f"Rule '{rule['id']}' has empty fix field"
            )


# ---------------------------------------------------------------------------
# Class 2: Rules YAML ↔ Rule Page Bidirectional Consistency
# ---------------------------------------------------------------------------


class TestRulesYamlMacroCompat:
    """Validates bidirectional consistency between rules.yml and rule pages."""

    def test_every_rule_id_has_page(self) -> None:
        """Every rule id in rules.yml has a matching .md file on disk."""
        rules = _load_rules()
        rules_dir = _DOCS_DIR / "rules"
        for rule in rules:
            page = rules_dir / f"{rule['id']}.md"
            assert page.exists(), (
                f"Rule '{rule['id']}' in rules.yml has no page at {page}"
            )

    def test_every_rule_page_has_entry(self) -> None:
        """Every .md file in docs/site/rules/ has a matching rules.yml entry."""
        rules = _load_rules()
        rule_ids = {r["id"] for r in rules}
        rules_dir = _DOCS_DIR / "rules"
        for page in sorted(rules_dir.glob("*.md")):
            page_id = page.stem
            assert page_id in rule_ids, (
                f"Rule page '{page.name}' has no entry in rules.yml"
            )


# ---------------------------------------------------------------------------
# Class 3: mkdocs.yml Nav Consistency
# ---------------------------------------------------------------------------


class _MkdocsLoader(yaml.SafeLoader):
    """SafeLoader that ignores !!python/name: and !!python/object: tags.

    mkdocs.yml uses these for plugin references (e.g., emoji handlers).
    We only need the nav structure, so resolve these as None.
    """


_MkdocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/",
    lambda loader, suffix, node: None,
)


def _extract_nav_paths(nav: list, collected: list[str] | None = None) -> list[str]:
    """Recursively extract all .md file paths from mkdocs nav structure."""
    if collected is None:
        collected = []
    for item in nav:
        if isinstance(item, str):
            if item.endswith(".md"):
                collected.append(item)
        elif isinstance(item, dict):
            for value in item.values():
                if isinstance(value, str) and value.endswith(".md"):
                    collected.append(value)
                elif isinstance(value, list):
                    _extract_nav_paths(value, collected)
    return collected


class TestMkdocsNavConsistency:
    """Validates that mkdocs.yml nav entries reference existing files."""

    def test_mkdocs_file_exists(self) -> None:
        """mkdocs.yml exists at the repo root."""
        assert _MKDOCS_PATH.exists(), f"Missing {_MKDOCS_PATH}"

    def test_all_nav_entries_exist_on_disk(self) -> None:
        """Every .md path in mkdocs.yml nav has a file on disk."""
        mkdocs = yaml.load(  # noqa: S506
            _MKDOCS_PATH.read_text(encoding="utf-8"), Loader=_MkdocsLoader
        )
        nav = mkdocs.get("nav", [])
        paths = _extract_nav_paths(nav)
        assert paths, "No .md paths found in mkdocs.yml nav"
        for rel_path in paths:
            # reference/ is auto-generated by gen-files plugin, skip it
            if rel_path.startswith("reference/"):
                continue
            full_path = _DOCS_DIR / rel_path
            assert full_path.exists(), (
                f"Nav entry '{rel_path}' does not exist at {full_path}"
            )
