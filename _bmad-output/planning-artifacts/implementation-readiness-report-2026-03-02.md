---
stepsCompleted: [1, 2, 3, 4, 5, 6]
documents:
  prd: prd.md
  architecture: architecture.md
  epics: epics-presence-mcp.md
  context: epics.md
---

# Implementation Readiness Assessment Report

**Date:** 2026-03-02
**Project:** docvet

## Document Inventory

| Document | File | Size | Modified |
|----------|------|------|----------|
| PRD | prd.md | 163KB | Feb 19 |
| Architecture | architecture.md | 223KB | Feb 21 |
| Epics (target) | epics-presence-mcp.md | 20KB | Mar 2 |
| Epics (baseline) | epics.md | 47KB | Mar 1 |

**Scope:** Epics 28 (Docstring Presence Check) and 29 (MCP Server & Agentic Integration)

**UX:** Not applicable (CLI tool)

## PRD Analysis

### Context

The PRD (prd.md) covers the original docvet scope — Epics 1-13, all complete. It defines FR1-FR127 and NFR1-NFR66 for enrichment, freshness, coverage, griffe, reporting, and v1.0 publish. Epics 28-29 represent a **new wave** with requirements sourced from GitHub issues and party-mode consensus, documented in epics-presence-mcp.md with its own FR/NFR numbering (FR1-FR5, NFR1-NFR4).

**Critical PRD reference:** FR37 explicitly states "The system can distinguish between symbols that have a docstring (analyze for completeness) and symbols with no docstring (skip — presence checking is interrogate's job)." Epic 28 fills this exact gap now that interrogate has been removed due to supply chain vulnerability.

### Wave 2 Functional Requirements (from epics-presence-mcp.md)

- **FR1:** Detect public symbols with no docstring, provide coverage percentage and configurable threshold
- **FR2:** Expose check capabilities via MCP server for programmatic agent access
- **FR3:** Publish LSP and MCP servers to Anthropic's marketplace/registry
- **FR4:** Scheduled CI workflow for weekly uv lock --upgrade (quick win)
- **FR5:** prefer-fenced-code-blocks reports ALL non-fenced patterns (quick win)

Total Wave 2 FRs: 5

### Wave 2 Non-Functional Requirements (from epics-presence-mcp.md)

- **NFR1:** Zero new runtime dependencies — presence check uses stdlib AST only
- **NFR2:** No double-counting — enrichment continues to skip undocumented symbols
- **NFR3:** Presence config: min-coverage threshold, ignore-init, ignore-magic, ignore-private
- **NFR4:** Complementary to ruff — position alongside Astral tools, never against

Total Wave 2 NFRs: 4

### Additional Requirements (from epics-presence-mcp.md)

- New module: `src/docvet/checks/presence.py`
- Run order: presence → enrichment → freshness → coverage → griffe
- Scope: modules, classes, functions, methods (properties deferred)
- Config section: `[tool.docvet.presence]` with `PresenceConfig` dataclass
- Output: individual `missing-docstring` findings + coverage summary
- Documentation: check page, rule page, migration guide from interrogate
- MCP server: `src/docvet/mcp.py`, stdio transport, `mcp` optional dep
- FR4-FR5 handled as quick wins outside of epics

### PRD Completeness Assessment

The original PRD is complete and mature (12 edit iterations, validated, all epics delivered). For Wave 2, requirements are properly sourced from GitHub issues and documented in the epics file itself. The PRD's explicit delegation of presence checking to interrogate (FR37) creates a clean rationale for Epic 28. No gaps identified between original PRD scope and Wave 2 extension.

## Epic Coverage Validation

### Coverage Matrix

| Requirement | Epic/Story Coverage | Status |
|-------------|-------------------|--------|
| FR1: Detect undocumented symbols, coverage %, threshold | Epic 28 — 28.1 ACs 1-3, 8-10 (detection + per-file stats); 28.2 ACs 4-5 (aggregate threshold) | Fully covered |
| FR2: MCP server exposing checks as tools | Epic 29 — 29.1 ACs 1-4 (tools + config); 29.2 ACs 1, 3-5 (CLI + tests) | Fully covered |
| FR3: Anthropic marketplace publishing | Epic 29 — 29.3 AC 3 (research-driven, conditional) | Conditionally covered |
| FR4: Scheduled uv lock --upgrade | Quick Win (outside epics) | Tracked |
| FR5: prefer-fenced-code-blocks all-patterns | Quick Win (outside epics) | Tracked |
| NFR1: Zero new runtime dependencies | Epic-level design constraint; 29.1 impl note (`mcp` as optional dep) | Mentioned, not AC-enforced |
| NFR2: No double-counting with enrichment | 28.2 AC 3 — explicit regression guard | Fully covered |
| NFR3: Presence config (4 options) | 28.1 ACs 4-7 (ignore-init, ignore-magic, ignore-private); 28.2 ACs 4-5 (min-coverage) | Fully covered across 28.1 + 28.2 |
| NFR4: Complementary to ruff positioning | 28.3 ACs 1, 5-6 (docs + README positioning) | Fully covered |

