---
stepsCompleted:
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
  - 7
  - 8
  - 'freshness-2'
  - 'freshness-4'
  - 'freshness-5'
  - 'freshness-6'
  - 'freshness-7'
  - 'freshness-8'
lastStep: 'freshness-8'
status: 'complete'
completedAt: '2026-02-09'
freshnessStartedAt: '2026-02-09'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/prd-validation-report.md'
  - '_bmad-output/project-context.md'
  - 'docs/index.md'
  - 'docs/architecture.md'
  - 'docs/product-vision.md'
  - 'docs/project-overview.md'
  - 'docs/development-guide.md'
  - 'docs/source-tree-analysis.md'
  - 'src/docvet/ast_utils.py'
  - 'src/docvet/config.py'
  - 'src/docvet/checks/__init__.py'
workflowType: 'architecture'
project_name: 'docvet'
user_name: 'Alberto-Codes'
date: '2026-02-09'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
42 FRs across 6 categories. The enrichment module is a single pure function that detects 14 scenarios (mapped to 10 rule identifiers) by combining AST node inspection with docstring section header matching. Key architectural groupings:

- **Section Detection (FR1-FR15):** 15 FRs defining what to detect — each maps to an AST pattern + docstring section check
- **Finding Production (FR16-FR22):** 7 FRs defining output shape — `Finding` dataclass, deduplication, zero-finding guarantees
- **Rule Management (FR23-FR25):** 3 FRs defining stable kebab-case identifiers and scenario-to-rule mapping
- **Configuration (FR26-FR31):** 6 FRs defining toggle behavior — 10 booleans + 1 list, defaults, validation
- **Symbol Analysis (FR32-FR38):** 7 FRs defining input processing — AST traversal, docstring parsing, graceful degradation
- **Integration (FR39-FR42):** 4 FRs defining the public API contract — pure function, shared `Finding` type, CLI wiring

**Non-Functional Requirements:**
19 NFRs across 5 categories that directly shape internal architecture:

- **Performance (NFR1-4):** Sub-50ms per file, linear memory scaling, no cross-file state — enforces stateless per-file processing
- **Correctness (NFR5-9):** Zero false positives, deterministic output, crash-proof on malformed input — enforces defensive parsing with fail-safe defaults
- **Maintainability (NFR10-13):** Rule independence, 3-file change ceiling for new rules, 90% coverage target — enforces modular rule structure
- **Compatibility (NFR14-16):** Python 3.12/3.13, cross-platform, no new deps — eliminates platform-conditional code paths
- **Integration (NFR17-19):** Frozen `Finding` shape, existing stub wiring, backward-compatible config — constrains API surface

**Scale & Complexity:**

- Primary domain: CLI developer tool (single-process, file-at-a-time)
- Complexity level: Medium
- Estimated architectural components: ~5 internal components (section parser, rule dispatcher, symbol analyzer, finding builder, config responder)

### Rule Complexity Tiering

The 10 rules vary significantly in architectural complexity. This tiering informs implementation sequencing and risk allocation:

| Tier | Rules | Characteristics |
|------|-------|----------------|
| **High** | `missing-attributes` | 5 detection branches (plain class, dataclass, NamedTuple, TypedDict, `__init__.py` module), deduplication required, needs AST + docstring + file_path context |
| **Medium** | `missing-raises`, `missing-yields`, `missing-receives`, `missing-warns` | AST body/expression inspection + docstring section presence check |
| **Low** | `missing-other-parameters`, `missing-examples`, `missing-cross-references`, `missing-typed-attributes`, `prefer-fenced-code-blocks` | Straightforward pattern match on AST signature or docstring content only |

### Rule Input Dependency Categories

Rules fall into three categories based on what inputs they inspect. These categories are not mutually exclusive — `missing-attributes` spans all three.

- **AST + docstring rules:** Inspect AST nodes (raise statements, yield expressions, warn calls, kwargs, class fields) and check for corresponding docstring section presence. Rules: `missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`, `missing-other-parameters`, `missing-attributes`, `missing-examples`
- **Docstring-only rules:** Inspect docstring content/format without AST inspection. Rules: `missing-typed-attributes`, `prefer-fenced-code-blocks`, `missing-cross-references`
- **Context-aware rules:** Branch on `file_path.endswith("__init__.py")` for module-level special handling. Rules: `missing-attributes`, `missing-examples`, `missing-cross-references`

### Shared Infrastructure: Section Header Parsing

Section header parsing is architecturally load-bearing — every rule depends on knowing which sections are present in a docstring. This must be centralized as a shared internal function (`_parse_sections(docstring: str) -> set[str]`) within `enrichment.py` (not `ast_utils.py`, since section parsing is enrichment-specific). Called once per symbol, the result is passed to each rule checker. This prevents subtle inconsistencies between rules and is a prerequisite for NFR11's 3-file change ceiling to hold.

Recognized headers (8 for detection + 2 for context): `Raises:`, `Yields:`, `Receives:`, `Warns:`, `Other Parameters:`, `Attributes:`, `Examples:`, `See Also:`, plus `Args:` and `Returns:` recognized but not checked for absence.

### AST Boundary Decision

The existing `Symbol` dataclass provides: `name`, `kind`, `line`, `docstring`, `parent`, `signature_range`, `body_range`. This is sufficient for **symbol-level metadata** but **not for body-level inspection**. Rules like `missing-raises`, `missing-yields`, `missing-receives`, and `missing-warns` need to inspect AST nodes *inside* function bodies (raise statements, yield expressions, `warnings.warn()` calls).

**Position:** `check_enrichment` receives the full `ast.Module` tree and re-walks relevant nodes locally. `Symbol` stays lightweight — it identifies *which* symbols to check and provides their docstrings. The enrichment module performs its own targeted AST inspection for body-level patterns. This keeps `ast_utils.py` general-purpose and avoids bloating `Symbol` with enrichment-specific fields.

### `missing-attributes` Dispatch Order

The `missing-attributes` rule has 5 detection branches. To satisfy FR18 (at most one finding per symbol per rule), branches are evaluated in **priority order with first-match-wins semantics — no fallthrough**:

1. Dataclass (decorator inspection)
2. NamedTuple (base class inspection)
3. TypedDict (base class inspection)
4. Plain class with `__init__` self-assignments
5. `__init__.py` module-level exports

This ordering is an **architectural constraint**, not an implementation detail. It ensures deterministic, predictable deduplication regardless of how the code is structured.

### Technical Constraints & Dependencies

- **Existing infrastructure:** `Symbol` dataclass (frozen, with `kind`, `docstring`, `line`, `parent` fields), `get_documented_symbols()` flat list, `EnrichmentConfig` with 10 booleans + 1 list
- **`file_path` parameter:** Required for `__init__.py` detection — 3 rules branch on this
- **Caller provides AST:** `check_enrichment` does not call `ast.parse()` — SyntaxError handling is the caller's responsibility
- **Google-style only:** Section headers are a fixed set of 8+2 strings
- **No cross-check imports:** `checks/enrichment.py` depends only on `checks.Finding` and `ast_utils`
- **Config schema:** `require-attributes: bool = True` is a new toggle (prerequisite PR)

### Cross-Cutting Concerns Identified

- **Config toggle respect:** Every rule must check its corresponding config toggle before producing findings — disabled rules produce zero findings unconditionally
- **No-docstring skip:** All rules skip symbols with no docstring (FR20, FR37) — presence checking is interrogate's domain
- **Malformed docstring resilience:** All rules must handle broken indentation, missing colons, and non-standard headers without crashing (NFR7, FR38) — `_parse_sections()` returns empty set on unparseable input
- **One-finding-per-symbol-per-rule deduplication:** Enforced structurally by the dispatch pattern (first-match-wins for `missing-attributes`) and by the rule-per-symbol iteration model for all other rules

## Existing Infrastructure Inventory

### Primary Technology Domain

**CLI tool / developer tooling** — Python single-process pipeline. Brownfield project (`projectType: cli_tool`, `projectContext: brownfield`). All foundational technology decisions are implemented, tested, and CI-enforced.

### Infrastructure the Enrichment Module Depends On

**`ast_utils.py` — Symbol Extraction:**
- `get_documented_symbols(source: str, tree: ast.Module) -> list[Symbol]` — the only `ast_utils` function enrichment calls
- Returns flat list of `Symbol` objects (frozen dataclass) with: `name`, `kind` (`"function" | "class" | "method" | "module"`), `line`, `end_line`, `docstring`, `parent` (enclosing class name or `None`)
- Enrichment iterates this list, skipping symbols with no docstring (FR20, FR37)

**`config.py` — EnrichmentConfig:**

Current state (9 booleans + 1 list):
- `require_raises`, `require_yields`, `require_receives`, `require_warns`, `require_other_parameters`, `require_typed_attributes`, `require_cross_references`, `prefer_fenced_code_blocks` (booleans)
- `require_examples` (list of symbol type strings)

