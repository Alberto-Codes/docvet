# Story 5.2: Drift and Age Detection Orchestrator

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to detect symbols where code has drifted ahead of its docstring by a configurable threshold or where the docstring has aged past a configurable limit,
so that periodic audits surface docstrings that may need review.

## Acceptance Criteria

1. **Given** a symbol where `max(code_timestamps) - max(docstring_timestamps) > drift_threshold * 86400`, **When** `check_freshness_drift` is called, **Then** it returns a `Finding` with `rule="stale-drift"`, `category="recommended"`, and a message including both dates and the day count (e.g., `Function 'process_batch' code modified 2025-12-14, docstring last modified 2025-10-02 (73 days drift)`)
2. **Given** a symbol where `now - max(docstring_timestamps) > age_threshold * 86400`, **When** `check_freshness_drift` is called, **Then** it returns a `Finding` with `rule="stale-age"`, `category="recommended"`, and a message including the docstring date and day count (e.g., `Function 'validate_schema' docstring untouched since 2025-09-15 (147 days)`)
3. **Given** a symbol that triggers both `stale-drift` and `stale-age`, **When** `check_freshness_drift` is called, **Then** it returns two findings for that symbol — the rules are independent (FR61 drift — per rule, not per mode)
4. **Given** a symbol where the drift is exactly at the threshold boundary (`code_max - doc_max == threshold * 86400`), **When** `check_freshness_drift` is called, **Then** it does not emit a `stale-drift` finding (strict greater-than comparison `>`, not `>=`)
5. **Given** a symbol where the docstring age is exactly at the threshold boundary, **When** `check_freshness_drift` is called, **Then** it does not emit a `stale-age` finding (strict greater-than `>`)
6. **Given** a symbol with no docstring (`docstring_range is None`), **When** `check_freshness_drift` is called, **Then** it produces zero findings for that symbol (FR54 — no docstring timestamps to evaluate)
7. **Given** a symbol with only a docstring (no code body, e.g., a stub), **When** `check_freshness_drift` is called, **Then** `stale-drift` cannot trigger (no code timestamps) but `stale-age` can still trigger based on docstring age alone
8. **Given** a symbol where code timestamps and docstring timestamps are within the drift threshold, **When** `check_freshness_drift` is called, **Then** it produces zero `stale-drift` findings for that symbol (FR62)
9. **Given** `config.drift_threshold = 30` and `config.age_threshold = 90` (defaults), **When** `check_freshness_drift` is called with no explicit config overrides, **Then** it applies the default thresholds (FR65)
10. **Given** `config.drift_threshold = 7` (custom override), **When** `check_freshness_drift` is called on a symbol where code is 10 days newer than docstring, **Then** it emits a `stale-drift` finding (FR63 — configurable threshold)
11. **Given** `config.age_threshold = 180` (custom override), **When** `check_freshness_drift` is called on a symbol whose docstring is 100 days old, **Then** it does not emit a `stale-age` finding (under the custom threshold — FR64)
12. **Given** a `now` parameter passed explicitly (Unix timestamp), **When** `check_freshness_drift` is called, **Then** it uses the provided `now` instead of `time.time()` (test determinism)
13. **Given** no `now` parameter, **When** `check_freshness_drift` is called, **Then** it defaults to `time.time()` for the current UTC timestamp
14. **Given** an empty `blame_output` string, **When** `check_freshness_drift` is called, **Then** it returns an empty list immediately (NFR25)
15. **Given** identical `blame_output`, identical `tree`, and identical `now` timestamp, **When** `check_freshness_drift` is called multiple times, **Then** it produces identical output every time (deterministic)

## Tasks / Subtasks

