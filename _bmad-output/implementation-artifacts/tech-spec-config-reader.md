---
title: 'Implement pyproject.toml config reader'
slug: 'config-reader'
created: '2026-02-07'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.12+', 'tomllib (stdlib)', 'dataclasses (stdlib)', 'pathlib (stdlib)', 'typer (CLI integration)']
files_to_modify: ['src/docvet/config.py (CREATE)', 'tests/unit/test_config.py (CREATE)', 'src/docvet/cli.py (MODIFY: add --config global option)']
code_patterns: ['nested frozen dataclasses', 'Annotated type aliases for CLI options', 'ctx.obj stores raw types (str not Path)', 'private _leading_underscore helpers', 'StrEnum for CLI-facing enums', 'from __future__ import annotations on every file']
test_patterns: ['test_<what>_<condition>_<expected>', 'tmp_path for filesystem tests', 'one assert per test', 'no docstrings on tests', 'CliRunner() no kwargs', 'assert exit_code and output']
---

# Tech-Spec: Implement pyproject.toml config reader

**Created:** 2026-02-07

## Overview

### Problem Statement

Every docvet check module (enrichment, freshness, coverage, griffe) depends on configuration values — src-root, exclude patterns, fail-on/warn-on severity, thresholds. No configuration module exists. Without it, checks cannot function and the CLI has no way to load user preferences.

### Solution

Create `src/docvet/config.py` that discovers and parses `[tool.docvet]` from `pyproject.toml`, returning a composition of nested frozen dataclasses (`DocvetConfig` containing `FreshnessConfig`, `EnrichmentConfig`). Uses stdlib `tomllib` (zero new dependencies). Follows the industry-standard pattern used by ruff, mypy, black, and pytest: walk up directory tree to find config, error on unknown keys with helpful messages listing valid alternatives, and allow CLI flag overrides. Exposes four public symbols: `DocvetConfig`, `FreshnessConfig`, `EnrichmentConfig`, and `load_config()`. The nested config classes are public because downstream check modules need them for type hints (e.g., `enrichment.py` type-hinting a parameter as `EnrichmentConfig`).

### Scope

**In Scope:**

- `src/docvet/config.py` module with nested frozen dataclasses (`DocvetConfig`, `FreshnessConfig`, `EnrichmentConfig`) and `load_config()` function — four public symbols (downstream checks need nested types for type hints)
- pyproject.toml discovery: walk up from CWD, stop at first `pyproject.toml` found (`.git` or filesystem root as safety net)
- `--config` CLI flag to override discovery with explicit path
- Default `src-root` using `[".", "src"]` heuristic (ruff/ty pattern — check if `src/` exists)
- `package-name` is optional with no default — only griffe check needs it; validated at check runtime, not config load
- Strict validation: error and exit on unknown keys with helpful messages (include offending key + list valid alternatives, ruff pattern)
- Sensible defaults when `[tool.docvet]` section is entirely missing — warn-on everything by default, empty fail-on
- Sensible defaults when no `pyproject.toml` is found anywhere — zero-config must work
- Single private helper for TOML kebab-case to Python snake_case translation
- Nested config sections: `[tool.docvet.freshness]`, `[tool.docvet.enrichment]`
- Full config schema: 16 user-facing leaf fields across 3 dataclasses (5 top-level + 2 freshness + 9 enrichment) plus `project_root` (internal) and 2 nested container fields
- Error handling: `tomllib.TOMLDecodeError` propagates, validation errors use `SystemExit(1)` to stderr — no custom exception class
- Unit tests covering: full config, partial config, missing config, missing file, invalid values, discovery

**Out of Scope:**

- Parsing `[tool.hatch.build.targets.wheel]` or any build-system config for auto-detection
- `--isolated` flag (can add in a future issue)
- CLI override merging logic (separate concern — wired up when checks are implemented)
- Multi-file config merging or per-directory config hierarchy
- Config file formats other than pyproject.toml (no `docvet.toml` yet)

## Context for Development

### Codebase Patterns

- All files use `from __future__ import annotations` at the top
- Google-style docstrings with one-line summary max 80 chars, ends with period
- Modern type hints: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- f-strings for formatting, no mutable defaults, no bare exceptions
- 88-char soft limit (formatter), 100-char hard limit (linter)
- Entry point: `docvet = "docvet.cli:app"` in pyproject.toml
- CLI global options in `@app.callback(invoke_without_command=True)`, stored in `ctx.obj` dict as **raw types** (strings, not enums/Paths)
- `Annotated` type aliases defined at module level for shared CLI options (e.g., `StagedOption`, `AllOption`)
- Private helpers use `_leading_underscore` prefix
- No `assert` in production code — proper error handling only
- Tests use `test_<what>_<condition>_<expected>` naming, one assert per test, no docstrings
- Test fixtures in `tests/conftest.py` (global), `tests/integration/conftest.py` (git-only)
- Valid check names: `enrichment`, `freshness`, `coverage`, `griffe`