Post-prerequisite PR (10 booleans + 1 list):
- Adds `require_attributes: bool = True` — controls the `missing-attributes` rule
- Backward-compatible: new field with default value, no existing config breaks

**`cli.py` — Stub Wiring:**
- `_run_enrichment(files: list[Path], config: DocvetConfig)` — existing stub, enrichment replaces the body
- CLI dispatch already handles discovery mode resolution and config loading

### Prerequisite PRs

Two PRs must ship before the main enrichment PR:

1. **Config update PR:** Add `require_attributes: bool = True` to `EnrichmentConfig`, update `_VALID_ENRICHMENT_KEYS`, update `_parse_enrichment` validation, update affected tests
2. **`checks` package PR:** Create `src/docvet/checks/__init__.py` with `Finding` frozen dataclass (6 fields: `file`, `line`, `symbol`, `rule`, `message`, `category`). Shared type contract for all check modules

### Technology Stack Reference

Build system, quality toolchain, testing infrastructure, and code style rules are documented in `_bmad-output/project-context.md` (73 rules) and `CLAUDE.md`. Key constraints relevant to enrichment:

- No new runtime dependencies — stdlib `ast`, `re`, and existing `ast_utils` only
- Google-style docstrings assumed throughout
- `from __future__ import annotations` in every file
- Checks are isolated — no cross-imports between check modules
- Tests use source string fixtures with `parse_source` factory, never mock AST nodes

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. Internal module organization (private function per rule)
2. AST node-to-Symbol mapping (line-based index)
3. Section header regex strategy (lenient with compiled pattern)

**Important Decisions (Shape Architecture):**
4. Finding message format (convention-based, two patterns)
5. Error handling strategy (defensive by design, no try/except)

**Deferred Decisions (Post-MVP):**
- Production hardening (orchestrator-level catch-all for unforeseen edge cases)
- Message truncation thresholds for long evidence lists
- Inline suppression mechanism (`# docvet: ignore[rule]`)

### Decision 1: Internal Module Organization

**Decision:** Private function per rule (Option A with uniform signature)

Each of the 10 rules is implemented as a `_check_*` private function with a uniform signature:

```python
def _check_missing_raises(
    symbol: Symbol,
    sections: set[str],
    node_index: dict[int, ast.AST],
    config: EnrichmentConfig,
    file_path: str,
) -> Finding | None:
```

**Config gating lives in the orchestrator**, not inside `_check_*` functions. The orchestrator checks the config toggle and skips calling a `_check_*` entirely when its toggle is off. This keeps detection logic pure — zero config awareness inside rule functions.

**Config gating clarification — boolean vs. list toggles:**
- **Boolean toggles** (9 rules): Orchestrator checks `config.require_raises`, etc. If `False`, skip the call entirely.
- **List toggle** (`require_examples`): Orchestrator checks `if not config.require_examples` (empty list is falsy). If non-empty, the `_check_missing_examples` function reads `config.require_examples` internally to determine which `symbol.kind` values trigger the rule. This is the only `_check_*` function that inspects config — justified because the gating is symbol-type-specific, not a simple on/off.

**Rationale:** Simplest structure satisfying NFR10 (rule independence) and NFR11 (3-file change ceiling). No registry, no abstraction — 10 functions, each self-contained and independently testable.

### Decision 2: AST Node-to-Symbol Mapping

**Decision:** Line-based index (Option C)

`_build_node_index(tree: ast.Module) -> dict[int, ast.AST]` performs one `ast.walk()` pass, collecting `FunctionDef | AsyncFunctionDef | ClassDef` nodes, indexed by `lineno`. Called once at the top of `check_enrichment`.

- Line numbers are unique per node — no name collision risk
- Nested functions handled correctly (each gets its own `lineno` entry)
- `node_index` replaces `tree` in the uniform `_check_*` signature — no rule needs to walk the raw tree
- Module symbols (line 1, no corresponding node) handled by `node_index.get()` returning `None`

**Note on `missing-attributes` branch 4 (plain class):** This branch requires a nested AST walk within the `ClassDef` node — `ClassDef.body` → find `FunctionDef` named `__init__` → walk its body for `ast.Assign` / `ast.AnnAssign` with `self.*` targets. The `ClassDef` is retrieved from `node_index`; the nested walk is internal to `_check_missing_attributes`. Implementing agents should expect this additional complexity in the highest-tier rule.

**Rationale:** O(1) lookup per rule per symbol vs. O(n) per walk. One pass over the tree serves all 4 medium-tier rules that need body inspection.

### Decision 3: Section Header Regex

**Decision:** Lenient matching with single compiled regex

```python
_SECTION_HEADERS = frozenset({
    "Args", "Returns", "Raises", "Yields", "Receives",
    "Warns", "Other Parameters", "Attributes", "Examples", "See Also",
})

_SECTION_PATTERN = re.compile(
    r"^\s*(Args|Returns|Raises|Yields|Receives|Warns|Other Parameters|Attributes|Examples|See Also):\s*$",
    re.MULTILINE,
)
```

`_parse_sections(docstring: str) -> set[str]` uses `re.findall()` with the capturing group, returning matched header names as a set.

- `\s*` (zero or more) leading whitespace — handles module-level docstrings with no indent
- False negatives (safe direction) preferred over false positives (NFR5)
- Code block edge case is theoretical and produces false negatives, not false positives
- `_SECTION_HEADERS` constant is testable and extensible (one-line future additions)

**Rationale:** Recognizes well-intentioned docstrings with varied indentation. A developer who wrote a complete `Raises:` section at any indent level has documented their raises — the tool should not produce a false positive.

### Decision 4: Finding Message Format

**Decision:** Convention-based, two patterns (not code-enforced)

Each `_check_*` owns its message f-string, following documented conventions:

**Missing-section rules** (7 rules):
`{SymbolKind} '{name}' {evidence} but has no {Section}: section`

Examples:
- `Function 'parse_config' raises ValueError, FileNotFoundError but has no Raises: section`
- `Dataclass 'ValidationResult' has 6 fields but has no Attributes: section`

**Format rules** (3 rules):
`{Section}: section in {symbolKind} '{name}' {format issue}`

Examples:
- `Attributes: section in class 'Foo' lacks typed format (name (type): description)`
- `Examples: section in function 'bar' uses doctest format (>>>) instead of fenced code blocks`

**Rationale:** Evidence is rule-specific (exception names, field count, etc.) — a shared template would be more complex than individual f-strings. Convention ensures consistency; per-rule ownership enables specificity. Truncation of long evidence lists is a per-rule implementation detail.

### Decision 5: Error Handling Strategy

**Decision:** Defensive by design, no try/except in MVP

Three defensive gates eliminate crash paths without exception handling:

1. **`_parse_sections()`** — regex on string input, always returns `set[str]`, empty set on no matches (never raises)
2. **`node_index.get(symbol.line)`** — `_check_*` functions use `.get()`, return `None` early if node is missing
3. **Orchestrator** — skips symbols with no docstring before calling any `_check_*`

No try/except in `_check_*` functions. They are pure logic, trusted through comprehensive tests. Swallowing exceptions would mask real bugs during development.

**Rationale:** Correctness through design, not exception catching. If a `_check_*` has a logic error, it should crash in tests so it gets fixed. Production hardening (orchestrator-level catch-all) deferred to post-MVP.

### Decision Impact Analysis

**Full Implementation Sequence (including prerequisites):**
1. **Prereq PR 1:** `require_attributes` config toggle in `config.py`
2. **Prereq PR 2:** `checks/__init__.py` with `Finding` frozen dataclass
3. `_SECTION_HEADERS` constant and `_SECTION_PATTERN` compiled regex (Decision 3)
4. `_parse_sections()` function (Decision 3)
5. `_build_node_index()` function (Decision 2)
6. 10 `_check_*` functions following uniform signature (Decisions 1, 4, 5)
7. `check_enrichment()` orchestrator with config gating (Decision 1)

**Cross-Decision Dependencies:**
- Decision 1 (module org) defines the signature that Decisions 2, 4, 5 fill in
- Decision 2 (node index) replaces `tree` in the signature from Decision 1
- Decision 3 (section parsing) produces the `sections` parameter consumed by all `_check_*` functions
- Decision 5 (error handling) shapes how Decisions 2 and 3 handle edge cases
- Prereq PR 2 (`Finding` dataclass) must exist before any `_check_*` function can be written

## Implementation Patterns & Consistency Rules

### Conflict Points Identified

7 areas where AI agents implementing the enrichment module could make inconsistent choices.

### Naming Patterns

