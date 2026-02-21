# Story 10.1: LICENSE and Package Metadata

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Python developer evaluating docvet,
I want to see a clear license and proper PyPI classifiers,
so that I can confirm the tool is safe to adopt in my project.

## Acceptance Criteria

1. **Given** `pyproject.toml` has no `license` field or classifiers, **when** LICENSE file and metadata are added, **then** a `LICENSE` file exists at the repository root containing the full MIT license text with copyright year 2026 and holder "Alberto-Codes".
2. **Given** no license field in `pyproject.toml`, **when** metadata is added, **then** `pyproject.toml` includes `license = {file = "LICENSE"}` (PEP 621 file-reference form).
3. **Given** no classifiers in `pyproject.toml`, **when** metadata is added, **then** `pyproject.toml` includes classifiers: `Development Status :: 5 - Production/Stable`, `Environment :: Console`, `Intended Audience :: Developers`, `License :: OSI Approved :: MIT License`, `Programming Language :: Python :: 3.12`, `Programming Language :: Python :: 3.13`, `Topic :: Software Development :: Quality Assurance`.
4. **Given** no keywords in `pyproject.toml`, **when** metadata is added, **then** `pyproject.toml` includes `keywords` with: `docstring`, `linter`, `mkdocs`, `interrogate`, `pydocstyle`, `darglint`, `documentation`, `quality`.
5. **Given** all changes applied, **when** `uv run pytest` is run, **then** all existing tests continue to pass.

## Tasks / Subtasks

