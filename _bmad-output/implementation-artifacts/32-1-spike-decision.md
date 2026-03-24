# Story 32.1: Fix Feasibility Spike — Decision Document

**Date**: 2026-03-23
**Status**: GO — proceed to Story 32.2

---

## 1. Insertion Strategy Evaluation

### 1.1 String ops + AST line numbers (CHOSEN)

**Approach**: Use `ast.parse()` to get the tree, `Symbol.docstring_range` for line ranges, `source.splitlines(keepends=True)` for line-level access, and string splicing for insertion.

**How it works**:
1. Parse findings into `{symbol_line: [findings]}` groups
2. Map `def`/`class` line numbers to AST nodes via `ast.walk()`
3. For each symbol (processed in **reverse** line order to preserve line numbers):
   a. Get `docstring_range` → `(start_line, end_line)` (1-based, inclusive)
   b. Check existing sections via regex match for idempotency
   c. Detect indentation from the closing `"""` line (multi-line) or opening line (one-liner)
   d. For one-liners: expand `"""Summary."""` to multi-line format + sections
   e. For multi-line: insert scaffold lines before the closing `"""` line
4. Return `"".join(lines)`

**Indentation detection**: The closing `"""` line's leading whitespace matches section header indentation in Google-style docstrings. For one-liners, the opening `"""` line's leading whitespace is used. Both are reliable because Python syntax enforces consistent indentation within a function/class body.

**Pros**:
- Zero runtime dependencies (stdlib `ast`, `re` only) — satisfies NFR3/NFR4
- Leverages existing `Symbol.docstring_range` from `ast_utils.py`
- Simple, testable, debuggable — ~120 lines of core logic
- Byte-for-byte preservation of existing content (only inserts, never modifies)
- Deterministic and idempotent by construction

**Cons**:
- Must handle one-liner expansion as a special case
- Heuristic-based for edge cases (raw docstrings, single quotes)
- No whitespace preservation guarantees beyond line-level (acceptable — docstrings are line-oriented)

### 1.2 textwrap/inspect for indentation

Evaluated `textwrap.dedent()` and `inspect.cleandoc()` for indentation detection.

**Finding**: Neither is suitable. `textwrap.dedent()` removes indentation rather than detecting it. `inspect.cleandoc()` normalizes the docstring text, discarding the original formatting we need to preserve.

**Better approach**: Direct indentation detection from the closing `"""` line is simpler and more reliable than any stdlib utility. The closing line's leading whitespace IS the content indentation, by Google-style convention.

### 1.3 libcst (REJECTED)

**What it offers**: Full Concrete Syntax Tree that preserves all whitespace, comments, and formatting. `CSTTransformer` enables safe tree modifications.

**Why rejected**:
- **NFR4 violation**: "Fix insertion uses AST line numbers for positioning — no libcst dependency" (architecture spec)
- **NFR3 violation**: Adds a runtime dependency beyond typer
- **Overkill**: We only insert text at known positions — no tree transformation needed
- **Heavy**: ~2MB package for a task achievable in ~120 lines of stdlib code

### 1.4 Decision

**Chosen approach**: String ops + AST line numbers (1.1).

**Rationale**: Satisfies all architectural constraints (zero runtime deps, AST line numbers for positioning). The POC demonstrates reliable operation across 14 test scenarios including all edge cases. The approach is simple enough to fully unit-test and maintain.

---

## 2. Proof-of-Concept Results

### 2.1 Core function signature

```python
def scaffold_missing_sections(
    source: str,
    findings: list[Finding],
) -> str:
    """Insert scaffolded sections into docstrings based on findings."""
```

The POC takes raw source text and a list of findings, returns modified source. It parses the AST internally (not passed in) to ensure the tree matches the source. For the production implementation (Story 32.2), the tree should be passed in to avoid double-parsing.

### 2.2 AC verification results

| AC | Test | Result |
|----|------|--------|
| 1 | One-line docstring → valid Python after insertion | **PASS** — `ast.parse()` succeeds, `docvet enrichment` produces zero findings for scaffolded sections |
| 2 | Multi-section preservation, byte-for-byte | **PASS** — `"    Args:\n        data: The input data.\n"` preserved exactly, Raises inserted after Returns |
| 3 | Second run produces identical output | **PASS** — `first_pass == second_pass` verified |

