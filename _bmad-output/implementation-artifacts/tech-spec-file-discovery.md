---
title: 'File Discovery Module'
slug: 'file-discovery'
created: '2026-02-08'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - 'Python 3.12+'
  - 'subprocess (stdlib) for git operations'
  - 'pathlib (stdlib) for filesystem walking'
  - 'fnmatch (stdlib) for exclude pattern matching'
  - 'collections.abc (stdlib) for Sequence type'
  - 'sys (stdlib) for stderr warnings'
files_to_modify:
  - 'src/docvet/discovery.py (new — DiscoveryMode enum + discover_files + private helpers)'
  - 'src/docvet/cli.py (modify — remove DiscoveryMode, import from discovery)'
  - 'tests/unit/test_discovery.py (new)'
  - 'tests/unit/test_cli.py (modify — update if DiscoveryMode import changes affect tests)'
  - 'tests/integration/test_discovery.py (new)'
  - '_bmad-output/project-context.md (modify — update DiscoveryMode migration note)'
  - 'docs/architecture.md (modify — mark discovery.py as Implemented)'
code_patterns:
  - 'DiscoveryMode enum moves to discovery.py (enum.Enum, not StrEnum) — cli.py imports from discovery'
  - 'DocvetConfig dataclass from config.py (frozen, src_root is str, project_root is Path, exclude is list[str])'
  - 'subprocess.run with capture_output=True, text=True, check=False for git commands'
  - 'from __future__ import annotations in every file'
  - 'print(..., file=sys.stderr) for warnings (matches config.py pattern)'
  - 'Private helpers prefixed with _ (single public function per module)'
  - 'Section separators: # ---- comments between logical blocks'
  - 'No assert in production code — proper error handling only'
test_patterns:
  - 'Unit tests: factory fixtures in test file, monkeypatch.chdir for CWD, capsys for stderr, mocker.patch where USED not DEFINED'
  - 'Integration tests: git_repo fixture from tests/integration/conftest.py, subprocess.run with capture_output=True check=True'
  - 'Two-layer split: unit (fast, mocked) / integration (real git repos)'
  - 'Test naming: test_<what>_when_<condition>_<expected_result>'
  - 'No docstrings on test functions (ruff D rules suppressed for tests)'
  - '--strict-markers enforced — register any new markers in pyproject.toml'
---

# Tech-Spec: File Discovery Module

**Created:** 2026-02-08

## Overview

### Problem Statement

All docvet checks need to know which Python files to analyze, but no discovery module exists yet. The CLI layer has `DiscoveryMode` enum resolution and mutual exclusivity enforcement, but nothing behind it — the check stubs currently ignore the discovery mode entirely. Without this module, no check can operate on real files.

### Solution

Create `src/docvet/discovery.py` with a `discover_files()` function that accepts a `DocvetConfig` object and `DiscoveryMode` enum. It supports four file discovery modes via git subprocess calls and filesystem walking, applies `.py` filtering and configurable exclude patterns following `.gitignore` semantics (industry standard from ruff/black/ty), and returns sorted absolute paths for deterministic downstream consumption. ALL mode uses `git ls-files` for automatic `.gitignore` respect, with `rglob` fallback for non-git directories.

### Scope

**In Scope:**
- `discover_files()` public function accepting `DocvetConfig` + `DiscoveryMode` + optional explicit file sequence
- Four modes: DIFF (git diff — working tree vs index), STAGED (git diff --cached — index vs HEAD), ALL (git ls-files scoped to src_root, rglob fallback), FILES (explicit paths)
- `.py` file filtering across all modes
- Exclude pattern matching using `.gitignore` semantics (pattern without `/` matches path components; pattern with `/` matches relative path)
- `.gitignore` respect in ALL mode via `git ls-files` (tracked + untracked-not-ignored)
- Explicit `--files` bypasses exclude patterns (industry convention: user intent overrides config)
- Non-existent explicit files: warn on stderr + skip (matches ruff/mypy behavior)
- No symlink following (industry standard — ruff, black, ty all skip symlinks)
- Sorted absolute paths output for deterministic results
- Graceful handling of non-git directories (ALL falls back to rglob; FILES works regardless; DIFF/STAGED return empty + stderr warning)
- Unit tests for ALL, FILES modes + filtering/exclusion logic
- Integration tests for DIFF, STAGED modes using `git_repo` fixture