### Files to Reference

| File | Purpose | Key Details |
| ---- | ------- | ----------- |
| `src/docvet/cli.py` | CLI entry — add `--config` global option | `main()` callback at line 159, `ctx.obj` dict pattern, `Annotated` aliases at line 43-47 |
| `src/docvet/__init__.py` | Package entry point | Module docstring only, 3 lines |
| `pyproject.toml` | Build config + existing `[tool.*]` sections | Reference for TOML patterns; no `[tool.docvet]` exists yet |
| `tests/unit/test_cli.py` | Test patterns to follow | 261 lines, `CliRunner()` no kwargs, `_strip_ansi()` helper, section comments |
| `tests/conftest.py` | Shared fixtures | `parse_source` factory fixture |
| `docs/product-vision.md` | Full config schema (lines 148-169) | Canonical source for all config keys and types |
| `_bmad-output/project-context.md` | AI agent rules | Line 110: `[tool.docvet]` may not exist = defaults, not error |

### Technical Decisions

1. **Discovery algorithm**: Walk up from CWD looking for `pyproject.toml`. Stop at first one found; `.git` boundary or filesystem root as safety net. Single config file per run (no merging). Supports monorepo layouts where `pyproject.toml` is nested below `.git`.
2. **Source root default**: Auto-detect `[".", "src"]` — if `src/` directory exists relative to pyproject.toml location, use `"src"`, otherwise `"."`. User can override via `src-root` config key to any arbitrary relative path (e.g., `"src/my_package"` as shown in the vision doc). The auto-detect heuristic only produces `"src"` or `"."` — it does not attempt deeper package detection. Users with non-standard layouts set `src-root` explicitly.
3. **`package-name` handling**: Optional field, no default, no auto-detection. Only griffe check needs it. If not set and griffe runs, griffe check errors at runtime — not the config loader. Keeps config module lean.
4. **Dataclass composition**: Top-level `DocvetConfig` composes `FreshnessConfig` and `EnrichmentConfig` as nested frozen dataclasses. Keeps each check's config isolated and extensible. Four public symbols: `DocvetConfig`, `FreshnessConfig`, `EnrichmentConfig`, `load_config()`. Nested config classes are public for downstream type hints.
5. **Validation strategy**: Strict — unknown keys cause immediate error with helpful message including the offending key name and listing all valid alternatives (ruff pattern). Invalid types/values also error.
6. **Error handling**: Three failure modes — (a) no pyproject.toml found: return all defaults silently (zero-config works), (b) malformed TOML: let `tomllib.TOMLDecodeError` propagate naturally, (c) validation errors (unknown keys, wrong types): `SystemExit(1)` with formatted message to stderr. No custom exception class.
7. **Kebab-to-snake translation**: Single private helper `_kebab_to_snake()` handles all TOML key name conversion during parsing. One place, no scattered conversions.
8. **Default severity**: `warn-on = ["freshness", "enrichment", "griffe", "coverage"]`, `fail-on = []`. All checks advisory by default — power users opt into fail-on. Avoids confusing first experience where optional-dep checks (griffe) cause hard failures.
9. **No new dependencies**: stdlib `tomllib` (Python 3.11+) for TOML parsing, `dataclasses` for config structure. Note: `tomllib.load()` requires binary mode (`open(path, "rb")`).
10. **`--config` CLI integration**: Add `ConfigOption` Annotated alias at module level. Store as `ctx.obj["config"] = str(config) if config is not None else None` — raw string, matching existing `ctx.obj["output"]` pattern.
11. **Config precedence**: defaults < pyproject.toml < CLI flags (industry standard). This module handles the first two layers. CLI merging is out of scope.

## Implementation Plan

### Tasks

- [x] Task 1: Create `FreshnessConfig` frozen dataclass
  - File: `src/docvet/config.py` (CREATE)
  - Action: Define `FreshnessConfig` as a `@dataclass(frozen=True)` with two fields:
    - `drift_threshold: int = 30`
    - `age_threshold: int = 90`
  - Notes: Start the file with `from __future__ import annotations`, module docstring, stdlib imports (`dataclasses`, `pathlib`, `sys`, `tomllib`). All private helpers and constants go in this file.

