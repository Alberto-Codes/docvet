# Enrichment Check

The enrichment check implements **Layer 3 (Completeness)** of docvet's quality model. It uses AST analysis to detect missing docstring sections — Raises, Yields, Attributes, Examples, and more — by inspecting your code's actual behavior and structure. 21 rules cover functions, methods, classes, and modules across required, recommended, and scaffold categories.

```bash
docvet enrichment --all
```

## Rules

| Rule ID | Category | Applies To | Description |
|---------|----------|------------|-------------|
| [`missing-raises`](../rules/missing-raises.md) | required | functions, methods | Function raises exceptions but has no `Raises:` section |
| [`missing-returns`](../rules/missing-returns.md) | required | functions, methods | Function returns a value but has no `Returns:` section |
| [`missing-yields`](../rules/missing-yields.md) | required | functions, methods | Generator yields but has no `Yields:` section |
| [`missing-receives`](../rules/missing-receives.md) | required | functions, methods | Generator uses `.send()` pattern but has no `Receives:` section |
| [`missing-warns`](../rules/missing-warns.md) | required | functions, methods | Function calls `warnings.warn()` but has no `Warns:` section |
| [`missing-deprecation`](../rules/missing-deprecation.md) | required | functions, methods | Function uses deprecation patterns but has no deprecation notice in docstring |
| [`missing-param-in-docstring`](../rules/missing-param-in-docstring.md) | required | functions, methods | Signature parameter not documented in `Args:` section |
| [`extra-param-in-docstring`](../rules/extra-param-in-docstring.md) | required | functions, methods | `Args:` section documents a parameter not in the function signature |
| [`missing-other-parameters`](../rules/missing-other-parameters.md) | recommended | functions, methods | Function accepts `**kwargs` but has no `Other Parameters:` section |
| [`missing-attributes`](../rules/missing-attributes.md) | required | classes, modules | Class or `__init__.py` module has undocumented attributes |
| [`undocumented-init-params`](../rules/undocumented-init-params.md) | required | classes | Class `__init__` takes parameters but neither class nor `__init__` docstring has an `Args:` section |
| [`missing-typed-attributes`](../rules/missing-typed-attributes.md) | recommended | classes | `Attributes:` section entries lack typed format `name (type): description` |
| [`missing-examples`](../rules/missing-examples.md) | recommended | classes, modules | Symbol kind in `require-examples` list lacks `Examples:` section |
| [`missing-cross-references`](../rules/missing-cross-references.md) | recommended | modules | Module missing or malformed `See Also:` section |
| [`extra-raises-in-docstring`](../rules/extra-raises-in-docstring.md) | recommended | functions, methods | Docstring documents exceptions not raised in the function body |
| [`extra-yields-in-docstring`](../rules/extra-yields-in-docstring.md) | recommended | functions, methods | Docstring has a `Yields:` section but the function does not yield |
| [`extra-returns-in-docstring`](../rules/extra-returns-in-docstring.md) | recommended | functions, methods | Docstring has a `Returns:` section but the function does not return a value |
| [`missing-return-type`](../rules/missing-return-type.md) | recommended | functions, methods | Returns section has no type and function has no return annotation |
| [`trivial-docstring`](../rules/trivial-docstring.md) | recommended | any symbol | Docstring summary line restates the symbol name without adding information |
| [`prefer-fenced-code-blocks`](../rules/prefer-fenced-code-blocks.md) | recommended | any symbol | `Examples:` section uses doctest `>>>` or rST `::` instead of fenced code blocks |
| [`scaffold-incomplete`](../rules/scaffold-incomplete.md) | scaffold | any symbol | Docstring contains unfilled `[TODO: ...]` placeholder markers from `docvet fix` |

**Required** rules flag structural gaps where the docstring is objectively incomplete. **Recommended** rules flag best-practice improvements that enhance documentation quality. **Scaffold** findings flag placeholder content that must be filled in before merging.

!!! note "Sphinx/RST mode"
    When [`docstring-style`](../configuration.md#docstring-style) is set to `"sphinx"`, section detection switches to RST field-list patterns and several rules are auto-disabled. See the [configuration reference](../configuration.md#docstring-style) for details.

!!! tip "Best practice"
    Start with `require-raises` and `missing-attributes` — these catch the most impactful gaps. Disable `require-other-parameters` if your project doesn't use `**kwargs` heavily.

## Example Output

``` linenums="1"
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
| `require-returns` | `bool` | `true` | Require `Returns:` sections when functions return a value |
| `require-yields` | `bool` | `true` | Require `Yields:` sections in generators |
| `require-receives` | `bool` | `true` | Require `Receives:` sections for `.send()` generators |
| `require-warns` | `bool` | `true` | Require `Warns:` sections when `warnings.warn()` is called |
| `require-other-parameters` | `bool` | `true` | Require `Other Parameters:` for `**kwargs` |
| `require-attributes` | `bool` | `true` | Require `Attributes:` sections on classes and modules |
| `require-typed-attributes` | `bool` | `true` | Require typed format in `Attributes:` entries |
| `require-cross-references` | `bool` | `true` | Require `See Also:` in module docstrings |
| `prefer-fenced-code-blocks` | `bool` | `true` | Prefer fenced code blocks over doctest `>>>` format |
| `require-param-agreement` | `bool` | `true` | Require parameter agreement between function signatures and `Args:` sections |
| `require-deprecation-notice` | `bool` | `true` | Require deprecation notice when function uses deprecation patterns |
| `exclude-args-kwargs` | `bool` | `true` | Exclude `*args` and `**kwargs` from parameter agreement checks |
| `check-trivial-docstrings` | `bool` | `true` | Flag docstrings whose summary line trivially restates the symbol name |
| `require-return-type` | `bool` | `false` | Require return type via typed `Returns:` entry or `->` annotation (opt-in) |
| `require-init-params` | `bool` | `false` | Require `Args:` section when `__init__` takes parameters (opt-in) |
| `check-extra-raises` | `bool` | `false` | Flag documented exceptions not raised in function body (opt-in due to propagated exception false positives) |
| `check-extra-yields` | `bool` | `true` | Flag `Yields:` section when function has no `yield` statement |
| `check-extra-returns` | `bool` | `true` | Flag `Returns:` section when function has no meaningful return |
| `require-examples` | `list[str]` | `["class", "protocol", "dataclass", "enum"]` | Symbol kinds requiring `Examples:` sections |
| `scaffold-incomplete` | `bool` | `true` | Detect unfilled `[TODO: ...]` placeholder markers left by `docvet fix` |

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

Add `--verbose` for file count and timing, or `-q` to suppress the summary line:

```bash
docvet enrichment --all --verbose
docvet enrichment --all -q
```

Or run enrichment as part of all checks:

```bash
docvet check --all
```
