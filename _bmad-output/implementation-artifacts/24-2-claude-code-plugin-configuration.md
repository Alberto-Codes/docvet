# Story 24.2: Claude Code Plugin Configuration

Status: done
Branch: `feat/lsp-24-2-claude-code-plugin-configuration`

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Claude Code user,
I want a plugin that registers docvet's LSP server for Python files,
so that I get automatic docstring diagnostics in Claude Code without manual setup.

## Acceptance Criteria

1. **Given** docvet is installed with `[lsp]` extra, **when** Claude Code reads the plugin configuration, **then** it discovers and starts `docvet lsp` as an LSP server for Python files (FR141).

2. **Given** a `.py` file is opened in Claude Code, **when** the plugin configuration is active, **then** the file is mapped to the `python` language, triggering LSP activation (FR142).

3. **Given** the plugin is installed, **when** its dependencies are checked, **then** no additional dependencies beyond `docvet[lsp]` are required (NFR76).

4. **Given** the plugin files exist at the repo root, **when** a user runs `claude plugin install github:Alberto-Codes/docvet`, **then** Claude Code installs the plugin and configures the LSP server automatically.

5. **Given** the plugin is installed but `docvet` is not in PATH or `pygls` is not installed, **when** the LSP server fails to start, **then** the `docvet lsp` command's existing graceful error handling provides a clear message (no additional error handling needed in the plugin).

6. **Given** the plugin `README.md`, **when** a user reads it, **then** they understand: prerequisites (`pip install docvet[lsp]`), installation (`claude plugin install`), what diagnostics they'll see, and how to verify it works.

7. **Given** all changes are applied, **when** `uv run pytest` is executed, **then** all tests pass (no regressions — this story adds config files only, no Python source changes).

## Tasks / Subtasks

- [x] Task 1: Create `.claude-plugin/plugin.json` at repo root (AC: 1, 3, 4)
  - [x] 1.1: Create `.claude-plugin/` directory at repo root
  - [x] 1.2: Write `plugin.json` with name, description, version, author, homepage, repository, license, and keywords
  - [x] 1.3: Add `lspServers` field pointing to `.lsp.json`

- [x] Task 2: Create `.lsp.json` at repo root (AC: 1, 2, 5)
  - [x] 2.1: Write `.lsp.json` with `docvet` server entry: command `docvet`, args `["lsp"]`, extensionToLanguage `.py` → `python`

- [x] Task 3: Create plugin `README.md` in `.claude-plugin/` (AC: 6)
  - [x] 3.1: Write README with Prerequisites, Installation, Features, Verification, and Troubleshooting sections
  - [x] 3.2: Include `pip install docvet[lsp]` as prerequisite
  - [x] 3.3: Include `claude plugin install github:Alberto-Codes/docvet` as primary install method
  - [x] 3.4: Document what diagnostics the user will see (enrichment, coverage, griffe — not freshness)
  - [x] 3.5: Include verification steps (open a Python file, check for squiggles)

- [x] Task 4: Remove prototype `docvet-lsp-plugin/` directory (AC: 7)
  - [x] 4.1: Delete `docvet-lsp-plugin/` (untracked prototype from debugging session, superseded by repo-root placement)

- [x] Task 5: Add `.claude-plugin/` to docs site exclusion if needed (AC: 7)
  - [x] 5.1: Check if `mkdocs.yml` `exclude_docs` or `nav` needs updating to avoid picking up the plugin README
  - [x] 5.2: No exclusion needed — `docs_dir: docs/site` means mkdocs only scans `docs/site/`, not repo root

- [x] Task 6: Run quality gates (AC: 7)
  - [x] 6.1: All 6 quality gates pass — no Python source changes, verification-only step confirmed

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | `.claude-plugin/plugin.json` exists with `lspServers` → `.lsp.json`; `.lsp.json` configures `docvet lsp` command | Pass (structural) |
| 2 | `.lsp.json` maps `.py` → `python` in `extensionToLanguage` | Pass (structural) |
| 3 | Plugin files are JSON config only — no runtime dependencies beyond `docvet[lsp]` | Pass (structural) |
| 4 | `.claude-plugin/plugin.json` at repo root enables `claude plugin install github:Alberto-Codes/docvet` | Pass (structural) |
| 5 | `docvet lsp` graceful error handling tested in Story 24.1 (`test_lsp.py`, 25 tests) — no plugin-level error handling needed | Pass (24.1 tests) |
| 6 | `.claude-plugin/README.md` covers prerequisites, installation, features, verification, troubleshooting | Pass (structural) |
| 7 | `uv run pytest` — 971 tests pass, zero regressions | Pass |

## Dev Notes

### This Is a Config-Only Story

