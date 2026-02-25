# Story 16.1: Config Parsing and Merge Logic

Status: review
Branch: `feat/config-16-1-extend-exclude`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Python developer configuring docvet**,
I want to add an `extend-exclude` key to `[tool.docvet]` that appends patterns to the defaults,
so that I can exclude additional directories without repeating the default list.

## Acceptance Criteria

1. **AC1 — extend-exclude alone appends to defaults:** Given a `pyproject.toml` with only `extend-exclude = ["vendor"]` (no `exclude` key), when docvet loads the configuration, then the resolved exclude list is `["tests", "scripts", "vendor"]`.

2. **AC2 — exclude alone replaces defaults (unchanged):** Given a `pyproject.toml` with only `exclude = ["vendor"]` (no `extend-exclude` key), when docvet loads the configuration, then the resolved exclude list is `["vendor"]`.

3. **AC3 — both keys compose:** Given a `pyproject.toml` with `exclude = ["vendor"]` and `extend-exclude = ["generated"]`, when docvet loads the configuration, then the resolved exclude list is `["vendor", "generated"]`.

4. **AC4 — neither key uses defaults:** Given a `pyproject.toml` with neither `exclude` nor `extend-exclude`, when docvet loads the configuration, then the resolved exclude list is the defaults `["tests", "scripts"]`.

5. **AC5 — non-list type rejected:** Given a `pyproject.toml` with `extend-exclude = "not-a-list"`, when docvet loads the configuration, then a validation error exits with a message indicating `extend-exclude` must be a list.

6. **AC6 — non-string entry rejected:** Given a `pyproject.toml` with `extend-exclude = [123]`, when docvet loads the configuration, then a validation error exits with a message indicating entries must be strings.

7. **AC7 — unknown key rejected (typo guard):** Given a `pyproject.toml` with `extend-excludes = ["vendor"]` (typo), when docvet loads the configuration, then a validation error exits for the unknown key.

## Tasks / Subtasks

