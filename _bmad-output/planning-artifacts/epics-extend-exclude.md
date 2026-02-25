---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
status: 'complete'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - 'gh-issue-18'
workflowType: 'epics'
projectName: 'docvet'
featureScope: 'extend-exclude'
---

# docvet - Epic Breakdown: extend-exclude

## Overview

This document provides the epic and story breakdown for the `extend-exclude` configuration feature (GitHub issue #18), decomposing requirements from the existing PRD, architecture, peer research findings, and the issue specification into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: The system shall accept an `extend-exclude` key in `[tool.docvet]` that takes a list of glob patterns (same format as `exclude`).

FR2: When only `extend-exclude` is set (no `exclude`), the final exclude list shall be the defaults (`["tests", "scripts"]`) plus the `extend-exclude` patterns.

FR3: When only `exclude` is set (no `extend-exclude`), the behavior shall be unchanged — `exclude` fully replaces the defaults (backward compatible).

FR4: When both `exclude` and `extend-exclude` are set, the final exclude list shall be the user-provided `exclude` list plus the `extend-exclude` patterns.

FR5: The `extend-exclude` patterns shall use the same fnmatch semantics as `exclude` — patterns without `/` match against every path component; patterns with `/` match the full relative path.

FR6: The system shall validate that `extend-exclude` is a list of strings, emitting a clear error on type mismatch (consistent with existing `exclude` validation).

FR7: The merge of `exclude` and `extend-exclude` shall happen at config load time — downstream consumers (`discovery.py`) shall receive a single `config.exclude` list with no awareness of `extend-exclude`.

### NonFunctional Requirements

NFR1: The merge formula shall follow the established convention used by ruff, black, and flake8: `final = (user_exclude or defaults) + extend_exclude`.

NFR2: The `extend-exclude` key shall use hyphenated TOML naming (`extend-exclude`) consistent with existing keys (`src-root`, `fail-on`, `warn-on`), mapped to underscore in Python (`extend_exclude`).

NFR3: Zero changes to `discovery.py` — the merge is purely a config concern, preserving the existing separation of config loading from file discovery.

NFR4: Backward compatibility — existing `pyproject.toml` configurations without `extend-exclude` shall produce identical behavior.

NFR5: Config validation shall reject unknown keys — `extend-exclude` must be added to `_VALID_TOP_KEYS`.

### Additional Requirements

- From architecture: Config parsing follows the established pattern in `_parse_docvet_section` with `_validate_type` calls for each field. The `load_config` function is the single merge point.
- From architecture: The `DocvetConfig` dataclass uses `field(default_factory=...)` for list defaults. `extend_exclude` should follow the same pattern.
- From peer research: ruff, black, and flake8 all use the same merge formula. isort uses `extend_skip` (underscore naming) but same semantics. mypy and pylint lack this feature and force users to repeat defaults — docvet should not follow that pattern.
- From peer research: No tool applies `force-exclude` semantics — `extend-exclude` only affects recursive discovery, not explicitly-passed files. docvet's `--files` mode already bypasses exclude patterns, which is consistent.
- Duplicate warning (originally FR7) dropped per team consensus — peer tools do not warn on duplicates and it adds complexity for zero user value.

### FR Coverage Map

| FR | Epic | Story | Description |
|----|------|-------|-------------|
| FR1 | 1 | 1.1 | Accept `extend-exclude` key |
| FR2 | 1 | 1.1 | Defaults + extend merge |
| FR3 | 1 | 1.1 | Exclude-only backward compat |
| FR4 | 1 | 1.1 | Both keys compose |
| FR5 | 1 | 1.2 | Same fnmatch semantics (verified end-to-end) |
| FR6 | 1 | 1.1 | Type validation |
| FR7 | 1 | 1.1 | Merge at config load time |

## Epic List

### Epic 1: Additive Exclude Configuration

Developers can add project-specific exclude patterns on top of docvet's defaults without repeating them, following the same `extend-exclude` convention used by ruff, black, and flake8.

**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7
**Stories:** 2

- **Story 1.1:** Config parsing, validation, and merge logic (FR1, FR2, FR3, FR4, FR6, FR7 + unit tests)
- **Story 1.2:** Integration verification and documentation (FR5, NFR3, NFR4 + integration tests + docs)

## Epic 1: Additive Exclude Configuration

Developers can add project-specific exclude patterns on top of docvet's defaults without repeating them, following the same `extend-exclude` convention used by ruff, black, and flake8.

### Story 1.1: Config Parsing and Merge Logic

As a **Python developer configuring docvet**,
I want to add an `extend-exclude` key to `[tool.docvet]` that appends patterns to the defaults,
So that I can exclude additional directories without repeating the default list.

**Acceptance Criteria:**

**AC1:** Given a `pyproject.toml` with only `extend-exclude = ["vendor"]` (no `exclude` key)
When docvet loads the configuration
Then the resolved exclude list is `["tests", "scripts", "vendor"]`

**AC2:** Given a `pyproject.toml` with only `exclude = ["vendor"]` (no `extend-exclude` key)
When docvet loads the configuration
Then the resolved exclude list is `["vendor"]` (defaults replaced, unchanged behavior)

**AC3:** Given a `pyproject.toml` with `exclude = ["vendor"]` and `extend-exclude = ["generated"]`
When docvet loads the configuration
Then the resolved exclude list is `["vendor", "generated"]`

**AC4:** Given a `pyproject.toml` with neither `exclude` nor `extend-exclude`
When docvet loads the configuration
Then the resolved exclude list is the defaults `["tests", "scripts"]`

**AC5:** Given a `pyproject.toml` with `extend-exclude = "not-a-list"`
When docvet loads the configuration
Then a clear validation error is raised indicating `extend-exclude` must be a list of strings

**AC6:** Given a `pyproject.toml` with `extend-exclude = [123]`
When docvet loads the configuration
Then a clear validation error is raised indicating list entries must be strings

**AC7:** Given a `pyproject.toml` with an unknown key like `extend-excludes` (typo)
When docvet loads the configuration
Then a validation error is raised for the unknown key

### Story 1.2: Integration Verification and Documentation

As a **Python developer using docvet in a project**,
I want `extend-exclude` patterns to work identically to `exclude` patterns during file discovery,
So that I can trust the merged list filters files correctly in all discovery modes.

**Acceptance Criteria:**

**AC1:** Given a git repository with `extend-exclude = ["vendor"]` in `pyproject.toml`
When a file `vendor/lib.py` is modified and `docvet check` runs (DIFF mode)
Then the file is excluded from discovery

**AC2:** Given a git repository with `extend-exclude = ["vendor"]` in `pyproject.toml`
When `docvet check --all` runs
Then files under `vendor/` are excluded from discovery

**AC3:** Given a git repository with `extend-exclude = ["vendor"]` in `pyproject.toml`
When a file `vendor/lib.py` is staged and `docvet check --staged` runs
Then the file is excluded from discovery

**AC4:** Given a git repository with `extend-exclude = ["*.generated"]` (pattern with no `/`)
When `docvet check --all` runs
Then any file whose path contains a component matching `*.generated` is excluded (fnmatch component-level matching)

**AC5:** Given a git repository with `extend-exclude = ["vendor/legacy/*.py"]` (pattern with `/`)
When `docvet check --all` runs
Then only files matching the full relative path pattern are excluded (fnmatch path-level matching)

**AC6:** Given a project using docvet with no `extend-exclude` configured
When any discovery mode runs
Then behavior is identical to the previous version (backward compatibility)

**AC7:** Given a developer reading the configuration documentation
When they view the config reference table at `docs/site/configuration.md`
Then `extend-exclude` is listed with its type (`list[str]`), default (`[]`), and description
