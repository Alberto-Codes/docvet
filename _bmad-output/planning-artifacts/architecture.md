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
  - 'griffe-2'
  - 'griffe-3-skipped'
  - 'griffe-4'
  - 'griffe-5'
  - 'griffe-6'
  - 'griffe-7'
  - 'griffe-8'
lastStep: 'griffe-8'
status: 'complete'
completedAt: '2026-02-09'
freshnessStartedAt: '2026-02-09'
griffeStartedAt: '2026-02-11'
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

---

## Griffe Compatibility Module — Project Context Analysis

_This section extends the architecture document to cover the griffe compatibility check (Layer 5: rendering). All enrichment, freshness, and coverage content above is preserved and unchanged._

### Griffe Requirements Overview

**Functional Requirements:**
17 FRs (FR81-FR97) across 5 categories. The griffe module is a single pure function (with filesystem I/O caveat) that detects rendering compatibility issues by loading a Python package via the griffe library and capturing parser warnings. Key architectural groupings:

- **Detection (FR81-FR85):** 5 FRs defining the warning capture pipeline — load package via griffe, capture parser warnings via logging handler, filter to discovered files. Three detection scenarios: missing type annotations (FR81), unknown parameters (FR82), formatting issues (FR83)
- **Finding Production (FR86-FR89):** 4 FRs defining output shape — reuses existing `Finding` dataclass, pattern-based rule classification (FR87), one finding per warning not per symbol (FR88), zero-finding guarantees (FR89)
- **Edge Cases (FR90-FR93):** 4 FRs defining graceful degradation — griffe not installed (FR90), package load failures (FR91), unrecognized warnings from future griffe versions (FR92), all files filtered out (FR93)
- **Integration (FR94-FR97):** 4 FRs defining the public API contract — accepts `src_root` + `files` (FR94), CLI wiring (FR95), temporary logging handler lifecycle (FR96), CLI-level griffe availability detection with verbose messaging (FR97)

**Non-Functional Requirements:**
10 NFRs (NFR39-NFR48) across 5 categories that directly shape griffe architecture:

- **Performance (NFR39-40):** Sub-10s for 200-file package, negligible overhead beyond griffe's own loading — performance is entirely griffe-dominated, docvet adds only warning mapping
- **Correctness (NFR41-43):** Zero findings on well-documented code, zero findings and no exceptions when griffe not installed, unrecognized warnings classified as `griffe-format-warning` not dropped
- **Maintainability (NFR44-45):** Testable with mocked logging output (no actual package loading needed), 2-file change ceiling for new rules (no config file)
- **Compatibility (NFR46):** Works with griffe 1.x releases, uses only stable public APIs
- **Integration (NFR47-48):** Frozen `Finding` shape reused, no cross-check imports

**Scale & Complexity:**

- Primary domain: CLI developer tool (single-process) — same as other checks
- Complexity level: Low-Medium (simpler logic than enrichment/freshness, but introduces a new integration domain: griffe API + Python logging)
- Estimated architectural components: ~3 internal components (warning capture handler, warning classifier, finding mapper)

**Architectural distinction from other checks:**
Griffe operates at the **package level** — it loads entire packages via `griffe.load()`, not individual files. This is fundamentally different from enrichment (per-file AST), freshness (per-file git output), and coverage (per-file filesystem walk). The `files` parameter acts as a post-load filter, not a per-file processing target. This means griffe always loads the full package even in `--staged` mode — performance is not proportional to file count.

### Griffe Technical Constraints & Dependencies

- **All shared infrastructure already implemented** (no prerequisite PRs needed):
  - `Finding` frozen dataclass with `__post_init__` self-validation (`checks/__init__.py`)
  - `_run_griffe` CLI stub in `cli.py` (accepts `files: list[Path], config: DocvetConfig`)
  - `griffe` CLI command with full discovery pipeline support (DIFF, STAGED, ALL, FILES modes)
  - `griffe` registered in `_VALID_CHECK_NAMES` and default `warn_on` list in `DocvetConfig`
  - Optional dependency: `griffe >=1.0` extra in `pyproject.toml`
  - `src-root` resolution logic in `cli.py` (shared with coverage)
  - File discovery via `discovery.py` (returns sorted absolute `.py` file paths)
- **No AST dependency** — griffe_compat does not import `ast` or `ast_utils`. Griffe handles all docstring parsing internally
- **No git dependency** — griffe_compat does not use subprocess or git. File discovery is the CLI's responsibility
- **No config dependency** — zero configuration parameters. No `GriffeConfig` dataclass needed
- **Conditional import** — `try: import griffe except ImportError: griffe = None` at module level. `TYPE_CHECKING` for type hints
- **Warning capture via standard Python logging** — attaches a handler to `logging.getLogger("griffe")`, not griffe internals. Handler must be removed after loading (no permanent global state modification)
- **Package-level loading** — `GriffeLoader(search_paths=[str(src_root)])` then `loader.load(package_name)`. If `src_root` contains multiple packages, all are loaded
- **Finding field extraction from warning messages** — griffe emits warnings in format `"{filepath}:{line}: {message}"`. Fields extracted via string splitting or regex

### CLI Stub Signature Mismatch

The existing `_run_griffe` stub accepts `(files: list[Path], config: DocvetConfig)` — matching other `_run_*` functions. But `check_griffe_compat` requires `(src_root: Path, files: Sequence[Path])` — it needs `src_root` for griffe's search path and has zero config dependency. This is a departure from the uniform `_run_*` signature pattern. The CLI wiring story must resolve `src_root` from `config.project_root / config.src_root` (same logic as coverage's `_run_coverage`) and pass it to `check_griffe_compat`. This is a constraint, not a decision — the function signature is defined by the PRD's integration contract.

### Symbol Name Extraction

The `Finding.symbol` field must come from somewhere. The PRD says it can be "extracted from griffe's warning context or from the message text." These are architecturally different:

- **From griffe objects:** After loading, walk griffe's object model to find which `Function`/`Class` owns each warning. More robust but couples to griffe's internal object API beyond the stable `load()`/`GriffeLoader` surface.
- **From message text:** Parse the symbol name out of the warning string format. Fragile but keeps dependency surface minimal.

This requires an explicit architectural decision in the decisions phase.

### Path Normalization for File Filtering (FR85)

Griffe emits file paths relative to its search path. Discovery returns sorted absolute paths. The `files` filter comparison (FR85) requires path normalization to reconcile these two representations. The context analysis for coverage didn't face this issue (coverage uses `Path.is_relative_to()` against `src_root`). Griffe filtering needs either: (a) resolve griffe's relative paths to absolute, or (b) make discovery paths relative to `src_root` before comparison. This is a design constraint that must be addressed in implementation patterns.

### Exception Surface for Package Loading

Unlike enrichment and freshness (defensive design, no try/except), griffe_compat **must** wrap `griffe.load()` in try/except because griffe can raise on user code issues. Expected exceptions include:
- `ModuleNotFoundError` — package not found under search path
- `SyntaxError` — user code has syntax errors
- Griffe-specific exceptions (e.g., alias resolution failures)

The catch scope must be defined precisely — not a bare `except Exception`. This requires an architectural decision.

### Griffe Cross-Cutting Concerns

