# Story 3.1: Missing Examples Detection

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want to detect public symbols and `__init__.py` modules that lack an `Examples:` section,
so that key API surfaces include usage examples for consumers.

## Acceptance Criteria

1. **Given** a class with a docstring and no `Examples:` section, and `config.require_examples = ["class"]`
   **When** `check_enrichment` is called
   **Then** it returns a `Finding` with `rule="missing-examples"`, `category="recommended"`

2. **Given** a protocol with a docstring and no `Examples:` section, and `config.require_examples = ["protocol"]`
   **When** `check_enrichment` is called
   **Then** it returns a `Finding` with `rule="missing-examples"`, `category="recommended"`

3. **Given** a class with a docstring and no `Examples:` section, and `config.require_examples = ["dataclass"]` (class not in list)
   **When** `check_enrichment` is called
   **Then** it returns zero findings for `missing-examples` on that class

4. **Given** `config.require_examples = []` (empty list)
   **When** `check_enrichment` is called
   **Then** it returns zero findings for `missing-examples` on any symbol (rule fully disabled)

5. **Given** the default config (`require_examples = ["class", "protocol", "dataclass", "enum"]`)
   **When** `check_enrichment` is called on a dataclass with no `Examples:` section
   **Then** it returns a `Finding` for `missing-examples`

6. **Given** a symbol with a docstring containing an `Examples:` section
   **When** `check_enrichment` is called
   **Then** it returns zero findings for `missing-examples` on that symbol

7. **Given** an `__init__.py` module with a module-level docstring and no `Examples:` section
   **When** `check_enrichment` is called with `file_path` ending in `__init__.py` and `require_examples` is non-empty
   **Then** it returns a `Finding` with `rule="missing-examples"` for the module-level symbol

8. **Given** a symbol with no docstring
   **When** `check_enrichment` is called
   **Then** it returns zero findings for `missing-examples` (undocumented symbols skipped)

## Tasks / Subtasks

