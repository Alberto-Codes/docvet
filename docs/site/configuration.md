# Configuration

docvet is configured through `[tool.docvet]` in your `pyproject.toml`. The entire section is optional — if missing, all defaults apply.

## Top-Level Options

These keys go directly under `[tool.docvet]`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `src-root` | `str` | `"."` (auto-detects `src/`) | Source directory relative to project root |
| `package-name` | `str` | auto-detected | Explicit package name override |
| `exclude` | `list[str]` | `["tests", "scripts"]` | Directory names to exclude from checks |
| `extend-exclude` | `list[str]` | `[]` | Additional patterns appended to `exclude` |
| `fail-on` | `list[str]` | `[]` | Check names that cause exit code 1 |
| `warn-on` | `list[str]` | `["freshness", "enrichment", "griffe", "coverage"]` | Check names reported without failing |

Valid check names for `fail-on` and `warn-on`: `enrichment`, `freshness`, `coverage`, `griffe`.

### `src-root` auto-detection

When `src-root` is not set in your config:

- If a `src/` directory exists at the project root, `src-root` defaults to `"src"`
- If no `src/` directory exists, `src-root` defaults to `"."` (project root)
- If `src-root` is explicitly set, the configured value is used as-is — no heuristic applied

### `fail-on` / `warn-on` precedence

If a check name appears in **both** `fail-on` and `warn-on`, docvet prints a warning to stderr and `fail-on` wins — the check is removed from `warn-on`.

!!! warning "Graceful deduplication"
    Adding `enrichment` to `fail-on` with the default `warn-on` list prints a warning to stderr and removes `enrichment` from `warn-on`. This is intentional — `fail-on` always takes priority.

### `extend-exclude`

Use `extend-exclude` to add patterns without replacing the defaults. This is useful when you want to keep the built-in `["tests", "scripts"]` exclusions and add project-specific ones:

```toml
[tool.docvet]
extend-exclude = ["vendor", "generated"]
```

The final exclude list becomes `["tests", "scripts", "vendor", "generated"]`. If you also set `exclude`, `extend-exclude` patterns are appended to your custom list instead of the defaults. Patterns follow the same matching rules as `exclude` — patterns without `/` match against individual path components, patterns with `/` match the full relative path.

### Example

```toml
[tool.docvet]
src-root = "src"
exclude = ["tests", "scripts", "migrations"]
fail-on = ["enrichment", "freshness"]
warn-on = ["griffe", "coverage"]
```

## Freshness Options

These keys go under `[tool.docvet.freshness]`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `drift-threshold` | `int` | `30` | Max days code can be ahead of docstring before flagging drift |
| `age-threshold` | `int` | `90` | Max days docstring can go without any update |

### Example

```toml
[tool.docvet.freshness]
drift-threshold = 14
age-threshold = 60
```

## Enrichment Options

These keys go under `[tool.docvet.enrichment]`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `require-raises` | `bool` | `true` | Require `Raises:` sections when exceptions are raised |
| `require-yields` | `bool` | `true` | Require `Yields:` sections in generators |
| `require-receives` | `bool` | `true` | Require `Receives:` sections for `.send()` generators |
| `require-warns` | `bool` | `true` | Require `Warns:` sections when `warnings.warn()` is called |
| `require-other-parameters` | `bool` | `true` | Require `Other Parameters:` for `**kwargs` |
| `require-attributes` | `bool` | `true` | Require `Attributes:` sections on classes and modules |
| `require-typed-attributes` | `bool` | `true` | Require typed format in `Attributes:` entries |
| `require-cross-references` | `bool` | `true` | Require `See Also:` in module docstrings |
| `prefer-fenced-code-blocks` | `bool` | `true` | Prefer fenced code blocks over doctest `>>>` format |
| `require-examples` | `list[str]` | `["class", "protocol", "dataclass", "enum"]` | Symbol kinds requiring `Examples:` sections |

### Example

```toml
[tool.docvet.enrichment]
require-warns = false
require-other-parameters = false
require-examples = ["class", "dataclass"]
```

## Complete Example

Here is a full `pyproject.toml` configuration showing all sections together:

=== "Full Configuration"

    ```toml linenums="1"
    [tool.docvet]
    src-root = "src" # (1)!
    package-name = "myapp"
    exclude = ["tests", "scripts", "migrations"] # (2)!
    extend-exclude = ["vendor", "*.generated"] # (3)!
    fail-on = ["enrichment", "freshness"] # (4)!
    warn-on = ["griffe", "coverage"]

    [tool.docvet.freshness]
    drift-threshold = 14 # (5)!
    age-threshold = 60

    [tool.docvet.enrichment]
    require-raises = true
    require-yields = true
    require-receives = false
    require-warns = false
    require-other-parameters = false
    require-attributes = true
    require-typed-attributes = true
    require-cross-references = true
    prefer-fenced-code-blocks = true
    require-examples = ["class", "dataclass"] # (6)!
    ```

    1. Auto-detected if you have a `src/` directory — only set this if your layout is non-standard.
    2. These directories are excluded from all checks. Add `migrations` for Django projects.
    3. Appended to the `exclude` list above — useful when you want to keep defaults and add more.
    4. Checks in `fail-on` cause exit code 1 — ideal for CI gates.
    5. Flag drift after just 2 weeks instead of the default 30 days.
    6. Only require `Examples:` on classes and dataclasses, not protocols or enums.

=== "Minimal Configuration"

    ```toml
    [tool.docvet]
    fail-on = ["enrichment"]
    ```

!!! info
    The `[tool.docvet]` section is entirely optional. If the section is missing, all defaults apply and no error is raised. Invalid keys cause an error on stderr and exit code 1.
