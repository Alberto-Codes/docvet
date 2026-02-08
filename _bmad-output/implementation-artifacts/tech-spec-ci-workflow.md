---
title: 'CI Workflow for Quality Gates'
slug: 'ci-workflow'
created: '2026-02-08'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['GitHub Actions', 'uv', 'astral-sh/setup-uv@v7', 'actions/checkout@v6', 'ruff', 'ty 0.0.1a33', 'pytest 9.x', 'pytest-cov', 'interrogate']
files_to_modify: ['pyproject.toml', 'src/docvet/__init__.py', 'tests/unit/test_init.py', '.github/workflows/ci.yml']
code_patterns: ['astral-sh/setup-uv@v7 with enable-cache + cache-suffix', 'matrix python-version', 'uv sync --dev', 'uv run for tool execution', 'concurrency with cancel-in-progress']
test_patterns: ['smoke test for entry point — assert main callable', 'test_package_importable — assert hasattr(docvet, main)', 'test_main_runs — call main() to cover function body for coverage gate']
---

# Tech-Spec: CI Workflow for Quality Gates

**Created:** 2026-02-08

## Overview

### Problem Statement

No CI exists for docvet. All quality checks (lint, format, type check, tests, docstring coverage) are manual. PRs can merge with broken lint, failing tests, or type errors. This blocks the entire build-brick-by-brick strategy since there's no safety net catching regressions.

### Solution

Create a single `.github/workflows/ci.yml` GitHub Actions workflow with four parallel jobs — lint, type check, test+coverage, and interrogate — running on PRs and pushes to `develop`/`main`. Uses `astral-sh/setup-uv` for fast Python/uv setup, Python 3.12+3.13 matrix on ubuntu-latest only.

### Scope

**In Scope:**
- `.github/workflows/ci.yml` with four jobs
- Lint job: `ruff check .` + `ruff format --check .`
- Type check job: `ty check` (hard fail, no continue-on-error)
- Test job: `pytest --cov=docvet --cov-report=term-missing --cov-fail-under=85`
- Interrogate job: docstring coverage check
- Python 3.12 + 3.13 matrix
- ubuntu-latest only
- Triggers on PR to develop/main AND push to develop/main
- `astral-sh/setup-uv` for uv installation and caching

