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
  - 'src/docvet/cli.py'
  - 'src/docvet/config.py'
  - 'src/docvet/reporting.py'
  - 'party-mode-session-2026-02-26-cli-ux-research'
workflowType: 'epics'
projectName: 'docvet'
featureScope: 'cli-ux'
---

# docvet - Epic Breakdown: CLI Output & User Experience

## Overview

This document provides the epic and story breakdown for docvet's **CLI Output & User Experience** overhaul — ensuring developers running docvet in any context (terminal, CI, pre-commit, GitHub Actions) get clear, brand-consistent feedback about what was vetted and what was found. The tool is published (v1.4.0 on PyPI), all 19 rules are implemented, and the docs site is live. This phase addresses the first-impression UX gap identified during hands-on evaluation.

## Problem Statement

Running `docvet check --all` on a clean codebase currently produces:

```
docvet: 'freshness' appears in both fail-on and warn-on; using fail-on
docvet: 'enrichment' appears in both fail-on and warn-on; using fail-on
docvet: 'griffe' appears in both fail-on and warn-on; using fail-on
docvet: 'coverage' appears in both fail-on and warn-on; using fail-on
Completed in 0.1s
```

A first-time user cannot tell: what files were checked, which checks ran, whether the result is good or bad, or why they're being warned about config they didn't explicitly set. The happy path — zero findings — is the **least informative** output. In CI and pre-commit contexts, the tool provides no human-readable success signal beyond exit code 0.

Peer tools (mypy: `Success: no issues found in N source files`, interrogate: `RESULT: PASSED`, pytest: `== N passed in Xs ==`) all provide explicit positive confirmation. docvet currently sits in the silent-Unix-tradition camp alongside ruff and flake8 — tools with massive existing adoption that can afford silence. As a new tool fighting for adoption, docvet cannot.

## Requirements Inventory

### Functional Requirements

**Default Output Overhaul:**

- FR-UX1: The `check` command shall print an unconditional summary line to stderr in all output tiers except quiet, using the format: `Vetted {N} files [{checks}] — {result}. ({elapsed}s)` where result is either `no findings` or `{N} findings ({X} required, {Y} recommended)`
- FR-UX2: The summary line shall use the verb "Vetted" to reinforce the product name as a brand verb — consistent across all contexts (terminal, CI, pre-commit, GitHub Actions)
- FR-UX3: The summary line shall include the list of checks that ran (e.g., `[enrichment, freshness, coverage, griffe]`) so users know the scope of the vetting
- FR-UX4: When griffe is not installed and the griffe check is skipped, the check list in the summary shall omit `griffe` rather than listing it

**Config Warning Cleanup:**

- FR-UX5: When the user sets `fail-on` in `[tool.docvet]` but does **not** explicitly set `warn-on`, overlap between `fail-on` and the default `warn-on` shall be resolved silently — no warning emitted
- FR-UX6: When the user explicitly sets **both** `fail-on` and `warn-on` with overlapping entries, the existing warning behavior shall be preserved (user made a deliberate conflicting choice)
- FR-UX7: Detection of "user explicitly set" vs "default value" shall be based on key presence in the parsed TOML section, not on value comparison

**Verbose Flag Redesign:**

- FR-UX8: The `--verbose` flag shall be available on both the app callback (before subcommand) and on each subcommand (after subcommand name), so that both `docvet --verbose check --all` and `docvet check --all --verbose` work
- FR-UX9: When `--verbose` is specified in both positions, the result shall be verbose (logical OR)
- FR-UX10: In verbose mode, per-check timing lines, file discovery count, and the verbose header shall continue to appear on stderr above the summary line

**Quiet Mode:**

- FR-UX11: A `-q`/`--quiet` flag shall suppress all non-finding output — no summary line, no timing, no config messages on stderr
- FR-UX12: In quiet mode, findings shall still be written to stdout (quiet suppresses metadata, not data)
- FR-UX13: When both `--quiet` and `--verbose` are specified, `--quiet` wins (quiet takes precedence)
- FR-UX14: The `-q`/`--quiet` flag shall be available on both the app callback and each subcommand, following the same dual-registration pattern as `--verbose`

**Subcommand Output Parity:**

