---
stepsCompleted:
  - 'step-01-validate-prerequisites'
  - 'step-02-design-epics'
  - 'step-03-create-stories'
  - 'step-04-final-validation'
status: 'complete'
inputDocuments:
  - 'gh-issue-103'
  - 'gh-issue-69'
  - 'gh-issue-19'
  - 'gh-issue-24'
  - '_bmad-output/planning-artifacts/architecture.md'
workflowType: 'epics'
projectName: 'docvet'
featureScope: 'next'
---

# docvet - Epic Breakdown: Next

## Overview

This document provides the epic and story breakdown for the next batch of docvet improvements, sourced from GitHub issues #103, #69, #19, and #24. Covers CI hardening, docs site UX, advanced exclude patterns, and CLI progress output.

## Requirements Inventory

### Functional Requirements

FR1: The publish workflow shall include a smoke test job that installs docvet from PyPI after release and verifies `docvet --version` succeeds.

FR2: The smoke test shall verify `docvet check --help` returns successfully.

FR3: Each rule reference page shall display a back-link to its parent check page (e.g., "Part of: Enrichment Check").

FR4: The back-link shall be generated from the `check` field in `docs/rules.yml` via the `rule_header()` macro.

FR5: The `_is_excluded` function shall support trailing-slash directory patterns (e.g., `build/`) matching directory-only.

FR6: The `_is_excluded` function shall support `**` glob patterns for cross-directory matching (e.g., `**/test_*.py`).

FR7: The CLI shall display a progress bar showing files processed when stderr is a TTY.

FR8: The CLI shall show per-check timing in `--verbose` mode (e.g., `enrichment: 42 files in 0.3s`).

FR9: The CLI shall show total execution time in the summary output.

### NonFunctional Requirements

NFR1: The smoke test shall wait for PyPI propagation (~60s) before attempting install.

NFR2: The smoke test job shall use `needs: [publish]` to depend on successful publication.

NFR3: Back-links shall be implemented in the `rule_header()` macro, not as manual per-page content.

NFR4: The supported exclude pattern subset shall be documented in `docs/site/configuration.md`.

NFR5: Existing fnmatch-based exclude patterns shall remain backward compatible.

NFR6: No progress output when stderr is piped or redirected.

NFR7: No new runtime dependencies — use stdlib or typer utilities only.

### Additional Requirements

- From architecture: `_is_excluded` lives in `src/docvet/discovery.py:106-129`, uses `fnmatch.fnmatch` for both component-level and path-level matching. Python 3.12+ `pathlib.PurePath.full_match()` supports `**` natively.
- From architecture: CLI entry point is `src/docvet/cli.py`, check dispatch is in `_discover_and_handle()`
- From architecture: `rule_header()` macro is in `docs/main.py`, rule metadata in `docs/rules.yml`
- From architecture: Publish workflow is `.github/workflows/publish.yml`
- From project conventions: No new runtime deps except typer (already present) and optionally griffe
- Negation patterns (`!pattern`) deferred to a future issue — requires stateful ordered evaluation, a design decision beyond current scope

### FR Coverage Map

| FR | Epic | Story | Description |
|----|------|-------|-------------|
| FR1 | 1 | 1.1 | Smoke test install + version check |
| FR2 | 1 | 1.1 | Smoke test help verification |
| FR3 | 2 | 2.1 | Back-link on rule pages |
| FR4 | 2 | 2.1 | Generated via `rule_header()` macro |
| FR5 | 3 | 3.1 | Trailing-slash directory patterns |
| FR6 | 3 | 3.1 | `**` glob patterns |
| FR7 | 4 | 4.1 | Progress bar on TTY |
| FR8 | 4 | 4.2 | Per-check timing in verbose mode |
| FR9 | 4 | 4.2 | Total execution time |

## Epic List

### Epic 1: Publish Reliability

After a PyPI release, a smoke test automatically verifies the published package installs and runs correctly — developers can trust that releases work.