- [x] Task 2: Create `EnrichmentConfig` frozen dataclass
  - File: `src/docvet/config.py`
  - Action: Define `EnrichmentConfig` as a `@dataclass(frozen=True)` with nine fields:
    - `require_examples: list[str] = field(default_factory=lambda: ["class", "protocol", "dataclass", "enum"])`
    - `require_raises: bool = True`
    - `require_yields: bool = True`
    - `require_warns: bool = True`
    - `require_receives: bool = True`
    - `require_other_parameters: bool = True`
    - `require_typed_attributes: bool = True`
    - `require_cross_references: bool = True`
    - `prefer_fenced_code_blocks: bool = True`
  - Notes: Use `field(default_factory=...)` for the list default to avoid mutable default.

- [x] Task 3: Create `DocvetConfig` top-level frozen dataclass
  - File: `src/docvet/config.py`
  - Action: Define `DocvetConfig` as a `@dataclass(frozen=True)` composing the nested configs:
    - `src_root: str = "."` (safe fallback — `load_config()` always resolves this via `_resolve_src_root()` heuristic before construction)
    - `package_name: str | None = None`
    - `exclude: list[str] = field(default_factory=lambda: ["tests", "scripts"])`
    - `fail_on: list[str] = field(default_factory=list)`
    - `warn_on: list[str] = field(default_factory=lambda: ["freshness", "enrichment", "griffe", "coverage"])`
    - `freshness: FreshnessConfig = field(default_factory=FreshnessConfig)`
    - `enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)`
    - `project_root: Path = field(default_factory=Path.cwd)` (resolved path to the directory containing the discovered pyproject.toml, or CWD if none found). **Note**: `load_config()` always passes an explicit `project_root` via `Path.cwd().resolve()` — the `default_factory` is only a fallback for bare `DocvetConfig()` construction. Using `.resolve()` in the loader captures the absolute path at load time, making it immune to later `os.chdir()` calls.
  - Notes: `project_root` is not a user-facing config key — it's set internally by the loader so downstream code knows where the project lives. **IMPORTANT**: The `src_root` default is `"."` (not `"src"`) because the dataclass default must be safe for direct construction. `load_config()` always applies the `_resolve_src_root()` heuristic which may upgrade it to `"src"` — but bare `DocvetConfig()` without the loader uses the safe fallback. **Bare construction semantics**: `DocvetConfig()` is intended for unit tests only (e.g., verifying defaults, frozen enforcement). Production code must always use `load_config()`, which applies discovery, validation, the `src_root` heuristic, and overlap auto-subtraction. Tests that need specific config values should construct `DocvetConfig(src_root="src", ...)` directly — this is safe because the test controls all inputs.

- [x] Task 4: Create `_kebab_to_snake()` helper
  - File: `src/docvet/config.py`
  - Action: Define `def _kebab_to_snake(key: str) -> str` that replaces `-` with `_`. Single line: `return key.replace("-", "_")`.
  - Notes: Used in all TOML-to-dataclass conversion paths.

- [x] Task 5: Create valid-key constants for validation
  - File: `src/docvet/config.py`
  - Action: Define module-level `frozenset` constants:
    - `_VALID_TOP_KEYS: frozenset[str]` = the valid keys in `[tool.docvet]`: `{"src-root", "package-name", "exclude", "fail-on", "warn-on", "freshness", "enrichment"}`
    - `_VALID_FRESHNESS_KEYS: frozenset[str]` = `{"drift-threshold", "age-threshold"}`
    - `_VALID_ENRICHMENT_KEYS: frozenset[str]` = all nine enrichment keys in kebab-case
    - `_VALID_CHECK_NAMES: frozenset[str]` = `{"enrichment", "freshness", "coverage", "griffe"}`
  - Notes: Used by validation to detect unknown keys and list valid alternatives in error messages.