**Out of Scope:**
- CLI wiring (connecting `discover_files` to check stubs) — separate PR (#16)
- Reporting integration
- Any check module implementations
- `--diff-filter` customization beyond the default `ACMR`
- `extend-exclude` config key (future enhancement — let users add to defaults without replacing)

## Context for Development

### Codebase Patterns

- Every file starts with `from __future__ import annotations`
- Google-style docstrings with full Args/Returns/Raises sections
- `subprocess.run` for git operations — no gitpython dependency
- `DocvetConfig` is a frozen dataclass: `project_root: Path`, `src_root: str` (relative, e.g. `"src"`), `exclude: list[str]` (default: `["tests", "scripts"]`)
- `DiscoveryMode` is `enum.Enum` (not StrEnum) with members: `DIFF`, `STAGED`, `ALL`, `FILES` — currently in `cli.py`, moving to `discovery.py` in this PR
- 88-char soft limit, 100-char hard limit
- f-strings for formatting, %-formatting for log messages
- Warnings use `print(..., file=sys.stderr)` — matches `config.py` pattern
- Private helpers use `_leading_underscore` naming
- Module-level section separators: `# ------- Comments -------`
- No `assert` in production code (S101 only suppressed in tests)
- Single public function per module pattern (e.g., `load_config` in `config.py`)

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `src/docvet/cli.py` | `class DiscoveryMode` (to be moved), `_resolve_discovery_mode()` helper, `_run_*` stubs |
| `src/docvet/config.py` | `class DocvetConfig` — `src_root`, `exclude`, `project_root` fields. `_validate_keys()` — stderr warning pattern to follow |
| `tests/integration/conftest.py` | `git_repo` fixture — `tmp_path` with `git init` + user config |
| `tests/unit/test_config.py` | Factory fixture pattern (`write_pyproject`) to emulate |
| `tests/unit/test_cli.py` | `CliRunner` + `_strip_ansi` helper pattern |
| `pyproject.toml` | `[tool.pytest.ini_options]` — `--strict-markers`, registered markers |

### Technical Decisions

1. **Accept `DocvetConfig` object** — Cleaner call site from CLI; config already bundles `src_root`, `exclude`, `project_root`
2. **Move `DiscoveryMode` enum to `discovery.py`** — Correct dependency direction: `cli → discovery → config`. Prevents circular `discovery → cli` import. The enum semantically belongs in the discovery module. CLI imports it from there. Project-context doc already planned this migration.
3. **`--all` walks `project_root / src_root`** — Respects configured source root, excludes tests/docs/scripts by path scoping
4. **`--diff-filter=ACMR`** — Excludes deleted files (Added, Copied, Modified, Renamed). Note: DIFF mode (`git diff --name-only`) compares working tree to **index** (staging area), not to HEAD. This means: a file modified but not staged appears in DIFF results; a file that was `git add`'d then not further modified does NOT appear. This is correct for docvet's workflow — DIFF catches "what you haven't staged yet" and STAGED catches "what you're about to commit."
5. **Exclude patterns follow `.gitignore` semantics** — Pattern without `/` matches any path component; pattern with `/` matches full relative path from project root. Uses `fnmatch` (stdlib). This matches ruff/black/ty conventions that users already understand. See **Exclude Pattern Matrix** below for exact specification.
6. **ALL mode uses `git ls-files`** — `git ls-files --cached --others --exclude-standard -- '*.py'` scoped to `src_root`. Gives `.gitignore` respect for free (skips `.venv`, `__pycache__`, `build/`, etc.). Falls back to `rglob` in non-git directories (note: non-git fallback does NOT get `.gitignore` filtering — users must rely on `exclude` patterns).
7. **Explicit `--files` bypasses exclude patterns** — Industry convention (ruff, mypy, black). If the user explicitly names a file, exclusions don't apply.
8. **Non-existent explicit files: warn + skip** — Matches ruff/mypy behavior. Print warning to stderr, continue with remaining files. Don't crash the run.
9. **No symlink following** — Industry standard (ruff, black, ty). Prevents infinite loops from circular symlinks. Enforced in `_walk_all` fallback via `Path.is_symlink()` check. For DIFF/STAGED modes, git itself does not follow symlinks in diff output (`--diff-filter=ACMR` excludes symlink-type changes unless the symlink target changed), so no additional filtering needed.
10. **Return `list[Path]`** — Absolute paths, sorted for determinism
11. **Non-git graceful fallback** — DIFF/STAGED return empty list + stderr warning if not in git repo; ALL falls back to `rglob`; FILES works regardless
12. **Single public API** — `discover_files()` is the only public function (plus `DiscoveryMode` enum). Helpers `_run_git()`, `_is_excluded()`, `_walk_all()` are private.
13. **`_run_git` returns `list[str]`** — Raw line output, not paths. Caller handles path resolution. Accepts `warn: bool = True` keyword arg. On failure with `warn=True`: `print(f"docvet: git {args[0]} failed: {stderr}", file=sys.stderr)` → return `[]`. On failure with `warn=False`: return `[]` silently. Matches `config.py` `"docvet: ..."` message prefix. `_walk_all` calls with `warn=False` to avoid confusing users when falling back to `rglob`.
14. **`_walk_all` validates `src_root` exists** — If `project_root / src_root` doesn't exist, warn on stderr + return `[]`. Config error, not a crash.

### Exclude Pattern Matrix

Exact matching semantics for `_is_excluded(rel_path, exclude)`:

**Rule**: When pattern has no `/`, it matches against **every** component of the path (directories AND filename) via `fnmatch`. This is intentional `.gitignore` behavior — pattern `"test_*"` would match both a directory named `test_utils/` and a file named `test_foo.py`. When pattern has `/`, it matches against the full relative path from project root.

| Pattern | Path (relative from project root) | Match? | Rule |
|---------|-----------------------------------|--------|------|
| `"tests"` | `tests/unit/test_foo.py` | Yes | Component match — `"tests"` == directory `tests` |
| `"tests"` | `src/docvet/test_utils.py` | No | `fnmatch("test_utils.py", "tests")` is False, `fnmatch("docvet", "tests")` is False, etc. |
| `"scripts"` | `scripts/gen.py` | Yes | Component match — `"scripts"` == directory `scripts` |
| `"*.pyc"` | `src/docvet/__pycache__/foo.pyc` | Yes | Glob matches filename `foo.pyc`. Also matches any directory named `*.pyc` (unlikely but consistent). |
| `"test_*"` | `test_utils/helper.py` | **Yes** | Component match — `fnmatch("test_utils", "test_*")` is True. This is intentional `.gitignore` behavior. |
| `"test_*"` | `src/docvet/test_helpers.py` | **Yes** | Component match — `fnmatch("test_helpers.py", "test_*")` is True (matches filename). |
| `"scripts/gen_*.py"` | `scripts/gen_docs.py` | Yes | Relative path match (has `/`) |
| `"scripts/gen_*.py"` | `other/scripts/gen_docs.py` | No | Must match from root (pattern has `/`) |

## Implementation Plan

### Tasks

- [ ] Task 1: Create `src/docvet/discovery.py` with `DiscoveryMode` enum and private helpers
  - File: `src/docvet/discovery.py` (new)
  - Action: Create the module with:
    - Module docstring
    - `from __future__ import annotations`
    - Imports: `enum`, `fnmatch`, `subprocess`, `sys` from stdlib; `Path` from `pathlib`; `Sequence` from `collections.abc`; `DocvetConfig` from `docvet.config`
    - `DiscoveryMode` enum (moved from `cli.py`): `DIFF = auto()`, `STAGED = auto()`, `ALL = auto()`, `FILES = auto()`. Keep as `enum.Enum` (not StrEnum).
    - `_run_git(args: list[str], cwd: Path, *, warn: bool = True) -> list[str]` — Run `subprocess.run(["git", *args], capture_output=True, text=True, check=False, cwd=cwd)`. On `returncode != 0`: if `warn` is True, `print(f"docvet: git {args[0]} failed: {result.stderr.strip()}", file=sys.stderr)` → return `[]`. On success: split stdout by newlines, strip whitespace, filter empty strings. The `warn` parameter allows `_walk_all` to suppress the git-failure warning when falling back to `rglob` (avoids confusing users who see a warning but then get results anyway).
    - `_is_excluded(rel_path: str, exclude: list[str]) -> bool` — First normalize `rel_path` to forward slashes (`rel_path.replace("\\", "/")`) for cross-platform safety (git returns POSIX paths, but `rglob` fallback may return OS-native paths on Windows). Then for each pattern in `exclude`: if pattern contains `/`, match against full normalized `rel_path` with `fnmatch.fnmatch`; if pattern has no `/`, match against each component of `PurePosixPath(rel_path).parts` with `fnmatch.fnmatch`. Return `True` on first match.
    - `_walk_all(config: DocvetConfig) -> list[Path]` — Resolve `root = config.project_root / config.src_root`. If `root` doesn't exist: warn `"docvet: src-root '{config.src_root}' not found"` to stderr → return `[]`. Try `git ls-files --cached --others --exclude-standard -- '*.py'` with `cwd=root` and `warn=False` (suppress git failure warning since we fall back silently). If git succeeds: resolve each line to absolute path, filter `.py` (defensive — `-- '*.py'` pathspec should already limit results, but filter ensures correctness if git behavior varies), filter `_is_excluded`, skip symlinks. If git fails (non-git directory): fallback to iterating `root.rglob("*.py")`, skip symlinks via `path.is_symlink()`, filter `_is_excluded` using path relative to `config.project_root`. **Path conversion**: use `PurePosixPath(path.relative_to(config.project_root)).as_posix()` to produce forward-slash relative path strings, ensuring cross-platform consistency with `_is_excluded`'s normalization.
  - Notes: Use `# ---------------------------------------------------------------------------` section separators between logical blocks (Enums, Private helpers, Public API). All functions get full Google-style docstrings (both public and private — project convention per CLAUDE.md). The module docstring is **mandatory** for `interrogate` compliance (95% threshold). `interrogate` config has `ignore-private = true` so private function docstrings won't be enforced by CI, but we add them anyway per project convention.

- [ ] Task 2: Implement `discover_files()` public function
  - File: `src/docvet/discovery.py`
  - Action: Add the public function:
    - Signature: `def discover_files(config: DocvetConfig, mode: DiscoveryMode, *, files: Sequence[Path] = ()) -> list[Path]`
    - **Guard**: At the top of the function, assert `config.project_root.is_absolute()` — raise `ValueError` if not. Prevents subtle bugs from manual `DocvetConfig` construction in tests or future callers. `load_config` always produces absolute paths, but direct construction might not.
    - DIFF mode: `_run_git(["diff", "--name-only", "--diff-filter=ACMR"], cwd=config.project_root)` → returns relative paths (e.g. `"src/docvet/cli.py"`). Pipeline: (1) filter lines ending `.py`, (2) pass relative path string to `_is_excluded(rel_path, config.exclude)`, (3) resolve to absolute via `(config.project_root / rel_path).resolve()`. **Order matters**: filter with relative paths FIRST, resolve to absolute LAST. Prefer a generator pipeline — chain filter steps lazily, let `sorted()` materialize the final list. Avoids intermediate list allocations for large repos.
    - STAGED mode: `_run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=config.project_root)` → same filtering pipeline as DIFF (relative → filter `.py` → `_is_excluded` → resolve absolute). Same generator pipeline approach.
    - ALL mode: delegate to `_walk_all(config)`
    - FILES mode: iterate `files`, for each: check `.suffix == ".py"` (skip non-Python), check `.exists()` (warn + skip if missing: `print(f"docvet: file not found: {path}", file=sys.stderr)`), resolve to absolute. Do NOT apply `_is_excluded` (explicit files bypass excludes).
    - All modes: return `sorted(paths)` for determinism
  - Notes: The `files` parameter is keyword-only. Empty tuple default means no `None` check needed — `files` is always iterable. If `mode is DiscoveryMode.FILES` and `files` is empty, return `[]`.

- [ ] Task 3: Update `src/docvet/cli.py` — remove `DiscoveryMode`, import from `discovery`
  - File: `src/docvet/cli.py`
  - Action:
    - Remove the `class DiscoveryMode(enum.Enum)` definition and its docstring
    - Remove `import enum` if no longer needed (check if `OutputFormat` and `FreshnessMode` still need it — they do, keep it)
    - Add import: `from docvet.discovery import DiscoveryMode`
    - Verify all references to `DiscoveryMode` still work (used in `_resolve_discovery_mode` return type, `_run_*` stubs, subcommand signatures)
  - Notes: `enum` import stays because `OutputFormat(enum.StrEnum)` and `FreshnessMode(enum.StrEnum)` still need it. Only the `DiscoveryMode` class moves.

- [ ] Task 4: Verify existing CLI tests still pass
  - File: `tests/unit/test_cli.py`
  - Action: Run `uv run pytest tests/unit/test_cli.py -v`. Tests reference `DiscoveryMode` only indirectly via CLI flags (not by importing the enum), so they should pass without changes. If any test imports `DiscoveryMode` from `docvet.cli`, update the import to `docvet.discovery`.
  - Notes: This is a verification step, not a code change step (unless imports need updating).

- [ ] Task 5: Create `tests/unit/test_discovery.py` — unit tests
  - File: `tests/unit/test_discovery.py` (new)
  - Action: Create unit test file with:
    - `from __future__ import annotations`
    - Imports: `from pathlib import Path`, `import subprocess`, `import pytest`, `from docvet.discovery import DiscoveryMode, discover_files, _is_excluded, _run_git`
    - **Mocking strategy**: `_is_excluded` and `_run_git` tests call the private functions **directly** with no mocking (they test pure logic). `discover_files` ALL/DIFF/STAGED tests mock `subprocess.run` at `"docvet.discovery.subprocess.run"` to control git behavior. Never mock `_run_git` or `_walk_all` — always mock at the `subprocess.run` boundary to test the actual fallback logic.
    - **`_is_excluded` tests** (test the exclude pattern matrix):
      - `test_is_excluded_when_component_matches_returns_true` — `"tests"` vs `"tests/unit/test_foo.py"` → True
      - `test_is_excluded_when_component_partial_match_returns_false` — `"tests"` vs `"src/docvet/test_utils.py"` → False
      - `test_is_excluded_when_filename_glob_matches_returns_true` — `"*.pyc"` vs `"src/__pycache__/foo.pyc"` → True
      - `test_is_excluded_when_path_pattern_matches_returns_true` — `"scripts/gen_*.py"` vs `"scripts/gen_docs.py"` → True
      - `test_is_excluded_when_path_pattern_wrong_root_returns_false` — `"scripts/gen_*.py"` vs `"other/scripts/gen_docs.py"` → False
      - `test_is_excluded_when_empty_exclude_returns_false` — `[]` vs any path → False
    - **`_run_git` tests** (mock subprocess):
      - `test_run_git_when_success_returns_lines` — mock `returncode=0`, stdout with lines → returns stripped list
      - `test_run_git_when_failure_returns_empty_and_warns` — mock `returncode=128` → returns `[]`, capsys stderr contains `"docvet: git"`
      - `test_run_git_when_failure_and_warn_false_returns_empty_silently` — mock `returncode=128`, `warn=False` → returns `[]`, capsys stderr is empty
      - `test_run_git_when_empty_stdout_returns_empty` — mock `returncode=0`, stdout="" → returns `[]`
    - **`discover_files` ALL mode tests** (mock git, use `tmp_path`):
      - `test_discover_files_all_mode_when_src_root_missing_warns_and_returns_empty` — no `src/` dir → `[]` + stderr warning
      - `test_discover_files_all_mode_non_git_fallback_returns_py_files` — mock git failure, create `.py` files in `tmp_path` tree → returns them
      - `test_discover_files_all_mode_non_git_fallback_skips_symlinks` — create symlink `.py` file → not in results
      - `test_discover_files_all_mode_non_git_fallback_applies_excludes` — `exclude=["tests"]`, create `tests/foo.py` → not in results
      - `test_discover_files_all_mode_non_git_fallback_filters_non_py` — create `.txt` file → not in results
    - **`discover_files` FILES mode tests**:
      - `test_discover_files_files_mode_returns_existing_py_files` — create `.py` files → returned
      - `test_discover_files_files_mode_when_file_missing_warns_and_skips` — non-existent path → skipped + stderr warning
      - `test_discover_files_files_mode_bypasses_exclude_patterns` — file in excluded dir → still returned
      - `test_discover_files_files_mode_filters_non_py` — `.txt` file → not in results
      - `test_discover_files_files_mode_when_empty_returns_empty` — `files=()` → `[]`
    - **General tests**:
      - `test_discover_files_returns_sorted_absolute_paths` — verify sorted + all `.is_absolute()`
      - `test_discover_files_returns_empty_list_when_no_matches` — empty dir → `[]`
      - `test_discover_files_when_project_root_relative_raises_value_error` — `DocvetConfig(project_root=Path("relative"))` → `ValueError`
  - Notes: Use `mocker.patch("docvet.discovery.subprocess.run")` for mocking. Use `capsys` for stderr assertions. Use `tmp_path` for filesystem trees. Follow `test_<what>_when_<condition>_<expected>` naming. Importing private functions (`_is_excluded`, `_run_git`) is acceptable for direct unit testing — ruff's `PLC2701` is not currently enabled. If it fires, add `"PLC2701"` to the `tests/**/*.py` per-file-ignores in `pyproject.toml`.

- [ ] Task 6: Create `tests/integration/test_discovery.py` — integration tests
  - File: `tests/integration/test_discovery.py` (new)
  - Action: Create integration test file using `git_repo` fixture:
    - `from __future__ import annotations`
    - Imports: `import subprocess`, `from pathlib import Path`, `import pytest`, `from docvet.config import DocvetConfig`, `from docvet.discovery import DiscoveryMode, discover_files`
    - Helper: `_git(args, cwd)` — `subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)`
    - Helper: `_make_config(git_repo, **overrides)` — return `DocvetConfig(project_root=git_repo, src_root=".", **overrides)`
    - **DIFF mode tests**:
      - `test_diff_mode_when_file_modified_returns_modified_file` — create file, commit, modify, run discover → file in results
      - `test_diff_mode_when_no_changes_returns_empty` — clean repo → `[]`
      - `test_diff_mode_filters_non_py_from_diff` — modify `.txt` file → not in results
      - `test_diff_mode_applies_exclude_patterns` — modify file in `tests/` dir, `exclude=["tests"]` → not in results
      - `test_diff_mode_when_file_renamed_returns_new_name` — `git mv old.py new.py` (unstaged rename via working tree), run discover → `new.py` in results, `old.py` not in results. Validates the "R" in `--diff-filter=ACMR`.
    - **STAGED mode tests**:
      - `test_staged_mode_when_file_staged_returns_staged_file` — create file, `git add`, run discover → file in results
      - `test_staged_mode_when_nothing_staged_returns_empty` — no staged changes → `[]`
      - `test_staged_mode_applies_exclude_patterns` — stage file in `tests/` dir, `exclude=["tests"]` → not in results
    - **ALL mode with git tests**:
      - `test_all_mode_with_git_returns_tracked_py_files` — commit `.py` files, run discover → returned
      - `test_all_mode_with_git_excludes_gitignored_files` — add `.py` to `.gitignore`, create file → not in results
      - `test_all_mode_applies_exclude_on_top_of_git` — tracked file in `tests/`, `exclude=["tests"]` → not in results
      - `test_all_mode_with_src_root_scoping` — create `src/pkg/mod.py` and `other/mod.py`, commit both, `src_root="src"` → only `src/pkg/mod.py` returned (validates `src_root` scoping to subdirectory)
    - **Empty repo tests** (note: `git diff --name-only` compares working tree to index — works fine with zero commits, returns empty. `git diff --cached` compares index to HEAD — with zero commits, it compares to empty tree, so staged files ARE returned correctly):
      - `test_diff_mode_when_empty_repo_returns_empty` — `git init` only, no files at all → `[]` (no error)
      - `test_staged_mode_when_empty_repo_with_staged_file_returns_file` — `git init`, create+stage `.py` file (no commit) → file in results (compares to empty tree)
  - Notes: Use real git operations (no mocks). `git_repo` fixture from `tests/integration/conftest.py`. Create `DocvetConfig` instances with `project_root=git_repo`.

- [ ] Task 7: Update project documentation
  - Files: `_bmad-output/project-context.md`, `docs/architecture.md`
  - Action:
    - `_bmad-output/project-context.md`: Update the Framework Rules section line about `DiscoveryMode` migration — change from "will move to `discovery.py`" to "lives in `discovery.py`" (migration complete). Add note about `discover_files()` accepting `DocvetConfig` and the `warn` parameter on `_run_git`.
    - `docs/architecture.md`: Change `discovery.py (Planned)` to `discovery.py (Implemented)`. Update the module description to reflect the actual implementation: four modes, `git ls-files` for ALL mode, `.gitignore`-semantic excludes, `DiscoveryMode` enum lives here. Also fix pre-existing staleness: change `config.py (Planned)` to `config.py (Implemented)` since it was already implemented in a prior PR.
  - Notes: Documentation updates are part of the implementation, not a post-merge afterthought. Keep descriptions concise — match the style of the existing architecture doc entries.

- [ ] Task 8: Run full quality gates
  - Action: Run all quality checks to verify nothing is broken:
    - `uv run ruff check .`
    - `uv run ruff format .`
    - `uv run ty check`
    - `uv run pytest --cov=docvet --cov-report=term-missing`
    - `uv run interrogate -v`
  - Notes: Fix any issues found. Ensure coverage stays >= 85%.

### Acceptance Criteria

**`_is_excluded` helper:**
- [ ] AC 1: Given pattern `"tests"` (no `/`), when checking path `"tests/unit/test_foo.py"`, then returns `True` (component match).
- [ ] AC 2: Given pattern `"tests"`, when checking path `"src/docvet/test_utils.py"`, then returns `False` (partial name, not component match).
- [ ] AC 3: Given pattern `"*.pyc"` (no `/`), when checking path `"src/__pycache__/foo.pyc"`, then returns `True` (filename glob match).
- [ ] AC 4: Given pattern `"scripts/gen_*.py"` (has `/`), when checking path `"scripts/gen_docs.py"`, then returns `True` (relative path match).
- [ ] AC 5: Given pattern `"scripts/gen_*.py"`, when checking path `"other/scripts/gen_docs.py"`, then returns `False` (must match from root).

**`_run_git` helper:**
- [ ] AC 6: Given a successful git command, when `_run_git` is called, then it returns a list of stripped non-empty stdout lines.
- [ ] AC 7: Given a failing git command (non-zero exit) with `warn=True` (default), when `_run_git` is called, then it returns `[]` and prints `"docvet: git <cmd> failed: <stderr>"` to stderr.
- [ ] AC 7b: Given a failing git command with `warn=False`, when `_run_git` is called, then it returns `[]` with NO stderr output.

**DIFF mode:**
- [ ] AC 8: Given a git repo with unstaged modifications to a `.py` file, when `discover_files` is called with `DiscoveryMode.DIFF`, then the modified file is in the result.
- [ ] AC 9: Given a git repo with unstaged modifications to a `.txt` file, when `discover_files` is called with `DiscoveryMode.DIFF`, then the `.txt` file is NOT in the result.
- [ ] AC 10: Given a clean git repo (no changes), when `discover_files` is called with `DiscoveryMode.DIFF`, then the result is `[]`.
- [ ] AC 11: Given a git repo with a modified `.py` file in an excluded directory, when `discover_files` is called with `DiscoveryMode.DIFF`, then the file is NOT in the result.

**STAGED mode:**
- [ ] AC 12: Given a git repo with a staged `.py` file, when `discover_files` is called with `DiscoveryMode.STAGED`, then the staged file is in the result.
- [ ] AC 13: Given a git repo with no staged changes, when `discover_files` is called with `DiscoveryMode.STAGED`, then the result is `[]`.
- [ ] AC 14: Given a git repo with a staged `.py` file in an excluded directory, when `discover_files` is called with `DiscoveryMode.STAGED`, then the file is NOT in the result.

**ALL mode:**
- [ ] AC 15: Given a git repo with tracked `.py` files, when `discover_files` is called with `DiscoveryMode.ALL`, then tracked files are returned.
- [ ] AC 16: Given a git repo with a `.gitignore`d `.py` file, when `discover_files` is called with `DiscoveryMode.ALL`, then the gitignored file is NOT in the result.
- [ ] AC 17: Given a non-git directory with `.py` files, when `discover_files` is called with `DiscoveryMode.ALL`, then files are returned via `rglob` fallback.
- [ ] AC 18: Given `src_root` that doesn't exist, when `discover_files` is called with `DiscoveryMode.ALL`, then result is `[]` and a warning is printed to stderr.
- [ ] AC 19: Given a non-git directory with a symlink `.py` file, when `discover_files` is called with `DiscoveryMode.ALL`, then the symlink is NOT in the result.
- [ ] AC 20: Given a non-git directory with files in an excluded dir, when `discover_files` is called with `DiscoveryMode.ALL`, then excluded files are NOT in the result.
- [ ] AC 21: Given a git repo with a tracked `.py` file in an excluded directory, when `discover_files` is called with `DiscoveryMode.ALL`, then the excluded file is NOT in the result (excludes apply on top of `git ls-files`).

**FILES mode:**
- [ ] AC 22: Given a list of existing `.py` files, when `discover_files` is called with `DiscoveryMode.FILES`, then all files are returned.
- [ ] AC 23: Given a list containing a non-existent file, when `discover_files` is called with `DiscoveryMode.FILES`, then the missing file is skipped and a warning is printed to stderr.
- [ ] AC 24: Given a list containing a `.py` file in an excluded directory, when `discover_files` is called with `DiscoveryMode.FILES`, then the file IS returned (explicit files bypass excludes).
- [ ] AC 25: Given a list containing a non-`.py` file, when `discover_files` is called with `DiscoveryMode.FILES`, then the non-Python file is NOT returned.
- [ ] AC 26: Given `files=()` (empty default) with `DiscoveryMode.FILES`, when `discover_files` is called, then result is `[]`.

**General:**
- [ ] AC 27: Given any discovery mode with results, when `discover_files` returns, then all paths are absolute and the list is sorted.
- [ ] AC 28: Given `DiscoveryMode.DIFF` in a non-git directory, when `discover_files` is called, then result is `[]` and a warning is printed to stderr.
- [ ] AC 29: Given `DiscoveryMode.STAGED` in a non-git directory, when `discover_files` is called, then result is `[]` and a warning is printed to stderr.

**Input validation:**
- [ ] AC 30: Given a `DocvetConfig` with a relative `project_root`, when `discover_files` is called, then it raises `ValueError`.

**Enum migration:**
- [ ] AC 31: Given the updated `cli.py` importing `DiscoveryMode` from `discovery`, when all existing CLI tests run, then they pass without modification.

## Additional Context

### Dependencies

- No new dependencies — all stdlib (`subprocess`, `pathlib`, `fnmatch`, `collections.abc`, `sys`, `enum`)
- Depends on existing: `DocvetConfig` from `config.py`
- `DiscoveryMode` enum moves INTO this module (was in `cli.py`). `cli.py` will import from `discovery.py`.

### Testing Strategy

- **Unit tests** (`tests/unit/test_discovery.py`):
  - `_is_excluded`: Full exclude pattern matrix (6 test cases covering all matching rules)
  - `_run_git`: Success, failure+warning, failure+silent, empty stdout (4 test cases)
  - ALL mode: missing `src_root`, non-git fallback, symlink skipping, exclude application, non-py filtering (5 test cases)
  - FILES mode: happy path, missing file warn+skip, exclude bypass, non-py filtering, None explicit_files (5 test cases)
  - General: sorted absolute paths, empty results, relative project_root guard (3 test cases)
  - Total: ~23 unit tests
  - Mocking: `mocker.patch("docvet.discovery.subprocess.run")` for git calls
  - Fixtures: `tmp_path` for filesystem trees, `capsys` for stderr

- **Integration tests** (`tests/integration/test_discovery.py`):
  - DIFF mode: modified file, no changes, non-py filtering, exclude patterns, renamed file (5 test cases)
  - STAGED mode: staged file, nothing staged, exclude patterns (3 test cases)
  - ALL mode: tracked files, gitignored files, excludes on top of git, src_root scoping (4 test cases)
  - Empty repo: diff and staged (2 test cases)
  - Total: ~15 integration tests
  - Uses `git_repo` fixture with real git operations

### Notes

- GitHub Issue: #6
- Branch: `feat/6-discovery`
- Closes: #6
- **Risk**: `git ls-files --others` may behave differently across git versions. Mitigated by integration tests with real git repos.
- **Risk**: Empty repo edge case — `git diff --cached` with zero commits compares index to empty tree (returns all staged files). This is correct behavior but may surprise users. Verified by integration test.
- **Future**: `extend-exclude` config key (Issue not yet created).
- **Future**: `_run_git` silently swallows stderr on success (returncode 0). Git sometimes writes warnings to stderr even on success (e.g., "warning: could not open directory"). Consider logging stderr on success in verbose mode.
- **Limitation**: Non-git fallback in ALL mode does not respect `.gitignore` — documented in technical decisions.
- **Convention**: Documentation updates (`project-context.md`, `architecture.md`) are part of every spec implementation, not post-merge follow-ups.