### Coverage Statistics

- Total Wave 2 FRs: 5
- FRs covered in epics: 3 (FR1, FR2, FR3)
- FRs tracked as quick wins: 2 (FR4, FR5)
- Total Wave 2 NFRs: 4
- NFRs covered: 4
- **Coverage: 100%** (all requirements have a traceable path)

### Gaps and Observations

**Low-severity gaps (documentation/traceability, not blocking):**

1. **NFR1 (zero runtime deps):** Stated as a design constraint but no story-level AC tests for it. Risk is low — the project already has this pattern established (coverage, enrichment, freshness all use stdlib only). During implementation, verify `pyproject.toml` gains no new mandatory deps.

2. **FR3 (marketplace publishing):** 29.3 AC 3 is research-driven and conditional. The story implementation notes explicitly acknowledge this: "If the registry doesn't exist yet or is invite-only, document the MCP server setup for manual configuration and note the registry status." This is appropriately scoped — marketplace publishing is best-effort.

3. **NFR3 traceability:** The epics document's FR Coverage Map assigns NFR3 to "Epic 28" broadly. In practice, `min-coverage` is a 28.2 concern (aggregate CLI layer) while `ignore-*` options are 28.1 concerns (per-file function). Both stories together cover all 4 options. Minor: override cases for `ignore-magic=False` and `ignore-private=False` are not explicitly AC'd (only defaults are), but these are straightforward config boolean inversions that will be covered by implementation testing.

**No blocking gaps identified.**

## UX Alignment

Not applicable — docvet is a CLI tool with no UI design requirements. UX considerations (terminal output formatting, exit codes, summary lines) are addressed directly in story ACs.

## Epic Quality Review

### Epic Structure

| Epic | User Value | Independence | Dependency Direction |
|------|-----------|-------------|---------------------|
| 28: Presence Check | Users detect undocumented symbols + enforce thresholds | Fully independent | None |
| 29: MCP Server | AI agents run checks programmatically via MCP | Depends on Epic 28 | Forward-only (correct) |

Both epics are user-value focused (not technical milestones). Dependencies flow forward only.

### Story Quality Summary

| Story | Value | Independence | AC Format | Testability | Completeness | Rating |
|-------|-------|-------------|-----------|------------|--------------|--------|
| 28.1 | PASS | PASS | PASS | MINOR | MINOR | MINOR |
| 28.2 | PASS | PASS | PASS | MINOR | MINOR | MINOR |
| 28.3 | PASS | PASS | PASS | PASS | MINOR | MINOR |
| 29.1 | PASS | PASS | PASS | MAJOR | MINOR | MAJOR |
| 29.2 | PASS | PASS | PASS | MAJOR | MINOR | MAJOR |
| 29.3 | PASS | PASS | MINOR | MAJOR | MINOR | MAJOR |

### Within-Epic Dependency Ordering

