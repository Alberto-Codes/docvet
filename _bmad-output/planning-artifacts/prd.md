---
stepsCompleted:
  - 'step-01-init'
  - 'step-02-discovery'
  - 'step-03-success'
  - 'step-04-journeys'
  - 'step-05-domain-skipped'
  - 'step-06-innovation-skipped'
  - 'step-07-project-type'
  - 'step-08-scoping'
  - 'step-09-functional'
  - 'step-10-nonfunctional'
  - 'step-11-polish'
  - 'step-12-complete'
status: 'complete'
lastEdited: '2026-02-11'
editHistory:
  - date: '2026-02-11'
    changes: 'Added griffe compatibility check (Layer 5) as next epic; added 1 journey, griffe module spec, 3 rules (griffe-missing-type, griffe-unknown-param, griffe-format-warning), FRs (FR81-FR97), NFRs (NFR39-NFR48); updated Executive Summary, Success Criteria, Product Scope to cover all four docvet-owned layers; moved coverage to Complete status; incorporated 6 party-mode review findings (CLI skip messaging, search path clarification, all-files-filtered-out FR, warning pattern enumeration, multi-finding-per-symbol clarification, format-warning split as growth candidate)'
  - date: '2026-02-11'
    changes: 'Fixed 3 validation findings: NFR3/NFR21 reworded as design invariants (measurability fix); FR44/FR51/FR79 removed module name references (implementation leakage fix); Journey traceability attribution corrected missing-typed-attributes from J2 to J4'
  - date: '2026-02-11'
    changes: 'Added coverage check (Layer 6) as next epic; added 1 journey, coverage module spec, 12 FRs (FR69-FR80), 6 NFRs (NFR33-NFR38); fixed 3 validation items (FR12 cross-ref definition, FR49 wording, stale-import traceability); incorporated 7 party-mode review findings (message content, src_root default, namespace workaround, symbol convention, deterministic ordering)'
  - date: '2026-02-09'
    changes: 'Added freshness check (Layer 4) as next epic; added 3 journeys, freshness module spec, 26 FRs, 13 NFRs; fixed enrichment traceability gap with edge-case journey'
classification:
  projectType: 'cli_tool'
  domain: 'developer_tooling'
  complexity: 'medium'
  projectContext: 'brownfield'
inputDocuments:
  - '_bmad-output/project-context.md'
  - 'docs/product-vision.md'
  - 'docs/architecture.md'
  - 'docs/project-overview.md'
  - 'docs/development-guide.md'
  - 'docs/source-tree-analysis.md'
  - 'docs/index.md'
  - '_bmad-output/implementation-artifacts/tech-spec-4-cli-scaffold.md'
  - '_bmad-output/implementation-artifacts/tech-spec-ci-workflow.md'
  - '_bmad-output/implementation-artifacts/tech-spec-config-reader.md'
  - '_bmad-output/implementation-artifacts/tech-spec-file-discovery.md'
  - '_bmad-output/implementation-artifacts/tech-spec-7-ast-helpers.md'
  - '_bmad-output/implementation-artifacts/tech-spec-wire-discovery-cli.md'
  - 'gh-issue-8'
  - 'gh-issue-9'
  - 'gh-issue-10'
  - 'gh-issue-11'
documentCounts:
  briefs: 0
  research: 0
  brainstorming: 0
  projectDocs: 17
workflowType: 'prd'
projectName: 'docvet'
featureScope: 'enrichment-freshness-coverage-and-griffe-checks'
---

# Product Requirements Document - docvet

**Author:** Alberto-Codes
**Date:** 2026-02-08

## Executive Summary

docvet is a Python CLI tool for comprehensive docstring quality vetting. This PRD defines requirements for four check modules: the **enrichment check** (Layer 3: completeness), the **freshness check** (Layer 4: accuracy), the **griffe compatibility check** (Layer 5: rendering), and the **coverage check** (Layer 6: visibility). Together they cover all four docvet-owned layers in the six-layer quality model.

The enrichment check fills a 4-year ecosystem gap by detecting missing docstring sections (Raises, Yields, Attributes, Examples, and more) through AST analysis. The freshness check detects stale docstrings — code that changed without a corresponding docstring update — by mapping git diff hunks and git blame timestamps to AST symbols. The griffe compatibility check catches docstrings that parse fine as text but produce warnings during mkdocs build — missing type annotations in Args, parameters documented but absent from the function signature, and formatting issues that degrade rendered documentation. The coverage check detects Python files invisible to mkdocstrings due to missing `__init__.py` files in parent directories. All four complement ruff (style) and interrogate (presence) rather than competing with them. darglint — the only prior tool in this space — has been unmaintained since 2022 and never addressed staleness, rendering, or visibility detection; ruff stops at D417 (param completeness).

**Target users:** Python developers writing Google-style docstrings, teams using mkdocs-material + mkdocstrings.

**Scope:** Enrichment: 10 rule identifiers covering 14 detection scenarios, `required` vs `recommended` categorization, full config via `[tool.docvet.enrichment]`. Freshness: 5 rule identifiers across diff mode (3 severity-tiered rules) and drift mode (2 threshold-based rules), full config via `[tool.docvet.freshness]`. Griffe: 3 rule identifiers for rendering compatibility warnings, optional dependency on griffe library, no per-check configuration. Coverage: 1 rule identifier for missing `__init__.py` detection, pure filesystem check with no configuration.

### Key Terms

