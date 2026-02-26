# Coverage Check

The coverage check implements **Layer 6 (Visibility)** of docvet's quality model. It detects missing `__init__.py` files in your source tree that would make Python packages invisible to mkdocs and other documentation generators. 1 rule.

```bash
docvet coverage --all
```

## Rules

| Rule ID | Category | Description |
|---------|----------|-------------|
| [`missing-init`](../rules/missing-init.md) | required | Directory in source tree lacks `__init__.py`, making its Python files invisible to documentation generators |

The check walks from each discovered file's parent directory up to the source root, looking for missing `__init__.py` files at each level. Findings are deduplicated per directory and include the count of affected files.

!!! tip "When this matters"
    If you use mkdocs + mkdocstrings (or any tool that discovers packages via `__init__.py`), a missing init file means that entire directory is invisible to your docs site — even if the code is importable at runtime.

## Example Output

``` linenums="1"
src/myapp/helpers/utils.py:1: missing-init Directory 'myapp/helpers' lacks __init__.py (3 files affected) [required]
src/myapp/plugins/auth.py:1: missing-init Directory 'myapp/plugins' lacks __init__.py (2 files affected) [required]

2 findings (2 required, 0 recommended)
```

## Configuration

!!! info
    This check has no check-specific configuration. There is no `[tool.docvet.coverage]` section.

### `src-root` behavior

The coverage check uses the `src-root` setting from `[tool.docvet]` to determine where to start scanning:

- If `src-root` is **not set** and a `src/` directory exists at the project root, it defaults to `"src"`
- If `src-root` is **not set** and no `src/` directory exists, it defaults to `"."` (project root)
- If `src-root` is **explicitly set**, the configured value is used as-is

```toml
[tool.docvet]
src-root = "src"
```

## Usage

Run the coverage check on your entire codebase:

```bash
docvet coverage --all
```

Check only files with unstaged changes (default):

```bash
docvet coverage
```

Check only staged files:

```bash
docvet coverage --staged
```

Check specific files:

```bash
docvet coverage --files src/myapp/helpers/utils.py --files src/myapp/plugins/auth.py
```

Add `--verbose` for file count and timing, or `-q` to suppress the summary line:

```bash
docvet coverage --all --verbose
docvet coverage --all -q
```

Or run coverage as part of all checks:

```bash
docvet check --all
```