**Epic 28:** Clean chain. 28.1 (pure function) → 28.2 (CLI wiring, uses 28.1's outputs) → 28.3 (docs, uses stable feature behavior). No issues.

**Epic 29:** 29.1 (core MCP module) → 29.2 (CLI wiring + tests) → 29.3 (docs + marketplace). One issue: 29.1 AC 5 (missing-dependency CLI error) belongs in 29.2.

### Findings by Severity

#### Critical Violations (must fix before implementation)

**None.** No technical epics, no circular dependencies, no forward dependency violations.

#### Major Issues (should fix — risk of implementation confusion)

1. **28.2: Exit-code ACs conflict with `fail_on` framework.** The ACs state "exit code is non-zero if any `missing-docstring` findings exist." But the existing `determine_exit_code` only returns 1 for checks in `config.fail_on`. Unless `presence` is added to `fail_on` by default, these ACs are incorrect. The story must specify whether the default config includes `presence` in `fail_on`, or whether the `min-coverage` threshold has its own exit-code mechanism that bypasses `fail_on`.

2. **29.1: Missing-dependency AC belongs in 29.2.** AC 5 ("Given the `mcp` optional dependency is not installed / When a user runs `docvet mcp`") is CLI behavior. Move it to 29.2 to avoid implementers writing CLI code inside the core module story.

3. **29.2: Parity AC may be false by design.** "Matches the same results as `docvet check --format json`" will not be true because the MCP response includes `presence_coverage` and has a different wrapper schema. Rewrite to: "Results include all findings that `docvet check --format json` would include, plus MCP-specific metadata."

4. **29.3: Marketplace AC is conditionally untestable.** The story mixes bounded docs work with open-ended external research. Either split into 29.3a (documentation) and 29.3b (marketplace research spike), or replace the marketplace AC with a conditional structure: "If registry exists → submit. If not → document manual config path and record registry status."

#### Minor Issues (low risk — resolve during story creation or implementation)

5. **28.1: `category` value for `missing-docstring` not specified.** Finding requires `"required"` or `"recommended"`. Add to implementation notes or as an AC line.

6. **28.1: Message template in implementation notes, not ACs.** Move `"Public {symbol_type} has no docstring"` into the AC for testability.

7. **28.2: `format_summary` modification not acknowledged.** Adding coverage % to the summary line requires modifying `format_summary`'s signature — this affects all existing check subcommands and their tests. Call it out in implementation notes.

8. **28.1: No parse-error contract.** What does `check_presence` do on `SyntaxError`? Specify in implementation notes.

9. **28.3: Interrogate config mapping not enumerated.** The migration guide would benefit from a table mapping interrogate options to `[tool.docvet.presence]` equivalents.

10. **29.2: "20+ rules" count will go stale.** Express as "all rules from all check modules" rather than a hardcoded count.

11. **29.2: "Shuts down cleanly without errors" is not measurable.** Specify: process exits 0, no stderr output.

## Summary and Recommendations

### Overall Readiness Status

**READY WITH CONDITIONS** — Epic 28 is implementation-ready with minor AC refinements needed. Epic 29 requires 4 targeted AC fixes before story creation.

### Scorecard

| Category | Epic 28 | Epic 29 |
|----------|---------|---------|
| FR coverage | 100% | 100% (FR3 conditional) |
| NFR coverage | 100% | 100% |
| Epic structure | No violations | No violations |
| Story independence | Clean chain | 1 misplaced AC |
| AC quality | Minor refinements | 4 major fixes needed |
| Architecture alignment | Fits existing patterns | New transport layer |

### Issues by Category

- **Critical violations:** 0
- **Major issues:** 4 (all in Epic 29 stories or 28.2 exit-code semantics)
- **Minor issues:** 7 (refinements resolvable during story creation)
- **Total:** 11

### Recommended Next Steps

1. **Fix 28.2 exit-code semantics** before story creation. Decide: does `presence` join the default `fail_on` list, or does `min-coverage` threshold have its own exit mechanism? This is an architectural decision that affects the CLI layer. Recommendation: `presence` subcommand uses its own threshold-based exit (like a standalone tool), while `docvet check` integrates presence into the standard `fail_on`/`warn_on` framework with `presence` in `fail_on` by default.

2. **Move 29.1 AC 5 to 29.2** and add a unit-test AC to 29.1 for the handler logic. This keeps 29.1 focused on the core module and 29.2 on CLI + integration testing.

3. **Rewrite 29.2 parity AC** to compare findings (not full JSON schema match). The MCP response wraps findings differently than CLI JSON output by design.

4. **Split or restructure 29.3** to separate bounded docs work from open-ended marketplace research. Recommendation: keep as one story but replace the marketplace AC with a conditional two-branch structure that is testable regardless of registry availability.

5. **Refine 28.1 ACs** during story creation: add `category` value, move message template from notes to AC, add parse-error contract to implementation notes.

6. **Proceed with Epic 28 implementation** — the 28.1 minor issues can be resolved during story creation. Epic 28 is the higher priority (fills the interrogate gap, no external dependencies).

### Final Note

This assessment identified 11 issues across 3 categories (0 critical, 4 major, 7 minor). The project has strong fundamentals — both epics are user-value focused, dependencies flow forward-only, FR coverage is 100%, and the established patterns (progressive build, pure functions, CLI wiring separation) carry forward cleanly. The major issues are concentrated in Epic 29's AC precision, not in architectural gaps. Epic 28 can proceed to sprint planning and story creation immediately; Epic 29 should have its 4 major AC issues resolved before story creation begins.