- [ ] Task 1: Implement `_is_protocol` and `_is_enum` helpers (AC: #2, #5)
  - [ ] 1.1 Create `_is_protocol(node: ast.ClassDef) -> bool` — check bases for `Protocol` or `typing.Protocol`
  - [ ] 1.2 Create `_is_enum(node: ast.ClassDef) -> bool` — check bases for `Enum`, `IntEnum`, `StrEnum`, `Flag`, `IntFlag` or `enum.*` variants
  - [ ] 1.3 Add unit tests for both helpers

- [ ] Task 2: Implement `_check_missing_examples` rule function (AC: #1-8)
  - [ ] 2.1 Create `_check_missing_examples(symbol, sections, node_index, config, file_path) -> Finding | None`
  - [ ] 2.2 Guard: if `"Examples"` in sections, return `None` (AC #6)
  - [ ] 2.3 Module branch: if `symbol.kind == "module"` and `_is_init_module(file_path)`, return Finding (AC #7)
  - [ ] 2.4 Class branch: classify inline using existing helpers (`_is_dataclass` → `"dataclass"`, `_is_protocol` → `"protocol"`, `_is_enum` → `"enum"`, else → `"class"`), check if type in `config.require_examples` (AC #1-5)
  - [ ] 2.5 Function/method: return `None` (not supported in config)
  - [ ] 2.6 Return `Finding` with `rule="missing-examples"`, `category="recommended"`
  - [ ] 2.7 Add direct `_check_missing_examples` unit tests

- [ ] Task 3: Wire into orchestrator (AC: #4, #8)
  - [ ] 3.1 Add dispatch after `_check_missing_attributes` block: `if config.require_examples:` gate
  - [ ] 3.2 Add orchestrator integration tests
  - [ ] 3.3 Update "all rules disabled" test (add source with class+docstring, set `require_examples=[]`)

- [ ] Task 4: Edge case and regression tests (all AC)
  - [ ] 4.1 Test: class with Examples section returns no finding (AC #6)
  - [ ] 4.2 Test: undocumented symbol returns no finding (AC #8)
  - [ ] 4.3 Test: empty `require_examples` list returns no findings (AC #4)
  - [ ] 4.4 Test: type not in list returns no finding (AC #3)
  - [ ] 4.5 Test: `__init__.py` module with Examples section returns no finding
  - [ ] 4.6 Test: non-`__init__.py` module returns no finding
  - [ ] 4.7 Test: NamedTuple/TypedDict do NOT trigger (not covered by any config value)
  - [ ] 4.8 Test: nested class inside function does not trigger (scope boundary)
  - [ ] 4.9 Test: `class Foo(Protocol, ABC):` classifies as protocol (multiple inheritance)
  - [ ] 4.10 Test: `class Color(str, Enum):` classifies as enum (mixin bases)

## Dev Notes

### Architecture Pattern: List-Config Gating (NEW)

This is the **first and only** `_check_*` function that inspects `config` internally. All other rules use boolean gating in the orchestrator only.

**Orchestrator pattern:**
```python
# Empty list is falsy — disables rule entirely (AC #4)
if config.require_examples:
    if f := _check_missing_examples(symbol, sections, node_index, config, file_path):
        findings.append(f)
```

**Inside `_check_missing_examples`:**
Classify the symbol inline (no separate helper function) and check if the classified type is in `config.require_examples`. This is the only `_check_*` function that reads config — justified because the gating is symbol-type-specific, not a simple on/off. Classification uses existing helpers: `_is_dataclass` → `"dataclass"`, `_is_protocol` → `"protocol"`, `_is_enum` → `"enum"`, else → `"class"`.

### Symbol Kind to Config Type Mapping

`Symbol.kind` values: `"function"`, `"class"`, `"method"`, `"module"`

Config type names in `require_examples`: `"class"`, `"protocol"`, `"dataclass"`, `"enum"`

**Mapping logic (inline in `_check_missing_examples`, for `symbol.kind == "class"`):**
1. `_is_dataclass(node)` → `"dataclass"` (means `@dataclass` decorator ONLY)
2. `_is_protocol(node)` → `"protocol"`
3. `_is_enum(node)` → `"enum"`
4. None of the above → `"class"` (plain class)

**Design decisions (settled in party-mode review):**
- **`"dataclass"` means `@dataclass` only.** NamedTuple and TypedDict do NOT map to any config type name — they are excluded from `missing-examples` detection entirely. If users want coverage for these, new config entries (`"namedtuple"`, `"typeddict"`) can be added in a future story.
- **No `_classify_for_examples` helper.** Classification is done inline inside `_check_missing_examples` using existing `_is_*` helpers. This follows the industry pattern (ruff, pylint) of keeping classification minimal rather than adding abstraction layers.
- **FR28 (config value validation) is deferred.** Validating that `require-examples` entries are recognized type names is out of scope for this story. If a user puts an unrecognized value like `"function"` in the list, it silently matches nothing. Validation will be added in a config-hardening story.

**Module handling:** Modules (`symbol.kind == "module"`) in `__init__.py` files trigger when `require_examples` is non-empty (any non-empty list enables module-level checking per AC #7). This is a different gating semantic — modules don't need their type name in the list. Non-`__init__.py` modules never trigger.

### Finding Message Format

Follow established patterns:
- Class: `Class 'Parser' has no Examples: section`
- Protocol: `Protocol 'Handler' has no Examples: section`
- Dataclass: `Dataclass 'Config' has no Examples: section`
- Enum: `Enum 'Color' has no Examples: section`
- Module: `Module '<module>' has no Examples: section`

### New Helper Functions Needed

**`_is_protocol(node: ast.ClassDef) -> bool`:**
- Pattern 1: `class Foo(Protocol):` — `ast.Name` with `id == "Protocol"`
- Pattern 2: `class Foo(typing.Protocol):` — `ast.Attribute` with `attr == "Protocol"`

**`_is_enum(node: ast.ClassDef) -> bool`:**
- Pattern 1: `class Color(Enum):` — `ast.Name` with `id in {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"}`
- Pattern 2: `class Color(enum.Enum):` — `ast.Attribute` with `attr in {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"}`

Follow same base-class inspection pattern as `_is_namedtuple` and `_is_typeddict`.

### Taxonomy-Table Ordering

Insert `_check_missing_examples` **after** `_check_missing_attributes` in both:
1. Function definition order in `enrichment.py`
2. Dispatch order in `check_enrichment` orchestrator

Full canonical order: `missing-raises`, `missing-yields`, `missing-receives`, `missing-warns`, `missing-other-parameters`, `missing-attributes`, `missing-typed-attributes`, `missing-examples`, `missing-cross-references`, `prefer-fenced-code-blocks`

**NOTE:** Per taxonomy table, `missing-typed-attributes` comes BEFORE `missing-examples`. However, `missing-typed-attributes` is Story 3.2 and not yet implemented. Place `_check_missing_examples` after `_check_missing_attributes` with a comment noting the taxonomy gap. When Story 3.2 adds `missing-typed-attributes`, it will be inserted between `_check_missing_attributes` and `_check_missing_examples`.

### Existing Helpers to Reuse (DO NOT REWRITE)

- `_is_dataclass(node)` — `enrichment.py:464` — detects `@dataclass` decorator (used for `"dataclass"` classification)
- `_is_init_module(file_path)` — `enrichment.py:554` — detects `__init__.py` paths (used for module branch)
- `_parse_sections(docstring)` — `enrichment.py:53` — extracts section headers
- `_build_node_index(tree)` — `enrichment.py:77` — O(1) node lookup

**Not used by this rule** (NamedTuple/TypedDict are excluded from missing-examples):
- `_is_namedtuple(node)` — `enrichment.py:504`
- `_is_typeddict(node)` — `enrichment.py:530`

### Test Conventions

- Use `_make_symbol_and_index(source)` helper for direct `_check_*` tests (returns first non-module symbol)
- Use `check_enrichment(source, tree, config, file_path)` for orchestrator integration tests
- Disable all other rules in config when testing `missing-examples` in isolation
- Use `EnrichmentConfig(require_raises=False, require_yields=False, require_warns=False, require_receives=False, require_other_parameters=False, require_attributes=False, require_examples=["class"])` pattern
- The "all rules disabled" test must be updated to include a symbol that would trigger `missing-examples` but doesn't because `require_examples=[]`

### Critical Learnings from Previous Epics

1. **Do NOT use `ast.walk()`** for body-level inspection — use scope-aware iterative walk. (However, `missing-examples` is primarily docstring-only, so body walk is NOT needed for this rule.)
2. **First implementation of new pattern gets extra review scrutiny** — the list-config gating pattern is new.
3. **The "all rules disabled" test breaks every time a new rule is added** — update it proactively.
4. **Cross-platform paths:** `_is_init_module` already handles both `/` and `\` separators — reuse it, don't reimagine.
5. **Node retrieval guard:** When accessing `node_index.get(symbol.line)`, always handle `None` return (module-level symbols won't have a node).

### Edge Cases to Test Proactively

- **Scope boundary:** Nested class inside a function should NOT trigger missing-examples for the outer function
- **Multiple inheritance:** `class Foo(Protocol, ABC):` should still classify as protocol
- **Cross-platform paths:** `_is_init_module` covers this, but verify with Windows-style paths in tests
- **Decorated protocols:** `@runtime_checkable class Foo(Protocol):` should still classify as protocol
- **Abstract enums:** `class Color(str, Enum):` should still classify as enum (mixin bases)

### Project Structure Notes

- All changes in 3 files max: `enrichment.py`, `test_enrichment.py`, (sprint-status.yaml)
- Config already has `require_examples` field with correct defaults — NO config changes needed
- `_SECTION_PATTERN` already recognizes `Examples:` — NO section parser changes needed
- Place new helpers (`_is_protocol`, `_is_enum`) before `_check_missing_examples` definition
- Place `_check_missing_examples` after `_check_missing_attributes` (line ~727)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1 lines 584-624]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 1 — uniform _check_* signature]
- [Source: _bmad-output/planning-artifacts/architecture.md#Config gating clarification — list toggle]
- [Source: _bmad-output/planning-artifacts/architecture.md#Taxonomy table ordering line 340]
- [Source: _bmad-output/planning-artifacts/architecture.md#Rule dependencies table line 549]
- [Source: _bmad-output/planning-artifacts/prd.md#FR9, FR10, FR27, FR28 lines 295, 448-451]
- [Source: _bmad-output/implementation-artifacts/2-2-plain-class-and-init-py-module-attributes-detection.md — _is_init_module pattern]
- [Source: _bmad-output/implementation-artifacts/epic-1-retrospective.md — scope-aware walk lesson]
- [Source: _bmad-output/implementation-artifacts/epic-2-retro-2026-02-08.md — novel edge case lesson]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