### 2.3 Edge case results

| Edge Case | Result | Notes |
|-----------|--------|-------|
| Nested class method | PASS | Correct 8-space indentation detected from closing `"""` |
| Multiple missing sections | PASS | Sections inserted in canonical Google-style order |
| Decorated function (@staticmethod) | PASS | `node.lineno` is the `def` line, not decorator — works correctly |
| Dataclass Attributes | PASS | Class-level docstring expanded with Attributes section |
| Empty findings | PASS | Source returned unchanged |
| @property | PASS | No crash, no modification |
| Async function | PASS | `AsyncFunctionDef` handled alongside `FunctionDef` |
| Raw docstring (r"""...""") | PASS | `r` prefix preserved on opening line, insertion works |
| Single quotes ('''...''') | PASS | Quote style detected and preserved |
| Module-level docstring | PASS | Only the targeted function's docstring modified |
| Tab indentation | PASS | Tab-based indent detected and used for sections |
| Idempotency after scaffold | PASS | Existing `Raises:` section detected, no duplicate insertion |

### 2.4 Docvet integration verification

After scaffolding a function with `missing-raises` and `missing-returns` findings:
```
$ docvet enrichment --files /tmp/ac1_full.py
Vetted 1 files [enrichment] — no findings. (0.0s)
```

The scaffolded `[TODO: describe]` placeholders satisfy enrichment rules because the section headers (`Raises:`, `Returns:`) are present — enrichment checks for section *presence*, not content quality.

---

## 3. Edge Case Catalog

### 3.1 Handled by POC

| Category | Edge Case | Handling Strategy |
|----------|-----------|-------------------|
| **Quote styles** | `"""..."""`, `'''...'''`, `r"""..."""` | Quote detection via `str.find()` for both styles; `r` prefix preserved on opening line |
| **Indentation** | Spaces (any level), tabs, mixed (tab + spaces) | Closing `"""` line indentation used for multi-line; opening line for one-liners |
| **Docstring forms** | One-liner, multi-line, multi-line with existing sections | One-liners expanded to multi-line before insertion; multi-line inserts before closing `"""` |
| **Symbol types** | Functions, async functions, methods, classmethods, staticmethods, dataclasses | All use `FunctionDef`/`AsyncFunctionDef`/`ClassDef` in AST — handled uniformly |
| **Decorators** | `@staticmethod`, `@classmethod`, `@property`, `@dataclass`, `@overload` | Finding `line` is the `def`/`class` keyword line, not decorator — node lookup correct |
| **Nesting** | Methods in classes, deeply nested classes | Each symbol processed independently by line number |
| **Multiple findings** | Multiple missing sections on one symbol | Deduplicated, sorted by canonical order, inserted as block |
| **Blank line handling** | Trailing blank before `"""`, no trailing blank | Pre-insertion blank-line check avoids double-blank separators |

### 3.2 Not handled (known limitations for Story 32.2)