- **Optional dependency handling (highest architectural novelty):** The griffe check is the only check module with an optional third-party dependency. Two-layer skip logic: (1) `check_griffe_compat` returns `[]` immediately if griffe is not importable, (2) CLI layer detects griffe availability before calling and handles verbose messaging / stderr warnings. This split keeps the pure function's contract clean
- **Logging handler lifecycle (highest-risk area):** The temporary handler attached to `logging.getLogger("griffe")` must be removed after loading completes, even on exceptions. Use try/finally or a context manager. Failure to remove leaves a handler that accumulates warnings across subsequent calls (relevant for test isolation and potential future watch mode)
- **Package-vs-file architecture mismatch:** All other checks process files individually. Griffe loads the entire package once and produces warnings for all files. The `files` parameter post-filters warnings to match discovery mode
- **Warning message parsing fragility:** Griffe's warning format (`{filepath}:{line}: {message}`) is not a documented API contract. Defensive parsing required — substring matching rather than exact string equality, unrecognized messages default to `griffe-format-warning`
- **One-finding-per-warning deduplication:** Intentionally different from enrichment's one-per-symbol-per-rule. Each griffe warning identifies a specific, individually-fixable issue (a specific parameter on a specific function)
- **Duplicate warning handling:** Griffe could emit duplicate warnings if import aliases cause the same module to be parsed twice. Design decision needed: deduplicate at the docvet level (by file+line+message tuple) or trust griffe. Either way, needs a test

### Test Strategy Constraints

Two viable unit test mock strategies exist for griffe, with different tradeoffs:

1. **Mock the classifier inputs** — create fake `LogRecord` objects with known format strings and feed them to the warning classifier. Fast, isolated, but doesn't test handler attachment/detachment lifecycle
2. **Mock `griffe.load()`** — patch the loader, configure griffe's logger to emit real warnings. Tests the full pipeline including handler lifecycle, but heavier

The logging handler lifecycle is identified as the highest-risk area. Strategy 1 alone leaves the riskiest code path uncovered in unit tests. The decisions phase should define which strategy is primary.

Additionally, testing the "griffe not installed" path (FR90) requires patching the module-level `griffe` variable to `None`. This interacts with Python's import caching and needs careful mock design.

## Griffe Core Architectural Decisions

### Griffe Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. Internal module organization (single file, function layout)
2. Warning capture mechanism (logging handler with per-object attribution)
3. Package loading & symbol attribution strategy (lazy parse + per-object walk)
4. Warning classification strategy (substring matching for 3 rules)