**Private function naming:**
- Pattern: `_check_{rule_id_with_underscores}` — directly derived from the kebab-case rule identifier
- `missing-raises` → `_check_missing_raises`
- `missing-attributes` → `_check_missing_attributes`
- `prefer-fenced-code-blocks` → `_check_prefer_fenced_code_blocks`
- **Anti-pattern:** `_check_raises`, `_raises_check`, `_detect_missing_raises` — any deviation from the rule ID

**Helper function naming:**
- Pattern: `_build_*` for index/data structure construction, `_parse_*` for text parsing, `_has_*` for boolean checks, `_is_*` for type/state checks
- Examples: `_build_node_index`, `_parse_sections`, `_has_self_assignments`, `_is_dataclass`
- **Anti-pattern:** Generic names like `_helper`, `_process`, `_do_check`

**Constants:**
- Pattern: `ALL_CAPS_WITH_UNDER` at module level (per project context rules)
- `_SECTION_HEADERS`, `_SECTION_PATTERN`
- Private constants prefixed with `_` (not exported)

### Structure Patterns

**File organization within `enrichment.py`:**
1. Module docstring
2. `from __future__ import annotations`
3. Stdlib imports (`ast`, `re`)
4. Local imports (`from docvet.ast_utils import ...`, `from docvet.checks import Finding`, `from docvet.config import EnrichmentConfig`)
5. Module-level constants (`_SECTION_HEADERS`, `_SECTION_PATTERN`)
6. Shared helper functions (`_parse_sections`, `_build_node_index`)
7. Rule-specific helper functions (`_has_self_assignments`, `_is_dataclass`, etc.)
8. `_check_*` functions (ordered by rule taxonomy table — same order as PRD)
9. `check_enrichment` public orchestrator (last function in file)

**Taxonomy-table order** is the canonical ordering used for both function definitions and dispatch:
`missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`, `missing-other-parameters`, `missing-attributes`, `missing-typed-attributes`, `missing-examples`, `missing-cross-references`, `prefer-fenced-code-blocks`

**`_check_missing_attributes` internal organization:**
- Two distinct code paths based on symbol type:
  - **Class symbols** (`symbol.kind == "class"`): Branches 1-4 use `node_index.get(symbol.line)` to retrieve the `ClassDef` node, then inspect decorators/bases/body
  - **Module symbols** (`symbol.kind == "module"`): Branch 5 checks `file_path.endswith("__init__.py")`, no node needed
- 5 branches ordered per architectural constraint, each as a helper function: `_is_dataclass(node)`, `_is_namedtuple(node)`, `_is_typeddict(node)`, `_has_self_assignments(node)`, `_is_init_module(file_path)`
- First match wins, no fallthrough

**Test organization:**
- `tests/unit/checks/test_enrichment.py` — organized by rule in taxonomy-table order
- Test naming: `test_{rule_id}_when_{condition}_returns_{expected}` (per project context)
- Example: `test_missing_raises_when_function_raises_without_section_returns_finding`

**Dual testing strategy:**
- **Simple rules (9 of 10):** Test through `check_enrichment` with targeted config (disable all rules except the one under test). Tests config gating AND detection logic in one shot.
- **`missing-attributes`:** Test `_check_missing_attributes` directly + test each branch helper (`_is_dataclass`, `_is_namedtuple`, etc.) individually + integration tests through `check_enrichment` for dispatch order verification.

### AST Inspection Patterns

**Node type checking:**
- Always use `isinstance()` — `isinstance(node, ast.Raise)`, never `type(node) is ast.Raise`
- Check both sync and async variants: `isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))`

**AST traversal rules:**
- Use **scope-aware iterative walk** for body-level inspection (e.g., finding `raise` statements, `yield` expressions, `warnings.warn()` calls within a function body). This prevents nested scope false positives where inner function/class statements are incorrectly attributed to the outer function:
  ```python
  stack = list(ast.iter_child_nodes(node))
  while stack:
      child = stack.pop()
      if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
          continue  # Don't descend into nested scopes
      # ... check for target AST node types ...
      stack.extend(ast.iter_child_nodes(child))
  ```
- Use `ast.walk(tree)` **only** for whole-tree collection where scope boundaries don't matter (e.g., `_build_node_index` collecting all `FunctionDef`/`ClassDef` nodes across the entire module)
- Use direct `.body` iteration for **immediate children** (e.g., finding `__init__` in `ClassDef.body`)
- **Critical:** `ast.walk(node)` traverses into nested scopes — never use it for body-level pattern detection in `_check_*` functions (NFR5 — zero false positives)

**Decorator inspection (for dataclass detection):**
- Check both `@dataclass` and `@dataclasses.dataclass`
- Handle `ast.Name` (simple decorator) and `ast.Attribute` (qualified decorator)
- Handle `ast.Call` (decorator with arguments: `@dataclass(frozen=True)`)

**Base class inspection (for NamedTuple/TypedDict):**
- Check `node.bases` for `ast.Name` with `id` in `{"NamedTuple", "TypedDict"}`
- Check `ast.Attribute` for qualified form: `typing.NamedTuple`, `typing.TypedDict`

**`self.*` assignment detection (for plain class attributes):**
- Walk `__init__` body for `ast.Assign` where target is `ast.Attribute` with `value.id == "self"`
- Also check `ast.AnnAssign` for annotated assignments: `self.x: int = 0`

### Finding Construction Pattern

**All `_check_*` functions construct findings identically:**

```python
return Finding(
    file=file_path,
    line=symbol.line,
    symbol=symbol.name,
    rule="missing-raises",  # literal string, matches rule taxonomy
    message=f"Function '{symbol.name}' raises ValueError but has no Raises: section",
    category="required",  # literal string from rule taxonomy
)
```

- `file` is always `file_path` (passed through, not computed)
- `line` is always `symbol.line` (not the AST node line)
- `symbol` is always `symbol.name`
- `rule` is always a string literal matching the rule taxonomy
- `category` is always a string literal (`"required"` or `"recommended"`) matching the rule taxonomy
- **Anti-pattern:** Computing line from AST node, using dynamic rule/category strings

### Orchestrator Pattern

**`check_enrichment` follows this exact sequence:**

```python
def check_enrichment(
    source: str,
    tree: ast.Module,
    config: EnrichmentConfig,
    file_path: str,
) -> list[Finding]:
    symbols = get_documented_symbols(source, tree)
    node_index = _build_node_index(tree)
    findings: list[Finding] = []

    for symbol in symbols:
        if not symbol.docstring:
            continue
        sections = _parse_sections(symbol.docstring)

        # Config-gated rule dispatch (taxonomy-table order)
        if config.require_raises:
            if f := _check_missing_raises(symbol, sections, node_index, config, file_path):
                findings.append(f)
        # ... repeat for each rule in taxonomy-table order ...

    return findings
```

- Symbols without docstrings skipped first (FR20)
- `_parse_sections` called once per symbol
- Config toggle checked before each `_check_*` call
- Walrus operator (`if f :=`) for concise finding collection
- Rules dispatched in taxonomy-table order

### Enforcement Guidelines

**All AI agents implementing enrichment MUST:**
- Follow the file organization order (constants → helpers → rules → orchestrator)
- Use taxonomy-table order for both function definitions and dispatch
- Use the uniform `_check_*` signature — no per-rule signature variations
- Construct `Finding` objects with literal `rule` and `category` strings
- Use `isinstance()` for AST node type checking
- Use scope-aware iterative walk for body-level inspection; `ast.walk()` only for whole-tree collection; direct `.body` iteration for immediate children
- Place config gating in the orchestrator, not in `_check_*` functions
- Name private functions derivable from the rule ID

**Pattern verification:** ruff + ty enforce naming, import order, and type consistency. Test coverage (>=90% on `enrichment.py`) enforces behavioral correctness.

## Project Structure & Boundaries

### Complete Project Directory Structure

Existing files shown as-is. **New files for enrichment** marked with `← NEW`.

```
src/docvet/
├── __init__.py
├── cli.py                    # _run_enrichment stub → wired to check_enrichment
├── config.py                 # EnrichmentConfig (add require_attributes) ← MODIFIED
├── discovery.py
├── ast_utils.py              # get_documented_symbols (consumed by enrichment)
├── reporting.py
└── checks/
    ├── __init__.py            ← NEW (Finding dataclass)
    └── enrichment.py          ← NEW (check_enrichment + 10 _check_* functions)

tests/
├── conftest.py               # parse_source factory (existing)
├── unit/
│   ├── test_config.py         # Tests for require_attributes toggle ← MODIFIED
│   └── checks/
│       ├── __init__.py
│       └── test_enrichment.py ← NEW (all enrichment rule tests)
├── integration/
│   └── conftest.py
└── fixtures/
    ├── complete_module.py     # Existing — zero findings expected
    ├── missing_raises.py      # Existing — missing-raises finding expected
    └── missing_yields.py      # Existing — missing-yields finding expected
```