- **Detection scenario**: A specific code pattern that triggers a check (e.g., "function with `raise` but no `Raises:` section"). 14 total for enrichment.
- **Rule identifier**: A stable kebab-case name emitted in findings (e.g., `missing-raises`, `stale-signature`, `griffe-missing-type`, `missing-init`). 10 enrichment + 5 freshness + 3 griffe + 1 coverage = 19 total. Multiple scenarios can share one rule ID.
- **Required vs recommended**: Category baked into each rule definition. Required = misleading omission; recommended = improvement opportunity. Freshness maps severity to category: HIGH→required, MEDIUM/LOW→recommended.
- **Missing vs incomplete**: Enrichment MVP detects *missing* sections only (no `Raises:` section at all). *Incomplete* sections (has `Raises:` but doesn't list all exceptions) are a Growth feature.
- **Diff mode**: Freshness check mode that analyzes `git diff` output to detect symbols where code changed but docstring did not. Primary workflow — fast, runs per-commit.
- **Drift mode**: Freshness check mode that analyzes `git blame` timestamps to detect docstrings that fell behind their code by configurable time thresholds. Periodic sweep — slower, runs quarterly.
- **Staleness severity**: Diff mode classifies findings as HIGH (signature changed), MEDIUM (body changed), or LOW (imports/formatting changed). Higher severity = greater likelihood the docstring actively misleads.
- **Griffe compatibility check**: Layer 5 (rendering) detection. Uses the griffe library (the mkdocstrings docstring parser) to parse docstrings and capture warnings that would appear during `mkdocs build`. Catches issues invisible to AST analysis — missing type annotations, unknown parameters, and malformed section formatting.
- **Rendering warning**: A griffe parser warning indicating a docstring element that will render incorrectly or incompletely in mkdocs-material documentation. Distinct from a missing section (enrichment) or stale content (freshness).
- **Coverage check**: Layer 6 (visibility) detection. Identifies Python files whose parent directories lack `__init__.py`, making them invisible to mkdocstrings — they exist but won't appear in generated documentation.
- **Package boundary**: The `src-root` directory (e.g., `src/` or project root) above which `__init__.py` is not required. Coverage walks upward from each file's parent to this boundary.

## Success Criteria

### User Success

- A developer runs `docvet enrichment` and gets a clear, prioritized list of missing docstring sections across their codebase
- Each finding is immediately actionable: file, line, symbol name, a human-readable kebab-case rule identifier (e.g., `missing-raises`), and a concise message explaining what's missing and why
- Findings are categorized as `required` (misleading omission) or `recommended` (improvement opportunity), so developers can triage effectively
- Well-documented code produces zero findings -- no false positives on complete docstrings
- The check respects existing `EnrichmentConfig` toggles, so teams customize which rules run without noise
- A developer runs `docvet freshness` and sees which docstrings are stale after code changes, with severity-tiered findings (HIGH for signature changes, MEDIUM for body changes, LOW for imports/formatting)
- A tech lead runs `docvet freshness --mode drift --all` and discovers docstrings that drifted out of sync over time — long-untouched docstrings on recently-modified code
- A developer runs `docvet coverage --all` and discovers Python files invisible to mkdocstrings because parent directories lack `__init__.py` — files that exist but won't appear in generated documentation
- A developer runs `docvet griffe` and discovers docstrings that will produce warnings during `mkdocs build` — missing type annotations in Args, parameters documented but absent from the function signature, and formatting issues that degrade rendered output

### Business Success

- Fills the explicit gap between ruff D417 (param completeness) and full section completeness -- no existing tool covers this
- Positions docvet as a credible addition to the Python quality toolchain alongside ruff, ty, and interrogate
- Rule identifiers follow industry convention (ty-style kebab-case), making docvet feel native to modern Python workflows
- All 14 detection scenarios (10 rule identifiers) ship together, delivering complete Layer 3 coverage in a single release
- No existing tool maps git diffs to AST symbols for stale docstring detection -- freshness check is a novel capability in the Python ecosystem
- Diff mode integrates into pre-commit workflows; drift mode enables periodic audits -- two time horizons, one tool
- Coverage check closes the visibility gap -- developers currently discover missing `__init__.py` only when mkdocs builds silently omit their modules; docvet catches this before deployment
- Griffe compatibility check catches rendering issues at lint time instead of during `mkdocs build` -- developers fix docstring formatting before deployment, not after a broken docs build
- Completes docvet's four-layer model (completeness, accuracy, rendering, visibility) -- the only Python tool providing unified docstring quality coverage from content to deployment

### Technical Success

- `check_enrichment(source, tree, config, file_path)` returns `list[Finding]` with zero side effects -- pure function, deterministic output
- `check_freshness_diff(file_path, diff_output, tree)` returns `list[Finding]` with deterministic severity assignment based on what changed
- `check_freshness_drift(file_path, blame_output, tree, config)` returns `list[Finding]` with configurable drift and age thresholds
- `check_coverage(src_root, files)` returns `list[Finding]` with pure filesystem logic -- no AST, no git, no configuration
- `check_griffe_compat(src_root, files)` returns `list[Finding]` by loading the package via griffe and capturing parser warnings -- optional dependency, graceful skip when griffe not installed
- Each `Finding` carries: `file`, `line`, `symbol`, `rule` (kebab-case stable identifier), `message`, `category` (`required` | `recommended`)
- All 14 enrichment detection scenarios (10 rule identifiers) implemented and individually toggleable via `EnrichmentConfig`
- All 5 freshness rule identifiers (3 diff + 2 drift) implemented with severity-to-category mapping
- Griffe check: 3 rule identifiers (`griffe-missing-type`, `griffe-unknown-param`, `griffe-format-warning`) capturing rendering compatibility warnings
- Coverage check: 1 rule identifier (`missing-init`) detecting missing `__init__.py` in parent directory hierarchies
- No new runtime dependencies for enrichment, freshness, or coverage -- stdlib `ast`, `pathlib`, and existing `ast_utils.Symbol` infrastructure. Griffe check requires optional `griffe` dependency
- Checks are isolated -- no imports from other check modules, no shared mutable state
- Quality gates pass: ruff, ty, pytest with >=85% coverage, interrogate

### Measurable Outcomes

- `tests/fixtures/missing_raises.py` produces exactly the expected `missing-raises` finding
- `tests/fixtures/missing_yields.py` produces exactly the expected `missing-yields` finding
- `tests/fixtures/complete_module.py` produces zero findings
- Each of the 10 enrichment rule identifiers has at least one dedicated unit test with a source string fixture
- `EnrichmentConfig` toggles (`require-raises = false`, etc.) suppress the corresponding rule's findings
- Unit tests with mocked git diff output produce expected severity findings for each diff mode rule (`stale-signature`, `stale-body`, `stale-import`)
- Unit tests with mocked git blame output produce expected drift findings (`stale-drift`, `stale-age`) at configurable thresholds
- Integration tests with real git repos (temp dirs with known commits) verify end-to-end diff and drift detection
- Edge case tests: new files produce zero findings, deleted functions produce zero findings
- Coverage unit tests with `tmp_path` filesystem fixtures verify `missing-init` detection across nested package hierarchies
- A properly packaged project (all `__init__.py` present) produces zero coverage findings
- Unit tests with known-bad docstrings (missing type annotations, unknown parameters, malformed formatting) produce expected griffe findings for each of the 3 rule identifiers
- Well-documented code with typed Args and valid parameter names produces zero griffe findings
- When griffe is not installed, `check_griffe_compat` returns an empty list without raising exceptions

## Product Scope

### Competitive Context

darglint -- the only tool that partially addressed Args/Returns/Raises alignment -- has been unmaintained since 2022. Ruff's D rules stop at D417 (param completeness) and explicitly chose not to go deeper into section completeness. No existing tool maps git diffs to AST symbols for stale docstring detection -- the closest prior art is manual `git blame` inspection. No existing linter catches griffe parser warnings before `mkdocs build` -- developers currently discover rendering issues only when reviewing built documentation. This leaves a 4-year vacuum in the ecosystem for docstring completeness (Layer 3), accuracy (Layer 4), and rendering compatibility (Layer 5). docvet fills all three gaps by complementing ruff (style) and interrogate (presence) rather than competing with them -- the six-layer quality model makes the composability explicit: layers 1-2 are delegated to existing tools, layers 3-6 are docvet's territory.

### MVP - Enrichment Check (Layer 3)

The enrichment MVP delivers all 10 rule identifiers (14 detection scenarios), the shared `Finding` type, full `EnrichmentConfig` integration, and comprehensive unit tests. This is fully implemented (3 epics, 11 stories, 415 tests). See "Project Scoping & Phased Development > Enrichment MVP Feature Set" for the authoritative implementation checklist.

### Freshness Check (Layer 4) — Complete

The freshness module delivers 5 rule identifiers across diff mode (3 severity-tiered rules) and drift mode (2 threshold-based rules), reuses the shared `Finding` type, integrates with existing `FreshnessConfig`, and includes unit tests with mocked git output plus integration tests with real git repos. See "Project Scoping & Phased Development > Freshness Feature Set" for the authoritative implementation checklist.

### Coverage Check (Layer 6) — Complete

The coverage module delivers 1 rule identifier (`missing-init`) that detects Python files invisible to mkdocstrings due to missing `__init__.py` in parent directories. The simplest of the four checks — pure filesystem traversal, no AST analysis, no git integration, no per-check configuration. This is fully implemented (1 epic, 2 stories, 557 tests). See "Project Scoping & Phased Development > Coverage Feature Set" for the authoritative implementation checklist.

### Next Epic — Griffe Compatibility Check (Layer 5)

The griffe epic delivers 3 rule identifiers (`griffe-missing-type`, `griffe-unknown-param`, `griffe-format-warning`) that capture rendering compatibility warnings by parsing docstrings with the griffe library — the same parser used by mkdocstrings during `mkdocs build`. Griffe is an optional dependency (`pip install docvet[griffe]`); the check gracefully skips when griffe is not installed. Operates at the package level (griffe loads entire packages, not individual files), with warnings filtered to discovered files and mapped to `Finding` objects. No per-check configuration. See "Project Scoping & Phased Development > Griffe Feature Set" for the authoritative implementation checklist.

### Growth & Vision

Growth features include inline suppression, JSON output, incomplete section detection (enrichment), hunk-level precision and auto-fix suggestions (freshness), and cross-check intelligence (enrichment + freshness + griffe + coverage combined findings). Vision includes editor/LSP integration and additional docstring style support. See "Project Scoping & Phased Development > Post-Epic Features" for the full Phase 2 and Phase 3 roadmap.

## User Journeys

### Journey 1: Dev During Development -- "The Missing Raises Catch"

**Persona:** Maya, a mid-level Python developer working on a data pipeline library. She writes Google-style docstrings diligently but sometimes forgets edge cases.

**Opening Scene:** Maya just finished implementing a new `parse_config()` function. It validates input and raises `ValueError` on bad keys and `FileNotFoundError` when the config path is missing. She wrote a clean docstring with `Args:` and `Returns:` sections but didn't add a `Raises:` section -- she was focused on the happy path.

**Rising Action:** Before committing, she runs `docvet enrichment` on her working directory. The terminal shows:

```
src/pipeline/config.py:42: missing-raises Function 'parse_config' raises ValueError, FileNotFoundError but has no Raises: section
```

One finding. Clear file, line, symbol, rule name, and a message that tells her exactly which exceptions she missed.

**Climax:** Maya opens the file, adds the `Raises:` section documenting both exceptions with descriptions. She runs `docvet enrichment` again -- zero findings. She knows her docstring now accurately describes the function's behavior.

**Resolution:** The downstream developer who calls `parse_config()` next week sees the `Raises:` section in their IDE tooltip and adds proper error handling. Maya's docstring prevented a silent failure in production.

### Journey 2: PR Workflow -- "The Pre-Commit Safety Net"

**Persona:** Raj, a senior developer on a team that runs `docvet check --staged` before every commit.

**Opening Scene:** Raj refactored a data validation class, converting it from a plain class to a `dataclass` with 6 fields. He updated the class docstring's summary line but didn't add an `Attributes:` section for the new fields.

**Rising Action:** He stages his changes and runs `docvet check --staged`. The enrichment check fires alongside freshness, coverage, and griffe:

```
src/models/validation.py:15: missing-attributes Dataclass 'ValidationResult' has 6 fields but no Attributes: section
```

The other three checks pass clean. Just this one enrichment finding.

**Climax:** Raj adds the `Attributes:` section with types and descriptions for all 6 fields. He re-stages and runs `docvet check --staged` again -- all clear. He commits with confidence.

**Resolution:** During PR review, the reviewer sees the complete `Attributes:` section and understands the dataclass instantly. No review comment asking "what does `threshold` do?" -- the docstring already answers it.

**Edge Case -- The Disagreement:** A week later, Raj gets a `missing-examples` finding on a private helper function `_normalize_path()`. He doesn't think a private utility needs an `Examples:` section. He adjusts `require-examples = ["class", "protocol", "dataclass"]` in `pyproject.toml`, removing the recommendation for plain functions. Next run, the finding is gone. The tool respects his judgment -- it's a guardrail, not a mandate.

### Journey 3: CI Pipeline -- "The Automated Gate"

**Persona:** The CI system running on a GitHub Actions PR workflow for a team using docvet with default configuration.

**Opening Scene:** A junior developer opens a PR that adds a generator function with `yield` statements but no `Yields:` section in the docstring. The PR triggers the CI pipeline.

**Rising Action:** The CI job runs `docvet check`. With default config, `enrichment` is in `warn-on` -- advisory mode. The enrichment check produces:

```
src/stream/processor.py:88: missing-yields Generator 'stream_events' uses yield but has no Yields: section
```

Docvet exits with code 0. The CI check passes green, but the finding appears in the build log as a warning.

**Climax:** The tech lead notices the warning in the PR log during review. She asks the developer to fix it. After three similar PRs in a row, she decides the team is ready for enforcement. She moves `enrichment` to `fail-on` in `pyproject.toml`:

```toml
[tool.docvet]
fail-on = ["enrichment"]
```

Now enrichment findings cause non-zero exit. CI goes red on incomplete docstrings.

**Resolution:** The next PR with a missing `Yields:` section fails CI automatically. The developer sees the failed check, reads the clear message, and fixes it before review. The team's documentation standard is enforced without human reviewers spending time on it. The gradual promotion from `warn-on` to `fail-on` let the team adopt at their own pace.

### Journey 4: Tech Lead Audit -- "The Codebase Sweep"

**Persona:** Carlos, a tech lead adopting docvet for his team's mkdocs-material documentation site. He wants to understand the documentation debt across the codebase.

**Opening Scene:** Carlos configures `[tool.docvet.enrichment]` in `pyproject.toml`, keeping all defaults (`require-raises = true`, `require-yields = true`, etc.) but setting `require-examples` to only `["protocol", "dataclass"]` -- his team doesn't need examples on every public function yet.

**Rising Action:** He runs `docvet enrichment --all`. The terminal shows 47 findings across 12 files. He sees a mix of `required` and `recommended` categories:

```
src/core/engine.py:23: missing-raises ...
src/core/engine.py:91: missing-warns ...
src/models/schema.py:15: missing-attributes ...
src/models/schema.py:44: missing-typed-attributes ...
src/protocols/handler.py:8: missing-examples ...
```

**Climax:** Carlos triages by rule. He creates a team issue for the 12 `missing-raises` findings (highest impact -- actively misleading callers). He deprioritizes the 5 `missing-examples` findings on protocols as a future sprint item. The kebab-case rule identifiers make it easy to grep, filter, and assign.

**Resolution:** Over two sprints, the team systematically works through the findings. Each sprint they re-run `docvet enrichment --all` and watch the count drop. Carlos eventually moves `enrichment` to `fail-on` to prevent new debt from accumulating.

### Journey 5: New Adopter -- "The First Run"

**Persona:** Priya, a developer who just heard about docvet and wants to try it on her existing Django REST framework project with ~200 Python files.

**Opening Scene:** Priya installs docvet (`pip install docvet`) and runs `docvet enrichment --all` with zero configuration. Default `EnrichmentConfig` applies -- all rules enabled.

**Rising Action:** The output is overwhelming: 183 findings scroll past. Every function that raises an exception, every generator, every class missing `Attributes:`. Priya's stomach drops -- "Is my code really this bad?"

**Climax:** But then she sees the summary at the bottom:

```
183 findings (34 required, 149 recommended)
```

That single line changes everything. 34 real issues where her docstrings actively mislead developers. 149 nice-to-haves that would make the docs better but aren't urgent. She's not drowning -- she has a clear path forward.

She adds targeted configuration to focus on what matters first:

```toml
[tool.docvet.enrichment]
require-warns = false
require-other-parameters = false
require-cross-references = false
prefer-fenced-code-blocks = false
require-examples = []
```

She re-runs: 34 findings. All `required` -- missing `Raises:`, `Yields:`, and `Attributes:` sections. Manageable.

**Resolution:** Priya fixes the 8 most critical findings in her core modules, commits, and sets up docvet in CI with `enrichment` in `warn-on`. She'll tighten the config as the team catches up. The tool met her where she was instead of demanding perfection on day one.

### Journey 6: The Stale Signature Catch (Diff Mode)

**Persona:** Nadia, a backend developer maintaining an HTTP client library. She writes Google-style docstrings and runs `docvet check --staged` as part of her pre-commit workflow.

**Opening Scene:** Nadia is refactoring `send_request()` in her HTTP client module. The function previously accepted a `timeout` parameter (seconds as float), but the team decided to rename it to `max_wait_seconds` for clarity and change its type from `float` to `int`. She updates the function signature, adjusts the body logic, and stages the changes. The docstring still reads `timeout (float): Number of seconds before the request times out.` in its `Args:` section -- she was focused on the behavioral change and forgot to update the documentation.

**Rising Action:** She runs `docvet check --staged`. The freshness check maps the staged diff hunks to AST symbols and detects that `send_request`'s signature lines are in the diff but its docstring lines are not. Because the signature changed (parameter renamed), this is a HIGH severity finding -- the docstring actively misleads callers about the parameter name. The terminal shows:

```
src/client/http.py:42: stale-signature Function 'send_request' signature changed but docstring not updated
```

One finding, category `required`. The enrichment and coverage checks pass clean. The `stale-signature` rule fires specifically because diff hunks overlap with the function's `def` line and parameter list -- the strongest signal that the docstring is stale.

**Climax:** Nadia opens `http.py`, sees the `Args:` section still referencing `timeout (float)`, and updates it to `max_wait_seconds (int): Maximum seconds to wait before the request times out.` She re-stages and runs `docvet check --staged` again -- zero findings. The docstring now matches the code.

**Resolution:** A teammate calls `send_request()` the next day, reads the docstring in their IDE, and passes `max_wait_seconds=30` on the first try. Without the freshness catch, they would have written `timeout=30`, hit a `TypeError`, and spent time debugging a documentation lie.

**Edge Case -- Body Change vs. Signature Change:** In the same PR, Nadia also modifies the retry logic inside `send_request()` without touching the signature. This produces a separate MEDIUM severity finding (`stale-body`) with category `recommended` -- the body changed but the docstring may or may not need updating. She reviews it, decides the docstring's description still accurately describes the retry behavior, and moves on. MEDIUM findings are advisory; HIGH findings demand action.

**Edge Case -- Import-Only Change:** Later that day, Nadia reorganizes the imports at the top of `http.py` -- reordering and grouping them per `isort` conventions. The diff touches lines within `send_request`'s enclosing range (between its decorator and the next function) but outside its signature, docstring, and body. The freshness check emits a LOW severity finding (`stale-import`) with category `recommended`. Nadia glances at it, confirms the docstring is unaffected by import reordering, and moves on. LOW findings are noise-reduction candidates -- teams that find them unhelpful can move freshness to `warn-on`.

### Journey 7: The Quarterly Documentation Audit (Drift Mode)

**Persona:** Marcus, a tech lead responsible for documentation quality across a 400-file Python monorepo. His team uses mkdocs-material for API docs and runs `docvet enrichment` in CI. He wants a periodic sweep to catch docstrings that drifted out of sync over time -- changes too old for diff mode to catch.

**Opening Scene:** Marcus configures drift thresholds in `pyproject.toml` based on his team's sprint cadence:

```toml
[tool.docvet.freshness]
drift-threshold = 30
age-threshold = 90
```

`drift-threshold = 30` means: flag any symbol where the code was modified 30+ days more recently than the docstring. `age-threshold = 90` means: flag any docstring untouched for 90+ days regardless of code changes -- ancient docs that need review.

**Rising Action:** He runs `docvet freshness --mode drift --all`. The drift check uses `git blame --line-porcelain` to compare per-line timestamps for each symbol's code vs. docstring. The terminal shows 23 findings:

```
src/core/engine.py:45: stale-drift Function 'process_batch' code modified 2025-12-14, docstring last modified 2025-10-02 (73 days drift)
src/core/engine.py:112: stale-drift Class 'BatchProcessor' code modified 2026-01-18, docstring last modified 2025-11-30 (49 days drift)
src/models/schema.py:23: stale-age Function 'validate_schema' docstring untouched since 2025-09-15 (147 days)
src/models/schema.py:67: stale-age Class 'SchemaRegistry' docstring untouched since 2025-10-01 (131 days)
...
```

15 `stale-drift` findings (category `recommended` -- code drifted from docs) and 8 `stale-age` findings (category `recommended` -- docstrings old enough to warrant review). All freshness drift/age findings are `recommended` because time-based heuristics indicate *potential* staleness, not confirmed misleading content.

**Climax:** Marcus triages by rule. He exports the findings, groups by module owner, and creates two team issues: one for the 15 `stale-drift` findings (prioritized by drift days -- the 73-day-old `process_batch` docstring goes first) and one for the 8 `stale-age` findings (lower priority -- these need review, not necessarily changes). The kebab-case rule identifiers make grep and filtering trivial: `docvet freshness --mode drift --all | grep stale-drift` isolates the active-drift subset.

**Resolution:** Over two sprints, the team works through both lists. Each developer runs `docvet freshness --mode drift` on their assigned files, updates docstrings, and verifies zero findings before marking the issue closed. Marcus re-runs the full sweep at the end of sprint 2: 3 findings remain (new drift from recent changes). He schedules the sweep as a quarterly recurring task. The combination of diff mode in CI (catching immediate staleness) and drift mode quarterly (catching accumulated drift) gives the team complete freshness coverage across time horizons.

### Journey 8: Enrichment Edge Case Variants

**Persona:** Wei, a developer running `docvet enrichment --all` during a refactoring sprint on a data processing library. She has fixed the `missing-raises`, `missing-yields`, `missing-attributes`, `missing-warns`, `missing-typed-attributes`, and `missing-examples` findings from earlier sprints. Four rules remain that she hasn't encountered before.

**Rising Action -- `missing-receives`:** Wei's library includes a coroutine-style generator that uses `value = yield` to receive values from callers via `.send()`. The function has a `Yields:` section but no `Receives:` section documenting what types callers should send:

```
src/pipeline/coroutines.py:34: missing-receives Generator 'accumulator' uses send pattern but has no Receives: section
```

Category `required`. The `value = yield` assignment is the trigger -- plain `yield` without assignment does not fire this rule. She adds `Receives:` documenting the expected input type.

**Rising Action -- `missing-other-parameters`:** A utility function accepts `**kwargs` and forwards them to an underlying API client. The docstring has `Args:` for the explicit parameters but nothing for the keyword arguments:

```
src/utils/api.py:78: missing-other-parameters Function 'call_endpoint' has **kwargs but has no Other Parameters: section
```

Category `recommended`. She adds `Other Parameters:` listing the common keyword arguments callers actually pass.

**Rising Action -- `missing-cross-references`:** An `__init__.py` module docstring has a `See Also:` section, but it lists related modules as plain text (`config`, `schema`) instead of using cross-reference syntax:

```
src/pipeline/__init__.py:1: missing-cross-references Module 'pipeline' See Also section lacks cross-reference syntax
```

Category `recommended`. Wei updates the entries to use mkdocs cross-reference format so they render as clickable links in the documentation site.

**Rising Action -- `prefer-fenced-code-blocks`:** A class docstring's `Examples:` section uses `>>>` doctest format instead of fenced code blocks:

```
src/models/registry.py:15: prefer-fenced-code-blocks Class 'Registry' Examples section uses >>> format instead of fenced code blocks
```

Category `recommended`. The `>>>` format works but renders poorly in mkdocs-material. Wei converts it to a triple-backtick fenced block with `python` syntax highlighting.

**Resolution:** Wei clears all four finding types in a single commit. These rules are lower-frequency than `missing-raises` or `missing-attributes` -- most codebases encounter them in a handful of files rather than dozens. But they close the completeness gap: every enrichment rule now has a demonstrated correction path, and Wei's library produces zero enrichment findings across all 10 rules.

### Journey 9: The Invisible Module (Coverage Check)

**Persona:** Tomás, a developer on a team that recently adopted mkdocs-material for API documentation. He added a new `analytics` subpackage to the project last sprint, creating `src/myproject/analytics/tracker.py` and `src/myproject/analytics/reporter.py` with thorough docstrings. The mkdocs build completed without errors, but neither module appeared in the generated API reference.

**Opening Scene:** Tomás spent 30 minutes debugging his mkdocs configuration before a teammate mentioned: "Did you add an `__init__.py` to the `analytics/` directory?" He hadn't. Without `__init__.py`, Python can't import the package, and mkdocstrings can't discover the modules. He creates the missing file, rebuilds, and the docs appear. He wishes he'd caught this before deploying a docs build with silently missing content.

**Rising Action:** Tomás adds `docvet coverage --all` to the team's CI pipeline. The next PR from a colleague adds a `src/myproject/exports/csv_writer.py` module nested two levels deep — but the colleague only created `src/myproject/exports/__init__.py`, forgetting that `src/myproject/exports/formats/` (an intermediate directory) also needs one. The coverage check catches it:

```
src/myproject/exports/formats/csv_writer.py:1: missing-init Directory 'formats' is missing __init__.py — file invisible to mkdocstrings
```

One finding, category `required`. The file path, directory name, and consequence are immediately clear.

**Climax:** The colleague creates `src/myproject/exports/formats/__init__.py`, re-runs `docvet coverage --all` — zero findings. Every Python file in the project is now importable and visible to mkdocstrings.

**Resolution:** The team keeps `docvet coverage` in `fail-on` in CI. Missing `__init__.py` is now caught at PR time, not after a docs deployment with silently absent modules. The check is fast (pure filesystem traversal, no AST or git needed) and produces zero findings on properly packaged code.

**Edge Case -- Top-Level Boundary:** Tomás notices that `docvet coverage` does not flag `src/myproject/__init__.py` as missing when it already exists, nor does it walk above `src/` (the configured `src-root`) looking for more `__init__.py` files. The check respects the package boundary: it walks from each file's parent up to `src-root`, not beyond.

### Journey 10: The Rendering Surprise (Griffe Compatibility Check)

**Persona:** Lina, a developer on a team that publishes API documentation with mkdocs-material + mkdocstrings. She writes thorough Google-style docstrings and runs `docvet check --staged` before every commit.

**Opening Scene:** Lina adds a new `fetch_records()` function to the data access layer. The function accepts three parameters and returns a list of records. She writes a clean docstring with `Args:`, `Returns:`, and `Raises:` sections. The enrichment check passes — all sections are present. Freshness passes — the docstring is brand new alongside the code. Coverage passes — all `__init__.py` files are in place. She commits and pushes.

**Rising Action:** The next morning, the tech lead notices the API docs site looks off. The `fetch_records()` page shows `Args:` parameters without type annotations — the rendered docs display bare parameter names with no types, making them harder to scan. The docstring read `limit: Maximum number of records to return` instead of `limit (int): Maximum number of records to return`. The mkdocs build log had a griffe warning: `No type or annotation for parameter 'limit'`. Nobody noticed because the build succeeded — griffe warnings don't fail builds by default.

**Climax:** The tech lead adds `docvet griffe` to the team's pre-commit workflow. Lina re-runs `docvet griffe --all` on her branch. The terminal shows:

```
src/data/access.py:42: griffe-missing-type Function 'fetch_records' parameter 'limit' has no type annotation in docstring or signature
src/data/access.py:42: griffe-missing-type Function 'fetch_records' parameter 'offset' has no type annotation in docstring or signature
src/data/access.py:42: griffe-missing-type Function 'fetch_records' parameter 'query' has no type annotation in docstring or signature
```

Three findings, all category `recommended`. She updates the `Args:` section to include types: `limit (int): Maximum number of records to return.` She re-runs — zero findings. The rendered docs now display clean, typed parameter lists.

**Resolution:** The team keeps `docvet griffe` in `warn-on`. The combination of enrichment (are all sections present?), freshness (are they up to date?), griffe (will they render correctly?), and coverage (will they be visible?) gives complete documentation quality coverage — from content to deployment.

**Edge Case -- Unknown Parameter:** A week later, a colleague refactors `fetch_records()` to remove the `query` parameter but forgets to update the docstring's `Args:` section. The enrichment check doesn't catch this (it detects missing sections, not extra entries). But the griffe check does:

```
src/data/access.py:42: griffe-unknown-param Function 'fetch_records' documents parameter 'query' which does not exist in the function signature
```

Category `required` — the docstring actively misleads callers about the function's interface. The colleague removes the stale `query` entry and commits clean.

**Edge Case -- Griffe Not Installed:** A contributor working on a minimal dev setup without the griffe extra (`pip install docvet` instead of `pip install docvet[griffe]`) runs `docvet check`. The griffe check silently skips — no error, no finding, zero noise. Enrichment, freshness, and coverage still run normally. The contributor sees a note in verbose output: `griffe: skipped (griffe not installed)`.

### Journey Requirements Traceability

All 10 enrichment rule identifiers are demonstrated across Journeys 1-5 and 8. Journeys 1-5 cover 6 rules: `missing-raises` (Journey 1), `missing-attributes` (Journey 2), `missing-typed-attributes` (Journey 4), `missing-yields` (Journey 3), `missing-warns` and `missing-examples` (Journeys 4-5). Journey 8 covers the remaining 4: `missing-receives`, `missing-other-parameters`, `missing-cross-references`, and `prefer-fenced-code-blocks`. All 5 freshness rule identifiers are demonstrated: Journey 6 covers diff mode (`stale-signature` HIGH/required, `stale-body` MEDIUM/recommended, `stale-import` LOW/recommended as edge case paragraph) and Journey 7 covers drift mode (`stale-drift` and `stale-age`, both recommended). All 3 griffe rule identifiers are demonstrated in Journey 10: `griffe-missing-type` (recommended, main scenario), `griffe-unknown-param` (required, edge case), and `griffe-format-warning` (recommended, implied by griffe's formatting checks). The 1 coverage rule identifier (`missing-init`) is demonstrated in Journey 9. All 19 rule identifiers (10 enrichment + 5 freshness + 3 griffe + 1 coverage) have journey coverage. CLI/reporting layer dependencies (output formatting, summary line, exit codes, discovery modes) are out of check module scope but required for full journey completion in the same release.

## Enrichment Module Specification

### Project-Type Overview

docvet is a non-interactive, scriptable CLI tool in the tradition of ruff, ty, and interrogate. The enrichment check (`check_enrichment`) is a pure function that produces a flat list of `Finding` objects -- it has no awareness of the CLI layer, output formatting, or exit codes. The CLI layer is the consumer: it calls the check, formats findings for terminal output, and maps `fail-on` / `warn-on` configuration to exit codes.

### Integration Contract

**Public API:**

```python
def check_enrichment(
    source: str,
    tree: ast.Module,
    config: EnrichmentConfig,
    file_path: str,
) -> list[Finding]:
```

- **Pure function**: no I/O, no side effects, deterministic output
- **Caller provides AST**: the function does not call `ast.parse()` -- the caller handles `SyntaxError`
- **`file_path` enables context-aware detection**: needed for `__init__.py` module rules and for populating `Finding.file` -- the function owns full `Finding` construction
- **Config toggles respected**: disabled rules produce zero findings, period
- **Returns empty list on clean code**: not `None`, not a sentinel
- **One finding per symbol per rule**: if multiple detection branches match the same symbol for the same rule (e.g., a `@dataclass` that also has `__init__` self-assignments), only one `missing-attributes` finding is emitted

**`Finding` dataclass (lives in `src/docvet/checks/__init__.py`):**

```python
@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    symbol: str
    rule: str        # kebab-case stable identifier
    message: str
    category: Literal["required", "recommended"]
```

**Import contract:**

- `checks/__init__.py` exports `Finding` only -- it is a shared types module, not a barrel file
- Each check module exports its own public function: `checks.enrichment.check_enrichment`, `checks.freshness.check_freshness`, etc.
- The CLI imports `Finding` from `docvet.checks` and `check_enrichment` from `docvet.checks.enrichment` independently
- No cross-imports between check modules -- each check depends only on `checks.Finding` and `ast_utils`

### Rule Taxonomy

The vision doc lists 14 detection scenarios. After consolidation, these map to **10 distinct rule identifiers**. The difference: multiple scenarios can emit the same rule ID when they detect the same kind of omission in different contexts.

| Rule Identifier | Category | Config Toggle | Detection Scenarios |
|----------------|----------|---------------|-------------------|
| `missing-raises` | required | `require-raises` | Functions/methods with `raise` statements lacking `Raises:` section |
| `missing-yields` | required | `require-yields` | Generator functions with `yield` lacking `Yields:` section |
| `missing-receives` | required | `require-receives` | Generators using `value = yield` lacking `Receives:` section |
| `missing-warns` | required | `require-warns` | Functions calling `warnings.warn()` lacking `Warns:` section |
| `missing-other-parameters` | recommended | `require-other-parameters` | Functions with `**kwargs` lacking `Other Parameters:` section |
| `missing-attributes` | required | `require-attributes` | Classes with `__init__` self-assignments, dataclasses, NamedTuples, TypedDicts, `__init__.py` modules -- all lacking `Attributes:` section |
| `missing-typed-attributes` | recommended | `require-typed-attributes` | `Attributes:` sections without `name (type): desc` format |
| `missing-examples` | recommended | `require-examples` (list) | Public symbols in the `require-examples` list (class, protocol, dataclass, enum) lacking `Examples:` section; `__init__.py` modules lacking `Examples:` |
| `missing-cross-references` | recommended | `require-cross-references` | `See Also:` sections without cross-reference syntax; `__init__.py` modules lacking `See Also:` section |
| `prefer-fenced-code-blocks` | recommended | `prefer-fenced-code-blocks` | `Examples:` sections using `>>>` doctest format instead of fenced code blocks |

**Key consolidations:**

- **`missing-attributes` covers all class-like constructs**: plain classes (via `__init__` self-assignments), dataclasses, NamedTuples, TypedDicts, and `__init__.py` module-level exports. One rule, one identifier, one toggle -- the detection logic branches internally by construct type. This is the most complex rule with 5 detection branches, but the output is always one finding per symbol.
- **`__init__.py` module rules are not separate rules**: they are existing rules (`missing-attributes`, `missing-examples`, `missing-cross-references`) applied to module-level symbols. No new rule identifiers needed.
- **`missing-examples` is controlled by a list, not a boolean**: `require-examples = ["class", "protocol", "dataclass", "enum"]` specifies which symbol types trigger the rule. Empty list disables it entirely.

### Config Schema Update

The existing `EnrichmentConfig` has 9 boolean toggles + 1 list. The rule taxonomy reveals one config gap:

**New toggle needed:** `require-attributes: bool = True`

This controls the `missing-attributes` rule. Without it, there's no way to disable Attributes checking for teams that don't document class fields in docstrings (preferring type annotations alone). Since `missing-attributes` is a `required` category rule, the toggle defaults to `True`. This is a backward-compatible addition -- new field with a default value, no existing code breaks.

**Updated `EnrichmentConfig` (10 booleans + 1 list):**

```toml
[tool.docvet.enrichment]
require-raises = true              # missing-raises
require-yields = true              # missing-yields
require-receives = true            # missing-receives
require-warns = true               # missing-warns
require-other-parameters = true    # missing-other-parameters
require-attributes = true          # missing-attributes (NEW)
require-typed-attributes = true    # missing-typed-attributes
require-cross-references = true    # missing-cross-references
prefer-fenced-code-blocks = true   # prefer-fenced-code-blocks
require-examples = ["class", "protocol", "dataclass", "enum"]  # missing-examples
```

Every rule now has a corresponding toggle. No always-on rules -- every team can customize to their needs.

### Scripting & CI Support

- **Exit codes**: `0` = no findings (or all findings in `warn-on` checks), `1` = findings in `fail-on` checks. Controlled by top-level `fail-on` / `warn-on` lists, not by individual rules.
- **Output format**: `file:line: rule message` (one finding per line) -- greppable, parseable, familiar to ruff/ty users.
- **Summary line**: `N findings (X required, Y recommended)` -- printed after all findings when count > 0. Part of the CLI/reporting layer, not the enrichment module.
- **Composability**: `docvet enrichment` runs only the enrichment check. `docvet check` runs all enabled checks. Each check produces `list[Finding]` independently -- no shared state between checks.

### Technical Guidance for Implementation

- **Section detection**: Google-style docstring section headers (`Args:`, `Returns:`, `Raises:`, etc.) detected via regex/string matching on the raw docstring text. No third-party parser needed.
- **AST infrastructure**: Reuses existing `ast_utils.Symbol` dataclass for symbol extraction. `Symbol.kind` distinguishes functions, classes, methods, and modules. `Symbol.docstring` provides the raw docstring text for section analysis.
- **`__init__.py` detection**: `file_path` parameter enables checking `file_path.endswith("__init__.py")`. When true, apply module-specific rules (`missing-attributes` for exports, `missing-examples`, `missing-cross-references`) to the module-level symbol.
- **Dataclass/NamedTuple/TypedDict detection**: AST decorator inspection for `@dataclass`, base class inspection for `NamedTuple`/`TypedDict`. These are well-defined AST patterns.
- **Deduplication**: `missing-attributes` detection branches (plain class, dataclass, NamedTuple, TypedDict, module) are checked in priority order. First match emits the finding; subsequent branches for the same symbol are skipped.
- **No new runtime dependencies**: stdlib `ast` + existing `ast_utils` + `re` for section header matching.

## Freshness Module Specification

### Project-Type Overview

The freshness check detects stale docstrings -- code that changed without a corresponding docstring update. It operates as a pair of pure functions (`check_freshness_diff` and `check_freshness_drift`) that take pre-parsed git output as strings, not raw git access. Both return `list[Finding]` using the same shared type as enrichment. The CLI layer handles all git subprocess calls and passes the output strings to the check functions -- the freshness module performs no I/O.

Diff mode is the primary workflow. It runs during pre-commit and CI, analyzing `git diff` output to flag symbols where code lines changed but docstring lines did not. Drift mode is for periodic audits. It analyzes `git blame --line-porcelain` output to flag docstrings that have fallen behind their code by configurable time thresholds. Teams use diff mode daily and drift mode quarterly.

### Integration Contract

**Public API:**

```python
def check_freshness_diff(
    file_path: str,
    diff_output: str,
    tree: ast.Module,
) -> list[Finding]:
    """Check for stale docstrings using git diff output."""

def check_freshness_drift(
    file_path: str,
    blame_output: str,
    tree: ast.Module,
    config: FreshnessConfig,
) -> list[Finding]:
    """Check for stale docstrings using git blame timestamps."""
```

**Key contract details:**

- **Two public functions, not one**: diff and drift have fundamentally different inputs (hunk ranges vs per-line timestamps), outputs (deterministic severity vs threshold-based), and usage patterns (every commit vs periodic sweep). A single function with a mode flag would obscure these differences.
- **No `source` parameter**: freshness does not parse docstring sections -- it only needs line-to-symbol mapping from the AST, not docstring text analysis.
- **Caller provides git output as strings**: `diff_output` is the raw output of `git diff` (or `git diff --cached`); `blame_output` is the raw output of `git blame --line-porcelain`. The functions parse these strings internally.
- **`check_freshness_diff` has no config parameter**: severity logic is deterministic based on what changed (signature vs body vs imports). No thresholds, no toggles.
- **`check_freshness_drift` takes `FreshnessConfig`**: drift detection requires `drift_threshold` (days between code and docstring edits) and `age_threshold` (days since docstring was last touched). The function should accept an optional `now` parameter (Unix timestamp) for testability — defaulting to `time.time()` when not provided. This makes drift mode deterministic in tests while remaining convenient in production.
- **`tree` provides symbol extraction**: both functions call `map_lines_to_symbols(tree)` from `ast_utils` to resolve changed lines to their enclosing symbols. The `Symbol.docstring_range`, `Symbol.signature_range`, and `Symbol.body_range` fields classify which part of a symbol was touched.
- **`file_path` is a string for `Finding.file` construction**: consistent with enrichment's contract.
- **Severity maps to `Finding.category`**: HIGH -> `"required"`, MEDIUM/LOW -> `"recommended"`. Diff mode severity is baked into the rule identifier (`stale-signature` is always required, `stale-body` and `stale-import` are always recommended). Drift mode findings are always `"recommended"`.
- **One finding per symbol per mode**: diff mode emits at most one finding per symbol, at the highest severity detected (signature change trumps body change trumps import change). Drift mode emits at most two findings per symbol (`stale-drift` and `stale-age` are independent checks).
- **Pure functions**: no I/O, no side effects, deterministic output. Empty `diff_output` or `blame_output` produces an empty list.
- **Returns empty list on clean code**: not `None`, not a sentinel.

**Import contract:**

- `checks.freshness` exports `check_freshness_diff` and `check_freshness_drift`
- Both functions import `Finding` from `docvet.checks` and `map_lines_to_symbols` from `docvet.ast_utils`
- No cross-imports between freshness and enrichment -- each depends only on `checks.Finding` and `ast_utils`

### Rule Taxonomy

5 rule identifiers: 3 for diff mode, 2 for drift mode. Each diff rule corresponds to a severity level. Drift rules are threshold-based and independent of each other.

| Rule Identifier | Category | Severity | Mode | Description |
|----------------|----------|----------|------|-------------|
| `stale-signature` | required | HIGH | diff | Function/method signature changed (parameters added, removed, renamed, retyped, or reordered), docstring not updated |
| `stale-body` | recommended | MEDIUM | diff | Function/method/class body changed (logic, control flow, return statements), docstring not updated |
| `stale-import` | recommended | LOW | diff | Only imports, formatting, or whitespace changed near symbol -- docstring likely still accurate |
| `stale-drift` | recommended | -- | drift | Code lines newer than docstring lines by more than `drift-threshold` days |
| `stale-age` | recommended | -- | drift | Docstring untouched for more than `age-threshold` days, regardless of code age |

**Key notes:**

- **Diff mode severity is deterministic and mutually exclusive per symbol**: the function classifies each changed line as signature, docstring, or body. If any signature line changed and no docstring line changed -> `stale-signature` (HIGH). Else if any body line changed and no docstring line changed -> `stale-body` (MEDIUM). Else if only import/formatting lines changed -> `stale-import` (LOW). Highest severity wins; one finding per symbol.
- **Docstring changes suppress findings**: if both code lines and docstring lines changed for a symbol, no finding is emitted -- the developer updated the docstring alongside the code.
- **Drift mode has no severity levels**: both drift rules are always `"recommended"`. Drift indicates potential staleness (time-based heuristic), not confirmed misleading content. A docstring untouched for 90 days may still be perfectly accurate.
- **`stale-drift` and `stale-age` are independent**: a single symbol can trigger both (code recently changed but docstring was already old) or either one alone.
- **`stale-age` is intentionally noisy on stable codebases**: a function written 91 days ago with a perfect, never-needs-updating docstring will still fire `stale-age`. This is a known trade-off — the rule flags docstrings that *may* need review, not docstrings that are *confirmed* stale. Teams on stable codebases should set a higher `age-threshold` or move freshness to `warn-on` to manage noise.
- **Category is baked into the rule definition**: `stale-signature` is always `"required"` because a signature change almost certainly invalidates the `Args:` documentation. The other four rules are always `"recommended"` because body/import/time-based changes may or may not affect docstring accuracy.

### Config Schema

`FreshnessConfig` exists in `config.py` with two fields. Both control drift mode only -- diff mode has no configurable thresholds.

```toml
[tool.docvet.freshness]
drift-threshold = 30   # days — code newer than docstring by this triggers stale-drift
age-threshold = 90     # days — docstring untouched for this long triggers stale-age
```

**What each threshold means:**

- **`drift-threshold`**: For each symbol, compare `max(code_line_timestamps)` vs `max(docstring_line_timestamps)`. If the code timestamp exceeds the docstring timestamp by more than `drift-threshold` days, emit `stale-drift`. Default 30 days balances signal (catch genuinely neglected docstrings) vs noise (ignore recent changes the developer hasn't gotten to yet).
- **`age-threshold`**: For each symbol, if `now - max(docstring_line_timestamps)` exceeds `age-threshold` days, emit `stale-age` regardless of code age. Default 90 days flags docstrings that haven't been reviewed in a quarter -- even if the code hasn't changed, the surrounding ecosystem may have shifted. Known trade-off: perfectly accurate docstrings on stable code will fire after the threshold. Teams on stable codebases may want `age-threshold = 180` or higher.

**Config design decisions:**

- Diff mode has no config toggles. Severity logic is deterministic: what changed dictates the rule and category. Adding per-rule disable toggles (e.g., `ignore-stale-import = true`) is a post-MVP candidate -- teams that find `stale-import` too noisy can move freshness to `warn-on` for now.
- Setting `drift-threshold = 0` or `age-threshold = 0` effectively makes that drift rule fire on every symbol with blame data -- not recommended but not prevented.
- Both thresholds are integers (days). Sub-day precision is unnecessary for periodic audit use cases.

### Scripting & CI Support

- **Output format**: `file:line: rule message` -- identical to enrichment. Example: `src/core/engine.py:42: stale-signature Function 'parse_config' signature changed but docstring not updated`
- **`docvet freshness`**: runs diff mode by default (matches the pre-commit workflow expectation).
- **`docvet freshness --mode drift`**: runs drift mode. Requires the working directory to be a git repository with committed history (blame needs commits).
- **`docvet check`**: runs freshness (diff mode) alongside enrichment and other enabled checks.
- **Exit codes**: governed by top-level `fail-on` / `warn-on` lists, not by individual freshness rules. Default config places freshness in `warn-on` (exit 0, advisory). Moving to `fail-on` makes `stale-signature` findings (category `"required"`) cause non-zero exit.
- **Severity in output**: conveyed via the rule identifier and category field in `Finding`, not via a separate severity column. `stale-signature` implies HIGH; `stale-body` implies MEDIUM; `stale-import` implies LOW. The output format does not expose severity directly -- the rule name is sufficient for filtering and triage.
- **Composability**: `docvet freshness` produces `list[Finding]` independently. `docvet check` aggregates findings from all checks. No shared mutable state between checks.

### Technical Guidance for Implementation

**Diff mode implementation:**

1. **Parse `git diff` output**: split on `@@ -a,b +c,d @@` hunk headers using regex. Extract the `+c,d` ranges -- these are the changed line numbers in the current file version. Ignore removed-only hunks (lines that existed in the old version but not the new).
2. **Map changed lines to symbols**: call `map_lines_to_symbols(tree)` to get a `dict[int, Symbol]`. For each changed line number, look up the containing symbol.
3. **Classify changed lines per symbol**: for each symbol that has changed lines, partition them using `Symbol.signature_range`, `Symbol.docstring_range`, and `Symbol.body_range`. Lines outside all three ranges (e.g., decorator lines, inter-symbol whitespace) are classified as formatting/import changes.
4. **Apply severity logic**: if docstring lines changed for a symbol -> skip (docstring was updated). Otherwise: signature lines changed -> `stale-signature` (HIGH/required). Body lines changed -> `stale-body` (MEDIUM/recommended). Only formatting/import lines -> `stale-import` (LOW/recommended). Highest severity wins per symbol.
5. **Emit findings**: one `Finding` per affected symbol, using `Symbol.line` for `Finding.line` and `Symbol.name` for `Finding.symbol`.

**Edge cases (diff mode):**

- **New files** (entire file is added): all lines are "changed" but no prior docstring existed to become stale. Skip -- no findings. Detection: diff output shows `--- /dev/null`.
- **Deleted symbols** (function removed): not in the AST -> `map_lines_to_symbols` won't map those lines. Naturally skipped.
- **Moved/renamed symbols (within file)**: treated as delete-plus-add. The old location is a deletion (skipped). The new location may produce a `stale-body` finding if the docstring wasn't updated. Cross-file moves are out of scope — freshness operates per-file on the diff for each file independently, without `--find-renames`.
- **Symbols with no docstring**: `Symbol.docstring_range` is `None`. No docstring to be stale -> skip. Presence checking is interrogate's job.
- **Multi-line signature changes**: a signature spanning lines 10-15 where only line 12 changed still counts as a signature change -> `stale-signature`.
- **Empty diff output**: return empty list immediately.

**Drift mode implementation:**

1. **Parse `git blame --line-porcelain` output**: extract per-line `author-time` (Unix timestamp) values. Each blame entry starts with a 40-char SHA line, followed by header fields including `author-time`, and ends with a tab-prefixed content line. Build a `dict[int, int]` mapping line number to timestamp.
2. **Group timestamps by symbol**: using `map_lines_to_symbols(tree)`, partition the line-to-timestamp mapping into per-symbol groups. For each symbol, separate timestamps into code timestamps and docstring timestamps using `Symbol.docstring_range`.
3. **Compute `stale-drift`**: `code_max = max(code_timestamps)`, `docstring_max = max(docstring_timestamps)`. If `code_max - docstring_max > drift_threshold * 86400` (seconds): emit `stale-drift`. Skip symbols where either group is empty.
4. **Compute `stale-age`**: `now = current UTC timestamp`. If `now - docstring_max > age_threshold * 86400`: emit `stale-age`. Skip symbols with no docstring timestamps.
5. **Emit findings**: up to two findings per symbol (one for each drift rule that triggers). Both use category `"recommended"`.

**Edge cases (drift mode):**

- **Uncommitted files** (no blame data): empty `blame_output` -> return empty list.
- **Symbols with no docstring**: no docstring timestamps -> skip both drift rules.
- **Symbols with only a docstring** (no code body, e.g., a stub): no code timestamps -> `stale-drift` cannot trigger (no code to be newer). `stale-age` can still trigger based on docstring age alone.
- **Boundary timestamps**: use strict greater-than comparison (`>`, not `>=`) for threshold checks to avoid false positives at exactly the threshold boundary.

**Dependencies:**

- No new runtime dependencies: stdlib `ast`, `re`, `time` (for drift mode `time.time()`), existing `ast_utils`
- Reuses `Finding` from `checks/__init__.py`
- Reuses `map_lines_to_symbols` and `Symbol` from `ast_utils` -- `Symbol.signature_range`, `Symbol.docstring_range`, `Symbol.body_range` provide the line classification infrastructure
- No cross-imports between freshness and enrichment modules
- `FreshnessConfig` imported from `docvet.config` (already exists with `drift_threshold` and `age_threshold` fields)

## Coverage Module Specification

### Project-Type Overview

The coverage check detects Python files that are invisible to mkdocstrings — they exist in the source tree but won't appear in generated API documentation because a parent directory lacks `__init__.py`. This is the simplest of the four checks: pure filesystem traversal with no AST parsing, no git integration, and no per-check configuration. The check mirrors Python's import resolution logic: if the interpreter can't import a module because the package hierarchy is broken, mkdocstrings can't document it either.

### Integration Contract

**Public API:**

```python
def check_coverage(
    src_root: Path,
    files: list[Path],
) -> list[Finding]:
    """Detect Python files invisible to mkdocstrings due to missing __init__.py."""
```

- **Pure function**: no I/O beyond filesystem stat calls (`Path.exists()`), deterministic output for a given filesystem state
- **`src_root` defines the package boundary**: the check walks upward from each file's parent directory, stopping at `src_root`. Directories at or above `src_root` are not checked — `src_root` itself is not expected to have `__init__.py`. Default: project root (git root or CWD) when `src-root` is not configured in `pyproject.toml`. If a file is not under `src_root` (e.g., test files outside the source tree), skip it — return no findings for that file
- **`files` is the discovery output**: the same `list[Path]` that enrichment and freshness receive from the CLI discovery pipeline
- **No config parameter**: coverage has no toggles or thresholds — it either finds a missing `__init__.py` or it doesn't
- **Deduplication**: each missing `__init__.py` directory is reported once, even if multiple files are affected by the same gap. The finding references one representative affected file
- **Returns empty list on fully packaged code**: not `None`, not a sentinel
- **Skips non-package files**: files directly under `src_root` (not in a subdirectory) are not checked — they are top-level modules, not packages

**Import contract:**

- `checks.coverage` exports `check_coverage`
- Imports `Finding` from `docvet.checks` and `Path` from `pathlib`
- No cross-imports between coverage and enrichment or freshness — depends only on `checks.Finding`

### Rule Taxonomy

1 rule identifier. The simplest taxonomy in docvet.

| Rule Identifier | Category | Description |
|----------------|----------|-------------|
| `missing-init` | required | A parent directory between the Python file and `src_root` lacks `__init__.py`, making the file invisible to mkdocstrings |

**Key notes:**

- **Category is always `required`**: a missing `__init__.py` is a definitive visibility gap, not a style preference. The file is genuinely invisible to mkdocstrings — there is no ambiguity.
- **One finding per missing directory, not per affected file**: if `pkg/sub/` lacks `__init__.py` and contains 5 Python files, the check emits one finding referencing the directory and one representative file, not 5 identical findings. The finding message includes the affected file count for triage (e.g., `Directory 'sub' is missing __init__.py — 5 files invisible to mkdocstrings`).
- **`__init__.py` can be empty**: the check verifies existence only, not content. An empty `__init__.py` satisfies the requirement.

### Scripting & CI Support

- **Output format**: `file:line: rule message` — identical to enrichment and freshness. Example: `src/myproject/analytics/tracker.py:1: missing-init Directory 'analytics' is missing __init__.py — file invisible to mkdocstrings`
- **`docvet coverage`**: runs the coverage check standalone.
- **`docvet check`**: runs coverage alongside enrichment, freshness, and griffe.
- **Exit codes**: governed by top-level `fail-on` / `warn-on` lists. Default config places coverage in `warn-on`. Moving to `fail-on` makes `missing-init` findings cause non-zero exit.
- **Line number**: always `1` (module level) — the finding applies to the file as a whole, not a specific line.
- **Symbol name**: `"<module>"` — consistent with the `ast_utils.Symbol.name` convention for module-level symbols used by enrichment and freshness. Maintains uniform `Finding.symbol` semantics across all checks.
- **Composability**: `docvet coverage` produces `list[Finding]` independently. `docvet check` aggregates findings from all checks.

### Technical Guidance for Implementation

1. **Collect directories to check**: for each file in `files`, compute all parent directories between the file's parent and `src_root` (exclusive). Use `Path.relative_to(src_root)` to get the relative path, then iterate over its parent chain.
2. **Check for `__init__.py`**: for each directory in the chain, check if `directory / "__init__.py"` exists. Collect directories where it does not.
3. **Deduplicate**: use a `set[Path]` of already-reported directories. Each missing directory is reported once with one representative affected file.
4. **Emit findings**: one `Finding` per missing directory. `file` = path to an affected `.py` file, `line` = 1, `symbol` = `"<module>"`, `rule` = `"missing-init"`, `category` = `"required"`. **Representative file selection**: use the lexicographically first affected file (sorted by path string) for deterministic output.

**Edge cases:**

- **Top-level modules** (files directly under `src_root`): not in a package, no `__init__.py` needed. Skip.
- **Namespace packages (PEP 420)**: out of MVP scope. Namespace packages intentionally omit `__init__.py` but are rare in mkdocstrings workflows. **Known limitation**: namespace package directories will produce false-positive `missing-init` findings. **Workaround**: add namespace package directories to the top-level `exclude` patterns in `[tool.docvet]`, which the discovery pipeline applies before files reach `check_coverage`. A future config toggle could allow excluding specific directories from coverage checking without excluding them from other checks.
- **Excluded directories**: files in excluded directories (from top-level config) are already filtered out by the discovery pipeline before reaching `check_coverage`. No additional exclusion logic needed.
- **Non-Python files**: discovery pipeline returns only `.py` files. No filtering needed in the check.
- **Symlinks**: discovery pipeline skips symlinks. No special handling needed.
- **Empty `__init__.py`**: satisfies the check. Content is irrelevant — existence is the requirement.

**Dependencies:**

- No new runtime dependencies: stdlib `pathlib` only
- Reuses `Finding` from `checks/__init__.py`
- No AST imports, no git imports, no `ast_utils` dependency
- No cross-imports between coverage and any other check module
- No `CoverageConfig` needed — zero configuration parameters

## Griffe Module Specification

### Project-Type Overview

The griffe compatibility check detects docstrings that produce warnings during mkdocs rendering — issues invisible to AST analysis alone. It operates by loading the package via the griffe library (the same parser used by mkdocstrings during `mkdocs build`) and capturing parser warnings. The check function returns `list[Finding]` using the same shared type as enrichment, freshness, and coverage. Unlike the other three checks, griffe is an **optional dependency** — the check gracefully skips when griffe is not installed, producing zero findings and no errors.

Griffe operates at the **package level** (loading entire packages via `griffe.load()`), not per-file like enrichment or freshness. The check loads the package from `src_root`, captures all parser warnings, filters them to the set of discovered files, and maps each warning to a `Finding`. This architectural difference from other checks is inherent to griffe's design — it needs package context (imports, class hierarchies, type aliases) to accurately validate docstrings against their parent symbols.

### Integration Contract

**Public API:**

```python
def check_griffe_compat(
    src_root: Path,
    files: Sequence[Path],
) -> list[Finding]:
    """Check docstrings for griffe parser warnings."""
```

- **Package-level operation**: uses `GriffeLoader(search_paths=[str(src_root)])` to load packages discovered under `src_root`, not per-file parsing. The loader resolves packages by walking the search path — no explicit package name derivation needed. This matches how mkdocstrings processes packages during `mkdocs build`
- **`src_root` defines the search path**: the same `src-root` used by coverage. The CLI resolves this from `[tool.docvet]` config or defaults to the project root. If `src_root` contains multiple top-level packages, all are loaded
- **`files` filters the output**: griffe loads the entire package but the function only emits findings for files in this list. This ensures discovery mode filtering (`--staged`, `--all`, `--files`) applies consistently
- **Optional dependency — graceful skip**: if griffe is not importable, returns an empty list immediately. No exception, no error finding. The CLI layer checks griffe availability *before* calling the function (via `importlib.util.find_spec("griffe")`) and handles the "not installed" messaging — emitting a verbose-mode note and, if griffe is in `fail-on`, a stderr warning that the check was skipped due to missing dependency. This keeps the pure function's contract clean and puts skip logic in the CLI where it belongs
- **Warning capture via Python logging**: attaches a handler to `logging.getLogger("griffe")` during package loading, collects warning-level log records, detaches the handler after loading completes. No global logging state is modified permanently
- **Pure function with I/O caveat**: the function performs filesystem I/O (griffe reads source files during loading) but has no side effects beyond that — no file writes, no network calls, deterministic output for a given filesystem state and griffe version
- **Returns empty list on clean code**: not `None`, not a sentinel
- **One finding per warning, multiple findings per symbol**: each griffe parser warning maps to exactly one `Finding`. A function with 3 untyped parameters produces 3 separate `griffe-missing-type` findings — one per parameter. This is intentionally different from enrichment's one-per-symbol-per-rule deduplication because each griffe warning identifies a specific, individually-fixable issue (a specific parameter, a specific line)

**`Finding` field mapping from griffe warnings:**

| Finding field | Source |
|---|---|
| `file` | Extracted from griffe warning message (format: `{filepath}:{line}: {message}`) |
| `line` | Extracted from griffe warning message line number |
| `symbol` | The griffe object's name (`Function.name`, `Class.name`, etc.) that owns the docstring |
| `rule` | Mapped from warning message pattern (see Rule Taxonomy) |
| `message` | Griffe's original warning text, optionally prefixed with symbol context |
| `category` | Determined by rule (see Rule Taxonomy) |

**Import contract:**

- `checks.griffe_compat` exports `check_griffe_compat`
- Conditional import: `try: import griffe except ImportError: griffe = None`
- Imports `Finding` from `docvet.checks` and `Path` from `pathlib`
- No cross-imports between griffe_compat and enrichment, freshness, or coverage — depends only on `checks.Finding`

### Rule Taxonomy

3 rule identifiers, mapped from griffe's warning message patterns. Each griffe warning string is classified into one of these rules via pattern matching.

| Rule Identifier | Category | Griffe Warning Pattern | Description |
|---|---|---|---|
| `griffe-missing-type` | recommended | `"No type or annotation for parameter '{name}'"` | Parameter in Args/Returns/Yields lacks a type annotation in both the docstring and the function signature |
| `griffe-unknown-param` | required | `"Parameter '{name}' does not appear in the function signature"` | Docstring documents a parameter that does not exist in the function signature — actively misleading |
| `griffe-format-warning` | recommended | All other griffe warnings (indentation, malformed entries, missing blank lines, skipped sections) | Formatting issues that degrade rendered documentation quality |

**Key notes:**

- **`griffe-unknown-param` is `required`**: a docstring that references a nonexistent parameter is actively misleading — callers may pass the documented name and get a `TypeError`. This is the griffe equivalent of enrichment's `missing-raises` severity level.
- **`griffe-missing-type` is `recommended`**: missing type annotations degrade rendering quality (mkdocs shows bare parameter names without types) but the documentation is not wrong — it's incomplete. Teams that rely on type annotations in signatures rather than docstrings may find these advisory.
- **`griffe-format-warning` is a catch-all for formatting issues**: includes indentation warnings (`"Confusing indentation for continuation line"`), malformed entries (`"Failed to get 'name: description' pair"`), missing blank lines (`"Missing blank line above {kind}"`), and skipped sections (`"Possible {kind} skipped, reasons: {reasons}"`). These affect rendering fidelity but do not misrepresent the API. Growth candidate: split section-detection warnings into a separate `griffe-skipped-section` rule if users need finer-grained filtering.
- **One finding per warning, not one per symbol**: griffe can produce multiple warnings for the same symbol (e.g., 3 parameters all missing types → 3 findings). This differs from enrichment (one finding per symbol per rule) because each griffe warning identifies a specific, individually-fixable issue.
- **Warning classification is pattern-based**: the function matches griffe's warning message strings against known patterns. Unrecognized warnings default to `griffe-format-warning`. This design is resilient to minor griffe version changes in message wording but may need updates for major griffe releases.
- **Griffe parser options**: the check uses griffe's default parser settings (`warn_unknown_params=True`, `warn_missing_types=True`, `warnings=True`). These match docvet's goals and are not user-configurable in the initial implementation.

### Config Schema

No `GriffeConfig` needed — zero configuration parameters. The griffe check uses griffe's default parser settings, which align with docvet's goals (warn on missing types and unknown parameters). The check's behavior is controlled entirely by griffe's built-in warning logic.

**What is not configurable (and why):**

- **Parser options**: griffe's `warn_unknown_params` and `warn_missing_types` default to `True`, matching docvet's intent. Exposing these as config toggles is a growth candidate if teams need to suppress specific warning types.
- **Per-rule disable toggles**: unlike enrichment's 10 boolean toggles, griffe's 3 rules are not individually toggleable. Teams that find specific griffe rules too noisy can move griffe to `warn-on` (advisory exit code) via the top-level `[tool.docvet]` config. Per-rule toggles are a growth candidate.
- **Docstring style**: the check assumes Google-style docstrings, consistent with docvet's overall design. Griffe supports Numpy and Sphinx styles, but docvet does not expose this option.

### Scripting & CI Support

- **Output format**: `file:line: rule message` — identical to enrichment, freshness, and coverage. Example: `src/data/access.py:42: griffe-missing-type Function 'fetch_records' parameter 'limit' has no type annotation in docstring or signature`
- **`docvet griffe`**: runs the griffe compatibility check standalone. Silently skips if griffe is not installed (exit 0, no output).
- **`docvet check`**: runs griffe alongside enrichment, freshness, and coverage. Griffe check silently skips if not installed — other checks run normally.
- **Exit codes**: governed by top-level `fail-on` / `warn-on` lists. Default config places griffe in `warn-on` (exit 0, advisory). Moving to `fail-on` makes `griffe-unknown-param` findings (category `"required"`) cause non-zero exit.
- **Optional dependency**: `pip install docvet[griffe]` installs the griffe extra. Without it, the check is a no-op. CI pipelines that want griffe checking must install the extra explicitly.
- **Composability**: `docvet griffe` produces `list[Finding]` independently. `docvet check` aggregates findings from all checks. No shared mutable state between checks.

### Technical Guidance for Implementation

1. **Conditional import**: at module level, `try: import griffe except ImportError: griffe = None`. Check `if griffe is None: return []` at function entry. Use `TYPE_CHECKING` for type hints to avoid runtime import issues.
2. **Load package via griffe**: use `griffe.GriffeLoader(search_paths=[str(src_root)])` to create a loader, then `loader.load(package_name)` where `package_name` is derived from the directory name under `src_root`. The loader caches directories and resolves aliases efficiently.
3. **Capture warnings via logging handler**: attach a custom `logging.Handler` subclass to `logging.getLogger("griffe")` before loading, collect `WARNING`-level records, detach after loading completes. Use a context manager or try/finally to ensure cleanup.
4. **Parse warning messages**: each griffe warning is a formatted string `"{filepath}:{line}: {message}"`. Extract `filepath`, `line`, and `message` via string splitting or regex. Match the `message` against known patterns to determine the rule identifier.
5. **Filter to discovered files**: only emit findings where the extracted `filepath` is in the `files` set (after path normalization). This ensures `--staged`, `--all`, and `--files` discovery modes work correctly.
6. **Map to Finding objects**: construct `Finding(file=filepath, line=line, symbol=symbol_name, rule=rule_id, message=message, category=category)`. The `symbol_name` can be extracted from griffe's warning context or from the message text.

**Edge cases:**

- **Griffe not installed**: return empty list immediately. No exception, no sentinel finding.
- **Empty file list**: return empty list (no files to check).
- **Package not loadable by griffe**: if `griffe.load()` raises an exception (e.g., syntax errors in source files), catch the exception, log a debug message, and return an empty list. Do not crash. Syntax error detection is not griffe's job — the user's editor and CI will catch those.
- **Griffe version differences**: warning message format may change between griffe versions. Use defensive pattern matching (substring checks rather than exact string equality) and classify unrecognized warnings as `griffe-format-warning`.
- **Non-Google docstrings in the project**: griffe parses with the configured style (Google). Non-Google docstrings will produce many irrelevant warnings. This is a known limitation — docvet assumes Google-style throughout.
- **Files outside `src_root`**: griffe loads from `src_root`, so files outside it won't be in the loaded package. These are naturally skipped — no special handling needed.

**Dependencies:**

- **Required**: `griffe` (optional dependency, installed via `pip install docvet[griffe]`)
- **Stdlib**: `logging`, `pathlib`
- Reuses `Finding` from `checks/__init__.py`
- No AST imports, no git imports, no `ast_utils` dependency
- No cross-imports between griffe_compat and any other check module
- No `GriffeConfig` needed — zero configuration parameters

## Project Scoping & Phased Development

### Strategy & Philosophy

**Approach:** Problem-solving MVP per layer -- deliver each specific capability that fills an ecosystem gap. The scaffolding (CLI, config, discovery, AST helpers) is already implemented; each epic adds a real check module.

**Enrichment scope boundary — missing vs incomplete:** Enrichment rules detect **missing sections only**. A function that raises `ValueError` and `TypeError` but has no `Raises:` section at all triggers `missing-raises`. A function that has a `Raises:` section documenting `ValueError` but not `TypeError` does **not** trigger a finding -- that's an *incomplete* section, which is a Growth feature (analogous to how ruff D417 checks param completeness but docvet Layer 3 checks section presence). This boundary keeps detection logic simple and false-positive risk low.

**Freshness scope boundary — diff vs blame:** Diff mode detects **immediate staleness** from the current commit/staged changes. Drift mode detects **accumulated staleness** over time via git blame timestamps. Diff mode is fast and deterministic; drift mode is slower and threshold-based. Both are pure functions — the CLI handles all git subprocess calls.

### Enrichment MVP Feature Set (Phase 1 — Complete)

**Status:** Fully implemented (3 epics, 11 stories, 415 tests).

**Core User Journeys Enabled:** Journeys 1-5 and 8. The enrichment module enables all enrichment journeys. Journey 3 (CI exit codes) and Journey 5 (summary line) also depend on CLI/reporting layer behavior that exists as stubs -- full journey completion requires wiring those stubs, which is out of enrichment module scope but in the same release scope.

**Prerequisite Deliverables (ship before main enrichment PR):**

1. **Config update PR:** Add `require-attributes: bool = True` to `EnrichmentConfig`, update `_VALID_ENRICHMENT_KEYS`, update `_parse_enrichment` validation, update affected tests. Small, isolated change.
2. **`checks` package PR:** Create `src/docvet/checks/__init__.py` with `Finding` dataclass. Establishes the shared type contract for all future checks. `Finding` is a frozen API -- its 6-field shape (`file`, `line`, `symbol`, `rule`, `message`, `category`) must remain stable across checks.

**Main Deliverable:**

- `check_enrichment(source, tree, config, file_path) -> list[Finding]` pure function in `checks/enrichment.py`
- All 10 rule identifiers covering 14 detection scenarios (missing section detection only, not incomplete section detection)
- Full respect for all 11 config toggles (10 booleans + `require-examples` list)
- Google-style section header detection for: `Raises:`, `Yields:`, `Receives:`, `Warns:`, `Other Parameters:`, `Attributes:`, `Examples:`, `See Also:` (8 headers detected; `Args:` and `Returns:` recognized but not checked for absence -- that's ruff's territory)
- One finding per symbol per rule (deduplication guarantee)
- Zero findings on complete, well-documented code
- Comprehensive unit tests using source string fixtures (≥85% project-wide coverage; aim for ≥90% on `checks/enrichment.py` specifically)
- Tests against existing fixture files (`missing_raises.py`, `missing_yields.py`, `complete_module.py`)
- CLI wiring via existing `_run_enrichment` stub in `cli.py`

### Freshness Feature Set (Phase 2 — Complete)

**Status:** Fully implemented (2 epics, 6 stories). Diff mode and drift mode both operational with CLI wiring.

**Core User Journeys Enabled:** Journeys 6-7. Journey 6 demonstrates diff mode (stale-signature, stale-body, stale-import). Journey 7 demonstrates drift mode (stale-drift, stale-age).

**Existing infrastructure (already implemented):**

- `Finding` dataclass in `checks/__init__.py` (shared with enrichment)
- `FreshnessConfig` in `config.py` with `drift_threshold` and `age_threshold` fields
- `_run_freshness` CLI stub in `cli.py`
- `Symbol` dataclass in `ast_utils.py` with `line`, `end_line`, `docstring`, `name`, `kind` fields
- `get_documented_symbols(tree)` in `ast_utils.py` for symbol extraction

**Prerequisite deliverables (ship before main freshness PR):**

1. **`Symbol` dataclass extension PR:** Add `signature_range`, `body_range`, and `docstring_range` fields to the `Symbol` dataclass in `ast_utils.py`. These line-range tuples enable freshness line classification — partitioning changed lines into signature, docstring, and body regions per symbol. Update `get_documented_symbols()` to populate the new fields during AST traversal. Update affected unit tests. Small, isolated change.
2. **`map_lines_to_symbols` PR:** Add `map_lines_to_symbols(tree) -> dict[int, Symbol]` to `ast_utils.py`. Maps every source line number to its enclosing `Symbol` (or `None` for inter-symbol gaps). Required by both diff mode (hunk-to-symbol mapping) and drift mode (blame-line-to-symbol grouping). Unit tests with known source strings. Small, isolated change.

**Main Deliverables:**

- `check_freshness_diff(file_path, diff_output, tree) -> list[Finding]` pure function in `checks/freshness.py`
- `check_freshness_drift(file_path, blame_output, tree, config) -> list[Finding]` pure function in `checks/freshness.py`
- All 5 rule identifiers: `stale-signature` (HIGH/required), `stale-body` (MEDIUM/recommended), `stale-import` (LOW/recommended), `stale-drift` (recommended), `stale-age` (recommended)
- Deterministic severity-to-category mapping for diff mode
- Configurable thresholds for drift mode (default: 30 days drift, 90 days age)
- One finding per symbol per mode (deduplication -- highest severity wins for diff mode)
- Zero findings on code where all changed symbols have updated docstrings
- Unit tests with mocked git diff and blame output strings (≥85% project-wide coverage; aim for ≥90% on `checks/freshness.py`)
- Integration tests with real git repos (temp dirs with known commits) for end-to-end diff and drift detection
- Edge case tests: new files, deleted functions, moved code, empty diff/blame output
- CLI wiring via existing `_run_freshness` stub in `cli.py`

### Coverage Feature Set (Phase 3 — Complete)

**Status:** Fully implemented (1 epic, 2 stories, 557 tests).

**Core User Journeys Enabled:** Journey 9. The coverage module enables the invisible-module detection workflow.

**Main Deliverables:**

- `check_coverage(src_root, files) -> list[Finding]` pure function in `checks/coverage.py`
- 1 rule identifier: `missing-init` (category `required`)
- Parent directory hierarchy walking from each file up to `src_root`
- Deduplication: one finding per missing directory, not per affected file
- Zero findings on properly packaged code (all `__init__.py` present)
- Unit tests with `tmp_path` filesystem fixtures (≥85% project-wide coverage)
- Edge case tests: top-level modules, nested packages, empty `__init__.py`
- CLI wiring: `_run_coverage` in `cli.py`

### Griffe Feature Set (Next Epic)

**Status:** Not started. All prerequisites exist: `Finding` dataclass, `_run_griffe` CLI stub, discovery pipeline, `griffe` in `_VALID_CHECK_NAMES` and default `warn_on`, optional `griffe` dependency in `pyproject.toml`.

**Core User Journeys Enabled:** Journey 10. The griffe module enables the rendering compatibility detection workflow.

**Existing infrastructure (already implemented):**

- `Finding` dataclass in `checks/__init__.py` (shared with enrichment, freshness, and coverage)
- `_run_griffe` CLI stub in `cli.py`
- `griffe` CLI command with full discovery pipeline support (DIFF, STAGED, ALL, FILES modes)
- `griffe` registered in `_VALID_CHECK_NAMES` and default `warn_on` list in `DocvetConfig`
- Optional dependency: `griffe` extra in `pyproject.toml`
- File discovery via `discovery.py` (returns sorted absolute `.py` file paths)
- `src-root` resolution logic in `cli.py` (shared with coverage)

**Prerequisite deliverables:** None. All shared infrastructure already exists.

**Main Deliverables:**

- `check_griffe_compat(src_root, files) -> list[Finding]` function in `checks/griffe_compat.py`
- 3 rule identifiers: `griffe-missing-type` (recommended), `griffe-unknown-param` (required), `griffe-format-warning` (recommended)
- Package-level loading via `griffe.GriffeLoader` with warning capture via `logging.Handler`
- Warning-to-Finding mapping with pattern-based rule classification
- Graceful skip when griffe not installed (return empty list, no exception)
- Zero findings on well-documented code with typed Args and valid parameter names
- Unit tests with known-bad docstrings (≥85% project-wide coverage)
- Edge case tests: griffe not installed, empty file list, package load errors, unrecognized warnings
- CLI wiring: replace `_run_griffe` stub in `cli.py`

### Post-Epic Features

**Growth (sequencing TBD based on early adopter feedback):**

Enrichment growth:
- Inline suppression: `# docvet: ignore[missing-raises]`
- Incomplete section detection (e.g., `Raises:` section exists but doesn't cover all raised exceptions)
- `--fix` suggestions (auto-insert empty section skeletons)

Freshness growth:
- Hunk-level precision (show exactly which hunk changed, not just the symbol)
- Auto-fix suggestions for stale `Args:` sections after signature changes
- Per-rule disable toggles (e.g., `ignore-stale-import = true`)

Coverage growth:
- Namespace package support (PEP 420): config toggle to exclude specific directories from `missing-init` checking
- `__init__.py` content analysis: detect empty `__init__.py` that should re-export package symbols
- Auto-fix: create missing `__init__.py` files via `--fix` flag

Griffe growth:
- Per-rule disable toggles (e.g., `disable-griffe-missing-type = true`) via `[tool.docvet.griffe]`
- Griffe parser option passthrough (`warn_unknown_params`, `warn_missing_types`) for teams that want to customize warning behavior
- Numpy/Sphinx docstring style support (griffe supports all three styles natively)

Shared growth:
- JSON output format for CI integration pipelines
- Rule documentation URLs in findings (ruff pattern)
- Per-rule severity override in config
- SARIF output format
- Cross-check intelligence (enrichment + freshness + griffe + coverage combined findings)

**Vision:**

- Editor/LSP integration for real-time feedback
- GitHub Actions annotation format for PR inline comments

### Risk Mitigation Strategy

**Enrichment Technical Risks (mitigated -- implementation complete):**

- `missing-attributes` has 5 detection branches with deduplication -- mitigated by implementing and testing each branch independently before composition
- Section header regex accuracy -- mitigated by starting with strict matching (exact names, correct indentation) and relaxing based on user feedback
- `Finding` is a frozen API consumed by all future checks -- mitigated by shipping it as a prerequisite PR with deliberate review before enrichment logic builds on it

**Freshness Technical Risks:**

- Git diff parsing edge cases (binary files, renames, merge commits) -- mitigated by testing with real git repos and diverse diff outputs; skip non-Python content early
- Git blame performance on large repos -- mitigated by drift mode being explicitly positioned as periodic (not per-commit); the pure function is fast, git blame I/O is the bottleneck
- Platform-specific git output variations -- mitigated by targeting git 2.x unified diff format, which is stable across platforms
- `Symbol.signature_range` / `Symbol.body_range` accuracy for line classification -- mitigated by reusing battle-tested `ast_utils` infrastructure from enrichment

**Coverage Technical Risks:**

- `src_root` resolution accuracy -- mitigated by reusing the existing `src-root` config from `DocvetConfig` and falling back to project root; well-defined boundary
- Namespace package false positives -- mitigated by explicitly scoping to mkdocstrings workflows where `__init__.py` is always required; namespace package support deferred to growth
- Cross-platform path handling -- mitigated by using `pathlib.Path` throughout (consistent on Linux/macOS/Windows)

**Griffe Technical Risks:**

- Griffe API stability -- mitigated by using only stable public APIs (`griffe.load()`, `GriffeLoader`) and capturing warnings via standard Python logging rather than griffe internals. Defensive pattern matching on warning messages absorbs minor wording changes across griffe versions
- Warning message parsing fragility -- mitigated by classifying unrecognized warnings as `griffe-format-warning` (catch-all rule) rather than dropping them. New griffe warning types produce findings rather than silent misses
- Package loading failures -- mitigated by wrapping `griffe.load()` in exception handling; syntax errors or import failures in user code produce zero findings rather than crashes
- Optional dependency UX -- mitigated by graceful skip (return empty list) when griffe is not installed, with verbose-mode messaging to guide installation

**Market Risks:** Minimal -- no existing tool maps git diffs to AST symbols for stale docstring detection. No existing linter catches griffe parser warnings before `mkdocs build`. Novel capabilities in the Python ecosystem. Coverage check fills a gap where developers currently discover missing `__init__.py` only after mkdocs builds silently omit modules.

**Resource Risks:** Solo developer. Griffe check is moderate complexity — requires understanding griffe's API and logging system, but no AST analysis or git integration. All scaffolding and shared infrastructure already exist. Minimal risk.

## Functional Requirements

### Section Detection

- **FR1:** The system can detect functions and methods that contain `raise` statements but lack a `Raises:` section in their docstring
- **FR2:** The system can detect generator functions that contain `yield` expressions but lack a `Yields:` section in their docstring
- **FR3:** The system can detect generators that use the `value = yield` send pattern but lack a `Receives:` section in their docstring
- **FR4:** The system can detect functions that call `warnings.warn()` but lack a `Warns:` section in their docstring
- **FR5:** The system can detect functions with `**kwargs` parameters but lack an `Other Parameters:` section in their docstring
- **FR6:** The system can detect classes with `__init__` self-assignments that lack an `Attributes:` section in their docstring
- **FR7:** The system can detect dataclasses, NamedTuples, and TypedDicts with fields that lack an `Attributes:` section in their docstring
- **FR8:** The system can detect `__init__.py` modules that lack an `Attributes:` section documenting their exports
- **FR9:** The system can detect public symbols (configurable by type) that lack an `Examples:` section in their docstring
- **FR10:** The system can detect `__init__.py` modules that lack an `Examples:` section in their docstring
- **FR11:** The system can detect `Attributes:` sections that lack typed format (`name (type): description`)
- **FR12:** The system can detect `See Also:` sections where entries lack cross-reference syntax (backtick-wrapped module paths, Sphinx role syntax such as `:func:` or `:class:`, or markdown cross-reference link format `[text][ref]`)
- **FR13:** The system can detect `__init__.py` modules that lack a `See Also:` section in their docstring
- **FR14:** The system can detect `Examples:` sections that use `>>>` doctest format instead of fenced code blocks
- **FR15:** The system can recognize `Args:` and `Returns:` section headers for docstring parsing context without checking for their absence

### Finding Production

- **FR16:** The system can produce a structured finding for each detected issue, carrying file path, line number, symbol name, rule identifier, human-readable message, and category
- **FR17:** The system can categorize each finding as `required` (misleading omission) or `recommended` (improvement opportunity) based on the rule definition
- **FR18:** The system can produce at most one finding per symbol per rule, even when multiple detection branches match the same symbol
- **FR19:** The system can produce zero findings when analyzing well-documented code with complete docstrings
- **FR20:** The system can produce zero findings for symbols that have no docstring
- **FR21:** The system can produce findings only for missing sections, not for sections that exist but are incomplete
- **FR22:** The system can provide Finding as an immutable (frozen) dataclass that cannot be modified after creation

### Rule Management

- **FR23:** The system can identify each finding with a stable, human-readable kebab-case rule identifier (e.g., `missing-raises`, `missing-yields`)
- **FR24:** A developer can reference rule identifiers in configuration, output filtering, and issue tracking
- **FR25:** The system can map 14 detection scenarios to 10 distinct rule identifiers, applying the same rule ID across related detection contexts

### Configuration

- **FR26:** A developer can enable or disable each of the 10 rules independently via boolean toggles in `[tool.docvet.enrichment]`
- **FR27:** A developer can configure which symbol types trigger the `missing-examples` rule via a list of type names (class, protocol, dataclass, enum)
- **FR28:** The system can validate `require-examples` entries against known symbol types, rejecting unrecognized entries at config load time
- **FR29:** A developer can disable all enrichment findings by setting `require-examples = []` and all boolean toggles to `false`
- **FR30:** The system can apply defaults (all rules enabled, `require-examples = ["class", "protocol", "dataclass", "enum"]`) when no enrichment configuration is provided
- **FR31:** The system can recognize 8 Google-style section headers (`Raises:`, `Yields:`, `Receives:`, `Warns:`, `Other Parameters:`, `Attributes:`, `Examples:`, `See Also:`) for missing section detection

### Symbol Analysis

- **FR32:** The system can analyze function and method symbols for raise statements, yield expressions, send patterns, warnings calls, and kwargs parameters
- **FR33:** The system can analyze class symbols to determine construct type (plain class with `__init__`, dataclass, NamedTuple, TypedDict)
- **FR34:** The system can analyze module symbols to determine if the source file is an `__init__.py`
- **FR35:** The system can extract and parse raw docstring text from symbols to identify which sections are present
- **FR36:** The system can analyze any symbol with a non-empty docstring, regardless of docstring length or section count
- **FR37:** The system can distinguish between symbols that have a docstring (analyze for completeness) and symbols with no docstring (skip -- presence checking is interrogate's job)
- **FR38:** The system can process docstrings with broken indentation, missing section-header colons, or non-standard header names without raising exceptions, producing zero findings for symbols whose docstrings cannot be reliably parsed

### Integration

- **FR39:** The system can accept source code, a parsed AST, configuration, and file path as inputs and return a list of findings as output
- **FR40:** The system can operate as a pure function with no I/O, no side effects, and deterministic output
- **FR41:** The system can provide `Finding` as a shared type importable by all check modules without cross-check dependencies
- **FR42:** A developer can run the enrichment check standalone via `docvet enrichment` or as part of all checks via `docvet check`

### Diff Mode Detection

- **FR43:** The system can parse git diff output to extract changed hunk line ranges for a given file
- **FR44:** The system can map changed line ranges to AST symbols using the existing line-to-symbol mapping infrastructure
- **FR45:** The system can classify each changed line within a symbol as belonging to the signature range, docstring range, or body range
- **FR46:** The system can detect symbols where code lines (signature or body) changed but docstring lines did not change
- **FR47:** The system can assign HIGH severity (category `required`) when a symbol's signature range contains changed lines
- **FR48:** The system can assign MEDIUM severity (category `recommended`) when a symbol's body range contains changed lines but its signature range does not
- **FR49:** The system can assign LOW severity (category `recommended`) when only lines within a symbol's enclosing line range but outside its signature, docstring, and body ranges changed, and no signature or body lines changed

### Drift Mode Detection

- **FR50:** The system can parse `git blame --line-porcelain` output to extract per-line modification timestamps for a given file
- **FR51:** The system can group per-line timestamps by symbol using the existing line-to-symbol mapping infrastructure
- **FR52:** The system can detect symbols where the most recent code modification exceeds the most recent docstring modification by more than a configurable drift threshold (default: 30 days)
- **FR53:** The system can detect symbols where the docstring has not been modified within a configurable age threshold (default: 90 days)
- **FR54:** The system can skip symbols with no docstring in both diff and drift modes, producing zero findings for undocumented symbols

### Freshness Edge Cases

- **FR55:** The system can produce zero freshness findings for newly created files where all lines appear as additions in the git diff
- **FR56:** The system can handle functions that appear in a git diff's deleted lines but no longer exist in the current AST, producing zero findings for those symbols
- **FR57:** The system can treat code relocated within a file as a delete-plus-add (body change at the new location, no finding at the old location), without requiring `git diff --find-renames`. Cross-file move detection is out of scope — freshness operates per-file on the diff output for each file independently
- **FR58:** The system can skip binary files and non-Python files present in git diff output without producing findings or raising exceptions

### Freshness Finding Production

- **FR59:** The system can produce a structured finding for each stale docstring, carrying file path, line number, symbol name, rule identifier, human-readable message, and category
- **FR60:** The system can produce freshness findings using the shared `Finding` dataclass without modification to the dataclass fields or behavior
- **FR61:** The system can produce at most one finding per symbol per mode, selecting the highest applicable severity when multiple change types affect the same symbol in diff mode
- **FR62:** The system can produce zero findings when analyzing code where all changed symbols have correspondingly updated docstrings

### Freshness Configuration

- **FR63:** A developer can configure the drift threshold (in days) via `drift-threshold` in `[tool.docvet.freshness]`
- **FR64:** A developer can configure the age threshold (in days) via `age-threshold` in `[tool.docvet.freshness]`
- **FR65:** The system can apply default thresholds (drift: 30 days, age: 90 days) when no `[tool.docvet.freshness]` section is provided in `pyproject.toml`

### Freshness Integration

- **FR66:** The system can accept file path, git output string (diff or blame), and parsed AST as inputs and return a list of findings as output
- **FR67:** A developer can run the freshness check standalone via `docvet freshness` or as part of all checks via `docvet check`
- **FR68:** A developer can select diff or drift mode via `--mode` CLI option, with diff as the default

### Coverage Detection

- **FR69:** The system can detect Python files whose parent directories lack `__init__.py`, making them invisible to mkdocstrings for API documentation generation
- **FR70:** The system can walk the directory hierarchy from each Python file's parent upward to the configured `src-root`, checking each intermediate directory for `__init__.py` existence
- **FR71:** The system can stop the upward directory walk at `src-root` — directories at or above `src-root` are not required to have `__init__.py`
- **FR72:** The system can skip top-level modules (Python files directly under `src-root`) since they are not in a package and do not require `__init__.py`
- **FR73:** The system can treat an empty `__init__.py` file as satisfying the requirement — only existence is checked, not content
- **FR74:** The system can produce at most one finding per missing `__init__.py` directory, even when multiple Python files are affected by the same gap

### Coverage Finding Production

- **FR75:** The system can produce a structured coverage finding carrying the path of a representative affected file (lexicographically first by path), line 1, `"<module>"` as symbol, `missing-init` as rule identifier, a message naming the directory missing `__init__.py` and the count of affected files, and category `required`
- **FR76:** The system can produce zero findings when all parent directories between discovered files and `src-root` contain `__init__.py`

### Coverage Integration

- **FR77:** The system can accept a `src-root` path and a list of discovered Python file paths as inputs and return a list of findings as output
- **FR78:** A developer can run the coverage check standalone via `docvet coverage` or as part of all checks via `docvet check`
- **FR79:** The system can operate as a pure function with no side effects beyond filesystem existence checks, producing deterministic output for a given filesystem state
- **FR80:** The system can skip files that are not under `src_root` (e.g., test files outside the source tree), producing zero findings for those files without raising exceptions

### Griffe Detection

- **FR81:** The system can detect docstring parameters that lack type annotations in both the docstring text and the function signature, producing a finding when griffe's parser warns about missing types
- **FR82:** The system can detect docstring parameters that do not appear in the function signature, producing a finding when griffe's parser warns about unknown parameters
- **FR83:** The system can detect docstring formatting issues (confusing indentation, malformed entries, missing blank lines, skipped sections) that degrade rendered documentation quality
- **FR84:** The system can load a Python package via griffe's package loader and capture parser warnings emitted during docstring parsing
- **FR85:** The system can filter captured griffe warnings to only those originating from files in the discovered file list, respecting `--staged`, `--all`, and `--files` discovery modes

### Griffe Finding Production

- **FR86:** The system can produce a structured griffe finding carrying file path, line number, symbol name, rule identifier (`griffe-missing-type`, `griffe-unknown-param`, or `griffe-format-warning`), griffe's warning message, and category (`required` or `recommended` based on rule)
- **FR87:** The system can classify each griffe warning into one of 3 rule identifiers by matching the warning message against known patterns: `"No type or annotation for parameter"` maps to `griffe-missing-type`, `"does not appear in the function signature"` maps to `griffe-unknown-param`, and all other warnings (indentation, malformed entries, missing blank lines, skipped sections) map to `griffe-format-warning`
- **FR88:** The system can produce one finding per griffe warning (not deduplicated per symbol), allowing multiple findings for the same symbol when griffe reports multiple individually-fixable issues (e.g., 3 untyped parameters on one function produce 3 separate findings)
- **FR89:** The system can produce zero findings when analyzing well-documented code with typed parameters and valid parameter names

### Griffe Edge Cases

- **FR90:** The system can return an empty list immediately when griffe is not installed, without raising exceptions or producing error findings
- **FR91:** The system can handle griffe package loading failures (syntax errors in user code, missing third-party imports, permission errors) by returning an empty list without crashing
- **FR92:** The system can classify griffe warnings from future griffe versions that do not match known patterns as `griffe-format-warning` rather than dropping them
- **FR93:** The system can produce zero findings when all discovered files are outside the loaded griffe package (e.g., all files filtered out after warning-to-file matching)

### Griffe Integration

- **FR94:** The system can accept a `src-root` path and a list of discovered Python file paths as inputs and return a list of findings as output
- **FR95:** A developer can run the griffe check standalone via `docvet griffe` or as part of all checks via `docvet check`
- **FR96:** The system can capture griffe parser warnings via a temporary logging handler attached to the griffe logger, removing the handler after loading completes to ensure no permanent modification to global logging state
- **FR97:** The CLI can detect griffe availability before invoking the check function and emit a verbose-mode note when griffe is skipped, plus a stderr warning when griffe is in `fail-on` but not installed

## Non-Functional Requirements

### Performance

- **NFR1:** The enrichment check can analyze a single file (≤1000 lines) in under 50ms -- aspirational benchmark validated during implementation, not a CI-enforced gate
- **NFR2:** The enrichment check can process a 200-file codebase via `docvet enrichment --all` in under 5 seconds on commodity hardware -- aspirational benchmark; the real gate is "fast enough for pre-commit hooks and CI pipelines without noticeable delay"
- **NFR3:** The enrichment check is designed to add negligible overhead beyond AST parsing -- design invariant, not a CI-enforced benchmark
- **NFR4:** Memory usage scales linearly with file count, not quadratically -- each file is processed independently with no cross-file state (design invariant, not tested explicitly)

### Correctness

- **NFR5:** The enrichment check produces zero false positives on well-documented code with complete docstrings (deterministic, reproducible)
- **NFR6:** The enrichment check produces identical output for identical input regardless of execution environment, time, or ordering
- **NFR7:** Malformed docstrings (broken indentation, missing colons, non-standard headers) result in zero findings for that symbol, never a crash or traceback
- **NFR8:** The enrichment check never modifies input data -- `source`, `tree`, and `config` remain unchanged after execution
- **NFR9:** Finding messages are actionable -- each message names the specific symbol, the specific issue, and what section is missing, enabling the developer to fix the problem without additional context

### Maintainability

- **NFR10:** Each of the 10 rules can be understood, modified, and tested independently without knowledge of other rules
- **NFR11:** Adding a new detection rule requires changes to at most 3 files: the rule implementation (`enrichment.py`), its config toggle (`config.py`), and its tests (`test_enrichment.py`)
- **NFR12:** Test coverage on `checks/enrichment.py` targets ≥90% (aspirational, not CI-enforced), with project-wide coverage maintaining the ≥85% CI gate
- **NFR13:** All quality gates pass: ruff check, ruff format, ty check, pytest, interrogate (95% docstring coverage)

### Compatibility

- **NFR14:** The enrichment check works on Python 3.12 and 3.13 (CI tests both versions)
- **NFR15:** The enrichment check works on Linux, macOS, and Windows without platform-specific code paths
- **NFR16:** No new runtime dependencies -- stdlib `ast`, `re`, and existing `ast_utils` only

### Integration

- **NFR17:** `Finding`'s 6-field shape (`file`, `line`, `symbol`, `rule`, `message`, `category`) is stable for v1 -- no fields are added, removed, or renamed within the v1 lifecycle
- **NFR18:** The enrichment check integrates with the existing CLI dispatch pattern (`_run_enrichment` stub) without requiring changes to CLI argument parsing or global option handling
- **NFR19:** Config additions (`require-attributes` toggle) are backward-compatible -- existing `pyproject.toml` files without this key continue to work with the default value

### Freshness Performance

- **NFR20:** Diff mode can process a single file's git diff and produce findings in under 100ms -- aspirational benchmark validated during implementation, not a CI-enforced gate
- **NFR21:** Drift mode performance is dominated by git blame I/O; the freshness pure function is designed to add negligible overhead beyond timestamp parsing and symbol comparison -- design invariant, not a CI-enforced benchmark
- **NFR22:** Memory usage for freshness scales linearly with file count -- each file is processed independently with no cross-file state

### Freshness Correctness

- **NFR23:** Non-signature code changes never produce HIGH severity findings -- body-only changes produce at most MEDIUM severity (category `recommended`)
- **NFR24:** Identical git diff input and identical AST produce identical severity assignment for the same symbol, regardless of execution environment or ordering
- **NFR25:** Malformed git output (truncated diffs, corrupted blame data, empty strings) results in zero findings for affected files, never exceptions or tracebacks
- **NFR26:** Finding messages name the specific symbol, the severity level, and the type of change detected (signature, body, or drift), enabling the developer to locate and fix the stale docstring without additional context

### Freshness Maintainability

- **NFR27:** Diff mode and drift mode can be tested independently using mocked git output strings with no filesystem or git subprocess calls
- **NFR28:** Adding a new severity level or drift rule requires changes to at most 3 files: the freshness module (`freshness.py`), config (`config.py`), and tests (`test_freshness.py`)

### Freshness Compatibility

- **NFR29:** Freshness functions handle git diff and git blame output from git 2.x without version-specific code paths
- **NFR30:** Freshness functions handle both `git diff` (unstaged) and `git diff --cached` (staged) output identically, as both use the same unified diff hunk format

### Freshness Integration

- **NFR31:** Freshness reuses the shared `Finding` dataclass without modification -- no new fields, no subclassing, no changes to the frozen 6-field shape
- **NFR32:** Freshness has no cross-imports with enrichment or any other check module -- it depends only on `checks.Finding` and `ast_utils`

### Coverage Performance

- **NFR33:** The coverage check can process a 200-file codebase via `docvet coverage --all` in under 1 second -- pure filesystem stat calls with no AST parsing, no git commands, and no subprocess overhead

### Coverage Correctness

- **NFR34:** The coverage check produces zero findings on a properly packaged project where all parent directories between Python files and `src-root` contain `__init__.py` (deterministic, reproducible)
- **NFR35:** The coverage check produces identical output for identical filesystem state regardless of execution environment, time, or file processing order — findings are sorted by directory path, and representative files are selected as the lexicographically first affected file

### Coverage Maintainability

- **NFR36:** The coverage check can be tested using `tmp_path` filesystem fixtures with no git repository, no AST parsing, and no external dependencies

### Coverage Compatibility

- **NFR37:** The coverage check works on Linux, macOS, and Windows using `pathlib.Path` for all path operations -- no platform-specific code paths

### Coverage Integration

- **NFR38:** Coverage has no cross-imports with enrichment, freshness, or any other check module -- it depends only on `checks.Finding` and `pathlib`

### Griffe Performance

- **NFR39:** The griffe check can process a 200-file package via `docvet griffe --all` in under 10 seconds -- aspirational benchmark; performance is dominated by griffe's package loading I/O, not docvet's warning mapping logic
- **NFR40:** The griffe check is designed to add negligible overhead beyond griffe's package loading and docstring parsing -- design invariant, not a CI-enforced benchmark

### Griffe Correctness

- **NFR41:** The griffe check produces zero findings on well-documented code where all parameters have type annotations and match the function signature (deterministic, reproducible)
- **NFR42:** The griffe check produces zero findings and raises no exceptions when griffe is not installed -- the check silently skips without affecting other checks
- **NFR43:** Unrecognized griffe warning messages (from future griffe versions) are classified as `griffe-format-warning` rather than dropped or causing exceptions

### Griffe Maintainability

- **NFR44:** The griffe check can be tested using mocked griffe logging output with no actual package loading, enabling fast unit tests with predictable warning scenarios
- **NFR45:** Adding a new griffe rule identifier requires changes to at most 2 files: the griffe module (`griffe_compat.py`) and its tests (`test_griffe_compat.py`). No config changes needed (zero configuration)

### Griffe Compatibility

- **NFR46:** The griffe check works with griffe 1.x releases, using only stable public APIs (`griffe.load()`, `GriffeLoader`) and standard Python logging for warning capture

### Griffe Integration

- **NFR47:** Griffe reuses the shared `Finding` dataclass without modification -- no new fields, no subclassing, no changes to the frozen 6-field shape
- **NFR48:** Griffe has no cross-imports with enrichment, freshness, coverage, or any other check module -- it depends only on `checks.Finding`, `pathlib`, and the optional `griffe` package