**Out of Scope:**
- Windows/macOS matrix (add when subprocess code exists)
- Release-please (issue #1)
- PyPI publishing (issue #2)
- Integration test runner (no integration tests exist yet)

## Context for Development

### Codebase Patterns

- Build system: hatchling (PEP 517/518)
- Dev deps managed via `[dependency-groups] dev` in pyproject.toml
- `uv sync --dev` installs all dev dependencies
- `.python-version` pinned to 3.12
- Test config in `[tool.pytest.ini_options]` — testpaths = ["tests"]
- ruff configured with Google docstrings, isort, line-length 88/100
- ty configured with `[tool.ty.src] include = ["src", "tests"]`
- interrogate configured at 95% fail-under
- **uv.lock is gitignored** — cannot use `--locked` flag, use `uv sync` without it
- **No test files exist yet** — must create smoke test for coverage gate

### Verified Local State (Step 2 Investigation)

| Check | Result | Action Needed |
| ----- | ------ | ------------- |
| `ruff check .` | FAIL — D104 (missing module docstring), D103 (missing function docstring) in `__init__.py` | Fix: add docstrings to `__init__.py` |
| `ruff format --check .` | PASS | None |
| `ty check` | PASS | None |
| `pytest` | N/A — no test files | Create `tests/unit/test_init.py` |

### Files to Modify/Create

| File | Action | Purpose |
| ---- | ------ | ------- |
| `pyproject.toml` | MODIFY | Add `interrogate` to dev dependencies |
| `src/docvet/__init__.py` | MODIFY | Add module + function docstrings to pass ruff D rules |
| `tests/unit/test_init.py` | CREATE | Smoke tests — assert `main` callable, importable, and runs; passes coverage gate |
| `.github/workflows/ci.yml` | CREATE | CI workflow — 4 parallel jobs |

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `pyproject.toml` | All tool configs (ruff, pytest, ty, interrogate, dev deps) |
| `.python-version` | Python version pin (3.12) |
| `tests/conftest.py` | Root test fixtures (parse_source factory) |
| `.gitignore` | Confirms uv.lock is excluded |

### Technical Decisions

- **uv over pip**: Project uses uv for dependency management (matches stream-ai-pipeline conventions)
- **ty as hard gate**: ty type checker failures block PRs — no continue-on-error
- **85% coverage enforcement**: Enterprise standard, enforced via `--cov-fail-under=85`
- **interrogate included now**: Even with minimal source, establishes the gate early
- **Four separate jobs**: Parallel execution for speed, clear failure attribution
- **All jobs independent**: No dependencies between jobs — parallel is faster, compute is cheap (Winston)
- **Cache key on pyproject.toml**: uv.lock is gitignored, so cache keyed on pyproject.toml hash (Winston)
- **Smoke test required**: Need `tests/unit/test_init.py` with at least one test so coverage gate doesn't fail on 0% (Amelia)
- **CI-friendly pytest flags**: Use `--tb=short` in workflow to keep Actions logs readable (Quinn)
- **Minimal docstring fix for __init__.py**: Two-liner — module docstring + function docstring, will be rewritten by issue #4 anyway (Amelia)
- **Three smoke tests**: `test_main_is_callable` + `test_package_importable` + `test_main_runs` — the third test actually calls `main()` to cover the function body and pass the 85% coverage gate (Adversarial Review F2)
- **Follow-up issue needed**: Commit uv.lock to repo so `--locked` can be used in CI (Mary, deferred)
- **Concurrency control**: Use `concurrency` with `cancel-in-progress: true` to cancel stale runs on rapid pushes (Winston + Barry)
- **Explicit job naming**: Workflow `name: CI`, jobs named `lint`, `type-check`, `test`, `interrogate` for clean GitHub checks UI (Amelia)
- **interrogate as dev dependency**: Must be added to `[dependency-groups] dev` — config exists but package was never listed as a dependency (Adversarial Review F1)
- **uv version not pinned in workflow**: `astral-sh/setup-uv@v7` installs latest uv by default; this is acceptable since uv is stable and backward-compatible (Adversarial Review F7)
- **Action versions verified**: `actions/checkout@v6` (v6.0.2) and `astral-sh/setup-uv@v7` (v7.3.0) confirmed via GitHub API (Adversarial Review F5)

## Implementation Plan

### Tasks

- [ ] Task 0: Add `interrogate` to dev dependencies in `pyproject.toml`
  - File: `pyproject.toml`
  - Action: Add `"interrogate>=5.0"` to the `[dependency-groups] dev` list
  - Notes: The `[tool.interrogate]` config already exists but interrogate itself is not installed as a dev dependency. Without this, `uv run interrogate` will fail with command-not-found in CI. Run `uv sync --dev` after to verify it installs.

- [ ] Task 1: Add docstrings to `src/docvet/__init__.py` to pass ruff D rules
  - File: `src/docvet/__init__.py`
  - Action: Add module-level docstring and function docstring to `main()`
  - Notes: Minimal fix — module docstring `"""Docstring quality vetting for Python projects."""` and function docstring `"""CLI entry point for docvet."""`. Add `from __future__ import annotations` per project convention. Will be fully rewritten by issue #4 (typer CLI scaffold).

- [ ] Task 2: Create smoke tests in `tests/unit/test_init.py`
  - File: `tests/unit/test_init.py`
  - Action: Create three smoke tests — `test_main_is_callable`, `test_package_importable`, and `test_main_runs`
  - Notes: `test_main_is_callable` imports `main` from `docvet` and asserts `callable(main)`. `test_package_importable` imports `docvet` and asserts `hasattr(docvet, "main")`. `test_main_runs` calls `main()` and verifies it completes without error — this is critical because without executing `main()`, the `print(...)` line inside it is never covered, resulting in ~67% line coverage which fails the 85% gate. Use `from __future__ import annotations`.

- [ ] Task 3: Create `.github/workflows/ci.yml` with four parallel jobs
  - File: `.github/workflows/ci.yml`
  - Action: Create the CI workflow with these specifications:
  - Notes:
    - **Workflow name**: `CI`
    - **Concurrency**: `group: ${{ github.workflow }}-${{ github.ref }}` with `cancel-in-progress: true`
    - **Triggers**: `pull_request` targeting `develop` and `main` branches; `push` to `develop` and `main` branches
    - **Shared setup pattern** (all jobs): `actions/checkout@v6` → `astral-sh/setup-uv@v7` with `enable-cache: true`, `cache-suffix: ${{ matrix.python-version }}` → `uv python install ${{ matrix.python-version }}` → `uv sync --dev`
    - **Matrix**: `python-version: ["3.12", "3.13"]`, `os: [ubuntu-latest]`
    - **Job `lint`**: `uv run ruff check .` then `uv run ruff format --check .`
    - **Job `type-check`**: `uv run ty check` (no `continue-on-error`, hard gate)
    - **Job `test`**: `uv run pytest --tb=short --cov=docvet --cov-report=term-missing --cov-fail-under=85`
    - **Job `interrogate`**: `uv run interrogate -v .`
    - **All jobs independent**: No `needs:` between jobs — run fully parallel
    - **Cache cleanup**: Add `uv cache prune --ci` as final step in each job to minimize cache size

### Acceptance Criteria

- [ ] AC 1: Given `src/docvet/__init__.py` has docstrings added, when `uv run ruff check .` is run locally, then it exits with code 0 (no D104/D103 violations)
- [ ] AC 2: Given `src/docvet/__init__.py` is formatted, when `uv run ruff format --check .` is run locally, then it exits with code 0
- [ ] AC 3: Given the codebase type checks cleanly, when `uv run ty check` is run locally, then it exits with code 0
- [ ] AC 4: Given `tests/unit/test_init.py` exists with three smoke tests (including `test_main_runs` which executes `main()`), when `uv run pytest --cov=docvet --cov-fail-under=85` is run locally, then all three tests pass and coverage is >= 85%
- [ ] AC 5: Given `src/docvet/__init__.py` has docstrings, when `uv run interrogate -v .` is run locally, then it reports >= 95% coverage and exits with code 0
- [ ] AC 6: Given the workflow file exists at `.github/workflows/ci.yml`, when a PR is opened targeting `develop`, then all four jobs (lint, type-check, test, interrogate) run on Python 3.12 and 3.13
- [ ] AC 7: Given all local checks pass (ACs 1-5), when the CI workflow runs in GitHub Actions, then all four jobs pass green on both Python versions
- [ ] AC 8: Given the workflow triggers on push, when commits are pushed to `develop` or `main`, then the CI workflow runs automatically

## Additional Context

### Dependencies

- Closes GitHub issue #3
- No dependency on other issues — this is foundational infra

### Testing Strategy

- The workflow itself is tested by pushing to the branch and observing GitHub Actions output
- Must add `tests/unit/test_init.py` with three smoke tests: `test_main_is_callable` (assert callable) + `test_package_importable` (assert hasattr) + `test_main_runs` (call main() to cover function body) so 85% coverage gate passes on the minimal codebase
- Verify `ruff check .`, `ruff format --check .`, and `ty check` pass locally before pushing
- Once CI is green, recommend enabling branch protection on `develop` requiring all checks to pass

### Notes

- `astral-sh/setup-uv@v7` is the latest action version — handles install + caching
- Use `enable-cache: true` with `cache-suffix` keyed on Python version for matrix builds
- `uv cache prune --ci` at end of workflow to minimize cache size
- ty is pre-release (0.0.1a33) but user explicitly wants it as hard gate
- uv docs recommend `uv sync --locked` but we gitignore uv.lock, so use `uv sync` without `--locked`
- uv version is not pinned in workflow — `astral-sh/setup-uv@v7` installs latest uv, which is acceptable
- `actions/checkout@v6` is current checkout action version