### Architectural Boundaries

**Public API boundary:**
- `check_enrichment(source, tree, config, file_path) -> list[Finding]` — the only public function in `enrichment.py`
- `Finding` — the only export from `checks/__init__.py`
- Everything else in `enrichment.py` is private (`_` prefixed)

**Module dependency boundary:**
```
cli.py
  → imports check_enrichment from docvet.checks.enrichment
  → imports Finding from docvet.checks
  → imports EnrichmentConfig from docvet.config
  → imports discover_files from docvet.discovery

checks/enrichment.py
  → imports Finding from docvet.checks
  → imports Symbol, get_documented_symbols from docvet.ast_utils
  → imports EnrichmentConfig from docvet.config
  → NEVER imports from docvet.cli, docvet.discovery, or other checks/*
```

**Data boundary:**
- No I/O inside enrichment — pure function, no file reads, no subprocess calls
- `source` and `tree` provided by caller (CLI reads files and calls `ast.parse`)
- `file_path` is a string for context only — enrichment never opens it

### Requirements to Structure Mapping

**FR Category → File Mapping:**

| FR Category | Primary File | Supporting Files |
|------------|-------------|-----------------|
| Section Detection (FR1-FR15) | `checks/enrichment.py` (`_check_*` functions) | — |
| Finding Production (FR16-FR22) | `checks/__init__.py` (`Finding` dataclass) | `checks/enrichment.py` (construction) |
| Rule Management (FR23-FR25) | `checks/enrichment.py` (rule ID literals in `_check_*`) | — |
| Configuration (FR26-FR31) | `config.py` (`EnrichmentConfig`) | `checks/enrichment.py` (orchestrator gating) |
| Symbol Analysis (FR32-FR38) | `ast_utils.py` (`get_documented_symbols`) | `checks/enrichment.py` (`_build_node_index`, `_parse_sections`) |
| Integration (FR39-FR42) | `cli.py` (`_run_enrichment`) | `checks/enrichment.py` (`check_enrichment`) |

**FR15 clarification:** `Args` and `Returns` are included in `_SECTION_PATTERN` for parsing context only — they allow `_parse_sections` to return a complete picture of which sections exist. No `_check_missing_args` or `_check_missing_returns` function exists because layers 1-2 (presence and style) are ruff/interrogate territory, not docvet's.

**Rule → Internal Function Mapping:**

| Rule | `_check_*` Function | Node Index Usage | Helpers Used |
|------|---------------------|-----------------|-------------|
| `missing-raises` | `_check_missing_raises` | Body walk (find `ast.Raise`) | `_parse_sections` |
| `missing-yields` | `_check_missing_yields` | Body walk (find `ast.Yield`) | `_parse_sections` |
| `missing-receives` | `_check_missing_receives` | Body walk (find `ast.Yield` as assignment target) | `_parse_sections` |
| `missing-warns` | `_check_missing_warns` | Body walk (find `warnings.warn()` call) | `_parse_sections` |
| `missing-other-parameters` | `_check_missing_other_parameters` | Signature only (`node.args.kwarg`) | `_parse_sections` |
| `missing-attributes` | `_check_missing_attributes` | Class node (decorators/bases/body) | `_is_dataclass`, `_is_namedtuple`, `_is_typeddict`, `_has_self_assignments`, `_is_init_module` |
| `missing-typed-attributes` | `_check_missing_typed_attributes` | Not used (docstring-only) | `_parse_sections` |
| `missing-examples` | `_check_missing_examples` | Not used (docstring-only + config list) | `_parse_sections`, `config.require_examples` |
| `missing-cross-references` | `_check_missing_cross_references` | Not used (docstring-only + `file_path`) | `_parse_sections` |
| `prefer-fenced-code-blocks` | `_check_prefer_fenced_code_blocks` | Not used (docstring-only) | `_parse_sections` |

### Data Flow

```
CLI (_run_enrichment)
  │
  │  reads file → source: str
  │  try: ast.parse(source) → tree: ast.Module
  │  except SyntaxError: skip file with warning, do NOT call check_enrichment
  │  loads config → config.enrichment: EnrichmentConfig
  │
  ▼
check_enrichment(source, tree, config, file_path)
  │
  │  get_documented_symbols(source, tree) → symbols: list[Symbol]
  │  _build_node_index(tree) → node_index: dict[int, ast.AST]
  │
  ▼
  for each symbol (skip if no docstring):
  │
  │  _parse_sections(symbol.docstring) → sections: set[str]
  │
  │  for each enabled rule (config gating, taxonomy-table order):
  │    _check_*(symbol, sections, node_index, config, file_path)
  │      → Finding | None
  │
  ▼
list[Finding] returned to CLI
```

### Integration Points

**Enrichment ↔ CLI integration:**
- CLI calls `check_enrichment` once per file (file-at-a-time processing)
- **CLI must wrap `ast.parse()` in try/except SyntaxError** — files that fail to parse are skipped with a warning, never passed to `check_enrichment`
- CLI aggregates `list[Finding]` across files
- CLI applies `fail-on` / `warn-on` logic to determine exit code
- CLI formats findings as `file:line: rule message` for terminal output

**Enrichment ↔ Config integration:**
- `EnrichmentConfig` loaded once by CLI, passed to every `check_enrichment` call
- Config is immutable within a run — no per-file config variation
- Missing `[tool.docvet.enrichment]` section → all defaults (all rules enabled)

**Enrichment ↔ AST Utils integration:**
- `get_documented_symbols` is the only `ast_utils` function called
- `Symbol` dataclass is the only type consumed
- No enrichment-specific changes to `ast_utils.py`

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
All 5 decisions interlock without contradiction:
- Decision 1 (uniform signature) defines the shape → Decisions 2 and 3 fill in the `node_index` and `sections` parameters
- Decision 2 (`node_index.get()`) and Decision 3 (`_parse_sections` returning empty set) both satisfy Decision 5 (defensive design) without try/except
- Decision 4 (per-rule message ownership) aligns with Decision 1 (each `_check_*` self-contained)
- Config gating clarification (boolean vs list toggle) is consistent between Decision 1 and the orchestrator pattern

**Pattern Consistency:**
- Naming conventions: `_check_*` from rule ID, `_build_*`/`_parse_*`/`_has_*`/`_is_*` for helpers — no conflicts
- Taxonomy-table order enforced for both function definitions and dispatch — single canonical ordering
- Finding construction uses literal strings for `rule` and `category` everywhere — no dynamic strings
- File organization order (constants → helpers → rules → orchestrator) supports top-down readability

**Structure Alignment:**
- 2 new files + 2 modified supports all 5 decisions without structural compromise
- Public API boundary (`check_enrichment` + `Finding`) cleanly separates enrichment internals from CLI
- Module dependency graph is acyclic: `cli → enrichment → {checks.Finding, ast_utils, config}` — no circular deps
- Data boundary (no I/O in enrichment) is structurally enforced by the function signature

### Requirements Coverage Validation ✅

**Functional Requirements (42/42 covered):**

| FR Category | FRs | Architecture Support |
|------------|-----|---------------------|
| Section Detection | FR1-FR15 | Each maps to a `_check_*` function + `_parse_sections` + `_SECTION_PATTERN` |
| Finding Production | FR16-FR22 | `Finding` dataclass (FR16-17, FR22), orchestrator patterns (FR18-FR21) |
| Rule Management | FR23-FR25 | Literal rule IDs in `_check_*`, taxonomy table, 14→10 mapping |
| Configuration | FR26-FR31 | Orchestrator config gating, `_check_missing_examples` list access, `_SECTION_HEADERS` constant |
| Symbol Analysis | FR32-FR38 | `_build_node_index` + body walk (FR32-33), `file_path` context (FR34), `_parse_sections` (FR35-36), docstring skip (FR37), defensive design (FR38) |
| Integration | FR39-FR42 | `check_enrichment` signature (FR39-40), `checks/__init__.py` export (FR41), CLI stub wiring (FR42) |

**Non-Functional Requirements (19/19 covered):**

| NFR Category | NFRs | Architecture Support |
|-------------|------|---------------------|
| Performance | NFR1-4 | Single-pass node index, compiled regex, stateless per-file processing, no cross-file state |
| Correctness | NFR5-9 | Lenient regex (false negatives > false positives), pure function design, defensive gates, actionable message conventions |
| Maintainability | NFR10-13 | Private function per rule, 3-file change ceiling via module structure, dual testing strategy, existing CI gates |
| Compatibility | NFR14-16 | Stdlib-only approach, no platform-specific code, no new deps |
| Integration | NFR17-19 | Frozen `Finding` dataclass, `_run_enrichment` stub, backward-compatible `require_attributes` default |

### Implementation Readiness Validation ✅