- FR-UX15: Individual subcommands (`enrichment`, `freshness`, `coverage`, `griffe`) shall follow the same three-tier output model as `check`
- FR-UX16: Each subcommand's summary line shall list only its own check name (e.g., `Vetted 12 files [enrichment] — no findings. (0.1s)`)

### NonFunctional Requirements

- NFR-UX1: The summary line format shall be stable for v1.x — scripts may parse it
- NFR-UX2: All output changes shall maintain the existing stream separation: findings on stdout, metadata/progress/summary on stderr
- NFR-UX3: Pre-commit hook output shall show the summary line (pre-commit captures stdout; the summary on stderr appears in pre-commit's own output)
- NFR-UX4: GitHub Actions job logs shall show the summary line clearly without noise from config warnings
- NFR-UX5: No new runtime dependencies — all output changes use stdlib and typer only
- NFR-UX6: All existing 729+ tests shall continue passing after each story, with test output assertions updated as needed
- NFR-UX7: The `--format markdown` and `--output` options shall continue to work correctly — summary line always on stderr regardless of output format or destination
- NFR-UX8: Zero-file edge cases (empty repo, all files excluded) shall produce a meaningful summary: `Vetted 0 files [...] — no findings. (0.0s)`

### Additional Requirements

**From Party Mode Research Session (2026-02-26):**

- "Vetted" chosen as the brand verb after competitive analysis — no other Python tool uses it, it's the verb form of the product name, and it communicates examination/approval rather than just pass/fail
- Three-tier output model (quiet/default/verbose) follows clig.dev best practices and matches the patterns of mypy, pytest, and interrogate
- Config overlap warning is the #1 noise source — fires 4x on the most common config pattern (`fail-on` set, `warn-on` not set) because defaults overlap
- `--verbose` placement before subcommand is a known Typer gotcha; dual registration is the standard solution
- Pre-commit captures stdout; GitHub Actions renders both streams; the summary line on stderr serves both contexts

**From Peer Tool Research:**

- mypy: `Success: no issues found in N source files` — explicit positive, quantified
- pytest: `== N passed in Xs ==` — green, framed, celebratory
- interrogate: `RESULT: PASSED (minimum: X%, actual: Y%)` — verdict with metrics
- ruff check: (silent) — Unix tradition, can afford it with massive adoption
- flake8: (silent) — same
- clig.dev: "It's rare that printing nothing at all is the best default behavior" for human users

**From Existing Code Analysis:**

- `cli.py:615`: `Completed in Xs` is the only unconditional stderr output — replace with summary line
- `cli.py:259`: `No findings.` is behind `if verbose` — make unconditional in default tier
- `cli.py:237-238`: Verbose header (`Checking N files [...]`) is verbose-only — merge concept into summary
- `config.py:551-570`: Overlap warning loop fires per-check — needs explicit-vs-default detection
- `reporting.py:129-139`: `format_verbose_header` can be refactored into `format_summary`

### FR Coverage Map

| FR | Story | Description |
|----|-------|-------------|
| FR-UX1 | 21.1 | Unconditional "Vetted" summary line |
| FR-UX2 | 21.1 | Brand verb in output |
| FR-UX3 | 21.1 | Check list in summary |
| FR-UX4 | 21.1 | Omit skipped checks from summary |
| FR-UX5 | 21.2 | Silent overlap resolution for default warn-on |
| FR-UX6 | 21.2 | Preserve warning for explicit both-set |
| FR-UX7 | 21.2 | Explicit-vs-default detection |
| FR-UX8 | 21.3 | Dual-register --verbose |
| FR-UX9 | 21.3 | Logical OR for both positions |
| FR-UX10 | 21.3 | Verbose tier content unchanged |
| FR-UX11 | 21.3 | --quiet flag |
| FR-UX12 | 21.3 | Quiet preserves findings on stdout |
| FR-UX13 | 21.3 | Quiet beats verbose |
| FR-UX14 | 21.3 | Quiet dual-registration |
| FR-UX15 | 21.4 | Subcommand three-tier model |
| FR-UX16 | 21.4 | Subcommand summary with own check name |

NFR coverage: NFR-UX1 (21.1), NFR-UX2 (cross-cutting), NFR-UX3 (21.1 verification), NFR-UX4 (21.2 verification), NFR-UX5 (cross-cutting), NFR-UX6 (21.5), NFR-UX7 (21.1), NFR-UX8 (21.1).

## Epic List

### Epic 21: CLI Output & User Experience

**Goal:** A developer running docvet in any context — terminal, CI, pre-commit, GitHub Actions — gets clear, brand-consistent feedback about what was vetted and what was found, using a three-tier output model (quiet/default/verbose) with the "Vetted" brand verb.

**User Value:** First-time users immediately understand what docvet checked and whether their docs are clean. CI engineers get a single summary line in job logs. Pre-commit users see meaningful output under the hook name. The tool feels polished and intentional, not silent or broken.

**Dependencies:** None — standalone epic. All changes are in `cli.py`, `config.py`, `reporting.py`, docs, and tests.

**Recommended Story Order:** 21.1 → 21.2 → 21.3 → 21.4 → 21.5

- **21.1 first**: The P0 fix — transforms the first impression for every user
- **21.2 second**: Eliminates the config noise that dominates current output
- **21.3 third**: Builds the full three-tier system (verbose + quiet)
- **21.4 fourth**: Extends the model to individual subcommands
- **21.5 last**: Test migration and docs update sweep

| Story | Theme | FRs Covered | Scope |
|-------|-------|-------------|-------|
| 21.1 | Default Output Overhaul | FR-UX1, FR-UX2, FR-UX3, FR-UX4 | `cli.py`, `reporting.py` — summary line, brand verb |
| 21.2 | Config Warning Cleanup | FR-UX5, FR-UX6, FR-UX7 | `config.py` — silent resolution, explicit detection |
| 21.3 | Verbose & Quiet Flag Redesign | FR-UX8–FR-UX14 | `cli.py` — dual-register, three tiers, quiet mode |
| 21.4 | Subcommand Output Parity | FR-UX15, FR-UX16 | `cli.py` — individual subcommands follow same model |
| 21.5 | Test Migration & Documentation | — | Tests, docs site updates |

---

## Epic 21: CLI Output & User Experience — Stories

### Story 21.1: Default Output Overhaul

As a **developer running docvet for the first time**,
I want to see a clear summary of what was checked and whether my docs are clean,
So that I immediately understand the result without needing verbose mode or guessing from exit codes.

**FRs covered:** FR-UX1, FR-UX2, FR-UX3, FR-UX4

**Acceptance Criteria:**

AC 1:
**Given** `docvet check --all` runs on a codebase with zero findings
**When** the command completes
**Then** stderr contains a summary line matching the format: `Vetted {N} files [{checks}] — no findings. ({elapsed}s)`
**And** the check list includes only checks that actually ran (e.g., `griffe` omitted if not installed)

AC 2:
**Given** `docvet check --all` runs on a codebase with findings
**When** the command completes
**Then** stdout contains the finding lines (unchanged format)
**And** stderr contains a summary line: `Vetted {N} files [{checks}] — {count} findings ({required} required, {recommended} recommended). ({elapsed}s)`

AC 3:
**Given** `docvet check --all` runs with `--format markdown` or `--output report.md`
**When** the command completes
**Then** the summary line still appears on stderr (not in the markdown output or file)

AC 4:
**Given** zero files are discovered (empty repo or all excluded)
**When** the command completes
**Then** the summary line reads: `Vetted 0 files [{checks}] — no findings. ({elapsed}s)`

AC 5:
**Given** griffe is not installed
**When** `docvet check --all` runs
**Then** the check list in the summary omits `griffe` (e.g., `[enrichment, freshness, coverage]`)

AC 6:
**Given** the existing `Completed in Xs` output on stderr (`cli.py:615`)
**When** the summary line is implemented
**Then** the `Completed in Xs` line is **replaced** by the summary line (not duplicated)
**And** the timing information is embedded in the summary line's `({elapsed}s)` suffix

AC 7:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass (existing output assertions updated as needed in this story for the `check` command only)

**Implementation notes:**
- Add `format_summary(file_count, checks, findings, elapsed)` to `reporting.py`
- Replace `cli.py:615` (`sys.stderr.write(f"Completed in {total_elapsed:.1f}s\n")`) with `sys.stderr.write(format_summary(...))`
- The `if verbose and not all_findings: sys.stdout.write("No findings.\n")` at `cli.py:259` can be removed — the summary line covers this
- The `format_verbose_header` function remains for verbose mode (separate concern, Story 21.3)

---

### Story 21.2: Config Warning Cleanup

As a **developer who set `fail-on` in their config**,
I want docvet to silently resolve the overlap with default `warn-on` values,
So that I don't see confusing warnings about a conflict I didn't create.

**FRs covered:** FR-UX5, FR-UX6, FR-UX7

**Acceptance Criteria:**

AC 1:
**Given** `pyproject.toml` with `fail-on = ["enrichment", "freshness", "coverage", "griffe"]` and no `warn-on` key
**When** docvet loads the configuration
**Then** the overlap between `fail-on` and default `warn-on` is resolved silently — zero warnings on stderr
**And** the resolved `warn-on` list is empty (all four checks promoted to fail-on)

AC 2:
**Given** `pyproject.toml` with `fail-on = ["enrichment"]` and no `warn-on` key
**When** docvet loads the configuration
**Then** zero warnings on stderr
**And** the resolved `warn-on` list is `["freshness", "griffe", "coverage"]` (defaults minus overlap)

AC 3:
**Given** `pyproject.toml` with both `fail-on = ["enrichment"]` and `warn-on = ["enrichment", "freshness"]` (explicit overlap)
**When** docvet loads the configuration
**Then** a warning is emitted: `docvet: 'enrichment' appears in both fail-on and warn-on; using fail-on`
**And** only the overlapping check produces a warning (one warning, not four)

AC 4:
**Given** `pyproject.toml` with neither `fail-on` nor `warn-on` set
**When** docvet loads the configuration
**Then** zero warnings on stderr (defaults don't conflict with themselves)

AC 5:
**Given** the detection mechanism for "user explicitly set" vs "default value"
**When** inspecting the implementation
**Then** detection is based on key presence in the parsed TOML `[tool.docvet]` section (checking if `"warn-on"` or `"warn_on"` key exists), not on value comparison

AC 6:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass (config test assertions updated for new warning behavior)

**Implementation notes:**
- In `config.py:load_config`, track whether `warn_on` was explicitly set: `warn_on_explicit = "warn_on" in parsed or "warn-on" in raw_section`
- Only emit overlap warnings when `warn_on_explicit is True`
- The overlap resolution logic (stripping from warn_on, fail_on wins) remains unchanged

---

### Story 21.3: Verbose & Quiet Flag Redesign

As a **developer using docvet in different contexts**,
I want `--verbose` to work after the subcommand name and a `--quiet` flag for minimal output,
So that I can control output verbosity naturally without memorizing flag ordering.

**FRs covered:** FR-UX8, FR-UX9, FR-UX10, FR-UX11, FR-UX12, FR-UX13, FR-UX14

**Acceptance Criteria:**

AC 1:
**Given** the `check` subcommand
**When** a user runs `docvet check --all --verbose`
**Then** the command succeeds with verbose output (per-check timing, file discovery, verbose header)
**And** the behavior is identical to `docvet --verbose check --all`

AC 2:
**Given** the `check` subcommand
**When** a user runs `docvet --verbose check --all --verbose` (both positions)
**Then** the command succeeds with verbose output (logical OR — both positions produce verbose)

AC 3:
**Given** the `check` subcommand
**When** a user runs `docvet check --all -q`
**Then** no summary line, timing, or config messages appear on stderr
**And** if there are findings, they still appear on stdout
**And** exit code reflects findings as usual

AC 4:
**Given** the `check` subcommand
**When** a user runs `docvet check --all -q --verbose` (both quiet and verbose)
**Then** quiet wins — no non-finding output on stderr

AC 5:
**Given** verbose mode is active
**When** `docvet check --all --verbose` runs
**Then** stderr shows (in order): file discovery count, per-check timing lines, summary line
**And** the summary line format is the same as default mode (from Story 21.1)

AC 6:
**Given** the `--verbose` and `-q`/`--quiet` flags
**When** inspecting the CLI help output for `docvet check --help`
**Then** both flags appear as options on the subcommand (not just on the app)

AC 7:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass

**Implementation notes:**
- Add `verbose` and `quiet` parameters to `check` command signature with `typer.Option`
- Resolve in function body: `verbose = verbose or ctx.obj.get("verbose", False)`, `quiet = quiet or ctx.obj.get("quiet", False)`
- Gate summary line: `if not quiet: sys.stderr.write(format_summary(...))`
- Gate verbose output: `if verbose and not quiet: sys.stderr.write(...)`
- Apply same pattern to app callback for `-q`/`--quiet`

---

### Story 21.4: Subcommand Output Parity

As a **developer running a single docvet check**,
I want the individual subcommands (`enrichment`, `freshness`, `coverage`, `griffe`) to show the same summary format as `check`,
So that the output experience is consistent regardless of which command I use.

**FRs covered:** FR-UX15, FR-UX16

**Acceptance Criteria:**

AC 1:
**Given** `docvet enrichment --all` runs with zero findings
**When** the command completes
**Then** stderr shows: `Vetted {N} files [enrichment] — no findings. ({elapsed}s)`

AC 2:
**Given** `docvet freshness --all` runs with findings
**When** the command completes
**Then** stderr shows: `Vetted {N} files [freshness] — {count} findings (...). ({elapsed}s)`
**And** findings appear on stdout

AC 3:
**Given** `docvet coverage --all` runs
**When** the command completes
**Then** stderr shows the summary line with `[coverage]` in the check list

AC 4:
**Given** `docvet griffe --all` runs with griffe installed
**When** the command completes
**Then** stderr shows the summary line with `[griffe]` in the check list

AC 5:
**Given** any individual subcommand with `--verbose` flag (in either position)
**When** the command completes
**Then** verbose-tier output appears (per-check timing, file count) followed by the summary line

AC 6:
**Given** any individual subcommand with `-q` flag
**When** the command completes
**Then** quiet-tier behavior applies (no summary, findings-only on stdout)

AC 7:
**Given** all changes are applied
**When** `uv run pytest` is executed
**Then** all tests pass

**Implementation notes:**
- Each `_run_*` subcommand function (`enrichment`, `freshness`, `coverage`, `griffe` in `cli.py`) currently has its own output handling
- Refactor to share the `format_summary` call with appropriate single-check name
- Apply the same `verbose`/`quiet` dual-registration pattern from Story 21.3

---

### Story 21.5: Test Migration & Documentation

As a **docvet contributor**,
I want all tests updated for the new output format and docs reflecting the three-tier model,
So that the test suite is green, docs are accurate, and future contributors understand the output design.

**Acceptance Criteria:**

AC 1:
**Given** any integration tests that assert on CLI output (e.g., checking for `Completed in`)
**When** updated for the new output format
**Then** assertions match the `Vetted N files [...]` summary line format
**And** all tests pass

AC 2:
**Given** the CLI Reference documentation page (`docs/site/cli-reference.md`)
**When** updated
**Then** it documents the three output tiers (quiet/default/verbose) with examples for each
**And** it documents the `-q`/`--quiet` flag and the `--verbose` dual-registration behavior
**And** example output uses the `Vetted` summary format

AC 3:
**Given** the CI Integration documentation page (`docs/site/ci-integration.md`)
**When** updated
**Then** it shows example GitHub Actions log output with the new summary format
**And** it shows example pre-commit output with the new summary format
**And** it documents the `-q` flag as useful for scripted/piped contexts

AC 4:
**Given** the Getting Started documentation page (`docs/site/getting-started.md`)
**When** updated
**Then** the quickstart example output matches the new default format

AC 5:
**Given** edge case tests
**When** the following scenarios are tested
**Then** each produces correct output:
- Zero files discovered → `Vetted 0 files [...] — no findings.`
- Griffe not installed → check list omits `griffe`
- `--format markdown` → summary on stderr, markdown on stdout/file
- `--output report.md` → summary on stderr, findings in file
- `--staged` with zero staged files → `Vetted 0 files [...]`
- Both `-q` and `--verbose` → quiet wins
- `--verbose` in both positions → verbose active

AC 6:
**Given** all changes across Stories 21.1–21.5
**When** `uv run pytest` is executed
**Then** all tests pass with zero failures
**And** `docvet check --all` on docvet's own codebase shows the new summary format

AC 7:
**Given** the docs site with updated pages
**When** `mkdocs build --strict` is executed
**Then** the build succeeds with zero warnings