- [x] Task 1: Add imports and drift constants to `src/docvet/checks/freshness.py` (AC: all)
  - [x] 1.1: Add `import time` to stdlib imports section (line 6 area)
  - [x] 1.2: Add `from datetime import datetime, timezone` to stdlib imports
  - [x] 1.3: Remove `# noqa: F401` from the `FreshnessConfig` import (it's now consumed by `check_freshness_drift`)
- [x] Task 2: Add `_compute_drift` helper to freshness.py after `_parse_blame_timestamps` (AC: 1, 4, 8)
  - [x] 2.1: Implement `_compute_drift(code_timestamps: list[int], doc_timestamps: list[int], threshold: int) -> bool` with Google-style docstring
  - [x] 2.2: Return `False` if either list is empty (guard for stub symbols or no-code symbols)
  - [x] 2.3: Compute `max(code_timestamps) - max(doc_timestamps) > threshold * 86400` with strict `>` comparison
- [x] Task 3: Add `_compute_age` helper after `_compute_drift` (AC: 2, 5, 7)
  - [x] 3.1: Implement `_compute_age(doc_timestamps: list[int], now: int, threshold: int) -> bool` with Google-style docstring
  - [x] 3.2: Return `False` if `doc_timestamps` is empty
  - [x] 3.3: Compute `now - max(doc_timestamps) > threshold * 86400` with strict `>` comparison
- [x] Task 4: Add `check_freshness_drift` public function after helpers (AC: 1-15)
  - [x] 4.1: Implement signature: `check_freshness_drift(file_path: str, blame_output: str, tree: ast.Module, config: FreshnessConfig, *, now: int | None = None) -> list[Finding]:`
  - [x] 4.2: Early return `[]` on empty `blame_output`
  - [x] 4.3: Parse blame timestamps via `_parse_blame_timestamps(blame_output)`; early return `[]` if empty
  - [x] 4.4: Build line map via `map_lines_to_symbols(tree)`
  - [x] 4.5: Group timestamps by symbol — for each `(line_num, ts)`, look up `line_map.get(line_num)`, partition into `code_timestamps` vs `docstring_timestamps` using `symbol.docstring_range`
  - [x] 4.6: Skip symbols with `docstring_range is None` (FR54)
  - [x] 4.7: Resolve `now` — use provided value or `int(time.time())`
  - [x] 4.8: For each symbol: run `_compute_drift` → emit `stale-drift` finding if True; run `_compute_age` → emit `stale-age` finding if True (independent checks, up to 2 findings per symbol)
  - [x] 4.9: Format `stale-drift` message: `{Kind} '{name}' code modified {code_date}, docstring last modified {doc_date} ({N} days drift)` using `datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()` for dates, `(code_max - doc_max) // 86400` for day count
  - [x] 4.10: Format `stale-age` message: `{Kind} '{name}' docstring untouched since {doc_date} ({N} days)` using `(effective_now - doc_max) // 86400` for day count
  - [x] 4.11: Use `_build_finding` for all finding construction
  - [x] 4.12: Sort findings by line number before returning
- [x] Task 5: Create unit tests in `tests/unit/checks/test_freshness.py` (AC: 1-15)
  - [x] 5.1: Add imports: `check_freshness_drift`, `_compute_drift`, `_compute_age` from `docvet.checks.freshness`; `FreshnessConfig` from `docvet.config`
  - [x] 5.2: Add `_DRIFT_SOURCE` test constant — Python source with 2+ functions at known line ranges (function with docstring, function without docstring, stub function with only docstring)
  - [x] 5.3: Add blame output builder helper or constants that produce `dict[int, int]` for controlled timestamp scenarios
  - [x] 5.4: `TestComputeDrift` class:
    - [x] 5.4a: Test drift exceeds threshold → `True`
    - [x] 5.4b: Test drift within threshold → `False`
    - [x] 5.4c: Test exact boundary → `False` (strict `>`)
    - [x] 5.4d: Test empty code timestamps → `False`
    - [x] 5.4e: Test empty doc timestamps → `False`
  - [x] 5.5: `TestComputeAge` class:
    - [x] 5.5a: Test age exceeds threshold → `True`
    - [x] 5.5b: Test age within threshold → `False`
    - [x] 5.5c: Test exact boundary → `False` (strict `>`)
    - [x] 5.5d: Test empty doc timestamps → `False`
  - [x] 5.6: `TestCheckFreshnessDrift` class:
    - [x] 5.6a: Test stale-drift finding produced (AC 1)
    - [x] 5.6b: Test stale-age finding produced (AC 2)
    - [x] 5.6c: Test both stale-drift and stale-age on same symbol (AC 3)
    - [x] 5.6d: Test exact drift boundary produces no finding (AC 4)
    - [x] 5.6e: Test exact age boundary produces no finding (AC 5)
    - [x] 5.6f: Test no-docstring symbol skipped (AC 6)
    - [x] 5.6g: Test stub-only symbol: stale-age can fire, stale-drift cannot (AC 7)
    - [x] 5.6h: Test within-threshold produces zero findings (AC 8)
    - [x] 5.6i: Test default thresholds applied (AC 9)
    - [x] 5.6j: Test custom drift threshold (AC 10)
    - [x] 5.6k: Test custom age threshold (AC 11)
    - [x] 5.6l: Test explicit `now` parameter used (AC 12)
    - [x] 5.6m: Test default `now` (AC 13) — mock `time.time`
    - [x] 5.6n: Test empty blame output returns `[]` (AC 14)
    - [x] 5.6o: Test deterministic output (AC 15)
    - [x] 5.6p: Test finding message format contains expected strings (dates, day count)
    - [x] 5.6q: Test finding fields: `rule`, `category`, `file`, `line`, `symbol` are correct
    - [x] 5.6r: Test lines not mapping to any symbol are silently skipped
    - [x] 5.6s: Test symbol where all timestamps identical (code == docstring) → no stale-drift
    - [x] 5.6t: Test findings sorted by line number
- [x] Task 6: Run quality gates (AC: all)
  - [x] 6.1: `uv run ruff check .` — all checks pass
  - [x] 6.2: `uv run ruff format --check .` — all files formatted
  - [x] 6.3: `uv run ty check` — all type checks pass
  - [x] 6.4: `uv run pytest tests/unit/checks/test_freshness.py -v` — all freshness tests pass
  - [x] 6.5: `uv run pytest` — full suite passes, 0 regressions

## Dev Notes

### This is Story 5.2 — Second Story in Epic 5 (Freshness Drift Mode)

This story extends `src/docvet/checks/freshness.py` (262 lines after Story 5.1) and `tests/unit/checks/test_freshness.py`. No new files created. No existing source files other than `freshness.py` are modified. This follows the proven parser → **orchestrator** → CLI wiring playbook from Epic 4.

### Current State of `freshness.py` (After Story 5.1, 262 lines)

```
freshness.py (262 lines):
1-11:    Module docstring, imports (ast, re, Literal, Symbol, map_lines_to_symbols, Finding, FreshnessConfig noqa)
12-28:   Module-level constants (_HUNK_PATTERN, rule IDs, _CLASSIFICATION_MAP)
29-62:   Shared helpers (_build_finding)
63-103:  Diff mode helpers (_parse_diff_hunks)
104-143: Diff mode helpers (_classify_changed_lines)
144-199: check_freshness_diff public function
200-204: Drift mode helpers section header
207-261: _parse_blame_timestamps

--- Story 5.2 adds here ---
NEW:     _compute_drift helper
NEW:     _compute_age helper
NEW:     check_freshness_drift public function
```

### Import Changes Required

**Add** to stdlib imports section (after `import re`, before `from typing`):
```python
import time
from datetime import datetime, timezone
```

**Remove** `# noqa: F401` from the `FreshnessConfig` import on line 11 — it's now consumed by `check_freshness_drift`. The import line should become:
```python
from docvet.config import FreshnessConfig
```

**Do NOT change** any other existing imports.

### `_compute_drift` Implementation (Architecture Decision 4)

```python
def _compute_drift(
    code_timestamps: list[int],
    doc_timestamps: list[int],
    threshold: int,
) -> bool:
    if not code_timestamps or not doc_timestamps:
        return False
    return max(code_timestamps) - max(doc_timestamps) > threshold * 86400
```

- Returns `False` when either list is empty — handles stubs (no code) and symbols with no docstring timestamps
- Strict `>` comparison — exact boundary does NOT trigger
- `threshold` is in days, converted to seconds via `* 86400`

### `_compute_age` Implementation

```python
def _compute_age(
    doc_timestamps: list[int],
    now: int,
    threshold: int,
) -> bool:
    if not doc_timestamps:
        return False
    return now - max(doc_timestamps) > threshold * 86400
```

- Returns `False` when no docstring timestamps
- Strict `>` — exact boundary does NOT trigger
- `now` is a Unix timestamp (seconds), passed in from the orchestrator

### `check_freshness_drift` Orchestrator (Architecture Decisions 1, 4, 5, 6)

**Signature:**
```python
def check_freshness_drift(
    file_path: str,
    blame_output: str,
    tree: ast.Module,
    config: FreshnessConfig,
    *,
    now: int | None = None,
) -> list[Finding]:
```

**Algorithm:**
1. Early return `[]` on empty `blame_output`
2. `timestamps = _parse_blame_timestamps(blame_output)` — early return `[]` if empty
3. `line_map = map_lines_to_symbols(tree)`
4. Group timestamps by symbol:
   - For each `(line_num, ts)` in timestamps, look up `line_map.get(line_num)`
   - If symbol found AND `symbol.docstring_range is not None`:
     - If `line_num` is within `symbol.docstring_range` → add `ts` to `doc_timestamps[symbol]`
     - Else → add `ts` to `code_timestamps[symbol]`
   - Skip lines that don't map to any symbol (silently)
   - Skip symbols with `docstring_range is None` (FR54)
5. Resolve `now`: `effective_now = now if now is not None else int(time.time())`
6. For each symbol with timestamps:
   - If `_compute_drift(code_ts, doc_ts, config.drift_threshold)` → emit `stale-drift` finding
   - If `_compute_age(doc_ts, effective_now, config.age_threshold)` → emit `stale-age` finding
7. Sort findings by `line`, return

**Message format — `stale-drift`:**
```python
code_date = datetime.fromtimestamp(max(code_ts), tz=timezone.utc).date().isoformat()
doc_date = datetime.fromtimestamp(max(doc_ts), tz=timezone.utc).date().isoformat()
days = (max(code_ts) - max(doc_ts)) // 86400
kind = symbol.kind.capitalize()
message = f"{kind} '{symbol.name}' code modified {code_date}, docstring last modified {doc_date} ({days} days drift)"
```

**Message format — `stale-age`:**
```python
doc_date = datetime.fromtimestamp(max(doc_ts), tz=timezone.utc).date().isoformat()
days = (effective_now - max(doc_ts)) // 86400
kind = symbol.kind.capitalize()
message = f"{kind} '{symbol.name}' docstring untouched since {doc_date} ({days} days)"
```

**Finding construction:** Always use `_build_finding(file_path, symbol, rule, message, category)`. Category is `"recommended"` for both drift rules.

### Timestamp Grouping Detail

The grouping logic needs careful handling. For each blame timestamp line:

```python
symbol_code_ts: dict[Symbol, list[int]] = {}
symbol_doc_ts: dict[Symbol, list[int]] = {}

for line_num, ts in timestamps.items():
    sym = line_map.get(line_num)
    if sym is None:
        continue  # Inter-symbol whitespace, skip
    if sym.docstring_range is None:
        continue  # FR54: no docstring, skip entirely

    ds, de = sym.docstring_range
    if ds <= line_num <= de:
        symbol_doc_ts.setdefault(sym, []).append(ts)
    else:
        symbol_code_ts.setdefault(sym, []).append(ts)
```

Then iterate over the **union** of symbols from both dicts — a symbol may only appear in one dict (e.g., a stub with only a docstring has doc timestamps but no code timestamps).

### Testing Approach

**Unit tests only for Story 5.2** — integration tests with real git repos come in Story 5.3.

**Test source constant** — create `_DRIFT_SOURCE` with multiple symbols at known line ranges:
```python
_DRIFT_SOURCE = '''\
"""Module docstring."""


def documented_func(x):
    """Func docstring."""
    return x + 1


def undocumented_func(x):
    return x + 1


def stub_func():
    """Only a docstring, no real body."""
'''
```

Use `ast.parse(_DRIFT_SOURCE)` to get the tree, then build blame output strings with controlled timestamps to test each scenario.

**Helper approach for blame output:** Build blame output programmatically from `(line_num, timestamp)` pairs using a helper function that generates valid porcelain format, OR use pre-built multiline string constants.

**Mocking `time.time`:** For AC 13 (default `now`), use `unittest.mock.patch("docvet.checks.freshness.time")` to control the return value. But prefer using the explicit `now` parameter for most tests — it's simpler and avoids mock complexity.

### Error Handling: Defensive by Design (Decision 6)

- Early return `[]` on empty blame output — before any processing
- Early return `[]` if `_parse_blame_timestamps` returns empty dict
- `_compute_drift` / `_compute_age` return `False` on empty timestamp lists
- Lines not in `line_map` silently skipped
- Symbols with no docstring silently skipped
- No try/except needed — all defensive gates are type-safe checks

### What NOT to Implement in Story 5.2

- CLI wiring changes — Story 5.3
- Integration tests with real git repos — Story 5.3
- `git blame` subprocess calls — Story 5.3 (CLI layer responsibility)
- Changes to `ast_utils.py`, `config.py`, or `cli.py` — none needed
- Per-rule disable toggles for drift mode — post-MVP

### Previous Story Learnings (Stories 5.1 + Epic 4 Retro)

- **Edge case test gaps found in every code review** — proactively test: exact boundary, empty lists, symbols with only docstring, identical timestamps, lines not mapping to symbols, multiple findings on same symbol
- **Don't add speculative imports** — only `import time` and `from datetime import datetime, timezone` are needed
- **Zero debugging when following architecture exactly** — stick to the spec
- **Test naming accuracy matters** — name tests after what they actually test
- **Documentation accuracy** — docstrings must match actual behavior
- **`_make_symbol` helper** exists in test file for creating test symbols — useful for unit-testing `_compute_drift`/`_compute_age` but most tests should use real `ast.parse` trees with `map_lines_to_symbols`

### Project Structure Notes

| File | Action |
|------|--------|
| `src/docvet/checks/freshness.py` | **MODIFY** — add `import time`, `from datetime import datetime, timezone`, remove `noqa: F401`, add `_compute_drift`, `_compute_age`, `check_freshness_drift` |
| `tests/unit/checks/test_freshness.py` | **MODIFY** — add new imports, test constants, `TestComputeDrift`, `TestComputeAge`, `TestCheckFreshnessDrift` test classes (~25 tests) |

No new files. No changes to any other source files.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 5.2 acceptance criteria, FRs: FR51, FR52, FR53, FR54, FR61, FR62, FR63, FR64, FR65, FR66]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Decisions 1 (module org), 4 (partition-then-decide), 5 (message format), 6 (error handling); freshness naming patterns; data flow diagram]
- [Source: `_bmad-output/planning-artifacts/prd.md` — Freshness Module Specification: drift mode implementation guidance, edge cases, config schema]
- [Source: `src/docvet/checks/freshness.py` — Current module state (262 lines): diff mode + `_parse_blame_timestamps` complete]
- [Source: `src/docvet/config.py` — `FreshnessConfig(drift_threshold=30, age_threshold=90)`]
- [Source: `src/docvet/ast_utils.py` — `Symbol` dataclass (signature_range, body_range, docstring_range), `map_lines_to_symbols` function]
- [Source: `_bmad-output/implementation-artifacts/5-1-blame-timestamp-parser.md` — Previous story: blame parser implementation, 16 tests, learnings]
- [Source: `_bmad-output/implementation-artifacts/epic-4-retro-2026-02-10.md` — Epic 4 retro: edge case gaps, documentation accuracy, three-story playbook validated]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debugging required — implementation followed architecture spec exactly.