No Python source code changes. No new tests needed (config files aren't testable in pytest). The deliverables are:
- `.claude-plugin/plugin.json` — plugin manifest
- `.lsp.json` — LSP server configuration
- `.claude-plugin/README.md` — plugin documentation

The `docvet lsp` command and `src/docvet/lsp.py` module were delivered in Story 24.1 and are fully tested (969+ tests). This story creates the Claude Code plugin wrapper that points to the existing command.

### Plugin File Placement — Repo Root, Not Subdirectory

Claude Code's `claude plugin install github:Alberto-Codes/docvet` expects plugin files at the **repo root**:
- `.claude-plugin/plugin.json` — inside the `.claude-plugin` directory (REQUIRED)
- `.lsp.json` — at repo root level (standard location)

This means the plugin is part of the main docvet repository, not a separate repo. This is the correct approach — docvet IS the tool, and the plugin just configures Claude Code to use it. There's no separate binary or additional code.

**The `docvet-lsp-plugin/` prototype directory** was created during debugging in the previous session. It should be deleted — its contents move to the repo root.

### plugin.json — Complete Metadata

```json
{
  "name": "docvet-lsp",
  "description": "Real-time docstring quality diagnostics for Python files",
  "version": "1.0.0",
  "author": {
    "name": "Alberto-Codes",
    "url": "https://github.com/Alberto-Codes"
  },
  "homepage": "https://alberto-codes.github.io/docvet/",
  "repository": "https://github.com/Alberto-Codes/docvet",
  "license": "MIT",
  "keywords": ["python", "docstring", "linting", "diagnostics", "lsp"],
  "lspServers": "./.lsp.json"
}
```

Key decisions:
- **`name`**: `docvet-lsp` — follows kebab-case convention, namespaces the plugin
- **`version`**: `1.0.0` — initial release, independent of docvet CLI version (plugin config has its own semver)
- **`lspServers`**: Points to `.lsp.json` rather than inlining — separates concerns and follows the common pattern for LSP-only plugins
- **`keywords`**: Agent/AI-oriented plus core functionality terms

### .lsp.json — Minimal Configuration

```json
{
  "docvet": {
    "command": "docvet",
    "args": ["lsp"],
    "extensionToLanguage": {
      ".py": "python"
    }
  }
}
```

Key decisions:
- **`command`**: `docvet` — assumes `docvet` is in PATH (installed via `pip install docvet[lsp]`)
- **`args`**: `["lsp"]` — invokes the `docvet lsp` subcommand from Story 24.1
- **No `initializationOptions`**: The LSP server has no configurable options beyond what `load_config()` reads from `pyproject.toml`
- **No `startupTimeout`/`maxRestarts`**: Use Claude Code defaults — the server starts fast (<100ms) and is stable
- **No `.pyi` mapping**: Python stub files don't have docstrings — no value in analyzing them

### Executable Requirement — User Must Install docvet

The Claude Code plugin system does NOT bundle executables. The `command: "docvet"` field requires that `docvet` is installed on the user's system and in PATH. The plugin README must clearly document:

```bash
pip install docvet[lsp]
```

This installs both `docvet` (the CLI with `lsp` subcommand) and `pygls` (the LSP protocol library). If the user has `docvet` installed but NOT the `[lsp]` extra, the `docvet lsp` command prints a clear error message (Story 24.1, AC7).

### Distribution Strategy

**Primary**: `claude plugin install github:Alberto-Codes/docvet`
- Requires `.claude-plugin/plugin.json` at repo root
- Users install directly from the GitHub repo
- Zero infrastructure needed — GitHub hosts the plugin

**Secondary (future)**: Anthropic Marketplace submission
- Requires separate submission at `claude.ai/settings/plugins/submit`
- Out of scope for this story — can be done after the plugin is validated
- Would enable `claude plugin install docvet-lsp` (no github: prefix)

**Local testing**: `claude --plugin-dir /path/to/docvet`
- For development and verification during this story

### Checks Run by the LSP Server (For README Documentation)

The LSP server runs three of docvet's four checks on individual files:

| Check | What It Detects | Severity |
|-------|----------------|----------|
| Enrichment | Missing Raises, Yields, Attributes, Examples, etc. (10 rules) | Warning (required) / Hint (recommended) |
| Coverage | Missing `__init__.py` for mkdocs discoverability (1 rule) | Warning |
| Griffe | Griffe parser warnings for mkdocs rendering (3 rules) | Warning |

**Not included**: Freshness (requires git context — diff/blame — not available in single-file LSP mode).

### Testing Approach — Manual Verification

Since this story creates only JSON config files and a markdown README, there are no pytest-testable deliverables. Verification is:

1. **Structural**: Files exist at correct paths with valid JSON
2. **Functional**: `claude --plugin-dir .` loads the plugin and the LSP server starts
3. **Quality gates**: Existing 969+ tests still pass (no Python changes)

The AC-to-Test Mapping for this story will reference manual verification steps and quality gate confirmation rather than specific test functions.

### Previous Story Intelligence

**From 24.1 (LSP Server for Real-Time Diagnostics):**
- The `docvet lsp` command is implemented and tested (23 unit tests)
- pygls v2 API is used — `LanguageServer` on STDIO
- Graceful error when pygls missing: `"LSP server requires pygls. Install with: pip install docvet[lsp]"` (uses `ModuleNotFoundError`)
- Server starts fast — config load + server.start_io() has negligible overhead
- The prototype `docvet-lsp-plugin/` was created during debugging — it has the right structure but lives in the wrong location (subdirectory instead of repo root)

**From 22.5 (Discoverability Metadata):**
- Agent/AI keywords already added to PyPI metadata
- GitHub topics already include AI-oriented terms
- Plugin keywords should align with existing discoverability strategy

### What NOT to Change

- Do NOT modify `src/docvet/lsp.py` — the LSP server is complete and tested
- Do NOT modify `src/docvet/cli.py` — the `lsp` subcommand is complete
- Do NOT modify `pyproject.toml` — optional dependencies are already correct
- Do NOT modify any test files — no new testable code in this story
- Do NOT add the plugin files to the docs site build — they're repo-root config
- Do NOT create a separate repository for the plugin — it lives in the main repo

### Project Structure Notes

- New directory: `.claude-plugin/` at repo root (contains `plugin.json` and `README.md`)
- New file: `.lsp.json` at repo root
- Deleted directory: `docvet-lsp-plugin/` (prototype, replaced by repo-root placement)
- No changes to `src/`, `tests/`, or `docs/`

### References

- [Source: _bmad-output/planning-artifacts/epics-agent-adoption.md — Epic 24, Story 24.2, FR141, FR142, NFR76]
- [Source: _bmad-output/implementation-artifacts/24-1-lsp-server-for-real-time-diagnostics.md — previous story, LSP server implementation]
- [Source: src/docvet/lsp.py — LSP server module (227 lines, pygls v2)]
- [Source: src/docvet/cli.py — `lsp` subcommand with graceful pygls import]
- [Source: Claude Code Plugin Documentation — plugin.json schema, .lsp.json format, distribution methods]
- [Source: GitHub Issue #63 — Claude Code plugin configuration]

### Documentation Impact

- Pages: `.claude-plugin/README.md` (new, plugin-specific docs), `docs/site/ci-integration.md` (could add "Editor Integration" section — deferred, already noted in 24.1)
- Nature of update: Plugin README covers installation and usage. Docs site update is optional follow-up.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` — zero lint violations
- [x] `uv run ruff format --check .` — zero format issues
- [x] `uv run ty check` — zero type errors
- [x] `uv run pytest` — 971 tests pass, no regressions
- [x] `uv run docvet check --all` — zero docvet findings (full-strength dogfooding)
- [x] `uv run interrogate -v` — docstring coverage 100.0% (minimum 95.0%)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug sessions required. Config-only story with zero implementation issues.

### Completion Notes List

- Created `.claude-plugin/plugin.json` with full metadata (name, description, version, author, homepage, repository, license, keywords, lspServers)
- Created `.lsp.json` with minimal LSP server configuration (`docvet lsp`, `.py` → `python`)
- Created `.claude-plugin/README.md` with Prerequisites, Installation, Features, Verification, and Troubleshooting sections
- Deleted `docvet-lsp-plugin/` prototype directory (superseded by repo-root placement)
- Verified mkdocs exclusion not needed (`docs_dir: docs/site` scopes away from repo root)
- All 6 quality gates pass — 971 tests, zero regressions

### Change Log

- 2026-02-27: Story 24.2 implemented — Claude Code plugin configuration files created at repo root
- 2026-02-27: Code review — 4 findings fixed (keywords overhauled via 34-plugin ecosystem research, README restructured to match official Anthropic plugin style, maxRestarts added to .lsp.json)

### File List

- `.claude-plugin/plugin.json` (new) — plugin manifest
- `.claude-plugin/README.md` (new) — plugin documentation
- `.lsp.json` (new) — LSP server configuration
- `docvet-lsp-plugin/` (deleted) — prototype directory removed

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

Claude Opus 4.6 (adversarial code review workflow)

### Outcome

Changes Requested → Fixed

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|
| R1 | MEDIUM | README missing minimum docvet version requirement | Fixed — added informational note: "requires docvet 1.6.0 or later" with upgrade command |
| R2 | MEDIUM | README missing uninstall instructions | Fixed — added Uninstall section with `claude plugin remove docvet-lsp`, moved to bottom per UX flow |
| R3 | LOW | README verification steps lack concrete code example | Fixed — added 5-line Python snippet with missing Raises section |
| R4 | LOW | plugin.json keywords don't match ecosystem conventions | Fixed — overhauled via 34-plugin primary research: `["python", "docstrings", "linting", "code-quality", "lsp", "language-server", "documentation", "mkdocs"]` |
| R5 | LOW | .lsp.json missing maxRestarts for crash recovery | Fixed — added `"maxRestarts": 3` per Piebald community pattern |
| R6 | LOW | README structure doesn't match official Anthropic plugin READMEs | Fixed — added Supported Extensions section, More Information links, restructured to match pyright-lsp |

### Verification

- [x] All acceptance criteria verified
- [x] All quality gates pass (971 tests, zero regressions)
- [x] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
