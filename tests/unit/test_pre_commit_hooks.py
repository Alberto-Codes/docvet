"""Tests for .pre-commit-hooks.yaml schema validation.

Validates the pre-commit hook definition file has all required fields
with correct values, ensuring the hook works when consumed by the
pre-commit framework.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml  # dev dependency: pyyaml

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HOOKS_PATH = _REPO_ROOT / ".pre-commit-hooks.yaml"

_REQUIRED_FIELDS = {"id", "name", "entry", "language", "types", "require_serial"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPreCommitHooksYaml:
    """Validates .pre-commit-hooks.yaml structure and field values."""

    def test_hooks_file_exists(self) -> None:
        """The hook definition file exists at the repo root."""
        assert _HOOKS_PATH.exists(), f"Missing {_HOOKS_PATH}"

    def test_hooks_file_is_valid_yaml(self) -> None:
        """The file parses as valid YAML without syntax errors."""
        content = _HOOKS_PATH.read_text(encoding="utf-8")
        hooks = yaml.safe_load(content)
        assert isinstance(hooks, list), "Expected a YAML list of hook definitions"

    def test_single_hook_defined(self) -> None:
        """Exactly one hook is defined (the docvet hook)."""
        hooks = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))
        assert len(hooks) == 1, f"Expected 1 hook, got {len(hooks)}"

    def test_all_required_fields_present(self) -> None:
        """All required pre-commit hook fields are present."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        missing = _REQUIRED_FIELDS - set(hook.keys())
        assert not missing, f"Missing required fields: {missing}"

    def test_id_is_docvet(self) -> None:
        """Hook id is 'docvet'."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert hook["id"] == "docvet"

    def test_language_is_python(self) -> None:
        """Hook language is 'python' for virtualenv-based installation."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert hook["language"] == "python"

    def test_types_contains_python(self) -> None:
        """Hook types list contains 'python' for .py file filtering."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert isinstance(hook["types"], list), "types must be a list, not a string"
        assert "python" in hook["types"]

    def test_entry_starts_with_docvet_check(self) -> None:
        """Hook entry starts with 'docvet check' to accept positional filenames."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert hook["entry"].startswith("docvet check"), (
            f"Entry should start with 'docvet check', got: {hook['entry']}"
        )

    def test_name_is_docvet(self) -> None:
        """Hook name is 'docvet'."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert hook["name"] == "docvet"

    def test_require_serial_is_true(self) -> None:
        """Hook uses require_serial to prevent parallel git races."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert hook["require_serial"] is True

    def test_description_field_present_and_nonempty(self) -> None:
        """Hook has a non-empty description for pre-commit metadata."""
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        assert "description" in hook, "Missing 'description' field"
        assert hook["description"].strip(), "Description must not be empty"

    def test_pass_filenames_not_disabled(self) -> None:
        """If pass_filenames is set, it must not be false.

        Pre-commit defaults pass_filenames to true. The hook relies on
        receiving filenames as positional args (story 23.2). Explicitly
        setting pass_filenames to false would break this contract.
        """
        hook = yaml.safe_load(_HOOKS_PATH.read_text(encoding="utf-8"))[0]
        if "pass_filenames" in hook:
            assert hook["pass_filenames"] is not False, (
                "pass_filenames must not be false — hook relies on positional filenames"
            )
