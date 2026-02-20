# Story 9.3: Version Bump and Build Configuration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a package maintainer preparing for v1.0 release,
I want the version set to 1.0.0 and non-distribution files excluded from the build,
so that the published package is correctly versioned and contains only production code.

## Acceptance Criteria

1. **Given** `pyproject.toml` with `version = "0.1.0"`, **when** the version is bumped, **then** `pyproject.toml` shows `version = "1.0.0"`.
2. **Given** no `--version` CLI flag exists, **when** a `--version` callback is implemented (via `importlib.metadata`), **then** `docvet --version` outputs `docvet 1.0.0` and exits.
3. **Given** no build exclusions configured, **when** `[tool.hatch.build.targets.sdist]` is added, **then** sdist excludes non-distribution directories: `tests/`, `_bmad-output/`, `_bmad/`, `.github/`, `docs/`, and fixture files.
4. **Given** version bump and build exclusions applied, **when** `uv build` is run, **then** both wheel (.whl) and sdist (.tar.gz) are produced, each under 500KB (NFR56).
5. **Given** the built wheel, **when** its contents are inspected (via `zipfile`), **then** it contains only `src/docvet/` package files — no tests, fixtures, docs, or BMAD artifacts.
6. **Given** all changes applied, **when** `uv run pytest` is run, **then** all existing tests continue to pass.

## Tasks / Subtasks