- [x] Task 1: Add `extend-exclude` to `_VALID_TOP_KEYS` frozenset (AC: #7)
  - [x] Add `"extend-exclude"` to the frozenset at line 173 of `config.py`
- [x] Task 2: Add type validation in `_parse_docvet_section` (AC: #5, #6)
  - [x] Add validation block after the `exclude` block (~line 426)
  - [x] Validate `extend_exclude` is a `list` via `_validate_type`
  - [x] Validate each entry is a `str` via `_validate_type` in a loop
- [x] Task 3: Add merge logic in `load_config` (AC: #1, #2, #3, #4)
  - [x] Read `raw_extend_exclude` from `parsed.get("extend_exclude")`
  - [x] Resolve base exclude: `user_exclude or defaults`
  - [x] Concatenate: `base + extend_exclude`
  - [x] Pass merged list as `exclude=` in `DocvetConfig` constructor
- [x] Task 4: Write unit tests for all 7 ACs (AC: #1-#7)
  - [x] `test_load_config_extend_exclude_appends_to_defaults`
  - [x] `test_load_config_exclude_only_replaces_defaults` (new — dedicated AC2 test)
  - [x] `test_load_config_exclude_and_extend_exclude_compose`
  - [x] `test_load_config_neither_exclude_uses_defaults` (new — dedicated AC4 test)
  - [x] `test_load_config_wrong_type_extend_exclude_exits`
  - [x] `test_load_config_non_string_extend_exclude_entry_exits`
  - [x] `test_load_config_unknown_key_extend_excludes_typo_exits`
- [x] Task 5: Run all quality gates

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| AC1 | `test_load_config_extend_exclude_appends_to_defaults` | PASS |
| AC2 | `test_load_config_exclude_only_replaces_defaults` | PASS |
| AC3 | `test_load_config_exclude_and_extend_exclude_compose` | PASS |
| AC4 | `test_load_config_neither_exclude_uses_defaults` | PASS |
| AC5 | `test_load_config_wrong_type_extend_exclude_exits` | PASS |
| AC6 | `test_load_config_non_string_extend_exclude_entry_exits` | PASS |
| AC7 | `test_load_config_unknown_key_extend_excludes_typo_exits` | PASS |

## Dev Notes

### Implementation Locations

| What | Where | Line |
|------|-------|------|
| `_VALID_TOP_KEYS` | `src/docvet/config.py` | 173 |
| `_parse_docvet_section` | `src/docvet/config.py` | 391 |
| `exclude` validation block | `src/docvet/config.py` | 421-424 |
| `load_config` exclude resolution | `src/docvet/config.py` | 555-565 |
| `DocvetConfig` dataclass | `src/docvet/config.py` | 117-167 |
| Unit tests | `tests/unit/test_config.py` | — |

### Merge Formula

```python
raw_exclude = parsed.get("exclude")
raw_extend = parsed.get("extend_exclude")

# Resolve base: user-provided replaces defaults
if isinstance(raw_exclude, list):
    base = [str(x) for x in raw_exclude]
else:
    base = list(defaults.exclude)

# Extend appends on top of base
if isinstance(raw_extend, list):
    final_exclude = base + [str(x) for x in raw_extend]
else:
    final_exclude = base
```

This follows the universal convention of ruff, black, and flake8: `final = (user_exclude or defaults) + extend_exclude`.

### Key Design Decision: No New Dataclass Field

`extend-exclude` is a **TOML-only directive** that merges into `exclude` at load time. The `DocvetConfig` dataclass does NOT get an `extend_exclude` field. Downstream consumers (`discovery.py`) only read `config.exclude` — they have zero awareness of `extend-exclude`. This preserves the clean separation between config loading and file discovery (NFR3).

### Validation Pattern to Follow

The `exclude` validation block (lines 421-424) is the exact pattern:

```python
if "exclude" in converted:
    _validate_type(converted["exclude"], list, "exclude", _TOOL_SECTION)
    for entry in converted["exclude"]:
        _validate_type(entry, str, "exclude", _TOOL_SECTION)
```

Replicate for `extend_exclude` with `"extend-exclude"` as the key name in error messages.

### Test Pattern to Follow

All config tests use this structure:

```python
def test_load_config_<scenario>(tmp_path, monkeypatch, write_pyproject, capsys):
    monkeypatch.chdir(tmp_path)
    write_pyproject('<toml content>')
    cfg = load_config()
    assert cfg.exclude == [<expected>]
```

For validation errors:

```python
def test_load_config_<scenario>_exits(tmp_path, monkeypatch, write_pyproject, capsys):
    monkeypatch.chdir(tmp_path)
    write_pyproject('<toml content>')
    with pytest.raises(SystemExit):
        load_config()
    assert "<expected substring>" in capsys.readouterr().err
```

### Files to Modify

- `src/docvet/config.py` — 3 touch points (valid keys, validation, merge)
- `tests/unit/test_config.py` — 5-7 new tests

### Files NOT to Modify

- `src/docvet/discovery.py` — zero changes (NFR3)
- `src/docvet/cli.py` — no new flags or subcommands
- Any check module — they consume `config.exclude` opaquely

### Project Structure Notes

- Alignment with unified project structure: all changes in `src/docvet/config.py` and `tests/unit/test_config.py`
- No new files created
- Naming follows existing kebab-case TOML → snake_case Python convention

### References

- [Source: `src/docvet/config.py` — `_VALID_TOP_KEYS` at line 173]
- [Source: `src/docvet/config.py` — `_parse_docvet_section` at line 391]
- [Source: `src/docvet/config.py` — `load_config` exclude resolution at lines 555-565]
- [Source: `tests/unit/test_config.py` — `write_pyproject` fixture at line 24]
- [Source: `_bmad-output/planning-artifacts/epics-extend-exclude.md` — FR1-FR7, NFR1-NFR5]
- [Source: GitHub issue #18]
- Peer research: ruff `extend-exclude`, black `--extend-exclude`, flake8 `extend-exclude` — all use same merge formula

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 753 passed, no regressions
- [x] `uv run docvet check --all` — zero findings on committed state (3 transient freshness findings from uncommitted working tree)
- [x] `uv run interrogate -v` — 100% docstring coverage (≥ 95%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. Zero-debug implementation.

### Completion Notes List

- Added `"extend-exclude"` to `_VALID_TOP_KEYS` frozenset (line 177)
- Added type validation block for `extend_exclude` in `_parse_docvet_section` (lines 426-431) — validates list type and string entries, using `"extend-exclude"` (kebab-case) in error messages
- Replaced inline exclude ternary in `load_config` with explicit `base_exclude` variable and `extend_exclude` merge (lines 562-570)
- Wrote 7 new unit tests covering all 7 ACs — AC2 and AC4 also have pre-existing coverage from existing tests
- All quality gates pass: ruff, ty, pytest (753 passed), docvet, interrogate (100%)

### Change Log

- 2026-02-25: Implemented extend-exclude config parsing, validation, and merge logic (Tasks 1-5)

### File List

- `src/docvet/config.py` — modified (3 touch points: valid keys, validation, merge)
- `tests/unit/test_config.py` — modified (7 new tests)

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