| Edge Case | Impact | Recommended Handling |
|-----------|--------|---------------------|
| **Closing `"""` on same line as content** (e.g., `    content."""`) | Rare in Google-style | Treat as multi-line; find `"""` within last line and split |
| **Empty docstrings** (`"""  """`, `""" """`) | Very rare | Treat as one-liner; expand with summary placeholder |
| **Docstring with only whitespace** | Very rare | Same as empty — expand |
| **f-string in docstring position** | Invalid per PEP — AST won't parse it as docstring | No action needed — `get_docstring_range()` returns None |
| **Encoding markers in docstring** | Extremely rare | Likely works (line-level ops don't modify content) but untested |
| **Windows line endings (CRLF)** | POC detects `\r\n` from source | Production should normalize or preserve consistently |
| **Sphinx/RST style scaffolding** | POC only generates Google-style sections | Story 32.2 should respect the file's detected style |

### 3.3 Not applicable (architecture prevents)

| Edge Case | Why Not Applicable |
|-----------|-------------------|
| **Comments between docstring lines** | Python doesn't allow comments inside triple-quoted strings |
| **String concatenation docstrings** | AST doesn't recognize `"""a""" """b"""` as a docstring |
| **Type stub files (.pyi)** | Stubs typically have no implementation body — no findings to scaffold |

---

## 4. Scaffold Finding Category Design

### 4.1 Category: `"scaffold"`

Extends `Finding.category` from `Literal["required", "recommended"]` to `Literal["required", "recommended", "scaffold"]`.

```python
@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    symbol: str
    rule: str
    message: str
    category: Literal["required", "recommended", "scaffold"]
```

**Category semantics**: `category = "scaffold"` is **blocking by default** — same exit-code behavior as `required` findings. Scaffold findings indicate sections that exist structurally but have placeholder content that must be filled in. The `docvet fix` command inserts the scaffolding; scaffold findings then enforce that users complete the content.

**Rationale for blocking behavior**: The purpose of `docvet fix` is to reduce friction, not to silence findings. A scaffolded `Raises: [TODO: describe]` is better than nothing (the section header exists, so the enrichment rule is satisfied), but the placeholder content is not documentation. Scaffold findings ensure the user follows through.

### 4.2 Placeholder marker format

**Chosen format**: `[TODO: describe]`

**Alternatives evaluated**:

| Format | Pros | Cons |
|--------|------|------|
| `[TODO: describe]` | Concise, grep-friendly, conventional bracket syntax | Generic — no section-specific guidance |
| `TODO(docvet): describe` | Matches TODO comment convention | Could be confused with code TODOs |
| `... (fill in)` | Minimal | Not grep-friendly, ambiguous |
| `${DESCRIBE}` | Template-like | Unfamiliar, could be confused with shell vars |

**Decision**: `[TODO: describe]` — concise, grep-friendly (`grep -r '\[TODO: describe\]'`), and the bracket syntax clearly marks it as a placeholder that must be replaced.

**Section-specific enhancement** (recommended for Story 32.2): When the finding message contains specific items (e.g., "raises ValueError, TypeError"), the placeholder can be enriched:

```
Raises:
    ValueError: [TODO: describe when this is raised]
    TypeError: [TODO: describe when this is raised]
```

This provides better guidance than a generic `[TODO: describe]`. Implementation: parse exception names from the finding message using a simple regex or structured finding data.

### 4.3 Actionable message format

**Format**: `"Fill in [Section] for '[symbol]' — describe [items]"`

**Examples**:
- `"Fill in Raises for 'validate_input' — describe ValueError, TypeError"`
- `"Fill in Yields for 'generate_items' — describe yielded values"`
- `"Fill in Attributes for 'Config' — describe host, port"`

**Rule name**: `scaffold-incomplete` (kebab-case, follows existing convention)

**Why actionable messages matter**: When `docvet check` runs after `docvet fix`, scaffold findings must clearly tell the user what to do. A message like `"Fill in Raises for 'validate_input'"` is more useful than `"Incomplete Raises section"`.

### 4.4 Exit code behavior

**Decision**: `scaffold` findings produce **non-zero exit code** (same as `required`).

| Finding category | Exit behavior | Rationale |
|------------------|---------------|-----------|
| `required` | Non-zero exit | Missing section — must fix |
| `recommended` | Zero exit (unless `--fail-on recommended`) | Style suggestion — optional |
| `scaffold` | Non-zero exit | Placeholder present — must complete |

This means `docvet fix` followed by `docvet check` will still fail until the user fills in the placeholders. This is intentional — the fix command scaffolds, the check command enforces completion.

**Configuration**: `[tool.docvet.enrichment] fail_on_scaffold = true` (default). Users can set `false` to treat scaffolds as warnings during development.

> **Design note for Story 32.2**: The existing config uses a top-level `fail-on` list of check names (`fail_on: list[str]` on `DocvetConfig`). The `fail_on_scaffold` boolean proposed above introduces a second dimension of fail-on control (per-category vs per-check). Story 32.2 must decide whether to: (a) use this per-category boolean under `[tool.docvet.enrichment]`, (b) extend the existing `fail-on` list pattern (e.g., `fail-on = ["enrichment:scaffold"]`), or (c) add a separate top-level key like `scaffold-behavior = "fail" | "warn"`. Evaluate consistency with the existing config surface before implementing.

### 4.5 Reporting integration

**Terminal output**: Scaffold findings display with `[scaffold]` category tag:
```
src/pkg/mod.py:42: scaffold-incomplete Fill in Raises for 'validate' — describe ValueError [scaffold]
```

**JSON output**: `"category": "scaffold"` in the findings array. No schema change needed — the field is already a string.

**Markdown report**: Scaffold findings appear in a dedicated "Scaffold (Incomplete)" section, separate from Required and Recommended.

**Summary counts**: `--summary` output includes scaffold count:
```
Vetted 10 files — 3 findings (1 required, 0 recommended, 2 scaffold)
```

### 4.6 Integration with `docvet fix`

The workflow:
1. **`docvet fix`**: Runs enrichment check → collects `required` findings with `missing-*` rules → calls `scaffold_missing_sections()` → writes modified files → re-runs enrichment check → emits `scaffold` findings for the newly inserted placeholders
2. **User edits**: Fills in `[TODO: describe]` placeholders with real content
3. **`docvet check`**: Detects remaining `[TODO: describe]` markers → emits `scaffold-incomplete` findings → non-zero exit until all placeholders are replaced

**Detection of scaffold markers**: The `scaffold-incomplete` rule scans docstring content for `[TODO: describe]` (or a configurable pattern). This is a new enrichment rule separate from the existing `missing-*` rules.

---

## 5. Go/No-Go Recommendation

### GO — Proceed to Story 32.2

**Confidence**: High. The POC demonstrates that string ops + AST line numbers is a reliable, zero-dependency insertion strategy that handles all common docstring formats and edge cases.

**Key validated assumptions**:
1. `Symbol.docstring_range` provides accurate line ranges for all docstring forms
2. Closing `"""` line indentation reliably indicates section header indentation
3. Reverse-order processing preserves line numbers across multiple insertions
4. Existing section detection via `_SECTION_PATTERN` enables idempotency
5. One-liner expansion to multi-line is straightforward (quote detection + line splicing)
6. docvet's own enrichment rules recognize scaffolded sections as present (zero findings)

**Risk assessment**:

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Non-standard docstring formatting breaks insertion | Low | POC handles all common patterns; edge cases documented |
| Line ending inconsistency across platforms | Low | POC detects and preserves line ending style |
| Performance with large files | Low | O(findings × symbols) per file — acceptable for typical codebases |
| Scaffold category breaks existing JSON consumers | Medium | Additive change — `"scaffold"` is a new category value, not a schema change. Downstream consumers that match on `"required"` or `"recommended"` will ignore scaffolds by default |

**Story 32.2 scope**:
1. Production implementation of `scaffold_missing_sections()` in `src/docvet/checks/fix.py`
2. `scaffold-incomplete` enrichment rule (detects `[TODO: describe]` markers)
3. Extension of `Finding.category` to include `"scaffold"`
4. Integration with reporting, exit codes, JSON output
5. CLI wiring: `docvet fix` subcommand with `--dry-run`, `--check` discovery flags

---

## 6. POC Source Code

The complete proof-of-concept implementation (~120 lines of core logic + ~200 lines of tests). This code is NOT production — Story 32.2 builds the real engine.

```python
"""POC: scaffold_missing_sections — AST + string ops insertion strategy."""

from __future__ import annotations

import ast
import re

# Canonical Google-style section order
SECTION_ORDER = [
    "Args", "Other Parameters", "Returns", "Yields", "Receives",
    "Raises", "Warns", "Attributes", "Examples", "See Also",
]

# Map enrichment rule names to section names
RULE_TO_SECTION: dict[str, str] = {
    "missing-raises": "Raises",
    "missing-yields": "Yields",
    "missing-receives": "Receives",
    "missing-warns": "Warns",
    "missing-other-parameters": "Other Parameters",
    "missing-attributes": "Attributes",
    "missing-typed-attributes": "Attributes",
    "missing-examples": "Examples",
    "missing-cross-references": "See Also",
    "missing-returns": "Returns",
}

SECTION_PATTERN = re.compile(
    r"^\s*(Args|Returns|Raises|Yields|Receives|Warns"
    r"|Other Parameters|Attributes|Examples|See Also"
    r"|Notes|References|Warnings|Extended Summary|Methods):\s*$",
    re.MULTILINE,
)

TODO_MARKER = "[TODO: describe]"


def _get_docstring_range(node: ast.AST) -> tuple[int, int] | None:
    """Get line range (1-based, inclusive) of a node's docstring."""
    if not isinstance(
        node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    ):
        return None
    if not node.body:
        return None
    first = node.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return (first.lineno, first.end_lineno or first.lineno)
    return None


def _detect_indent(lines: list[str], doc_start_0: int, doc_end_0: int) -> str:
    """Detect docstring section header indentation."""
    if doc_start_0 != doc_end_0:
        closing = lines[doc_end_0]
        stripped = closing.lstrip()
        return closing[: len(closing) - len(stripped)]
    line = lines[doc_start_0]
    stripped = line.lstrip()
    return line[: len(line) - len(stripped)]


def scaffold_missing_sections(source: str, findings: list[dict]) -> str:
    """Insert scaffolded sections into docstrings based on findings."""
    if not findings:
        return source

    tree = ast.parse(source)

    by_line: dict[int, list[dict]] = {}
    for f in findings:
        if f["rule"] in RULE_TO_SECTION:
            by_line.setdefault(f["line"], []).append(f)
    if not by_line:
        return source

    node_map: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node_map[node.lineno] = node

    lines = source.splitlines(keepends=True)
    newline = "\n"
    for ln in lines:
        if ln.endswith("\r\n"):
            newline = "\r\n"
            break
        if ln.endswith("\n"):
            break

    for sym_line in sorted(by_line.keys(), reverse=True):
        node = node_map.get(sym_line)
        if not node:
            continue
        doc_range = _get_docstring_range(node)
        if not doc_range:
            continue

        doc_start_0, doc_end_0 = doc_range[0] - 1, doc_range[1] - 1
        docstring = ast.get_docstring(node, clean=False) or ""
        existing = set(SECTION_PATTERN.findall(docstring))

        to_add = []
        seen = set()
        for f in by_line[sym_line]:
            s = RULE_TO_SECTION.get(f["rule"])
            if s and s not in existing and s not in seen:
                to_add.append(s)
                seen.add(s)
        if not to_add:
            continue

        order_map = {s: i for i, s in enumerate(SECTION_ORDER)}
        to_add.sort(key=lambda s: order_map.get(s, 999))
        indent = _detect_indent(lines, doc_start_0, doc_end_0)

        if doc_start_0 == doc_end_0:  # One-liner
            content = lines[doc_start_0].rstrip("\r\n")
            for q in ('"""', "'''"):
                first_q = content.find(q)
                last_q = content.rfind(q)
                if first_q != -1 and last_q != -1 and first_q != last_q:
                    summary = content[first_q + 3 : last_q].strip()
                    prefix = content[:first_q]
                    new_lines = [f"{prefix}{q}{summary}{newline}"]
                    for section in to_add:
                        new_lines.extend([
                            newline,
                            f"{indent}{section}:{newline}",
                            f"{indent}    {TODO_MARKER}{newline}",
                        ])
                    new_lines.append(f"{indent}{q}{newline}")
                    lines[doc_start_0 : doc_end_0 + 1] = new_lines
                    break
            continue

        # Multi-line
        scaffold = []
        prev = lines[doc_end_0 - 1].rstrip("\r\n") if doc_end_0 > 0 else ""
        prev_blank = not prev.strip()
        for i, section in enumerate(to_add):
            if not (i == 0 and prev_blank):
                scaffold.append(newline)
            scaffold.append(f"{indent}{section}:{newline}")
            scaffold.append(f"{indent}    {TODO_MARKER}{newline}")
        lines[doc_end_0:doc_end_0] = scaffold

    return "".join(lines)
```

**Test verification summary** (14/14 pass):
- AC1: one-liner expansion ✓
- AC2: multi-section byte-for-byte preservation ✓
- AC3: idempotency ✓
- Edge cases: nested methods, multiple sections, decorators, dataclasses, async, raw, single-quotes, tabs, module-level ✓
- docvet integration: scaffolded file produces zero enrichment findings ✓