- [ ] Task 1: Bump version in `pyproject.toml` (AC: #1)
  - [ ] 1.1 Change `version = "0.1.0"` to `version = "1.0.0"` in `pyproject.toml`
- [ ] Task 2: Add `--version` flag to CLI (AC: #2)
  - [ ] 2.1 Add `importlib.metadata` import to `cli.py`
  - [ ] 2.2 Add a `_version_callback` function that prints `docvet {version}` and raises `typer.Exit()`
  - [ ] 2.3 Add `--version` option to the `main` callback using `typer.Option(callback=_version_callback, is_eager=True)`
  - [ ] 2.4 Update `main` docstring to document the new `version` parameter
- [ ] Task 3: Configure sdist build exclusions (AC: #3)
  - [ ] 3.1 Add `[tool.hatch.build.targets.sdist]` section to `pyproject.toml` with `exclude` list
- [ ] Task 4: Add tests for `--version` flag (AC: #2, #6)
  - [ ] 4.1 Test `docvet --version` outputs version string and exits with code 0
  - [ ] 4.2 Test version string matches `importlib.metadata.version("docvet")`
- [ ] Task 5: Build and verify artifacts (AC: #4, #5)
  - [ ] 5.1 Run `uv build` — produces both `.whl` and `.tar.gz`
  - [ ] 5.2 Verify wheel contains only `docvet/` package files (no tests, fixtures, docs)
  - [ ] 5.3 Verify sdist excludes `tests/`, `_bmad-output/`, `_bmad/`, `.github/`, `docs/`
  - [ ] 5.4 Verify both artifacts are under 500KB
- [ ] Task 6: Run all quality gates (AC: #6)
  - [ ] 6.1 `uv run pytest` — all existing tests pass
  - [ ] 6.2 `uv run ruff check .` — no lint errors
  - [ ] 6.3 `uv run ruff format --check .` — no formatting issues

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| #1 | Manual: inspect `pyproject.toml` | |
| #2 | `test_version_flag_outputs_version`, `test_version_flag_exits_zero` | |
| #3 | Manual: inspect sdist contents after `uv build` | |
| #4 | Manual: `uv build` + file size check | |
| #5 | Manual: `python -m zipfile -l dist/*.whl` | |
| #6 | Full test suite pass | |

## Dev Notes

### Implementation Strategy

**Task 1 — Version bump:** Single-line change in `pyproject.toml`. Straightforward.

**Task 2 — `--version` flag:** Use typer's eager callback pattern. The standard approach:

```python
import importlib.metadata

def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        version = importlib.metadata.version("docvet")
        typer.echo(f"docvet {version}")
        raise typer.Exit()
```

Then add to `main` callback:

```python
version: Annotated[
    bool | None,
    typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
] = None,
```

**Key detail:** The `is_eager=True` flag ensures `--version` is processed before any other option validation. This means `docvet --version` works without requiring a subcommand.

**Key detail:** Use `importlib.metadata.version("docvet")` (stdlib since Python 3.8) — NOT `importlib.util`. The `importlib.util` import already in `cli.py` (line 7) is for griffe spec detection and is unrelated.

**Key detail:** `importlib.metadata.version()` reads from the installed package's metadata. In dev mode (`uv sync` / editable install), it reads from `pyproject.toml` via hatchling. This means the version shown by `--version` will match `pyproject.toml` automatically.

**Task 3 — Sdist exclusions:** Hatchling's `src` layout already scopes the wheel to `src/docvet/`, so wheel exclusions are unnecessary. Only sdist needs exclusions:

```toml
[tool.hatch.build.targets.sdist]
exclude = [
    "tests/",
    "_bmad-output/",
    "_bmad/",
    ".github/",
    "docs/",
]
```

**Rationale:** Sdist is a source distribution — by default it includes everything in the repo. Users who install from sdist don't need tests, CI config, planning artifacts, or docs source. The wheel (binary distribution) already only includes `src/docvet/` via hatchling's src layout convention.

### Previous Story Intelligence (9.1 + 9.2)

**From 9.1:**
- `[tool.docvet.enrichment]` section already exists in `pyproject.toml` — don't overwrite
- All docstring findings resolved — new changes should maintain zero findings
- `typer.Exit` is used in the Raises docstring (not `click.exceptions.Exit`)

**From 9.2:**
- `__all__: list[str] = []` already set in `cli.py` — keep as empty (version callback is internal)
- 723 tests passing as baseline (story 9.2 added 45 tests to baseline of 678)
- `importlib.util` import exists on line 7 of `cli.py` — `importlib.metadata` is a separate import, add it alongside
- `E402` per-file-ignore for `checks/__init__.py` already in `pyproject.toml`

### Git Intelligence

Last 5 commits are all part of the v1.0 push:
- `feat(cli): add __all__ exports` (9.2)
- `feat(cli): add unified output pipeline and resolve all docvet findings` (9.1 + 8.3)
- `docs(prd): add v1.0 Polish and Publish phase`
- `feat(cli): wire unified output and exit code pipeline` (8.3)
- `feat(reporting): add core reporting functions module` (8.2)

All are on `develop`. Branch for this story: `feat/freshness-9-3-version-bump-and-build-config` (note: scope should match the primary area — `cli` scope is more appropriate since the main code change is the `--version` flag).

**Suggested branch:** `feat/cli-9-3-version-bump-and-build-config`

### Testing Strategy

Add tests in `tests/unit/test_cli.py`:

```python
def test_version_flag_outputs_version(runner):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "docvet" in result.output
    assert "1.0.0" in result.output  # or use importlib.metadata.version
```

**Gotcha with CliRunner:** Typer's `CliRunner` captures `typer.Exit()` as exit code 0. The `--version` callback raises `typer.Exit()` which should result in `exit_code == 0`.

**Gotcha with `resilient_parsing`:** The `main` callback already has `if ctx.resilient_parsing: return` guard (line 439). The `is_eager=True` on `--version` means it fires before `resilient_parsing` is checked, so no conflict.

### Files to Modify

| File | Changes |
|------|---------|
| `pyproject.toml` | Version bump `0.1.0` → `1.0.0`, add `[tool.hatch.build.targets.sdist]` |
| `src/docvet/cli.py` | Add `importlib.metadata` import, `_version_callback`, `--version` option to `main` |
| `tests/unit/test_cli.py` | Add `--version` flag tests |

### Project Structure Notes

- All source files are in `src/docvet/` with `checks/` subpackage
- All files use `from __future__ import annotations`
- 88-char soft limit (formatter), 100-char hard limit (linter)
- Google-style docstrings throughout
- Test files go in `tests/unit/` — existing CLI tests are in `tests/unit/test_cli.py`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.3]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-G2 — Version bump to 1.0.0]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-G5 — Build exclusions config]
- [Source: _bmad-output/planning-artifacts/epics.md#NFR56 — Package size under 500KB]
- [Source: CLAUDE.md#Build & Development — hatchling build system]
- [Source: _bmad-output/project-context.md#Technology Stack — Build: hatchling (PEP 517/518)]
- [Source: _bmad-output/project-context.md#Critical Don't-Miss Rules — Never add __main__.py]
- [Source: 9-1-fix-docvet-findings-on-own-codebase.md#Completion Notes]
- [Source: 9-2-add-all-exports-to-all-public-modules.md#Completion Notes]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