**Important Decisions (Shape Architecture):**
5. Exception handling strategy (layered: load-time + walk-time + handler cleanup)
6. Finding message format (griffe's original warning text with symbol prefix)

**Deferred Decisions (Post-MVP):**
- Per-rule disable toggles (e.g., `disable-griffe-missing-type = true`) via `[tool.docvet.griffe]`
- Duplicate warning deduplication (trust griffe for MVP, add dedup if observed in practice)
- Custom griffe parser options (expose `warn_unknown_params`, `warn_missing_types` as config)
- Numpy/Sphinx docstring style support

### Griffe Decision 1: Internal Module Organization

**Decision:** Single `griffe_compat.py` file with one public function

Consistent with the one-file-per-check pattern (enrichment.py, freshness.py, coverage.py). Griffe is the simplest check module — one public function, ~3-4 private helpers, estimated ~200-300 lines.

**File organization within `griffe_compat.py`:**
1. Module docstring
2. `from __future__ import annotations`
3. Stdlib imports (`logging`, `pathlib`, `typing`)
4. Conditional griffe import (`try/except ImportError`)
5. Local imports (`from docvet.checks import Finding`)
6. Module-level constants (warning classification patterns)
7. `_WarningCollector` logging handler class
8. Private helpers (`_classify_warning`, `_walk_objects`, `_resolve_file_set`)
9. `check_griffe_compat` public function (last function in file)

**Rationale:** Same structural pattern as all other checks. One file is sufficient — no sub-package needed. The module is significantly simpler than enrichment (~1250 lines) or freshness (~560 lines).

**Anti-patterns:**
- `checks/griffe_compat/__init__.py` + submodules — premature, breaks one-file-per-check
- Placing griffe helpers in `ast_utils.py` — griffe has no AST dependency
- Importing from other check modules — violates isolation rule

### Griffe Decision 2: Warning Capture Mechanism

**Decision:** Custom `logging.Handler` subclass with per-object attribution via snapshot pattern

```python
class _WarningCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
```

**Attachment pattern — try/finally for guaranteed cleanup:**
```python
griffe_logger = logging.getLogger("griffe")
handler = _WarningCollector()
griffe_logger.addHandler(handler)
try:
    # ... load package and trigger parsing ...
finally:
    griffe_logger.removeHandler(handler)
```

**Per-object attribution via snapshot:**
```python
for obj in objects_to_check:
    before = len(handler.records)
    _ = obj.docstring.parsed  # triggers parsing, emits warnings synchronously
    after = len(handler.records)
    for record in handler.records[before:after]:
        # All warnings in this slice belong to obj
        findings.append(_build_finding(record, obj))
```

**Why this works:** Griffe's docstring parsing is synchronous — accessing `obj.docstring.parsed` triggers the Google parser, which calls `docstring_warning()` → `logger.warning()` → our handler collects the record — all before the property access returns. No concurrent parsing, no interleaving.

**Known limitation — cached docstrings:** The `parsed` property is a cached property on `Docstring`. If griffe internally accesses `.parsed` during loading for any reason (type resolution, alias resolution), the second access returns the cached result and emits zero warnings. With `allow_inspection=False` and no `resolve_aliases` call, this is unlikely. As a defensive measure, implementations may check `"parsed" in obj.docstring.__dict__` and skip already-parsed docstrings with a debug log. This is a known limitation, not a blocker.

**Rationale:** The snapshot pattern gives exact symbol attribution without any reverse-lookup or line-range mapping. We know the symbol name (`obj.name`) at the time we trigger parsing. This is architecturally simpler than the alternative (bulk-parse, then reverse-map via line numbers), and more robust (no edge cases with overlapping docstring ranges).

**Anti-patterns:**
- Patching `docstring_warning()` directly — couples to griffe internals
- Using `warnings.catch_warnings()` — griffe uses `logging`, not `warnings` module
- Global handler that persists beyond the check — leaks state between runs

### Griffe Decision 3: Package Loading & Symbol Attribution Strategy

**Decision:** Load package with lazy parsing, walk tree with file filtering, per-object triggered parsing

**Three-phase pipeline:**

**Phase 1 — Load:**
```python
package = griffe.load(
    package_name,
    search_paths=[str(src_root)],
    docstring_parser="google",
    allow_inspection=False,
)
```
- `docstring_parser="google"` — sets the parser but does NOT trigger parsing (lazy)
- `allow_inspection=False` — prevents runtime import fallback, raises `ModuleNotFoundError` if sources not found on disk (safer for a linter)
- `package_name` derived from directory structure (see package discovery below)

**Package name derivation:**
Walk `src_root` for immediate child directories containing `__init__.py`. Each such directory's name is a loadable package name. Example: if `src_root` is `src/` and `src/docvet/__init__.py` exists, then `package_name = "docvet"`. If `src_root` contains multiple packages (e.g., `src/docvet/` and `src/utils/`), load each separately. Bare `.py` files directly under `src_root` (not in a package) are skipped — griffe requires package structure.

```python
for child in sorted(src_root.iterdir()):
    if child.is_dir() and (child / "__init__.py").exists():
        package_name = child.name
        # load this package
```

**Phase 2 — Walk & Filter:**
```python
def _walk_objects(
    obj: griffe.Object,
    file_set: set[Path],
) -> Iterator[griffe.Object]:
```
- Recursively walk `obj.members.values()`
- Skip aliases (`obj.is_alias`) to avoid `AliasResolutionError`
- Skip objects without docstrings (`obj.docstring is None`)
- Skip objects whose `obj.filepath` is not in `file_set` (file filtering for FR85)
- Yield matching objects

**Phase 3 — Parse & Collect:**
- For each yielded object, trigger `obj.docstring.parsed` (snapshot pattern from Decision 2)
- Warnings emitted during parsing are attributed to the current object
- Construct `Finding` for each warning

**Path normalization for file filtering (FR85):**
Discovery returns absolute paths. Griffe objects have `obj.filepath` as an absolute `Path`. Direct comparison using a `set[Path]` of resolved absolute paths.

```python
def _resolve_file_set(files: Sequence[Path]) -> set[Path]:
    return {f.resolve() for f in files}
```

When comparing, resolve griffe's filepath too: `obj.filepath.resolve() in file_set`. This handles any CWD-relative paths consistently. Note: `resolve()` follows symlinks — if the project uses symlinks, both sides must be resolved for consistent comparison. This is the standard approach; symlink edge cases are a known limitation.

**Rationale:** Phase separation (load → walk → parse) keeps each concern isolated. File filtering at the walk stage is more efficient than post-filtering warnings (never triggers parsing for irrelevant files). Per-object parsing gives exact symbol attribution. Absolute path comparison avoids CWD-dependency bugs.

### Griffe Decision 4: Warning Classification Strategy

**Decision:** Substring matching with ordered priority, catch-all fallback

```python
_MISSING_TYPE_PATTERN = "No type or annotation for"
_UNKNOWN_PARAM_PATTERN = "does not appear in the function signature"

def _classify_warning(message: str) -> tuple[str, str]:
    """Classify a griffe warning into rule ID and category."""
    if _UNKNOWN_PARAM_PATTERN in message:
        return ("griffe-unknown-param", "required")
    if _MISSING_TYPE_PATTERN in message:
        return ("griffe-missing-type", "recommended")
    return ("griffe-format-warning", "recommended")
```

**Priority order matters:** `griffe-unknown-param` is checked first because it's the only `required`-category rule. If a warning message somehow matches both patterns (unlikely but defensive), the higher-severity rule wins.

**Substring matching (not regex):** Griffe's warning messages are well-structured strings. Substring matching is simpler, faster, and resilient to minor wording changes across griffe versions. Regex is overkill for two fixed substrings.

**Handles message variants:** Griffe sometimes appends `". Did you mean '{starred_name}'?"` to unknown-param warnings (e.g., `"Parameter 'query' does not appear in the function signature. Did you mean '*query'?"`). Substring matching with `in` handles this correctly — the pattern matches regardless of trailing text.

**Catch-all `griffe-format-warning`:** Any warning that doesn't match the two specific patterns is classified as a format warning. This satisfies FR92 (future griffe versions) — new warning types produce findings rather than being dropped.

**Known warning messages that map to `griffe-format-warning`:**
- `"Confusing indentation for continuation line..."` — indentation issues
- `"Failed to get 'name: description' pair from..."` — malformed entries
- `"Failed to get 'exception: description' pair from..."` — malformed Raises entries
- `"Failed to get name, annotation or description from..."` — parse failures

**Note on griffe log levels:** The `_classify_warning` function only sees WARNING-level records. Some griffe messages (like "Possible section skipped") are emitted at DEBUG level. Our handler collects at WARNING level, which correctly excludes debug-level messages.

**Rationale:** Simple, deterministic, forward-compatible. Two `in` checks and a fallback — no regex compilation, no pattern maintenance burden. Matches the PRD's specification exactly.

### Griffe Decision 5: Exception Handling Strategy

**Decision:** Layered exception handling — load-time explicit catch, walk-time alias skip, handler cleanup via try/finally

Unlike enrichment and freshness (defensive design, no try/except), griffe_compat **must** use exception handling because it delegates to an external library that performs filesystem I/O on arbitrary user code.

**Layer 1 — Package loading (`griffe.load()`):**
```python
try:
    package = griffe.load(package_name, ...)
except (griffe.LoadingError, ModuleNotFoundError, OSError, SyntaxError):
    return []
```

Explicit exception types rather than bare `except Exception`:
- `griffe.LoadingError` — griffe's wrapper for load failures (wraps `SyntaxError`, `ImportError`, `UnicodeDecodeError`, `OSError` internally, but can also be raised directly)
- `ModuleNotFoundError` — package not found under search path (raised when `allow_inspection=False` and sources not on disk)
- `OSError` — filesystem permission errors, missing directories
- `SyntaxError` — user code has syntax errors (can propagate unwrapped in some code paths)

**Why not bare `except Exception`:** While the PRD says "return empty list without crashing" (FR91), catching `MemoryError` or `RecursionError` silently would mask serious issues. The explicit list covers all expected griffe failure modes. If an unexpected exception type surfaces in practice, it surfaces as a crash (bug report) rather than a silent skip (mysterious missing findings).

**Conditional import caveat:** `griffe.LoadingError` is only available when griffe is installed. The exception list must be inside the `if griffe is not None` guard:

```python
if griffe is None:
    return []
# griffe is guaranteed importable from here
try:
    package = griffe.load(...)
except (griffe.LoadingError, ModuleNotFoundError, OSError, SyntaxError):
    return []
```

**Layer 2 — Object tree walking:**
```python
if obj.is_alias:
    continue  # Skip aliases — accessing their attributes can raise AliasResolutionError
```
Proactive skip rather than reactive catch. Aliases are indirection objects that may point to unresolved targets. Accessing their `docstring` or `filepath` can raise `AliasResolutionError` or `CyclicAliasError`. Since aliases point to objects defined elsewhere (which we'll visit when walking their home module), skipping them loses no coverage.

**Layer 3 — Handler cleanup (try/finally):**
```python
handler = _WarningCollector()
griffe_logger.addHandler(handler)
try:
    # ... all load + walk + parse logic ...
finally:
    griffe_logger.removeHandler(handler)
```
Guarantees handler removal even if an unexpected exception propagates. Prevents handler accumulation across multiple check invocations.

**Rationale:** Three defensive layers, each addressing a different risk surface. Layer 1 (explicit catch list) balances safety with debuggability. Layer 2 (alias skip) is proactive prevention. Layer 3 (try/finally) is resource cleanup. Together they satisfy FR90, FR91, and the logging handler lifecycle concern.

### Griffe Decision 6: Finding Message Format

**Decision:** Use griffe's original warning text as the `Finding.message`, prefixed with symbol context

**Message format:**
```
{SymbolKind} '{name}' {griffe_warning_text}
```

Examples:
- `Function 'fetch_records' No type or annotation for parameter 'limit'`
- `Function 'fetch_records' Parameter 'query' does not appear in the function signature`
- `Class 'Config' Failed to get 'name: description' pair from '    invalid_line'`

**Symbol kind display:** `obj.kind.value.capitalize()` → `"Function"`, `"Class"`, `"Module"`, `"Attribute"`. Consistent with enrichment and freshness patterns (`symbol.kind.capitalize()`). Note: griffe uses `Kind` enum with string values (`"function"`, `"class"`, etc.), not the same as `Symbol.kind` from `ast_utils` — but `.capitalize()` produces the same display names.

**Finding field mapping:**

| Finding field | Source |
|---|---|
| `file` | `str(obj.filepath.resolve())` (absolute path, consistent with discovery) |
| `line` | Parsed from warning message (see below) — the specific docstring line where the issue occurs |
| `symbol` | `obj.name` (from griffe object, known via snapshot attribution) |
| `rule` | From `_classify_warning()` (Decision 4) |
| `message` | `f"{obj.kind.value.capitalize()} '{obj.name}' {warning_text}"` |
| `category` | From `_classify_warning()` (Decision 4) |

**Warning message parsing for line and text extraction:**
The log record's `getMessage()` returns the full formatted string: `"{filepath}:{lineno}: {message}"`. Parse with:
```python
_WARNING_PATTERN = re.compile(r"^(.+?):(\d+): (.+)$")
```
Extract `lineno` (group 2) for `Finding.line` and `message_text` (group 3) for the message suffix. The lineno is the precise line within the docstring where the issue occurs (`docstring.lineno + offset`), providing better developer experience than pointing to the function definition line.

**Rationale:** Same pattern as enrichment and freshness — messages name the symbol, the issue, and evidence. Preserving griffe's warning text ensures accuracy. Symbol prefix ensures actionability. Using the warning's precise lineno provides maximum developer utility.

### Griffe Decision Impact Analysis

**Implementation Sequence:**
1. Module-level constants, conditional import, and `_WarningCollector` class (Decisions 1, 2)
2. `_classify_warning` function (Decision 4)
3. `_walk_objects` generator function (Decision 3, Layer 2 of Decision 5)
4. `_resolve_file_set` helper (Decision 3)
5. `check_griffe_compat` public orchestrator tying all phases together (Decisions 1-6)

**Cross-Decision Dependencies:**
- Decision 1 (module org) defines the file layout that all other decisions fill in
- Decision 2 (warning capture) produces the `LogRecord` objects consumed by Decision 4 (classification) and Decision 6 (message format)
- Decision 3 (loading & walking) determines which objects trigger parsing and how symbol names are attributed
- Decision 4 (classification) produces the `(rule, category)` tuple consumed by Decision 6 (finding construction)
- Decision 5 (exception handling) wraps Decisions 2 and 3 with safety layers
- Decision 6 (message format) parses the LogRecord message for both the display text and the precise line number
- All decisions depend on the existing `Finding` dataclass — no changes needed

## Griffe Implementation Patterns & Consistency Rules

### Griffe Conflict Points Identified

6 areas where AI agents implementing the griffe module could make inconsistent choices.

### Griffe Naming Patterns

**Private function naming:**
- Pattern: `_classify_*` for categorization, `_walk_*` for tree traversal, `_resolve_*` for normalization, `_build_*` for construction
- `_classify_warning`, `_walk_objects`, `_resolve_file_set`, `_build_finding_from_record`
- Handler class: `_WarningCollector` (not `_GriffeHandler`, `_LogCapture`, or `_WarningHandler` — the name describes what it does, not what library it wraps)
- **Anti-pattern:** Generic names like `_process`, `_handle`, `_check_warning`

**Constants:**
- Pattern: `ALL_CAPS_WITH_UNDER` at module level, private prefix `_`
- `_MISSING_TYPE_PATTERN`, `_UNKNOWN_PARAM_PATTERN`, `_WARNING_PATTERN`
- **Anti-pattern:** `MISSING_TYPE_SUBSTR`, `_PATTERN_FOR_MISSING_TYPE`, `GRIFFE_PATTERNS` — inconsistent with enrichment/freshness naming

**Symbol kind display names:**
- Use `obj.kind.value.capitalize()` for messages: `"Function"`, `"Class"`, `"Module"`, `"Attribute"`
- Griffe's `Kind` enum uses string values (`"function"`, `"class"`, etc.)
- Same `.capitalize()` pattern as enrichment (`symbol.kind.capitalize()`) and freshness — consistent across all checks
- **Anti-pattern:** Hardcoded strings like `"function"`, mapping dicts, `str(obj.kind)`

### Griffe Structure Patterns

**File organization within `griffe_compat.py` (defined in Decision 1), with additional constraints:**

- `_WarningCollector` class appears before helper functions (it's used by the orchestrator)
- `_classify_warning` appears before `_walk_objects` (classification is conceptually simpler)
- `_build_finding_from_record` appears after `_classify_warning` (it calls classify)
- `_resolve_file_set` appears near `_walk_objects` (they're co-dependent)
- `check_griffe_compat` is always the last function in the file
- No forward references to helpers defined later in the file

**Conditional import block:**
```python
from typing import TYPE_CHECKING

try:
    import griffe
except ImportError:
    griffe = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from griffe import Object as GriffeObject
```
- `TYPE_CHECKING` guard for type hints that reference griffe types
- `type: ignore[assignment]` on the `griffe = None` line (ty/mypy can't narrow this)
- Type hints in function signatures use string literals or `TYPE_CHECKING`-guarded imports
- **Anti-pattern:** `import griffe as _griffe`, conditional `from griffe import ...` blocks, runtime type checks against griffe types

**Test organization:**
- `tests/unit/checks/test_griffe_compat.py` — single test file, matching source structure
- Test naming: `test_{rule_id}_when_{condition}_returns_{expected}` (same as all other checks)
- Test grouping: (1) handler tests, (2) classification tests, (3) walk/filter tests, (4) orchestrator tests, (5) edge case tests
- Mocked griffe objects and log records in unit tests — no actual package loading
- `tests/fixtures/griffe_pkg/` — small Python package with known-bad docstrings for integration smoke tests
- **Anti-pattern:** Testing through CLI runner, loading real packages in unit tests, testing griffe's own parsing behavior

### Griffe Warning Parsing Patterns

**Log record message parsing:**
```python
_WARNING_PATTERN = re.compile(r"^(.+?):(\d+): (.+)$")

match = _WARNING_PATTERN.match(record.getMessage())
if match:
    filepath_str, line_str, message_text = match.groups()
    line = int(line_str)
```
- Always use `record.getMessage()` to get the formatted string (not `record.message` which may have lazy formatting)
- Parse with a compiled regex, not `str.split(":")` (filenames on Windows contain `:`; the non-greedy `.+?` handles this)
- If the pattern doesn't match (defensive), skip the record — produce zero findings rather than crash
- **Anti-pattern:** `str.split(":", 2)`, `str.partition(":")`, accessing `record.args` directly

**Classification is pure function:**
- `_classify_warning(message: str) -> tuple[str, str]` takes only the message text (group 3 from regex), not the full log record
- Returns `(rule_id, category)` tuple
- No side effects, no state, easily unit-testable
- **Anti-pattern:** Passing the full LogRecord, returning a Finding, embedding classification in the orchestrator

### Griffe Finding Construction Pattern

**All finding construction uses `_build_finding_from_record` helper:**

```python
def _build_finding_from_record(
    record: logging.LogRecord,
    obj: GriffeObject,
) -> Finding | None:
    match = _WARNING_PATTERN.match(record.getMessage())
    if not match:
        return None
    _filepath_str, line_str, message_text = match.groups()
    line = int(line_str)
    rule, category = _classify_warning(message_text)
    return Finding(
        file=str(obj.filepath),
        line=line,
        symbol=obj.name,
        rule=rule,
        message=f"{obj.kind.value.capitalize()} '{obj.name}' {message_text}",
        category=category,
    )
```

- Returns `Finding | None` — `None` when the log record doesn't match the expected format (defensive)
- Encapsulates the full parse → classify → construct pipeline in one place
- The orchestrator's snapshot loop stays clean: `if f := _build_finding_from_record(record, obj): findings.append(f)`

**Finding `file` field format:**
- Use `str(obj.filepath)` — absolute path as string
- `obj.filepath` is an absolute `Path` set by griffe during loading
- This is consistent with discovery, which returns absolute `Path` objects. The CLI normalizes for display when formatting output (`file:line: rule message`)
- All checks should emit absolute paths in `Finding.file`; the reporting layer handles display format
- **Anti-pattern:** `str(obj.filepath.resolve())` (unnecessary if already absolute), `str(obj.relative_filepath)` (relative to CWD, fragile), `str(obj.filepath.relative_to(src_root))` (loses project context)

**Finding field details:**
- `file` — `str(obj.filepath)` (absolute path, consistent with discovery)
- `line` — from the parsed warning message (the specific docstring line where the issue occurs), NOT `obj.lineno` (the def/class keyword line) and NOT `obj.docstring.lineno` (the docstring start line)
- `symbol` — `obj.name` (from griffe object, known via snapshot attribution)
- `rule` and `category` — from `_classify_warning()`, never computed inline
- `message` — `f"{obj.kind.value.capitalize()} '{obj.name}' {message_text}"` format

### Griffe Orchestrator Pattern

**`check_griffe_compat` follows this exact sequence:**

```python
def check_griffe_compat(
    src_root: Path,
    files: Sequence[Path],
) -> list[Finding]:
    if griffe is None:
        return []
    if not files:
        return []

    file_set = _resolve_file_set(files)
    findings: list[Finding] = []

    griffe_logger = logging.getLogger("griffe")
    handler = _WarningCollector()
    griffe_logger.addHandler(handler)
    try:
        for child in sorted(src_root.iterdir()):
            if not child.is_dir() or not (child / "__init__.py").exists():
                continue
            try:
                package = griffe.load(
                    child.name,
                    search_paths=[str(src_root)],
                    docstring_parser="google",
                    allow_inspection=False,
                )
            except (griffe.LoadingError, ModuleNotFoundError, OSError, SyntaxError):
                continue  # skip this package, try next

            for obj in _walk_objects(package, file_set):
                before = len(handler.records)
                _ = obj.docstring.parsed
                after = len(handler.records)
                for record in handler.records[before:after]:
                    if f := _build_finding_from_record(record, obj):
                        findings.append(f)
    finally:
        griffe_logger.removeHandler(handler)

    return findings
```

- Guard clauses first: `griffe is None` → `[]`, `not files` → `[]`
- Handler attached once, wrapping all package loads (not per-package)
- **`src_root.iterdir()` is inside the try/finally** — if `iterdir()` raises `PermissionError` or `FileNotFoundError`, the handler is still cleaned up. The exception propagates (not caught) because an invalid `src_root` is a caller error, not a graceful-skip scenario
- Package load failures skip to next package via `continue`, not `return []`
- `sorted(src_root.iterdir())` for deterministic package ordering
- **Snapshot loop uses `before:after` slice** (not `before:`) — `after = len(handler.records)` captured after `.parsed` access. This prevents re-processing records from previous objects
- Handler removed in `finally` regardless of exceptions

**Duplicate warning policy (MVP):** Trust griffe to not emit duplicates. No dedup at the docvet level. If duplicates are observed in practice, add dedup by `(file, line, message)` tuple as a post-MVP enhancement. Tests should include a case verifying that a known scenario does NOT produce duplicates.

**FR97 boundary (CLI responsibility, not check function):** `check_griffe_compat` does NOT handle verbose messaging about griffe availability. The CLI layer detects griffe availability before calling the function (via `importlib.util.find_spec("griffe")`) and handles:
- Verbose-mode note: `"griffe: skipped (griffe not installed)"`
- Stderr warning when griffe is in `fail-on` but not installed
This keeps the pure function's contract clean.

### Griffe Test Strategy Patterns

**Mock strategy mapping by test target:**

| Test Target | Mock Strategy | What's Mocked |
|---|---|---|
| `_classify_warning` | None (pure function) | Nothing — test with known warning strings |
| `_WarningCollector` | Logger interaction | Emit records to `logging.getLogger("griffe")`, verify collection |
| `_walk_objects` | `MagicMock(spec=griffe.Function)` | Griffe Object attributes: `name`, `kind`, `filepath`, `docstring`, `is_alias`, `members` |
| `_build_finding_from_record` | `MagicMock` for LogRecord + Object | `record.getMessage()` returns known format string |
| `check_griffe_compat` (happy path) | `mocker.patch("docvet.checks.griffe_compat.griffe.load")` | Returns mock package with mock objects |
| `check_griffe_compat` (griffe missing) | `mocker.patch("docvet.checks.griffe_compat.griffe", None)` | Module-level griffe import |
| `check_griffe_compat` (load failure) | `mocker.patch` with `side_effect=` | `griffe.load` raises specific exception |
| `check_griffe_compat` (empty files) | None | Pass `files=[]`, verify `[]` returned |
| Integration smoke test | Real `griffe.load` on fixture pkg | Nothing — `tests/fixtures/griffe_pkg/` |

**`_WarningCollector` focused tests:**
- Verify it collects WARNING-level records
- Verify it ignores DEBUG and INFO records
- Verify `records` is a plain list supporting the snapshot pattern (index access, length)
- Verify records contain the formatted message string via `getMessage()`

**"Griffe not installed" test isolation:**
- Tests for the `griffe is None` path must NOT import `griffe` at the test module level
- Use `mocker.patch("docvet.checks.griffe_compat.griffe", None)` to simulate missing import
- If the test file needs griffe for other tests (e.g., creating mock objects with `spec=`), use a conditional import guarded by `pytest.importorskip("griffe")` or isolate the "not installed" tests in a separate test class/section

**Integration fixture package (`tests/fixtures/griffe_pkg/`):**
- Small package with `__init__.py` + one module containing known-bad docstrings
- At minimum: one function with untyped parameters, one function documenting a nonexistent parameter, one function with malformed formatting
- Used for one smoke test that validates the full pipeline: load → walk → parse → classify → construct
- NOT used for unit tests — unit tests use mocks for speed and isolation

### Griffe Enforcement Guidelines

**All AI agents implementing griffe_compat MUST:**
- Follow the file organization order (imports → constants → handler → helpers → orchestrator)
- Use the conditional import pattern with `TYPE_CHECKING` guard exactly as specified
- Use `_WarningCollector` handler class with try/finally cleanup
- Use the snapshot pattern with `before:after` slice for per-object warning attribution
- Skip aliases (`obj.is_alias`) when walking the griffe object tree
- Use substring matching (not regex) for warning classification in `_classify_warning`
- Use `_build_finding_from_record` helper for all finding construction
- Use `obj.kind.value.capitalize()` for symbol kind in messages
- Parse warning messages with `_WARNING_PATTERN` regex, not string splitting
- Construct Finding with `line` from the parsed warning (not `obj.lineno`)
- Use `str(obj.filepath)` for Finding `file` field (absolute path)
- Return `[]` immediately when `griffe is None` or `not files`
- Catch explicit exception types around `griffe.load()`, not bare `except Exception`
- Place handler attachment/removal in the orchestrator's try/finally, not in helpers
- Trust griffe for deduplication — no docvet-level dedup in MVP
- Place `src_root.iterdir()` inside the try/finally block (handler cleanup, not exception swallowing)

**Pattern verification:** ruff + ty enforce naming, import order, and type consistency. Test coverage (>=85% project-wide) enforces behavioral correctness. The `_classify_warning` function and `_WarningCollector` class are independently unit-testable.

## Griffe Project Structure & Boundaries

### Updated Project Directory Structure

Existing files shown as-is. **New files for griffe** marked with `← NEW`.

```
src/docvet/
├── __init__.py
├── cli.py                    # _run_griffe stub (wired in separate CLI story)
├── config.py                 # No GriffeConfig needed (zero config)
├── discovery.py
├── ast_utils.py              # Not used by griffe (no AST dependency)
└── checks/
    ├── __init__.py            # Finding dataclass (shared, no changes needed)
    ├── enrichment.py          # check_enrichment (existing, no changes needed)
    ├── freshness.py           # check_freshness_diff/drift (existing, no changes needed)
    ├── coverage.py            # check_coverage (existing, no changes needed)
    └── griffe_compat.py       ← NEW (check_griffe_compat)

tests/
├── conftest.py               # Shared fixtures (existing)
├── unit/
│   ├── test_config.py
│   ├── test_ast_utils.py
│   ├── test_cli.py
│   └── checks/
│       ├── __init__.py
│       ├── test_enrichment.py
│       ├── test_freshness.py
│       ├── test_coverage.py
│       ├── test_finding.py
│       └── test_griffe_compat.py  ← NEW (all griffe rule tests, mocked griffe objects)
├── integration/
│   ├── conftest.py
│   ├── test_discovery.py
│   └── test_griffe_compat.py     ← NEW (smoke test; requires pytest.importorskip("griffe"))
└── fixtures/
    ├── complete_module.py
    ├── missing_raises.py
    ├── missing_yields.py
    ├── nested_symbols.py
    └── griffe_pkg/                ← NEW (fixture package for integration tests)
        ├── __init__.py            ← NEW (empty, makes directory a package)
        └── bad_docstrings.py      ← NEW (see fixture content spec below)
```

**Fixture package content spec (`tests/fixtures/griffe_pkg/bad_docstrings.py`):**
- At least one function with a documented parameter lacking a type annotation → triggers `griffe-missing-type`
- At least one function documenting a nonexistent parameter → triggers `griffe-unknown-param`
- At least one function with malformed docstring formatting → triggers `griffe-format-warning`
- At least one **well-documented function** that produces zero warnings → validates negative case in integration tests

**Integration test note:** `tests/integration/test_griffe_compat.py` must use `pytest.importorskip("griffe")` at the module level — griffe is an optional dependency and CI may run without it.

**Scope summary:** The main griffe PR adds 1 source file (`checks/griffe_compat.py`), 1 unit test file (`tests/unit/checks/test_griffe_compat.py`), 1 integration test file (`tests/integration/test_griffe_compat.py`), and 1 fixture package (`tests/fixtures/griffe_pkg/`). No modifications to existing source files. CLI wiring (`_run_griffe` stub replacement, `src_root` resolution) is a **separate CLI wiring story** — same pattern as enrichment, freshness, and coverage.

### Griffe Architectural Boundaries

**Public API boundary:**
- `check_griffe_compat(src_root: Path, files: Sequence[Path]) -> list[Finding]` — single public function
- Everything else in `griffe_compat.py` is private (`_` prefixed): `_WarningCollector`, `_classify_warning`, `_walk_objects`, `_resolve_file_set`, `_build_finding_from_record`

**Caller contract (CLI responsibility):**
- CLI **must validate `src_root` exists** before calling `check_griffe_compat`. An invalid `src_root` (non-existent directory, permission error on `iterdir()`) is a caller error — the function does not catch `PermissionError` or `FileNotFoundError` from `src_root.iterdir()`. These exceptions propagate to the caller. This mirrors coverage's contract where `src_root` is assumed valid.

**Module dependency boundary:**
```
cli.py (separate wiring story)
  → imports check_griffe_compat from docvet.checks.griffe_compat
  → imports Finding from docvet.checks
  → resolves src_root from config.project_root / config.src_root (same as coverage)
  → validates src_root exists before calling
  → passes src_root + discovered files to check_griffe_compat

checks/griffe_compat.py (main griffe PR)
  → imports Finding from docvet.checks
  → imports griffe conditionally (try/except ImportError)
  → NEVER imports from docvet.cli, docvet.discovery, docvet.config, docvet.ast_utils
  → NEVER imports from checks.enrichment, checks.freshness, checks.coverage
```

**Data boundary:**
- Griffe_compat performs filesystem I/O **only indirectly** — `griffe.load()` reads Python source files from disk
- `src_root` is the filesystem root for griffe's search path — the function needs it for both package discovery and loading
- `files` is a filter set — restricts which objects produce findings, does not control what griffe loads (griffe always loads entire packages)
- No subprocess calls, no git dependency, no AST dependency
- Finding construction uses `obj.filepath` (absolute Path from griffe) and `obj.name` (from griffe object model)

**Path normalization invariant:** Both sides of the file filter comparison must be absolute paths for set membership to work. `_resolve_file_set` calls `f.resolve()` on input files. Griffe sets `obj.filepath` as an absolute `Path` during loading. The invariant is: `_walk_objects` compares `obj.filepath` against `file_set` entries — both must be absolute. If either side is relative, the filter silently misses matches. Tests must verify this invariant with absolute paths.

**Dependency novelty (unique to griffe):**
- Only check module with an optional third-party dependency (`griffe >=1.0`)
- Only check module using `try/except ImportError` at module level
- Only check module using `logging.Handler` for input capture
- Only check module that loads at package granularity (not file granularity)

**`_walk_objects` recursion depth note:** The function recursively walks `obj.members.values()`. Recursion depth equals package nesting depth — typically 3-5 levels for real-world packages. This is well within Python's default recursion limit (1000). An iterative stack (like enrichment's scope-aware walk) is unnecessary for MVP. If a pathological package triggers `RecursionError`, convert to iterative stack as a post-MVP enhancement.

### Griffe Requirements to Structure Mapping

**FR Category → File Mapping:**

| FR Category | FRs | Primary File | Key Functions |
|---|---|---|---|
| Detection | FR81-FR84 | `checks/griffe_compat.py` | `check_griffe_compat`, `_WarningCollector`, `_build_finding_from_record` |
| File Filtering | FR85 | `checks/griffe_compat.py` | `_walk_objects`, `_resolve_file_set` |
| Finding Production | FR86-FR89 | `checks/griffe_compat.py` | `_build_finding_from_record`, `_classify_warning` |
| Edge Cases | FR90-FR93 | `checks/griffe_compat.py` | Guard clauses, exception handling in `check_griffe_compat` |
| Integration — Check Function | FR94, FR96 | `checks/griffe_compat.py` | `check_griffe_compat` (FR94: public API), try/finally handler lifecycle (FR96) |
| Integration — CLI Wiring | FR95, FR97 | `cli.py` (separate story) | `_run_griffe` stub replacement, griffe availability detection |

**Rule → Internal Function Mapping:**

| Rule | Classification Pattern | Key Helpers | Category |
|---|---|---|---|
| `griffe-missing-type` | `"No type or annotation for" in msg` | `_classify_warning`, `_build_finding_from_record` | `"recommended"` |
| `griffe-unknown-param` | `"does not appear in the function signature" in msg` | `_classify_warning`, `_build_finding_from_record` | `"required"` |
| `griffe-format-warning` | catch-all (no pattern match) | `_classify_warning`, `_build_finding_from_record` | `"recommended"` |

### Griffe Data Flow

```
CLI (_run_griffe) — separate wiring story
  │
  │  Resolves src_root from config.project_root / config.src_root
  │  Validates src_root exists (caller contract)
  │  Discovers files via discovery.py (DIFF, STAGED, ALL, or FILES mode)
  │
  ▼
check_griffe_compat(src_root, files)
  │
  │  Guard: griffe is None → return []
  │  Guard: not files → return []
  │  _resolve_file_set(files) → file_set: set[Path]  (absolute paths via .resolve())
  │
  │  Attach _WarningCollector to logging.getLogger("griffe")
  │
  ▼
  for child in sorted(src_root.iterdir()):                    ← package discovery
  │  skip if not dir or no __init__.py
  │
  │  griffe.load(child.name, search_paths=[src_root], ...)    ← Phase 1: Load
  │    (catches LoadingError, ModuleNotFoundError, OSError, SyntaxError → continue)
  │
  │  _walk_objects(package, file_set)                          ← Phase 2: Walk & Filter
  │    recursive walk of obj.members.values() (depth ≈ package nesting, typically 3-5)
  │    skip aliases (obj.is_alias)
  │    skip objects without docstrings (obj.docstring is None)
  │    skip objects whose obj.filepath not in file_set (absolute path comparison)
  │
  │  for each yielded object:                                  ← Phase 3: Parse & Collect
  │    before = len(handler.records)
  │    _ = obj.docstring.parsed                                (triggers warnings synchronously)
  │    after = len(handler.records)
  │    for record in handler.records[before:after]:
  │      _build_finding_from_record(record, obj) → Finding | None
  │        _WARNING_PATTERN.match(record.getMessage())         (extract filepath, line, message)
  │        _classify_warning(message) → (rule, category)
  │        Finding(file, line, symbol, rule, message, category)
  │
  ▼
  Remove handler in finally block
  │
  ▼
list[Finding] returned to CLI
```

### Griffe Integration Points

**Griffe ↔ CLI integration (separate wiring story):**
- CLI resolves `src_root` from `config.project_root / config.src_root` (same pattern as `_run_coverage`)
- CLI validates `src_root` exists before calling `check_griffe_compat`
- CLI passes `src_root` + `files` to `check_griffe_compat` — no subprocess calls needed
- CLI handles FR97: griffe availability detection, verbose messaging, stderr warnings
- CLI aggregates `list[Finding]` across all checks
- CLI applies `fail-on` / `warn-on` logic to determine exit code

**Griffe ↔ griffe library integration:**
- `griffe.load()` is the only griffe API call (stable public API, griffe >=1.0)
- `griffe.Object` tree walked via `.members.values()` and `obj.is_alias`
- `obj.docstring.parsed` triggers lazy parsing (Google docstring parser)
- Warning capture via standard Python `logging` — no griffe internals accessed
- File paths from `obj.filepath` (absolute `Path` set by griffe)
- Symbol names from `obj.name`, kind from `obj.kind.value`

**Griffe ↔ Finding integration:**
- Reuses existing frozen `Finding` dataclass — no modifications needed
- `__post_init__` self-validation ensures all fields are valid at construction time
- No griffe-specific `Finding` subclass or extension

**Testing integration:**
- **Unit tests:** Mocked griffe objects (`MagicMock(spec=griffe.Function)`) and log records — no actual package loading
- **Integration tests:** Real `griffe.load()` on `tests/fixtures/griffe_pkg/` — validates full pipeline end-to-end. Requires `pytest.importorskip("griffe")`
- **"Griffe not installed" tests:** `mocker.patch("docvet.checks.griffe_compat.griffe", None)` — isolates import-missing path
- **Multi-package test scenario:** Unit test with mocked `src_root.iterdir()` returning two packages — one loads successfully, one raises `LoadingError`. Verifies `continue` behavior on load failure doesn't abort the entire run

## Griffe Architecture Validation Results

### Coherence Validation

**Decision Compatibility:**
All 6 griffe decisions interlock without contradiction:
- Decision 1 (single file) defines the container for all other decisions
- Decision 2 (logging handler) produces the `LogRecord` objects consumed by Decision 4 (classification) and Decision 6 (message format)
- Decision 3 (load → walk → parse) orchestrates the pipeline, using Decision 2's snapshot pattern for symbol attribution
- Decision 4 (substring classification) is a pure function with no dependencies on other decisions
- Decision 5 (layered exceptions) wraps Decisions 2 and 3 without altering their semantics
- Decision 6 (message format) consumes outputs from Decisions 3 and 4

No version conflicts — griffe `>=1.0` is the only external dependency, and the architecture uses only stable public APIs (`griffe.load()`, `logging.getLogger()`, `obj.docstring.parsed`).

**Note on context analysis text:** The context analysis section (griffe-2) mentions `GriffeLoader` as a loading alternative. Decision 3 chose `griffe.load()` as the authoritative API. When any discrepancy exists between context analysis and decisions, **decisions are authoritative**.

**Pattern Consistency:**
- Naming follows established project conventions: `_check_*`/`_classify_*`/`_build_*`/`_walk_*` prefixes match enrichment and freshness
- Finding construction via dedicated helper (`_build_finding_from_record`) mirrors freshness's `_build_finding` pattern
- File organization (constants → handler → helpers → orchestrator) parallels all other check modules
- `obj.kind.value.capitalize()` for display names consistent with `symbol.kind.capitalize()` in enrichment/freshness

**Structure Alignment:**
- One source file + one unit test file + one integration test file — same pattern as coverage
- Fixture package (`griffe_pkg/`) mirrors `tests/fixtures/` organization
- Module dependency boundary (never imports cli, discovery, config, ast_utils, other checks) consistent with all other checks
- Public API contract (`check_griffe_compat(src_root, files) -> list[Finding]`) matches coverage's pattern

### Requirements Coverage Validation

**Functional Requirements (FR81-FR97): 17/17 covered**

| FR | Summary | Covered By |
|---|---|---|
| FR81 | Missing type annotation detection | Decision 4 (`_classify_warning` → `griffe-missing-type`) |
| FR82 | Unknown parameter detection | Decision 4 (`_classify_warning` → `griffe-unknown-param`) |
| FR83 | Formatting issue detection | Decision 4 (catch-all → `griffe-format-warning`) |
| FR84 | Package loading via griffe | Decision 3 (`griffe.load()` with lazy parsing) |
| FR85 | File filtering to discovered set | Structure (`_walk_objects` + `_resolve_file_set`) |
| FR86 | Finding structure (6 fields) | Decision 6 + existing `Finding` dataclass |
| FR87 | Warning classification (3 rules) | Decision 4 (substring matching, priority order) |
| FR88 | One finding per warning (no dedup) | Patterns (orchestrator snapshot loop, trust griffe) |
| FR89 | Zero findings on well-documented code | Patterns (no warnings → no findings) |
| FR90 | Graceful handling when griffe missing | Decision 5 + Patterns (`griffe is None → return []`) |
| FR91 | Package load failure handling | Decision 5 (explicit exception types → `continue`) |
| FR92 | Future griffe version warnings | Decision 4 (catch-all `griffe-format-warning`) |
| FR93 | Zero findings when all files filtered | Structure (`_walk_objects` skips non-matching files) |
| FR94 | Public API: `(src_root, files) -> list[Finding]` | Decision 3 + Structure (caller contract) |
| FR95 | CLI `docvet griffe` command | Structure (CLI wiring, separate story) |
| FR96 | Temporary logging handler lifecycle | Decision 2 (try/finally) |
| FR97 | CLI griffe availability detection | Structure (CLI wiring, separate story) |

**Non-Functional Requirements (NFR39-NFR48): 10/10 covered**

| NFR | Summary | Covered By |
|---|---|---|
| NFR39 | Sub-10s for 200-file package | Context Analysis (griffe-dominated performance) |
| NFR40 | Negligible docvet overhead | Context Analysis (pure mapping layer) |
| NFR41 | Zero findings on clean code | Decision 4 + Patterns (deterministic output) |
| NFR42 | Silent skip when griffe missing | Decision 5 + Patterns (guard clause) |
| NFR43 | Future-proof classification | Decision 4 (catch-all fallback) |
| NFR44 | Testable with mocked logging | Patterns (mock strategy table) |
| NFR45 | 2-file change ceiling for new rules | Decision 1 + Decision 4 (centralized classification) |
| NFR46 | griffe 1.x compatibility | Decision 3 (stable public APIs only) |
| NFR47 | Shared Finding dataclass reuse | Decision 6 (no modification to Finding) |
| NFR48 | No cross-check imports | Structure (module dependency boundary) |

### Implementation Readiness Validation

**Decision Completeness:**
- All 6 decisions include code examples, rationale, and anti-patterns
- The orchestrator pseudocode in Patterns section is complete and implementable
- Warning classification logic is fully specified (two patterns + catch-all)
- Exception handling lists exact exception types (no ambiguity)

**Structure Completeness:**
- All new files identified with `← NEW` markers
- Fixture package content spec defines minimum required functions
- Integration test note specifies `pytest.importorskip` requirement
- Multi-package test scenario explicitly called out
- Integration test path resolution: use `Path(__file__).parent.parent / "fixtures" / "griffe_pkg"` or a conftest fixture to locate the fixture package — do not hardcode absolute paths

**Pattern Completeness:**
- Mock strategy mapping table covers all test targets
- `_WarningCollector` focused test expectations defined
- "Griffe not installed" isolation approach specified
- Finding field sources fully mapped (file, line, symbol, rule, message, category)
- Multi-package test should assert finding order matches alphabetical package order (verifies `sorted(src_root.iterdir())`)

**Type hint safety (enforcement clarification):**
- `from __future__ import annotations` (required in every project file) defers all annotation evaluation to string form. This makes `GriffeObject` references in function signatures safe at runtime even when griffe is not installed — the string `"GriffeObject"` is never evaluated
- Corollary: **never add runtime `isinstance` checks against griffe types** (e.g., `isinstance(obj, griffe.Function)`). These would fail when griffe is not installed. Use duck typing or `obj.kind` checks instead

### Gap Analysis Results

**Critical Gaps:** None identified. All 17 FRs and 10 NFRs have explicit architectural coverage.

**Important Gaps:** None — party mode reviews across 4 rounds surfaced and resolved all 30 findings before implementation begins.

**Scope Boundaries (not gaps):**
1. **Duplicate warning deduplication** — deferred to post-MVP. Trust griffe for now; add dedup by `(file, line, message)` if observed in practice
2. **Per-rule disable toggles** — deferred to post-MVP. No `[tool.docvet.griffe]` config section in MVP
3. **Numpy/Sphinx docstring styles** — out of scope. Google-style only, consistent with all other checks
4. **`_walk_objects` recursion depth** — documented as MVP-acceptable (typical depth 3-5). Convert to iterative stack if `RecursionError` reported

### Architecture Completeness Checklist

**Requirements Analysis**

- [x] Project context thoroughly analyzed (17 FRs, 10 NFRs)
- [x] Scale and complexity assessed (low-medium, simpler than enrichment/freshness)
- [x] Technical constraints identified (optional dep, logging handler, package-level loading)
- [x] Cross-cutting concerns mapped (optional dep handling, handler lifecycle, path normalization, warning dedup)

**Architectural Decisions**

- [x] 6 decisions documented with rationale, code examples, and anti-patterns
- [x] Technology stack constrained to griffe 1.x + stdlib logging + pathlib
- [x] Integration patterns defined (griffe ↔ CLI, griffe ↔ Finding, griffe ↔ griffe library)
- [x] Performance addressed (griffe-dominated, negligible docvet overhead)

**Implementation Patterns**

- [x] Naming conventions established (`_classify_*`, `_walk_*`, `_build_*`, `_resolve_*`)
- [x] Structure patterns defined (file organization order, conditional import block)
- [x] Warning parsing patterns specified (regex for log records, substring for classification)
- [x] Process patterns documented (snapshot loop, try/finally cleanup, guard clauses)
- [x] Type hint safety clarified (`from __future__ import annotations` makes griffe types safe)

**Project Structure**

- [x] Complete directory structure with NEW markers
- [x] Component boundaries established (public API, module dependency, data boundary, caller contract)
- [x] Integration points mapped (CLI, griffe library, Finding, testing)
- [x] Requirements-to-structure mapping complete (FR→file table, rule→function table)
- [x] Test path resolution documented for integration fixture

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High

**Key Strengths:**
- Complete FR and NFR coverage with no critical gaps
- All 6 decisions interlock coherently — no contradictions or incompatibilities
- Code examples and anti-patterns provide clear implementation guidance for AI agents
- Per-object snapshot pattern is architecturally simpler than alternatives (no reverse-lookup needed)
- Four rounds of party mode review resolved 30 findings before implementation begins
- Mock strategy mapping table eliminates test design ambiguity
- Explicit caller contract (CLI validates `src_root`) prevents boundary confusion
- Type hint safety explicitly documented — prevents runtime griffe type errors

**Areas for Future Enhancement:**
- Duplicate warning deduplication (observe first, add if needed)
- Per-rule disable toggles via `[tool.docvet.griffe]` config
- Iterative `_walk_objects` for pathological nesting depths
- Custom griffe parser options (`warn_unknown_params`, `warn_missing_types`)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all 6 architectural decisions exactly as documented
- Use implementation patterns consistently — conditional import, snapshot loop, substring classification
- Respect project structure and boundaries — no cross-check imports, no I/O beyond griffe's own
- Refer to this document for all architectural questions before escalating
- Use the mock strategy mapping table when writing tests
- When context analysis text conflicts with decisions, **decisions are authoritative**
- Never add runtime `isinstance` checks against griffe types — use duck typing or `obj.kind`

**Prerequisite:** Epic definition must be completed via the BMAD epic creation workflow before story creation begins. The architecture defines the two-story decomposition but does not create the epic or stories.

**Implementation Sequence (two-story pattern):**

**Story 1 — Core function + tests:**
- AC sketch:
  - (a) `check_griffe_compat` returns findings for all 3 rule types given appropriate warnings
  - (b) Returns `[]` when griffe is not installed (`griffe is None`)
  - (c) Returns `[]` when `files` is empty
  - (d) Skips packages that fail to load (continues to next package)
  - (e) Handler removed after execution (try/finally)
  - (f) File filtering restricts findings to discovered file set
  - (g) Integration smoke test passes against `tests/fixtures/griffe_pkg/`

**Story 2 — CLI wiring:**
- AC sketch:
  - (a) `docvet griffe` runs standalone and produces formatted output
  - (b) `docvet check` includes griffe findings alongside other checks
  - (c) Verbose mode shows skip message when griffe not installed
  - (d) `src_root` resolved from `config.project_root / config.src_root`
  - (e) Stderr warning when griffe in `fail-on` but not installed