- [x] Task 6: Create `_validate_keys()` helper
  - File: `src/docvet/config.py`
  - Action: Define `def _validate_keys(data: dict[str, object], valid_keys: frozenset[str], section: str) -> None`. Collect ALL unknown keys first, then report them all at once. For each key in `data`, check if it's in `valid_keys`. Collect all unknown keys into a list. If the list is non-empty, print to stderr ALL unknown keys in a single message: `"docvet: unknown config keys in {section}: {', '.join(sorted(unknown_keys))}. Valid keys: {', '.join(sorted(valid_keys))}"` and call `sys.exit(1)`.
  - Notes: `section` is a human-readable label like `"[tool.docvet]"` or `"[tool.docvet.freshness]"`. Reports all errors at once (matching ruff's behavior) so users can fix all typos in a single pass.

- [x] Task 7: Create `_validate_check_names()` and `_validate_types()` helpers
  - File: `src/docvet/config.py`
  - Action:
    - Define `def _validate_check_names(names: list[str], field_name: str) -> None`. Validates that every entry in `names` is a member of `_VALID_CHECK_NAMES`. If any invalid, print to stderr: `"docvet: unknown check '{name}' in {field_name}. Valid checks: {sorted_valid_names}"` and call `sys.exit(1)`.
    - Define `def _validate_type(value: object, expected: type, key: str, section: str) -> None`. Type-checks a single config value. If `not isinstance(value, expected)`, print to stderr: `"docvet: '{key}' in {section} must be {expected.__name__}, got {type(value).__name__}"` and call `sys.exit(1)`.
  - Notes: `_validate_check_names` is used for `fail-on` and `warn-on` lists. `_validate_type` is used in `load_config()` step 9 for top-level fields (`src-root` must be `str`, `package-name` must be `str`, `exclude` must be `list`) AND in `_parse_freshness()`/`_parse_enrichment()` for nested fields. For list fields, also validate that each entry is a `str`.

- [x] Task 8: Create `_find_pyproject()` discovery function
  - File: `src/docvet/config.py`
  - Action: Define `def _find_pyproject(start: Path | None = None) -> Path | None`. Starting from `start` (default `Path.cwd()`), walk up parent directories looking for `pyproject.toml`. Return the first `Path` found, or `None` if nothing found. **Check order at each directory level is critical — check `pyproject.toml` FIRST, then `.git`:** (a) `pyproject.toml` file exists in current directory — return it, (b) `.git` directory exists (but no `pyproject.toml` here) — return `None`, (c) reached filesystem root (`path == path.parent`) — return `None`. This means if `.git` and `pyproject.toml` coexist in the same directory, `pyproject.toml` wins.
  - Notes: Use `path.resolve()` on the start path to normalize. Check `(path / "pyproject.toml").is_file()` and `(path / ".git").exists()` at each level. **Wrap the directory traversal loop in `try/except OSError` — if a permission error or broken symlink is encountered during walk-up, return `None` (treat as "not found" rather than crashing).** This matches the "High-risk item" identified in the Notes section.

- [x] Task 9: Create `_resolve_src_root()` helper
  - File: `src/docvet/config.py`
  - Action: Define `def _resolve_src_root(project_root: Path, configured: str | None) -> str`. If `configured` is not `None`, return it as-is. Otherwise, check if `(project_root / "src").is_dir()` — if yes return `"src"`, otherwise return `"."`.
  - Notes: `project_root` is the directory containing the discovered pyproject.toml.

- [x] Task 10: Create `_parse_freshness()` helper
  - File: `src/docvet/config.py`
  - Action: Define `def _parse_freshness(data: dict[str, object]) -> FreshnessConfig`. Validates keys against `_VALID_FRESHNESS_KEYS`, converts kebab-to-snake, constructs `FreshnessConfig` with values from `data` merged over defaults.
  - Notes: Type-check that values are `int`. If wrong type, `sys.exit(1)` with message like `"docvet: 'drift-threshold' in [tool.docvet.freshness] must be an integer, got str"`.

- [x] Task 11: Create `_parse_enrichment()` helper
  - File: `src/docvet/config.py`
  - Action: Define `def _parse_enrichment(data: dict[str, object]) -> EnrichmentConfig`. Same pattern as `_parse_freshness()` — validate keys against `_VALID_ENRICHMENT_KEYS`, convert kebab-to-snake, type-check (`bool` for most fields, `list[str]` for `require-examples`), construct `EnrichmentConfig`.
  - Notes: For `require-examples`, validate each entry is a string.

- [x] Task 12a: Create `_parse_docvet_section()` helper
  - File: `src/docvet/config.py`
  - Action: Define `def _parse_docvet_section(data: dict[str, object]) -> dict[str, object]`. Encapsulates all validation and parsing of a non-empty `[tool.docvet]` dict. Logic:
    1. Call `_validate_keys(data, _VALID_TOP_KEYS, "[tool.docvet]")`.
    2. Convert top-level keys with `_kebab_to_snake()`. **CRITICAL: validation (step 1) MUST happen on the original kebab-case keys BEFORE conversion in step 2. Never reorder these steps.**
    3. Extract nested sections: `freshness_data = data.pop("freshness", {})`, `enrichment_data = data.pop("enrichment", {})`.
    4. Call `_parse_freshness()` and `_parse_enrichment()` on nested dicts, store results back in `data`.
    5. Type-validate top-level string fields (`src_root`, `package_name`) and list fields (`exclude`, `fail_on`, `warn_on`) using `_validate_type()`.
    6. Validate `fail_on` and `warn_on` with `_validate_check_names()`.
    7. Return the processed `data` dict ready for `DocvetConfig` construction.
  - Notes: Extracted from Task 12 to keep `load_config()` clean. This function is only called when `data` is non-empty. Build error messages using intermediate variables to stay under the 100-char linter limit — never construct long f-strings on a single line. **Note**: The returned dict may contain `fail_on` and `warn_on` with overlapping entries — overlap resolution (auto-subtract) is handled by the caller (`load_config()` step 7), not here.

- [x] Task 12b: Create `load_config()` public function
  - File: `src/docvet/config.py`
  - Action: Define `def load_config(path: Path | None = None) -> DocvetConfig`. This is one of the four public symbols. Clean orchestration logic:
    1. If `path` is provided, use it directly. If the file doesn't exist, raise `FileNotFoundError` (explicit `--config` path should exist).
    2. If `path` is `None`, call `_find_pyproject()`. If returns `None`, set `project_root = Path.cwd().resolve()` and `parsed = {}`.
    3. If a pyproject.toml was found, set `project_root` to its parent directory (resolved). Open with `open(pyproject_path, "rb")` and parse with `tomllib.load()`.
    4. Extract `data = toml_data.get("tool", {}).get("docvet", {})`.
    5. If `data` is non-empty, call `parsed = _parse_docvet_section(data)`. Otherwise `parsed = {}`.
    6. **Always** resolve `src_root` via `_resolve_src_root(project_root, parsed.get("src_root"))` — this runs for ALL code paths including zero-config and missing-section.
    7. **Resolve overlap between `fail_on` and `warn_on`**: After merging parsed values with defaults, if any check name appears in both `fail_on` and `warn_on`, auto-subtract those from `warn_on`. This applies in ALL cases: (a) user sets `fail-on` without overriding `warn-on` (default still contains the promoted check), and (b) user explicitly sets both lists with overlapping entries. Setting `fail-on` promotes checks from advisory to blocking — they are automatically removed from `warn-on`. **No error, no `SystemExit` — just auto-subtract.** Implementation: `final_warn_on = [c for c in warn_on if c not in fail_on_set]`.
    8. Construct and return `DocvetConfig(**{**parsed, "project_root": project_root, "src_root": resolved_src_root, "warn_on": final_warn_on})`. The `parsed` dict keys map 1:1 to `DocvetConfig` field names (kebab-to-snake already applied by `_parse_docvet_section`). Explicit keyword args for `project_root`, `src_root`, and `warn_on` override any values in `parsed` since they were resolved in steps 6-7. Omitted keys fall through to dataclass defaults.
  - Notes: **No early returns before step 6.** Every code path (no file found, file found but no section, file found with section) must flow through `_resolve_src_root()` to correctly apply the `src/` heuristic. The `project_root` field is always set using `.resolve()` to capture the absolute path at load time, making it immune to later `os.chdir()` calls.

- [x] Task 13: Add `--config` global option to CLI
  - File: `src/docvet/cli.py` (MODIFY)
  - Action: Add `ConfigOption` Annotated alias at module level (near line 43-47 with the other aliases):
    ```python
    ConfigOption = Annotated[
        Path | None, typer.Option("--config", help="Path to pyproject.toml.", exists=False)
    ]
    ```
    Add `config: ConfigOption = None` parameter to the `main()` callback. Store as `ctx.obj["config"] = str(config) if config is not None else None`.
  - Notes: Match the exact pattern of `output` in the existing callback. Use `exists=False` on the typer Option to prevent typer from validating path existence at parse time — `load_config()` handles that with a proper `FileNotFoundError`. If `exists=False` is not supported in the current typer version, fall back to using `str` instead of `Path` for the type hint. The `_print_global_context()` helper can optionally print the config path when verbose is enabled. **Bridge code**: When a subcommand eventually calls `load_config()`, it will convert `ctx.obj["config"]` back to a `Path`: `config_path = Path(ctx.obj["config"]) if ctx.obj.get("config") else None` then `cfg = load_config(path=config_path)`. This bridge lives in the subcommand, NOT in the callback — but documenting it here so the dev agent understands the intended data flow: CLI stores raw string -> subcommand converts to Path -> `load_config()` accepts `Path | None`.

- [x] Task 14: Create unit tests for dataclasses
  - File: `tests/unit/test_config.py` (CREATE)
  - Action: Create test file with `from __future__ import annotations`, import `DocvetConfig`, `FreshnessConfig`, `EnrichmentConfig`, `load_config` from `docvet.config`. Test sections:
    - **Dataclass defaults**: verify all default values are correct for each dataclass
    - **Frozen enforcement**: verify `FrozenInstanceError` raised when mutating fields
    - **Nested composition**: verify `DocvetConfig().freshness` is a `FreshnessConfig` and `DocvetConfig().enrichment` is an `EnrichmentConfig`
  - Notes: No docstrings on test functions. Follow `test_<what>_<condition>_<expected>` naming.

- [x] Task 15: Create unit tests for discovery
  - File: `tests/unit/test_config.py`
  - Action: Add test section for `_find_pyproject` (import as private, test via `load_config` behavior or import directly). Tests using `tmp_path`:
    - **pyproject.toml in CWD**: create file, verify found
    - **pyproject.toml in parent**: create nested structure, verify walk-up works
    - **No pyproject.toml anywhere**: verify returns `None` / defaults
    - **Stops at .git boundary**: create `.git` dir above, verify doesn't walk past it
    - **Stops at first pyproject.toml**: create two at different levels, verify closest wins
    - **.git and pyproject.toml coexist**: create both in same directory, verify pyproject.toml is found
    - **Permission error during walk-up**: mock `Path.is_file()` to raise `OSError`, verify returns `None` gracefully
    - **Zero-config src_root with src/ dir**: create `src/` dir in `tmp_path` (no pyproject.toml), use `monkeypatch.chdir(tmp_path)`, call `load_config()`, verify `config.src_root` is `"src"` (heuristic works even when no pyproject.toml is found)
    - **Zero-config src_root without src/ dir**: empty `tmp_path` (no pyproject.toml, no `src/`), use `monkeypatch.chdir(tmp_path)`, call `load_config()`, verify `config.src_root` is `"."` (safe fallback)
  - Notes: **Two isolation mechanisms**: (1) For `_find_pyproject()` tests, use the `start` parameter — pass `start=tmp_path / "subdir"` to constrain discovery to the `tmp_path` tree. (2) For `load_config()` tests (which has no `start` param), use `monkeypatch.chdir(tmp_path)` to set CWD into the `tmp_path` tree. `_find_pyproject()` defaults to `Path.cwd()` when no `start` is given, so `monkeypatch.chdir()` effectively constrains discovery. Do NOT rely on `os.chdir()` directly — always `monkeypatch.chdir()` (scoped to test, automatically reverted).

- [x] Task 16: Create unit tests for config loading
  - File: `tests/unit/test_config.py`
  - Action: Add test section for `load_config`. Tests using `tmp_path`:
    - **Full config**: write complete `[tool.docvet]` TOML, verify all fields populated
    - **Partial config**: write only `src-root`, verify rest are defaults
    - **Missing section**: write `pyproject.toml` with no `[tool.docvet]`, verify all defaults
    - **Empty file**: write empty `pyproject.toml`, verify all defaults
    - **Nested freshness**: write `[tool.docvet.freshness]` with custom thresholds
    - **Nested enrichment**: write `[tool.docvet.enrichment]` with some booleans flipped
    - **Explicit path**: pass `path=` argument to `load_config`, verify uses that file
    - **Explicit path missing**: pass non-existent `path=`, verify `FileNotFoundError`
    - **src-root auto-detect with src/**: create `src/` dir, verify defaults to `"src"`
    - **src-root auto-detect without src/**: no `src/` dir, verify defaults to `"."`
    - **package-name omitted**: verify `None` default
    - **package-name set**: verify value preserved
  - Notes: Write TOML strings to `tmp_path / "pyproject.toml"` using `Path.write_text()`.

- [x] Task 17: Create unit tests for validation
  - File: `tests/unit/test_config.py`
  - Action: Add test section for validation. Tests:
    - **Unknown top-level key**: write `[tool.docvet]` with `bogus = true`, verify `SystemExit` with error message containing `"bogus"` and listing valid keys
    - **Unknown freshness key**: write `[tool.docvet.freshness]` with `bad-key = 1`, verify `SystemExit`
    - **Unknown enrichment key**: write `[tool.docvet.enrichment]` with `bad-key = true`, verify `SystemExit`
    - **Invalid check name in fail-on**: write `fail-on = ["bogus"]`, verify `SystemExit` mentioning `"bogus"` and valid check names
    - **Invalid check name in warn-on**: same pattern
    - **Wrong type for drift-threshold**: write `drift-threshold = "thirty"`, verify `SystemExit`
    - **Wrong type for boolean field**: write `require-raises = "yes"`, verify `SystemExit`
    - **Malformed TOML**: write syntactically invalid TOML (e.g., `[tool.docvet` missing closing bracket), verify `tomllib.TOMLDecodeError` is raised
    - **Wrong type for exclude**: write `exclude = "not-a-list"`, verify `SystemExit`
    - **Wrong type for src-root**: write `src-root = 123`, verify `SystemExit`
    - **Overlap auto-subtract**: write `fail-on = ["freshness"]` with no explicit `warn-on`, verify `config.warn_on` does not contain `"freshness"` (auto-subtracted from default)
    - **Multiple unknown keys reported at once**: write `[tool.docvet]` with `bogus1 = true` and `bogus2 = false`, verify error message contains both key names
  - Notes: Use `pytest.raises(SystemExit)` to catch exits. Capture stderr with `capsys.readouterr().err` to verify error message content (validation helpers print to stderr before calling `sys.exit(1)`). Use `pytest.raises(tomllib.TOMLDecodeError)` for malformed TOML test.

- [x] Task 18: Create unit tests for `--config` CLI flag
  - File: `tests/unit/test_cli.py` (MODIFY — this is CLI behavior, follows existing patterns in this file)
  - Action: Add tests using `CliRunner` in the existing "Global options" section:
    - **--config flag appears in help**: verify `--config` shown in `docvet --help`
    - **--config with valid path**: verify exits successfully
    - **--config with missing path**: verify error behavior
  - Notes: These test the CLI integration only, not the config loading logic (that's covered in Tasks 14-17). Goes in `test_cli.py` because it tests CLI flag behavior, matching the existing pattern where `--verbose`, `--format`, and `--output` tests live.

### Acceptance Criteria

- [x] AC 1: Given no pyproject.toml exists anywhere in the directory tree, when `load_config()` is called with no arguments, then a `DocvetConfig` with all default values is returned and `project_root` is `Path.cwd()`.
- [x] AC 2: Given a pyproject.toml exists with no `[tool.docvet]` section, when `load_config()` is called, then a `DocvetConfig` with all default values is returned and `project_root` points to the directory containing the pyproject.toml.
- [x] AC 3: Given a pyproject.toml exists with a complete `[tool.docvet]` section, when `load_config()` is called, then all configured values are present in the returned `DocvetConfig` and defaults are used for any omitted keys.
- [x] AC 4: Given a pyproject.toml with `[tool.docvet.freshness]` containing custom thresholds, when `load_config()` is called, then `config.freshness.drift_threshold` and `config.freshness.age_threshold` reflect the custom values.
- [x] AC 5: Given a pyproject.toml with `[tool.docvet.enrichment]` containing `require-raises = false`, when `load_config()` is called, then `config.enrichment.require_raises` is `False` and all other enrichment booleans remain `True`.
- [x] AC 6: Given a pyproject.toml with an unknown key like `bogus = true` in `[tool.docvet]`, when `load_config()` is called, then a `SystemExit(1)` is raised and the error message to stderr includes the offending key name and lists all valid keys.
- [x] AC 7: Given a pyproject.toml with `fail-on = ["bogus"]`, when `load_config()` is called, then a `SystemExit(1)` is raised and the error message includes `"bogus"` and lists valid check names.
- [x] AC 8: Given a pyproject.toml exists three directories above CWD, when `load_config()` is called, then the discovery walks up and finds the file correctly.
- [x] AC 9: Given a `.git` directory exists between CWD and the pyproject.toml, when `load_config()` is called, then discovery stops at `.git` and returns defaults (does not cross the boundary).
- [x] AC 10: Given `load_config(path=Path("explicit/pyproject.toml"))` is called with an explicit path, when the file exists, then that file is used (discovery is skipped).
- [x] AC 11: Given `load_config(path=Path("nonexistent.toml"))` is called with a non-existent explicit path, when called, then `FileNotFoundError` is raised.
- [x] AC 12: Given a project with a `src/` directory and no explicit `src-root` config, when `load_config()` is called, then `config.src_root` is `"src"`.
- [x] AC 13: Given a project without a `src/` directory and no explicit `src-root` config, when `load_config()` is called, then `config.src_root` is `"."`.
- [x] AC 14: Given `package-name` is not set in config, when `load_config()` is called, then `config.package_name` is `None`.
- [x] AC 15: Given the default config with no overrides, when `load_config()` is called, then `config.fail_on` is `[]` and `config.warn_on` is `["freshness", "enrichment", "griffe", "coverage"]`.
- [x] AC 16: Given all `DocvetConfig`, `FreshnessConfig`, and `EnrichmentConfig` dataclasses, when any field is assigned after construction, then `dataclasses.FrozenInstanceError` is raised.
- [x] AC 17: Given the CLI app, when `docvet --help` is invoked, then `--config` appears in the output with help text.
- [x] AC 18: Given the CLI app, when `docvet --config path/to/pyproject.toml check` is invoked, then the config path is stored in `ctx.obj["config"]` as a string.
- [x] AC 19: Given `.git` and `pyproject.toml` coexist in the same directory, when `load_config()` is called from that directory, then the `pyproject.toml` is found and used (`.git` does not prevent discovery when both are in the same directory).
- [x] AC 20: Given a pyproject.toml with syntactically invalid TOML, when `load_config()` is called, then `tomllib.TOMLDecodeError` is raised (propagated naturally, not caught).
- [x] AC 21: Given a pyproject.toml with `exclude = "not-a-list"` (wrong type), when `load_config()` is called, then `SystemExit(1)` is raised with an error message about the type mismatch.
- [x] AC 22: Given a pyproject.toml with `fail-on = ["freshness"]` and no explicit `warn-on` (so the default includes `"freshness"`), when `load_config()` is called, then `config.fail_on` is `["freshness"]` and `config.warn_on` does NOT contain `"freshness"` (auto-subtracted — setting `fail-on` promotes checks from advisory to blocking).

## Additional Context

### Dependencies

- **stdlib only**: `tomllib`, `dataclasses`, `pathlib`, `sys`
- **No new runtime deps** (project rule: stdlib + typer only)
- Downstream consumers: all check modules (`enrichment.py`, `freshness.py`, `coverage.py`, `griffe_compat.py`) and `cli.py`
- This module has zero upstream dependencies within docvet — it's the foundation layer

### Testing Strategy

- **Unit tests** in `tests/unit/test_config.py` — all tests use `tmp_path` for filesystem isolation
- **Test grouping by section** (matching `test_cli.py` pattern):
  1. Dataclass defaults & frozen enforcement
  2. Discovery (`_find_pyproject` walk-up behavior)
  3. Config loading (full, partial, missing, nested sections)
  4. Validation (unknown keys, invalid check names, wrong types)
  5. CLI integration (`--config` flag)
- **Fixtures**: Factory fixture `write_pyproject(tmp_path)` that returns a helper to write TOML content to `tmp_path / "pyproject.toml"` — add to `tests/unit/test_config.py` as a local fixture (not global conftest, since it's config-specific)
- **Test isolation**: Never use `os.chdir()` directly — always `monkeypatch.chdir()` (scoped to test) or the `start` parameter on `_find_pyproject()`. `pytest-randomly` reorders tests; direct `os.chdir()` would poison subsequent tests
- **Coverage**: All 22 ACs trace to specific tests. Target 100% branch coverage on `config.py`.

### Notes

- **High-risk item**: The `_find_pyproject()` walk-up must handle symlinks and permission errors gracefully. Use `path.resolve()` and catch `OSError` during directory traversal.
- **Error message prefix**: ALL validation error messages must use the `"docvet: "` prefix consistently (Tasks 6, 7, 10, 11). This ensures the tool's output looks cohesive. Format: `"docvet: <error description>"` printed to stderr before `sys.exit(1)`.
- **TOML kebab-case mapping**: The full mapping of 16 user-facing TOML keys to dataclass fields (14 require conversion, 1 has no change, 1 — `package-name` — is optional):
  - `src-root` -> `src_root`
  - `package-name` -> `package_name`
  - `fail-on` -> `fail_on`
  - `warn-on` -> `warn_on`
  - `drift-threshold` -> `drift_threshold`
  - `age-threshold` -> `age_threshold`
  - `require-examples` -> `require_examples`
  - `require-raises` -> `require_raises`
  - `require-yields` -> `require_yields`
  - `require-warns` -> `require_warns`
  - `require-receives` -> `require_receives`
  - `require-other-parameters` -> `require_other_parameters`
  - `require-typed-attributes` -> `require_typed_attributes`
  - `require-cross-references` -> `require_cross_references`
  - `prefer-fenced-code-blocks` -> `prefer_fenced_code_blocks`
  - `exclude` -> `exclude` (no change — single word)
- **Future considerations** (out of scope):
  - `--isolated` flag to ignore all config files
  - `docvet.toml` as standalone config file (ruff pattern)
  - Per-directory config hierarchy
  - `--config KEY=VALUE` inline TOML overrides (ruff/ty pattern)