**Decision Completeness:**
- All 5 decisions include rationale, code examples, and anti-patterns
- Uniform `_check_*` signature specified with exact type annotations
- Prerequisite PRs identified with specific scope (config toggle, `Finding` dataclass)
- Implementation sequence numbered 1-7 with cross-decision dependencies mapped
- Config gating exception (`require_examples` list) explicitly documented
- Each `_check_*` function includes a test case where `node_index.get(symbol.line)` returns `None`, confirming the defensive early-return path (module-level symbols, decorator-only symbols, etc.)

**Structure Completeness:**
- File tree shows every new/modified file with markers
- Import paths specified for all cross-module dependencies
- FR→file mapping table covers all 42 FRs
- Rule→function mapping table covers all 10 rules with node index usage and helpers

**Pattern Completeness:**
- AST inspection patterns cover all node types: `ast.Raise`, `ast.Yield`, `ast.Call`, `ast.Name`, `ast.Attribute`, decorator handling, base class inspection, `self.*` assignment detection
- `missing-attributes` branch 4 nested walk explicitly called out as highest-complexity area
- `missing-other-parameters` uses signature-only access (`node.args.kwarg`), distinct from body walk rules
- Dual testing strategy differentiates simple rules (through orchestrator) from complex rules (direct + helper testing)
- Body-walk rules (`missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`) retrieve the function node via `node_index.get(symbol.line)` and use scope-aware iterative walk (not `ast.walk()`) to avoid nested scope false positives

### Gap Analysis Results

**Critical Gaps:** 0 — No missing decisions that block implementation.

**Important Gaps:** 0

1. **`missing-cross-references` detection criteria — RESOLVED.** Previously undefined (flagged as weakest FR, S=3/M=3/A=3/R=3). Now formally specified below.

   **Cross-Reference Syntax Definition (FR12)**

   Targets mkdocs-material + mkdocstrings (autorefs plugin) conventions. A `See Also:` section is considered to contain valid cross-references if **any line** matches at least one of these patterns:

   | Pattern | Example | Convention |
   |---------|---------|------------|
   | Backtick-quoted identifier | `` `qualified.name` `` | mkdocstrings autorefs |
   | Markdown reference link | `[text][identifier]` or `[identifier][]` | Markdown / mkdocs |
   | Sphinx/intersphinx role | `` :role:`target` `` | Sphinx interop |

   **Detection regex patterns:**
   ```
   `[^`]+`              — backtick-quoted identifier
   \[[^\]]+\]\[         — Markdown reference link opening
   :\w+:`[^`]+`         — Sphinx/intersphinx role
   ```

   **Detection logic:** If a `See Also:` section exists and contains **no lines** matching any of the above patterns, fire `missing-cross-references` finding. This is a docstring-only check (no AST body walk needed).

**Scope Boundaries (not gaps):**

1. **Decorator detection scope.** MVP supports `@dataclass` and `@dataclasses.dataclass` forms only — aliased imports (`from dataclasses import dataclass as dc`) are explicitly out of MVP scope.
2. **`async` generator edge cases.** `async for`/`async with` patterns and their interaction with `missing-yields`/`missing-receives` are not explicitly addressed. The `ast.walk()` approach handles `ast.AsyncFunctionDef` but the specific `ast.Yield` vs `ast.YieldFrom` distinction within async generators could be clarified in the tech spec.

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed (42 FRs, 19 NFRs, 5 journeys)
- [x] Scale and complexity assessed (medium, CLI single-process)
- [x] Technical constraints identified (no new deps, Google-style only, caller handles SyntaxError)
- [x] Cross-cutting concerns mapped (config toggle respect, no-docstring skip, malformed resilience, deduplication)

**✅ Architectural Decisions**

- [x] 5 critical/important decisions documented with rationale and code examples
- [x] Technology stack constrained to stdlib `ast` + `re` + existing `ast_utils`
- [x] Integration patterns defined (CLI ↔ enrichment, enrichment ↔ config, enrichment ↔ ast_utils)
- [x] Performance addressed (single-pass node index, compiled regex, stateless processing)

**✅ Implementation Patterns**

- [x] Naming conventions established (`_check_*`, `_build_*`, `_parse_*`, `_has_*`, `_is_*`)
- [x] Structure patterns defined (file organization order, taxonomy-table ordering)
- [x] AST inspection patterns specified (isinstance, ast.walk vs .body, decorator/base class handling)
- [x] Process patterns documented (finding construction, orchestrator dispatch, config gating)

**✅ Project Structure**

- [x] Complete directory structure with NEW/MODIFIED markers
- [x] Component boundaries established (public API, module dependencies, data boundary)
- [x] Integration points mapped (CLI, config, ast_utils)
- [x] Requirements-to-structure mapping complete (FR→file table, rule→function table)

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Complete FR and NFR coverage with no critical gaps
- All decisions interlock coherently — no contradictions or incompatibilities
- Code examples and anti-patterns provide clear implementation guidance for AI agents
- Prerequisite PRs cleanly isolate dependencies from the main implementation
- Defensive error handling eliminates crash paths by design rather than exception catching
- Dual testing strategy appropriately scales test depth with rule complexity

