# Griffe Check

The griffe check implements **Layer 5 (Rendering)** of docvet's quality model. It captures warnings from the griffe docstring parser to detect issues that would cause broken rendering in mkdocs-material + mkdocstrings documentation sites. 3 rules.

```bash
docvet griffe --all
```

!!! warning "Optional Dependency"
    The griffe check requires the optional `griffe` extra:

    ```bash
    pip install docvet[griffe]
    ```

    When griffe is not installed, docvet skips this check gracefully — no error, no finding, just a silent skip.

## Rules

| Rule ID | Category | Description |
|---------|----------|-------------|
| `griffe-unknown-param` | required | Docstring documents a parameter not in the function signature |
| `griffe-missing-type` | recommended | Parameter or return value lacks a type annotation in the docstring |
| `griffe-format-warning` | recommended | Docstring format issue that would break mkdocs rendering |

!!! tip "Catch these early"
    `griffe-unknown-param` is the most impactful rule — it catches renamed or removed parameters that still appear in the docstring. These cause visible rendering errors on your docs site.

## Example Output

``` linenums="1"
src/myapp/utils.py:42: griffe-unknown-param Function 'parse_config' 'timeout' does not appear in the function signature [required]
src/myapp/utils.py:42: griffe-missing-type Function 'parse_config' No type or annotation for parameter 'retries' [recommended]
src/myapp/models.py:15: griffe-format-warning Class 'User' Possible name/annotation mix-up in parameter 'name' [recommended]

3 findings (1 required, 2 recommended)
```

## Configuration

!!! info
    This check has no check-specific configuration. There is no `[tool.docvet.griffe]` section.

The griffe check parses docstrings using griffe's Google-style parser and captures any warnings emitted during parsing. No thresholds or toggles are needed — if griffe flags it, docvet reports it.

## Usage

Run the griffe check on your entire codebase:

```bash
docvet griffe --all
```

Check only files with unstaged changes (default):

```bash
docvet griffe
```

Check only staged files:

```bash
docvet griffe --staged
```

Check specific files:

```bash
docvet griffe --files src/myapp/utils.py --files src/myapp/models.py
```

Or run griffe as part of all checks (skipped automatically if griffe is not installed):

```bash
docvet check --all
```