**FRs covered:** FR1, FR2
**Stories:** 1

- **Story 1.1:** Post-publish PyPI smoke test (FR1, FR2 + NFR1, NFR2)

### Epic 2: Documentation Site Navigation

Developers browsing rule reference pages can navigate back to the parent check page via a breadcrumb link — improving wayfinding in the docs.

**FRs covered:** FR3, FR4
**Stories:** 1

- **Story 2.1:** Rule page breadcrumb back-links (FR3, FR4 + NFR3)

### Epic 3: Advanced Exclude Patterns

Developers can use familiar `.gitignore`-style patterns in `exclude` and `extend-exclude` — trailing-slash directory matching and `**` cross-directory globs.

**FRs covered:** FR5, FR6
**Stories:** 2

- **Story 3.1:** Trailing-slash and double-star pattern support (FR5, FR6 + NFR5 + unit tests)
- **Story 3.2:** Integration tests and documentation (NFR4 + integration tests + docs update)

### Epic 4: CLI Progress & Timing

Developers running docvet get real-time progress feedback and execution timing — visibility into what's happening and how long checks take.

**FRs covered:** FR7, FR8, FR9
**Stories:** 2

- **Story 4.1:** Progress bar for file discovery and check execution (FR7 + NFR6, NFR7)
- **Story 4.2:** Per-check timing and total execution time (FR8, FR9 + NFR7)

## Epic 1: Publish Reliability

After a PyPI release, a smoke test automatically verifies the published package installs and runs correctly — developers can trust that releases work.

### Story 1.1: Post-publish PyPI smoke test

As a **maintainer**,
I want a CI job that installs docvet from PyPI after each release and verifies it works,
So that I can trust published releases are functional without manual verification.

**Acceptance Criteria:**

**Given** the publish workflow completes successfully
**When** the smoke-test job runs
**Then** it waits for PyPI propagation (~60s) before attempting install
**And** it installs `docvet` from PyPI using `pip install --no-cache-dir docvet==$VERSION` (version from the release tag, no cached wheels)
**And** it runs `docvet --version` and verifies exit code 0
**And** it runs `docvet check --help` and verifies exit code 0

**Given** the publish job fails
**When** the workflow evaluates job dependencies
**Then** the smoke-test job is skipped (via `needs: [publish]`)

## Epic 2: Documentation Site Navigation

Developers browsing rule reference pages can navigate back to the parent check page via a breadcrumb link — improving wayfinding in the docs.

### Story 2.1: Rule page breadcrumb back-links

As a **developer reading docvet rule documentation**,
I want each rule reference page to show a back-link to its parent check page,
So that I can navigate from a specific rule to the broader check context without using the sidebar.

**Acceptance Criteria:**

**Given** the `docs/rules.yml` file contains a `check` field for each rule (e.g., `check: enrichment`)
**When** the `rule_header()` macro in `docs/main.py` renders a rule page
**Then** it generates a visible back-link with text "Part of: {Check} Check" (e.g., "Part of: Enrichment Check")
**And** the link points to the corresponding check page (e.g., `checks/enrichment.md`)

**Given** a rule entry in `docs/rules.yml` with a valid `check` field
**When** the docs site is built with `mkdocs build --strict`
**Then** the build succeeds with zero warnings related to back-links

**Given** every rule page in the docs site
**When** a developer visits any rule page
**Then** the back-link is rendered consistently in the same position across all rule pages (via the macro, not manual content per NFR3)

## Epic 3: Advanced Exclude Patterns

Developers can use familiar `.gitignore`-style patterns in `exclude` and `extend-exclude` — trailing-slash directory matching and `**` cross-directory globs.

### Story 3.1: Trailing-slash and double-star pattern support

As a **developer configuring docvet**,
I want to use trailing-slash patterns (`build/`) and double-star globs (`**/test_*.py`) in my exclude configuration,
So that I can precisely target directories and cross-directory file patterns without listing every path.

