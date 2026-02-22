# Enrichment Check

The enrichment check implements **Layer 3 (Completeness)** of docvet's quality model. It uses AST analysis to detect missing docstring sections — Raises, Yields, Attributes, Examples, and more — by inspecting your code's actual behavior and structure. 10 rules cover functions, methods, classes, and modules across required and recommended categories.

```bash
docvet enrichment --all
```

## Rules

| Rule ID | Category | Applies To | Description |
|---------|----------|------------|-------------|
| `missing-raises` | required | functions, methods | Function raises exceptions but has no `Raises:` section |
| `missing-yields` | required | functions, methods | Generator yields but has no `Yields:` section |
| `missing-receives` | required | functions, methods | Generator uses `.send()` pattern but has no `Receives:` section |
| `missing-warns` | required | functions, methods | Function calls `warnings.warn()` but has no `Warns:` section |
| `missing-other-parameters` | recommended | functions, methods | Function accepts `**kwargs` but has no `Other Parameters:` section |
| `missing-attributes` | required | classes, modules | Class or `__init__.py` module has undocumented attributes |
| `missing-typed-attributes` | recommended | classes | `Attributes:` section entries lack typed format `name (type): description` |
| `missing-examples` | recommended | classes, modules | Symbol kind in `require-examples` list lacks `Examples:` section |
| `missing-cross-references` | recommended | modules | `__init__.py` module missing `See Also:` section |
| `prefer-fenced-code-blocks` | recommended | any symbol | `Examples:` section uses doctest `>>>` instead of fenced code blocks |

**Required** rules flag structural gaps where the docstring is objectively incomplete. **Recommended** rules flag best-practice improvements that enhance documentation quality.

## Example Output

```
src/myapp/utils.py:42: missing-raises Function 'parse_config' raises ValueError but has no Raises: section [required]
src/myapp/models.py:15: missing-attributes Dataclass 'UserProfile' has no Attributes: section [required]
src/myapp/generators.py:28: missing-yields Function 'stream_results' yields but has no Yields: section [required]
src/myapp/api.py:73: missing-other-parameters Function 'create_client' accepts **kwargs but has no Other Parameters: section [recommended]

4 findings (3 required, 1 recommended)
```

## Configuration

The enrichment check is configured under `[tool.docvet.enrichment]` in your `pyproject.toml`. Each rule has a boolean toggle (except `require-examples` which takes a list).

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `require-raises` | `bool` | `true` | Require `Raises:` sections when exceptions are raised |
| `require-yields` | `bool` | `true` | Require `Yields:` sections in generators |
| `require-receives` | `bool` | `true` | Require `Receives:` sections for `.send()` generators |
| `require-warns` | `bool` | `true` | Require `Warns:` sections when `warnings.warn()` is called |
| `require-other-parameters` | `bool` | `true` | Require `Other Parameters:` for `**kwargs` |
| `require-attributes` | `bool` | `true` | Require `Attributes:` sections on classes and modules |
| `require-typed-attributes` | `bool` | `true` | Require typed format in `Attributes:` entries |
| `require-cross-references` | `bool` | `true` | Require `See Also:` in `__init__.py` modules |
| `prefer-fenced-code-blocks` | `bool` | `true` | Prefer fenced code blocks over doctest `>>>` format |
| `require-examples` | `list[str]` | `["class", "protocol", "dataclass", "enum"]` | Symbol kinds requiring `Examples:` sections |

Example configuration to disable specific rules:

```toml
[tool.docvet.enrichment]
require-warns = false
require-other-parameters = false
require-examples = ["class", "dataclass"]
```

## Usage

Run the enrichment check on your entire codebase:

```bash
docvet enrichment --all
```

Check only files with unstaged changes (default):

```bash
docvet enrichment
```

Check only staged files (useful in pre-commit hooks):

```bash
docvet enrichment --staged
```

Check specific files:

```bash
docvet enrichment --files src/myapp/utils.py --files src/myapp/models.py
```

Or run enrichment as part of all checks:

```bash
docvet check --all
```