- [x] Task 1: Create LICENSE file at repository root (AC: #1)
  - [x] 1.1 Create `LICENSE` file with MIT license text, copyright 2026 Alberto-Codes
- [x] Task 2: Add `license` field to `pyproject.toml` (AC: #2)
  - [x] 2.1 Add `license = {file = "LICENSE"}` to the `[project]` section
- [x] Task 3: Add `classifiers` to `pyproject.toml` (AC: #3)
  - [x] 3.1 Add `classifiers` list with all 7 required classifiers
- [x] Task 4: Add `keywords` to `pyproject.toml` (AC: #4)
  - [x] 4.1 Add `keywords` list with all 8 required keywords
- [x] Task 5: Run quality gates and verify build (AC: #5)
  - [x] 5.1 `uv run pytest` — all existing tests pass (729 passed, 1 skipped)
  - [x] 5.2 `uv run ruff check .` — no lint errors
  - [x] 5.3 `uv run ruff format --check .` — no formatting issues
  - [x] 5.4 `uv build` — wheel METADATA verified: license text inlined, all 7 classifiers present, all 8 keywords present

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | Manual: `LICENSE` file exists at repo root with MIT text, copyright 2026 Alberto-Codes | Pass |
| #2 | Manual: `pyproject.toml` contains `license = {file = "LICENSE"}` (line 6) | Pass |
| #3 | Manual: `pyproject.toml` contains all 7 classifiers (lines 11-18) | Pass |
| #4 | Manual: `pyproject.toml` contains all 8 keywords (lines 20-28) | Pass |
| #5 | `uv run pytest` — 729 passed, 1 skipped, 0 failed | Pass |

## Dev Notes

### Implementation Strategy

This is a metadata-only story. No source code changes, no new tests needed. Two files modified/created:

1. **`LICENSE`** (new file at repo root) — Standard MIT license text. Use 2026 as copyright year, "Alberto-Codes" as holder.

2. **`pyproject.toml`** (modify `[project]` section) — Add three fields after `readme`:

```toml
license = {file = "LICENSE"}
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Quality Assurance",
]
keywords = [
    "docstring",
    "linter",
    "mkdocs",
    "interrogate",
    "pydocstyle",
    "darglint",
    "documentation",
    "quality",
]
```

**Field placement in `pyproject.toml`:** PEP 621 convention is: name → version → description → readme → license → authors → requires-python → classifiers → keywords → dependencies. Insert `license` after `readme`, then `classifiers` and `keywords` after `authors`.

**License choice:** MIT — matches the positioning as a developer tool (permissive, universally adoptable). FR-G1 specifies "MIT or Apache-2.0" — MIT is simpler and more common for Python developer tools.

**`uv_build` and LICENSE:** The `uv_build` backend (switched in 9.3) automatically includes `LICENSE` files in both wheel and sdist when referenced via `license = {file = "LICENSE"}`. No additional build config needed.

### Previous Story Intelligence (9.3)

- Build backend is `uv_build` (not hatchling) — include-based defaults handle LICENSE automatically
- Version is `1.0.0` — already set
- 725 tests as baseline (Story 9.3 final count)
- `pyproject.toml` currently has: `name`, `version`, `description`, `readme`, `authors`, `requires-python`, `dependencies`, `optional-dependencies`, `scripts`, `build-system`
- No `license`, `classifiers`, or `keywords` fields exist yet

### Epic 9 Retro Action Items (relevant)

The retro identified 3 tech debt items and 6 action items. Two are relevant context:
- **Tech debt #3:** `pyproject.toml` tool config bloat — minimize unnecessary overrides. This story adds *project* metadata (not tool config), so no conflict.
- **Action #6:** `.pre-commit-config.yaml` setup — already done in commit `c4be928`.

### Git Intelligence

Last 5 commits:
- `c4be928` chore: extract Finding, add Examples docstrings, and pre-commit hooks (#61)
- `b1c53bb` feat(cli): version bump to 1.0.0, --version flag, and uv_build backend (#60)
- `6b90eb4` feat(cli): add __all__ exports to all public modules (#59)
- `43c82a7` feat(cli): add unified output pipeline and resolve all docvet findings (#58)
- `08c75a8` docs(prd): add v1.0 Polish and Publish phase (#57)

All on `develop`. Epic 9 is fully merged. Clean starting point.

**Suggested branch:** `feat/cli-10-1-license-and-package-metadata`

### Files to Modify

| File | Changes |
|------|---------|
| `LICENSE` | **New file** — MIT license text |
| `pyproject.toml` | Add `license`, `classifiers`, `keywords` to `[project]` section |

### Anti-Pattern Prevention

- **Do NOT use `license = "MIT"`** (SPDX string form). Use `license = {file = "LICENSE"}` (file-reference form) — this is what PyPI and `uv_build` expect for proper license file inclusion in wheels.
- **Do NOT add `license-files`** field — `uv_build` auto-discovers `LICENSE*` files when `license.file` is set.
- **Do NOT modify any source code** — this is a metadata-only story.
- **Do NOT add or remove tool config sections** — only modify the `[project]` table.

### Project Structure Notes

- `LICENSE` goes at repository root (same level as `pyproject.toml`)
- All source files remain in `src/docvet/` — no changes
- No test changes needed — this is pure metadata

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 10.1]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-G1 — LICENSE file]
- [Source: _bmad-output/planning-artifacts/epics.md#FR113 — PyPI classifiers and tags]
- [Source: _bmad-output/planning-artifacts/epics.md#NFR55 — Pure Python wheel]
- [Source: pyproject.toml — current state of [project] section]
- [Source: 9-3-version-bump-and-build-configuration.md — uv_build backend context]
- [Source: epic-9-retro-2026-02-21.md — tech debt and action items]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — clean implementation with no errors or retries.

### Completion Notes List

- Created MIT LICENSE file at repo root (copyright 2026 Alberto-Codes)
- Added `license = {file = "LICENSE"}` to `[project]` section (PEP 621 file-reference form)
- Added 7 PyPI classifiers covering dev status, environment, audience, license, Python versions, and topic
- Added 8 keywords for PyPI discoverability
- Field placement follows PEP 621 convention: name → version → description → readme → license → authors → requires-python → classifiers → keywords → dependencies
- `uv build` verified: wheel METADATA correctly inlines full license text, all classifiers, and all keywords
- 729 tests pass, ruff clean, formatting clean
- No source code changes — metadata-only story

### Change Log

- 2026-02-21: Implemented story 10.1 — LICENSE file and package metadata (license, classifiers, keywords)

### File List

- `LICENSE` (new) — MIT license text
- `pyproject.toml` (modified) — Added `license`, `classifiers`, `keywords` fields to `[project]` section