**Acceptance Criteria:**

**Given** an exclude pattern ending with `/` (e.g., `build/`)
**When** `_is_excluded` evaluates a file path
**Then** it matches only paths where a directory component equals the pattern prefix (e.g., `build/output.py` matches, `rebuild/main.py` does not)

**Given** an exclude pattern containing `**` (e.g., `**/test_*.py`)
**When** `_is_excluded` evaluates a file path
**Then** it matches paths across any directory depth using `pathlib.PurePath.full_match()` (e.g., `src/tests/test_foo.py` matches, `src/foo.py` does not)

**Given** an existing fnmatch-compatible pattern (e.g., `*.pyc`, `test_*`)
**When** `_is_excluded` evaluates a file path
**Then** the pattern continues to work identically to current behavior (backward compatibility per NFR5)

**Given** both `exclude` and `extend-exclude` contain advanced patterns
**When** `_is_excluded` evaluates a file path
**Then** patterns from both config keys are evaluated correctly

### Story 3.2: Integration tests and documentation

As a **developer configuring docvet**,
I want the supported exclude pattern syntax documented with examples,
So that I know which patterns are available and can configure them confidently.

**Acceptance Criteria:**

**Given** a temporary git repo with files in nested directories
**When** an integration test runs docvet with a trailing-slash exclude pattern (e.g., `build/`)
**Then** files under that directory are excluded and files elsewhere are checked

**Given** a temporary git repo with files matching a `**` glob pattern
**When** an integration test runs docvet with a double-star exclude pattern (e.g., `**/test_*.py`)
**Then** matching files across all directory depths are excluded

**Given** a temporary git repo with a mix of simple and advanced patterns in config
**When** an integration test runs docvet
**Then** all pattern types work together correctly (simple fnmatch, trailing-slash, double-star)

**Given** the configuration documentation at `docs/site/configuration.md`
**When** a developer reads the exclude pattern section
**Then** it documents the supported pattern subset: simple globs, trailing-slash directory patterns, and `**` cross-directory globs with examples for each (per NFR4)

## Epic 4: CLI Progress & Timing

Developers running docvet get real-time progress feedback and execution timing — visibility into what's happening and how long checks take.

### Story 4.1: Progress bar for file processing

As a **developer running docvet**,
I want to see a progress bar showing files being processed,
So that I get real-time feedback on long-running checks instead of staring at a silent terminal.

**Acceptance Criteria:**

**Given** docvet is running with stderr connected to a TTY
**When** checks are processing files
**Then** a progress bar is displayed on stderr showing files processed out of total (e.g., `Processing: 42/128 files`)

**Given** docvet is running with stderr piped or redirected (not a TTY)
**When** checks are processing files
**Then** no progress output is written to stderr (per NFR6)

**Given** the progress bar implementation
**When** reviewing the dependency tree
**Then** no new runtime dependencies are introduced — only stdlib or typer utilities are used (per NFR7)

**Given** docvet completes all checks
**When** the final report is displayed
**Then** the progress bar is cleared and does not interfere with the report output

### Story 4.2: Per-check timing and total execution time

As a **developer running docvet**,
I want to see how long each check takes and the total execution time,
So that I can identify slow checks and understand overall performance.

**Acceptance Criteria:**

**Given** docvet is running with `--verbose` flag
**When** each check completes
**Then** a timing line is printed to stderr showing the check name, file count, and elapsed time (e.g., `enrichment: 42 files in 0.3s`)

**Given** docvet is running without `--verbose` flag
**When** each check completes
**Then** no per-check timing lines are printed

**Given** docvet completes all checks
**When** the summary output is displayed
**Then** the total execution time is shown (e.g., `Completed in 1.2s`) regardless of verbose mode

**Given** the timing implementation
**When** reviewing the dependency tree
**Then** no new runtime dependencies are introduced — only stdlib or typer utilities are used (per NFR7)