### Completion Notes List

- Implemented `_compute_drift` helper (strict `>` comparison, empty-list guards)
- Implemented `_compute_age` helper (strict `>` comparison, empty-list guard)
- Implemented `check_freshness_drift` orchestrator: blame parsing → line-to-symbol mapping → timestamp grouping (code vs docstring buckets) → independent drift/age checks → sorted findings
- Added `import time` and `from datetime import datetime, timezone` to stdlib imports
- Removed `# noqa: F401` from `FreshnessConfig` import (now consumed by `check_freshness_drift`)
- 31 new tests added: 5 (`TestComputeDrift`) + 4 (`TestComputeAge`) + 22 (`TestCheckFreshnessDrift`)
- All 15 acceptance criteria covered by tests with deterministic timestamps
- `_build_blame` test helper generates porcelain blame output from `(line_num, timestamp)` pairs
- `_DRIFT_SOURCE` test constant provides documented, undocumented, and stub functions at known line ranges
- Total test suite: 519 tests passing (91 freshness, 428 other), 0 regressions
- All quality gates pass: ruff check, ruff format, ty check

### Change Log

- 2026-02-11: Implemented drift and age detection orchestrator (Story 5.2) — `_compute_drift`, `_compute_age`, `check_freshness_drift` + 31 unit tests
- 2026-02-11: Code review fixes — added `test_finding_message_format_age`, `test_whitespace_only_blame_output_returns_empty_list`, strengthened `test_stale_drift_finding_produced` with stale-age absence assertion

### File List

- `src/docvet/checks/freshness.py` — MODIFIED (262 → 411 lines): added imports, `_compute_drift`, `_compute_age`, `check_freshness_drift`
- `tests/unit/checks/test_freshness.py` — MODIFIED (930 → 1376 lines): added imports, drift test constants, `_build_blame` helper, `TestComputeDrift`, `TestComputeAge`, `TestCheckFreshnessDrift`
