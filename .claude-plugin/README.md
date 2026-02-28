# docvet LSP Plugin for Claude Code

Real-time docstring quality diagnostics for Python files, powered by [docvet](https://alberto-codes.github.io/docvet/).

## Supported Extensions

`.py`

## Prerequisites

Install docvet with LSP support:

```bash
pip install docvet[lsp]
```

This installs both `docvet` (the CLI) and `pygls` (the LSP protocol library).

> **Note:** The `lsp` subcommand requires docvet 1.6.0 or later. If `docvet lsp` is not recognized, update with `pip install --upgrade docvet[lsp]`.

## Installation

```bash
claude plugin install github:Alberto-Codes/docvet
```

## Features

The plugin runs three of docvet's four checks on every Python file you open or save:

| Check | What It Detects | Severity |
|-------|----------------|----------|
| Enrichment | Missing Raises, Yields, Attributes, Examples, and more (10 rules) | Warning / Hint |
| Coverage | Missing `__init__.py` for mkdocs discoverability (1 rule) | Warning |
| Griffe | Griffe parser warnings for mkdocs rendering (3 rules) | Warning |

Freshness checks (stale docstrings) require git context and are not available in single-file LSP mode.

## Verification

Create or open a Python file with a known docstring issue:

```python
def greet(name):
    """Say hello."""
    if not name:
        raise ValueError("name must not be empty")
    return f"Hello, {name}"
```

A diagnostic should appear on the function — the docstring is missing a `Raises:` section for `ValueError`. Hover over the diagnostic to see the rule name and message.

## Troubleshooting

**No diagnostics appear:**

- Verify docvet is installed: `docvet --version`
- Verify the LSP extra is installed: `docvet lsp` should start the server (press Ctrl+C to stop)
- If you see `"LSP server requires pygls"`, reinstall with: `pip install docvet[lsp]`

**Wrong diagnostics or false positives:**

- docvet reads configuration from `pyproject.toml` in your project root (`[tool.docvet]` section)
- See the [configuration reference](https://alberto-codes.github.io/docvet/configuration/) for available options

## Uninstall

```bash
claude plugin remove docvet-lsp
```

## More Information

- [Documentation](https://alberto-codes.github.io/docvet/)
- [Configuration Reference](https://alberto-codes.github.io/docvet/configuration/)
- [GitHub Repository](https://github.com/Alberto-Codes/docvet)
