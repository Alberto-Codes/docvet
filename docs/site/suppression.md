# Inline Suppression

Suppress specific docvet findings with inline comments. This works like ruff's `# noqa`, mypy's `# type: ignore`, or pylint's `# pylint: disable`.

## Syntax

### Line-Level

Place a comment on the `def` or `class` keyword line:

| Syntax | Effect |
|--------|--------|
| `# docvet: ignore[missing-raises]` | Suppress one rule on this symbol |
| `# docvet: ignore[rule1,rule2]` | Suppress multiple rules on this symbol |
| `# docvet: ignore` | Suppress all rules on this symbol |

```python
def connect(host, port):  # docvet: ignore[missing-raises]
    """Connect to the server."""
    if not host:
        raise ValueError("host required")
```

### File-Level

Place a comment before the first `def` or `class`:

| Syntax | Effect |
|--------|--------|
| `# docvet: ignore-file[missing-examples]` | Suppress one rule for the entire file |
| `# docvet: ignore-file[rule1,rule2]` | Suppress multiple rules for the entire file |
| `# docvet: ignore-file` | Suppress all rules for the entire file |

```python
# docvet: ignore-file[missing-examples]

def helper():
    """Internal helper — examples not needed."""
    ...
```

## Rules

Use the kebab-case rule ID from docvet's output. Run `docvet --format json check --all` to see exact rule IDs, or consult the [CLI reference](cli-reference.md).

Common rules to suppress:

- `missing-raises` — function raises exceptions you intentionally leave undocumented
- `missing-examples` — internal utility where examples add no value
- `missing-cross-references` — module with no related modules to link
- `stale-body` — intentional code change where the docstring is still accurate

## Behavior

- **Always active** — no configuration toggle required.
- **Post-filter** — all checks run normally; suppression partitions findings afterward. No check logic is modified.
- **Exit code** — suppressed findings do not count toward exit code 1. Only active findings determine pass/fail.
- **Verbose output** — `--verbose` lists suppressed findings on stderr with a `[suppressed]` tag.
- **JSON output** — `--format json` includes a `"suppressed"` array alongside `"findings"`.
- **Invalid rules** — a warning is emitted to stderr. The directive is recorded for forward-compatibility, but only matching rule IDs suppress findings — a typo will not hide anything.
- **Unused suppressions** — a comment suppressing a rule that has no finding is silently ignored (no `RUF100`-style check in v1).

## Placement Rules

The suppression comment must be on the **`def`/`class` keyword line** — the same line reported in `finding.line`. This matches how ruff's `# noqa` works.

| Placement | Works? |
|-----------|--------|
| `def foo():  # docvet: ignore[rule]` | Yes |
| `def long_name(  # docvet: ignore[rule]` | Yes (multi-line sig) |
| `@decorator  # docvet: ignore[rule]` | **No** — decorator line is ignored |
| `# docvet: ignore[rule]` (line above def) | **No** — must be on the def line |

## Whitespace Tolerance

These are all equivalent:

```python
# docvet: ignore[missing-raises]
#docvet:ignore[missing-raises]
#  docvet:  ignore[missing-raises]
# docvet: ignore[ missing-raises ]
```