**Areas for Future Enhancement:**
- Cross-reference syntax definition (deferred to tech spec — structural support is in place)
- Decorator alias detection (explicit MVP scope boundary — can be added per NFR11's 3-file ceiling)
- Message truncation thresholds for long evidence lists (explicitly deferred to post-MVP)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently — taxonomy-table order, uniform signatures, literal strings
- Respect project structure and boundaries — no cross-check imports, no I/O in enrichment
- Refer to this document for all architectural questions before escalating

**First Implementation Priority:**
1. Prerequisite PR 1: `require_attributes` config toggle
2. Prerequisite PR 2: `checks/__init__.py` with `Finding` dataclass
3. Main enrichment PR: `check_enrichment` + 10 `_check_*` functions + tests

---

## Freshness Module — Project Context Analysis

_This section extends the architecture document to cover the freshness check (Layer 4: accuracy). All enrichment content above is preserved and unchanged._

### Freshness Requirements Overview

**Functional Requirements:**
26 FRs (FR43-FR68) across 6 categories. The freshness module is a pair of pure functions that detect stale docstrings by combining git output parsing with AST line-to-symbol mapping. Key architectural groupings:

- **Diff Mode Detection (FR43-FR49):** 7 FRs defining the hunk-to-symbol pipeline — parse git diff, map changed lines to symbols, classify by range (signature/body/import), assign severity
- **Drift Mode Detection (FR50-FR54):** 5 FRs defining the blame-to-symbol pipeline — parse git blame line-porcelain, group timestamps by symbol, compare code vs docstring ages. Drift-specific edge cases (uncommitted files, symbols with only a docstring, boundary timestamps) are documented at the Technical Guidance level in the PRD, not elevated to FRs — this is a scope boundary, not a gap
- **Edge Cases (FR55-FR58):** 4 FRs defining diff mode boundary behavior — new files, deleted symbols, within-file moves, non-Python files
- **Finding Production (FR59-FR62):** 4 FRs defining output shape — reuses existing `Finding` dataclass (which self-validates via `__post_init__`), deduplication (highest severity per symbol), zero-finding guarantees
- **Configuration (FR63-FR65):** 3 FRs defining drift thresholds — `drift-threshold` (days), `age-threshold` (days), defaults
- **Integration (FR66-FR68):** 3 FRs defining the public API contract — pure functions, CLI wiring, mode selection

**Non-Functional Requirements:**
13 NFRs (NFR20-NFR32) across 5 categories that directly shape freshness architecture:

- **Performance (NFR20-22):** Sub-100ms per file for diff mode, no overhead beyond timestamp parsing for drift, linear memory — enforces stateless per-file processing (same invariant as enrichment). Note: existing `map_lines_to_symbols` uses O(n*m) approach (lines × symbols) — adequate for NFR20 on typical files but flagged as post-MVP optimization candidate for large files
- **Correctness (NFR23-26):** Non-signature changes never produce HIGH severity, deterministic output, crash-proof on malformed git output, actionable messages — enforces defensive parsing with fail-safe empty returns
- **Maintainability (NFR27-28):** Diff and drift independently testable with mocked strings, 3-file change ceiling for new rules — enforces modular structure parallel to enrichment
- **Compatibility (NFR29-30):** Git 2.x output format, `git diff` and `git diff --cached` handled identically — eliminates version-specific code paths
- **Integration (NFR31-32):** Frozen `Finding` shape reused without modification, no cross-check imports — constrains API surface identically to enrichment

**Scale & Complexity:**

- Primary domain: CLI developer tool (single-process, file-at-a-time) — same as enrichment
- Complexity level: Medium (lower than enrichment — 2 functions vs 10 rules, but git output parsing introduces a new domain with its own edge cases)
- Estimated architectural components: ~4 internal components (diff parser, blame parser, line classifier, finding builder)

### Freshness Technical Constraints & Dependencies

- **All shared infrastructure already implemented** (no prerequisite PRs needed — the PRD's prerequisite list is stale):
  - `Symbol` dataclass with `signature_range`, `body_range`, `docstring_range` fields (`ast_utils.py:16-47`)
  - `map_lines_to_symbols(tree)` (`ast_utils.py:264-292`)
  - `Finding` frozen dataclass with `__post_init__` self-validation (`checks/__init__.py:19-65`)
  - `FreshnessConfig` with `drift_threshold` and `age_threshold` (`config.py:16-20`)
  - `_run_freshness` CLI stub in `cli.py`
- **Caller provides git output as strings** — `check_freshness_diff` and `check_freshness_drift` do not call git subprocesses; the CLI handles all I/O
- **Two public functions, not one** — diff and drift have fundamentally different inputs, outputs, and usage patterns. This has a testing implication: integration tests need two structurally different git repo fixture setups (staged/unstaged changes for diff, committed history with blame data for drift)
- **No new runtime dependencies** — stdlib `ast`, `re`, `time` + existing `ast_utils`
- **No cross-check imports** — freshness depends only on `checks.Finding` and `ast_utils`
- **`Finding` self-validates** — `__post_init__` enforces non-empty strings, positive line numbers, and valid category values. Freshness finding construction does not need redundant validation

### Freshness Cross-Cutting Concerns

- **Git output parsing resilience (highest-risk area):** Both functions must handle specific git output edge cases without crashing — empty list return on unparseable input (mirrors enrichment's `_parse_sections` empty-set pattern). Known edge cases to handle:
  - **Diff mode:** binary file markers (`Binary files ... differ`), rename headers (`rename from`/`rename to`), combined diffs from merge commits, `--- /dev/null` for new files, diff output with no hunks
  - **Drift mode:** boundary commits (initial commit markers), uncommitted changes (zero SHA), empty blame output for new/untracked files, non-UTF-8 content lines
- **No-docstring skip:** Both modes skip symbols with `docstring_range is None` — undocumented symbols cannot have stale docstrings (presence checking is interrogate's domain)
- **One-finding-per-symbol deduplication:** Diff mode: highest severity wins per symbol (signature > body > import). Drift mode: up to two findings per symbol (`stale-drift` and `stale-age` are independent checks)
- **Severity-to-category mapping:** Baked into rule definitions, not dynamic. `stale-signature` → `"required"`, all others → `"recommended"`

## Freshness Core Architectural Decisions

### Freshness Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. Internal module organization (mode-oriented single file)
2. Git diff hunk parsing strategy (line-by-line iteration)
3. Git blame timestamp parsing strategy (line-by-line state machine)
4. Line classification & severity assignment (partition-then-decide)

**Important Decisions (Shape Architecture):**
5. Finding message format (two patterns — diff and drift)
6. Error handling strategy (defensive by design, no try/except)

**Deferred Decisions (Post-MVP):**
- Per-rule disable toggles for diff mode (e.g., `ignore-stale-import = true`)
- Hunk-level precision in finding messages (show exactly which lines changed)
- Auto-fix suggestions for stale `Args:` sections
- Graduate `freshness.py` to sub-package when >2000 lines or when growth features introduce a third public entry point

### Freshness Decision 1: Internal Module Organization

**Decision:** Mode-oriented sections within a single `freshness.py` file

Industry research (ruff, mypy, pylint, flake8, pyright) confirms the consensus: **start flat, split when there's a concrete reason.** Flake8's pycodestyle has two modes (`logical` and `physical`) as two functions in the same file — directly parallel to freshness. Pylint's split trigger is "multiple checker classes," not file size. Enrichment is ~1,243 lines in one file. Freshness is estimated at ~560 lines — well within single-file comfort.

**File organization within `freshness.py`:**
1. Module docstring
2. `from __future__ import annotations`
3. Stdlib imports (`ast`, `re`, `time`)
4. Local imports (`from docvet.ast_utils import ...`, `from docvet.checks import Finding`, `from docvet.config import FreshnessConfig`)
5. Module-level constants (severity/category mappings, regex patterns)
6. Shared helper functions (`_build_finding`)
7. Diff mode helpers (`_parse_diff_hunks`, `_classify_changed_lines`)
8. `check_freshness_diff` public function
9. Drift mode helpers (`_parse_blame_timestamps`, `_compute_drift`, `_compute_age`)
10. `check_freshness_drift` public function

**Rationale:** One file per check module, consistent with enrichment. Mode-oriented grouping supports top-to-bottom readability — a reviewer can read all diff logic or all drift logic without jumping. Two public functions at the mode boundaries make the API surface immediately visible.

**Anti-patterns:**
- `checks/freshness/__init__.py` + `diff.py` + `drift.py` — premature sub-packaging, breaks one-file-per-check pattern
- Interleaving diff and drift helpers — makes mode boundaries unclear
- A single `check_freshness(mode=...)` dispatcher function — obscures the fundamentally different inputs and signatures

### Freshness Decision 2: Git Diff Hunk Parsing Strategy

**Decision:** Line-by-line iteration returning `set[int]`

```python
def _parse_diff_hunks(diff_output: str) -> set[int]:
```

Iterates lines of the raw diff output in a single pass:
- Detects `--- /dev/null` → sets `is_new_file` flag, returns empty set (FR55)
- Detects `Binary files` → returns empty set (FR58)
- Detects `@@ ... +(\d+)(?:,(\d+))? @@` hunk headers → extracts `(start, count)` ranges
- Expands ranges to individual line numbers: `range(start, start + count)`
- Skips rename headers, mode change lines, and other non-hunk content silently
- Returns `set[int]` of all changed line numbers in the current file version

**Rationale:** Single pass handles all edge cases naturally — new file detection, binary file skipping, and hunk extraction happen in the same iteration without requiring separate pre-filtering. Returns `set[int]` for O(1) membership testing in downstream `_classify_changed_lines`. Mirrors enrichment's approach where `_parse_sections` does one pass over docstring text.

**Why not `re.findall` on the whole string:** Would capture hunk headers but miss `--- /dev/null` and `Binary files` markers, requiring a second pass for edge case detection.

### Freshness Decision 3: Git Blame Timestamp Parsing Strategy

**Decision:** Line-by-line state machine returning `dict[int, int]`

```python
def _parse_blame_timestamps(blame_output: str) -> dict[int, int]:
```

Parses `git blame --line-porcelain` format using a simple state machine:
- SHA line: `line.split()` → extract `final_line` (3rd field) as current line number
- `author-time` line: `startswith("author-time")` → extract Unix timestamp
- Tab-prefixed content line: marks end of block, emit `{line_number: timestamp}` mapping
- Silently skip all other header fields (`author`, `author-mail`, `committer`, etc.)

Returns `dict[int, int]` mapping 1-based line numbers to Unix timestamps.

**Edge case handling:**
- Empty input → return empty dict immediately
- Boundary commits (initial commit) → parsed normally, `author-time` is still present
- Uncommitted changes (zero SHA `0000000...`) → parsed normally, `author-time` reflects working copy time
- Lines that don't match expected format → silently skipped

**Rationale:** Blame porcelain format is structured and sequential — a state machine is the natural fit. No regex needed for the SHA line (positional split). Minimal regex for `author-time` extraction. Single pass, O(n) with line count.

### Freshness Decision 4: Line Classification & Severity Assignment

**Decision:** Partition-then-decide with priority-ordered early returns

```python
def _classify_changed_lines(
    changed_lines: set[int],
    symbol: Symbol,
) -> str | None:
```

For a given symbol, classifies its changed lines and returns a severity string:

1. Compute intersection of `changed_lines` with each symbol range
2. If any changed line in `symbol.docstring_range` → return `None` (docstring updated, suppress finding)
3. If any changed line in `symbol.signature_range` → return `"signature"` (HIGH → `"required"`)
4. If any changed line in `symbol.body_range` → return `"body"` (MEDIUM → `"recommended"`)
5. Otherwise → return `"import"` (LOW → `"recommended"`)

**Rationale:** Priority order matches the PRD's "highest severity wins" rule. The docstring-change check as the first gate is the most important behavior — it suppresses the entire finding when the developer updated the docstring alongside the code. Single function, no intermediate data structures, deterministic output. The `str | None` return type mirrors enrichment's `Finding | None` pattern — `None` means "no finding."

**Note:** `symbol.signature_range` is `None` for classes and modules (they have no `def` line). When `None`, step 3 is skipped — class body changes produce `"body"` (MEDIUM), not `"signature"` (HIGH). This correctly reflects that a class has no signature to become stale.

### Freshness Decision 5: Finding Message Format

**Decision:** Two patterns — diff mode and drift mode — with per-function message ownership

**Diff mode messages:**
`{SymbolKind} '{name}' {change_type} changed but docstring not updated`

Examples:
- `Function 'send_request' signature changed but docstring not updated`
- `Method 'process' body changed but docstring not updated`
- `Function 'parse' imports/formatting changed but docstring not updated`

**Drift mode messages — `stale-drift`:**
`{SymbolKind} '{name}' code modified {code_date}, docstring last modified {doc_date} ({N} days drift)`

Example:
- `Function 'process_batch' code modified 2025-12-14, docstring last modified 2025-10-02 (73 days drift)`

**Drift mode messages — `stale-age`:**
`{SymbolKind} '{name}' docstring untouched since {doc_date} ({N} days)`

Example:
- `Function 'validate_schema' docstring untouched since 2025-09-15 (147 days)`

**Rationale:** Messages name the symbol, the issue, and evidence (change type for diff, dates/days for drift). Actionable without additional context (NFR26). Drift messages include both dates and day counts — dates for human context, day counts for threshold comparison. Per-function message ownership, same as enrichment's Decision 4.

### Freshness Decision 6: Error Handling Strategy

**Decision:** Defensive by design, no try/except — identical pattern to enrichment's Decision 5

Three defensive gates eliminate crash paths without exception handling:

1. **`_parse_diff_hunks()`** — line iteration with format checks, returns empty `set[int]` on empty/unparseable input (never raises)
2. **`_parse_blame_timestamps()`** — state machine with format checks, returns empty `dict[int, int]` on empty/unparseable input (never raises)
3. **Both public functions** — return `[]` immediately on empty git output string, before calling any parser

Additional gate: during line iteration, lines that don't match expected format are silently skipped (binary markers, rename headers, corrupted lines). This produces false negatives (missed findings) rather than crashes — safe direction, consistent with enrichment's NFR5 → freshness's NFR25.

No try/except in any function. Malformed git output produces zero findings, not crashes. Production hardening (orchestrator-level catch-all) deferred to post-MVP, same as enrichment.

**Rationale:** Correctness through design, not exception catching. If a parser has a logic error, it should crash in tests so it gets fixed. The three defensive gates cover all known edge cases identified in the cross-cutting concerns analysis.

### Freshness Decision Impact Analysis

**Implementation Sequence:**
1. Module-level constants and `_build_finding` shared helper (Decisions 1, 5)
2. `_parse_diff_hunks` function (Decision 2, 6)
3. `_classify_changed_lines` function (Decision 4)
4. `check_freshness_diff` public orchestrator (Decisions 1, 4, 5)
5. `_parse_blame_timestamps` function (Decision 3, 6)
6. `_compute_drift` and `_compute_age` helpers (Decision 4)
7. `check_freshness_drift` public orchestrator (Decisions 1, 5)

**Cross-Decision Dependencies:**
- Decision 1 (module org) defines the file layout that all other decisions fill in
- Decision 2 (diff parsing) produces the `set[int]` consumed by Decision 4 (classification)
- Decision 3 (blame parsing) produces the `dict[int, int]` consumed by drift helpers
- Decision 4 (classification) produces the severity string consumed by Decision 5 (message format)
- Decision 6 (error handling) shapes how Decisions 2 and 3 handle edge cases
- All decisions depend on existing `Symbol` range fields from `ast_utils.py` — no prerequisite work needed

## Freshness Implementation Patterns & Consistency Rules

### Freshness Naming Patterns

**Private function naming:**
- Diff mode: `_parse_diff_hunks`, `_classify_changed_lines`
- Drift mode: `_parse_blame_timestamps`, `_compute_drift`, `_compute_age`
- Shared: `_build_finding`
- Pattern: `_parse_*` for text parsing, `_classify_*` for categorization, `_compute_*` for calculations, `_build_*` for construction
- **Anti-pattern:** `_process_diff`, `_handle_blame`, `_get_severity` — generic verbs that don't describe the operation

**Constants:**
- Rule identifiers as string literals: `"stale-signature"`, `"stale-body"`, `"stale-import"`, `"stale-drift"`, `"stale-age"`
- Hunk header regex: `_HUNK_PATTERN = re.compile(r"^@@ .+\+(\d+)(?:,(\d+))? @@")`
- Private constants prefixed with `_` (not exported), `ALL_CAPS_WITH_UNDER` at module level
- **Anti-pattern:** Enum classes for severity or rule IDs — overkill for 5 string literals, inconsistent with enrichment

**Symbol kind display names:**
- Use `symbol.kind.capitalize()` for messages: `"Function"`, `"Class"`, `"Method"`, `"Module"`
- Same pattern as enrichment's finding messages

### Freshness Structure Patterns

**Source ordering (defined in Decision 1), with additional constraints:**

- `check_freshness_diff` appears before `check_freshness_drift` — diff mode is the primary workflow
- Each public function's helpers appear directly above it — no forward references to helpers defined later in the file
- Constants at top, shared helpers next, then diff block, then drift block

**Test organization:**
- `tests/unit/checks/test_freshness.py` — single test file, matching source structure
- Test naming: `test_{rule_id}_when_{condition}_returns_{expected}` (same as enrichment)
- Test grouping by mode: diff mode tests first, drift mode tests second
- Mocked git output as multiline strings in test functions, not external fixture files — keeps tests self-contained and readable
- Integration tests in `tests/integration/test_freshness_diff.py` and `tests/integration/test_freshness_drift.py` — separate files because they need different git repo fixtures

### Freshness Git Output Parsing Patterns

**Line iteration idiom:**
```python
for line in diff_output.splitlines():
    if line.startswith("Binary files"):
        return set()
    # ... etc
```
- Always use `.splitlines()`, not `.split("\n")` — handles `\r\n` on Windows
- Early returns for whole-file skip conditions (binary, new file)
- Silent skip for unrecognized lines — no warnings, no exceptions

**Range expansion idiom:**
```python
match = _HUNK_PATTERN.match(line)
if match:
    start = int(match.group(1))
    count = int(match.group(2) or "1")  # missing count means 1 line
    changed.update(range(start, start + count))
```

**Set intersection for range checks:**
```python
changed_in_sig = changed_lines & set(range(sig_start, sig_end + 1))
```
- Use `&` (set intersection) for readability over iteration
- Ranges are inclusive on both ends (matching `Symbol` range convention)

### Freshness Finding Construction Pattern

**All finding construction uses `_build_finding` shared helper:**

```python
def _build_finding(
    file_path: str,
    symbol: Symbol,
    rule: str,
    message: str,
    category: Literal["required", "recommended"],
) -> Finding:
    return Finding(
        file=file_path,
        line=symbol.line,
        symbol=symbol.name,
        rule=rule,
        message=message,
        category=category,
    )
```

- `file` is always `file_path` (passed through, not computed)
- `line` is always `symbol.line` (not a changed line number)
- `symbol` is always `symbol.name`
- `rule` is always a string literal from the 5-rule taxonomy
- `category` is always a string literal — `"required"` for `stale-signature`, `"recommended"` for all others
- **Anti-pattern:** Constructing `Finding` directly in each function, computing line from diff hunks

**Why a shared helper (different from enrichment):** Enrichment's 10 `_check_*` functions each construct findings inline because message format varies per rule. Freshness has only 5 rules with less message variation, and the `file_path → file`, `symbol.line → line`, `symbol.name → symbol` mapping is mechanical. A shared helper eliminates duplication and ensures consistency.

### Freshness Enforcement Guidelines

**All AI agents implementing freshness MUST:**
- Follow the file organization order (constants → shared → diff block → drift block)
- Use `.splitlines()` for git output parsing, never `.split("\n")`
- Use set operations for range intersection checks
- Construct findings via `_build_finding`, not inline `Finding()`
- Use string literals for rule identifiers and categories — no enums, no variables
- Return empty list/set/dict on empty input — never `None`
- Silently skip unrecognized git output lines — no warnings, no exceptions
- Use `symbol.kind.capitalize()` in finding messages

**Pattern verification:** ruff + ty enforce naming, import order, and type consistency. Test coverage (>=90% on `freshness.py`) enforces behavioral correctness.

## Freshness Project Structure & Boundaries

### Updated Project Directory Structure

Existing files shown as-is. **New files for freshness** marked with `← NEW`.

```
src/docvet/
├── __init__.py
├── cli.py                    # _run_freshness stub (wired in separate CLI story)
├── config.py                 # FreshnessConfig (existing, no changes needed)
├── discovery.py
├── ast_utils.py              # Symbol, map_lines_to_symbols (existing, no changes needed)
├── reporting.py
└── checks/
    ├── __init__.py            # Finding dataclass (shared, no changes needed)
    ├── enrichment.py          # check_enrichment (existing, no changes needed)
    └── freshness.py           ← NEW (check_freshness_diff + check_freshness_drift)

tests/
├── conftest.py               # parse_source factory (existing)
├── unit/
│   ├── test_config.py
│   ├── test_ast_utils.py
│   └── checks/
│       ├── __init__.py
│       ├── test_enrichment.py
│       └── test_freshness.py  ← NEW (all freshness rule tests, mocked git output)
├── integration/
│   ├── conftest.py            # Git repo fixtures (existing + new freshness helpers)
│   ├── test_freshness_diff.py  ← NEW (real git repos, staged/unstaged changes)
│   └── test_freshness_drift.py ← NEW (real git repos, committed history + blame)
└── fixtures/
    ├── complete_module.py
    ├── missing_raises.py
    └── missing_yields.py
```

**Scope clarification:** The main freshness PR adds 1 source file (`checks/freshness.py`) and 3 test files. No modifications to existing source files. CLI wiring (`_run_freshness` stub replacement, `git diff`/`git blame` subprocess calls) is a **separate integration story** — same pattern as enrichment, where `_run_enrichment` was wired after the main enrichment PR.

### Freshness Architectural Boundaries

**Public API boundary:**
- `check_freshness_diff(file_path, diff_output, tree) -> list[Finding]` — public function #1
- `check_freshness_drift(file_path, blame_output, tree, config, *, now=None) -> list[Finding]` — public function #2
- Everything else in `freshness.py` is private (`_` prefixed)

**Config asymmetry (design invariant, not accident):**
- `check_freshness_diff` has **zero config dependency** — severity logic is fully determined by the inputs (what changed). No thresholds, no toggles. This is intentional: diff mode behavior should be deterministic and non-configurable.
- `check_freshness_drift` takes `FreshnessConfig` — drift detection requires `drift_threshold` and `age_threshold`. The function also accepts an optional `now` parameter (Unix timestamp) for test determinism, defaulting to `time.time()`.

**Module dependency boundary:**
```
cli.py (separate wiring story)
  → imports check_freshness_diff, check_freshness_drift from docvet.checks.freshness
  → imports Finding from docvet.checks
  → imports FreshnessConfig from docvet.config
  → runs git diff / git blame via subprocess, passes output strings to freshness

checks/freshness.py (main freshness PR)
  → imports Finding from docvet.checks
  → imports Symbol, map_lines_to_symbols from docvet.ast_utils
  → imports FreshnessConfig from docvet.config (drift mode only)
  → NEVER imports from docvet.cli, docvet.discovery, or checks.enrichment
```

**Data boundary:**
- No I/O inside freshness — pure functions, no file reads, no subprocess calls
- `diff_output` and `blame_output` are strings provided by the CLI
- `tree` provided by caller (CLI reads file and calls `ast.parse`)
- `file_path` is a string for `Finding.file` construction — freshness never opens it

### Freshness Requirements to Structure Mapping

**FR Category → File Mapping:**

| FR Category | Primary File | Supporting Files |
|------------|-------------|-----------------|
| Diff Mode Detection (FR43-FR49) | `checks/freshness.py` (`_parse_diff_hunks`, `_classify_changed_lines`, `check_freshness_diff`) | `ast_utils.py` (`map_lines_to_symbols`, `Symbol`) |
| Drift Mode Detection (FR50-FR54) | `checks/freshness.py` (`_parse_blame_timestamps`, `_compute_drift`, `_compute_age`, `check_freshness_drift`) | `ast_utils.py` (`map_lines_to_symbols`, `Symbol`) |
| Edge Cases (FR55-FR58) | `checks/freshness.py` (handled within `_parse_diff_hunks` and `check_freshness_diff`) | — |
| Finding Production (FR59-FR62) | `checks/__init__.py` (`Finding` dataclass, existing) | `checks/freshness.py` (`_build_finding`) |
| Configuration (FR63-FR65) | `config.py` (`FreshnessConfig`, existing) | `checks/freshness.py` (`check_freshness_drift` consumes config) |
| Integration (FR66-FR68) | `cli.py` (`_run_freshness` stub, separate story) | `checks/freshness.py` (`check_freshness_diff`, `check_freshness_drift`) |

**Rule → Internal Function Mapping:**

| Rule | Public Function | Key Helpers | Severity | Category |
|------|----------------|-------------|----------|----------|
| `stale-signature` | `check_freshness_diff` | `_parse_diff_hunks`, `_classify_changed_lines` | HIGH | `"required"` |
| `stale-body` | `check_freshness_diff` | `_parse_diff_hunks`, `_classify_changed_lines` | MEDIUM | `"recommended"` |
| `stale-import` | `check_freshness_diff` | `_parse_diff_hunks`, `_classify_changed_lines` | LOW | `"recommended"` |
| `stale-drift` | `check_freshness_drift` | `_parse_blame_timestamps`, `_compute_drift` | — | `"recommended"` |
| `stale-age` | `check_freshness_drift` | `_parse_blame_timestamps`, `_compute_age` | — | `"recommended"` |

### Freshness Data Flow

```
CLI (_run_freshness) — separate wiring story
  │
  │  For diff mode:
  │    runs git diff (or git diff --cached) → diff_output: str
  │    reads file → source: str
  │    ast.parse(source) → tree: ast.Module
  │
  │  For drift mode:
  │    runs git blame --line-porcelain → blame_output: str
  │    reads file → source: str
  │    ast.parse(source) → tree: ast.Module
  │    loads config → config.freshness: FreshnessConfig
  │
  ▼
check_freshness_diff(file_path, diff_output, tree)
  │
  │  _parse_diff_hunks(diff_output) → changed_lines: set[int]
  │  if not changed_lines: return []
  │  map_lines_to_symbols(tree) → line_map: dict[int, Symbol]
  │
  │  Invert line_map: for each line in changed_lines,
  │    look up line_map.get(line), accumulate into
  │    symbol_changes: dict[Symbol, set[int]]
  │
  ▼
  for each (symbol, its_changed_lines) in symbol_changes:
  │  skip if symbol.docstring_range is None
  │  _classify_changed_lines(its_changed_lines, symbol) → severity: str | None
  │  if severity is not None:
  │    _build_finding(file_path, symbol, rule, message, category)
  │
  ▼
list[Finding] returned to CLI

check_freshness_drift(file_path, blame_output, tree, config, *, now=None)
  │
  │  _parse_blame_timestamps(blame_output) → timestamps: dict[int, int]
  │  if not timestamps: return []
  │  map_lines_to_symbols(tree) → line_map: dict[int, Symbol]
  │
  │  Group timestamps by symbol: for each (line, ts),
  │    look up line_map.get(line), partition into
  │    code_timestamps vs docstring_timestamps per symbol
  │
  ▼
  for each symbol with timestamps:
  │  skip if symbol.docstring_range is None
  │  _compute_drift(code_ts, doc_ts, config.drift_threshold) → bool
  │  _compute_age(doc_ts, now or time.time(), config.age_threshold) → bool
  │  emit 0-2 findings per symbol (stale-drift, stale-age independent)
  │
  ▼
list[Finding] returned to CLI
```

### Freshness Integration Points

**Freshness ↔ CLI integration (separate wiring story):**
- CLI calls `check_freshness_diff` once per file in diff mode (file-at-a-time processing)
- CLI calls `check_freshness_drift` once per file in drift mode
- **CLI must run git subprocess calls** and pass raw output strings — freshness performs no I/O
- **CLI must wrap `ast.parse()` in try/except SyntaxError** — files that fail to parse are skipped
- CLI aggregates `list[Finding]` across files
- CLI applies `fail-on` / `warn-on` logic to determine exit code

**Freshness ↔ Config integration:**
- `FreshnessConfig` loaded once by CLI, passed to every `check_freshness_drift` call
- `check_freshness_diff` has no config dependency — zero config awareness by design
- Missing `[tool.docvet.freshness]` section → defaults (30 days drift, 90 days age)

**Freshness ↔ AST Utils integration:**
- `map_lines_to_symbols` is the primary `ast_utils` function called
- `Symbol` dataclass consumed for line ranges and metadata
- No freshness-specific changes to `ast_utils.py`

**Testing integration:**
- **Unit tests:** Mocked git output as multiline strings in test functions (self-contained, no external fixture files)
- **Integration tests:** Real git repos via `tmp_path` + shared fixture helpers in `tests/integration/conftest.py`
  - Diff mode fixtures: `make_commit_with_diff(tmp_path, original_content, modified_content)` — creates a repo with one file, commits original, modifies, returns diff output
  - Drift mode fixtures: `make_repo_with_blame_history(tmp_path, commits)` — creates a repo with sequential commits at controlled timestamps, returns blame output
- **Primary integration testing approach:** Capture real git output, pass to freshness functions directly (function-level, not CLI runner). CLI end-to-end tests are a separate concern.
