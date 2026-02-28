---
title: Editor Integration
---

# Editor Integration

Get real-time docstring diagnostics as you code. Install the LSP extra, point your editor at `docvet lsp`, and see findings inline.

## Quick Start

```bash
pip install docvet[lsp]
```

This installs both `docvet` (the CLI) and `pygls` (the LSP protocol library). Then follow the setup for your editor below.

## LSP Server

The `docvet lsp` subcommand starts a [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) server on stdio. Any editor with LSP support can use it.

### Which Checks Run

The LSP server runs three of docvet's four checks on every file you open or save:

| Check | Rules | What It Detects |
|-------|-------|-----------------|
| Enrichment | 10 | Missing Raises, Yields, Attributes, Examples, and more |
| Coverage | 1 | Missing `__init__.py` for mkdocs discoverability |
| Griffe | 3 | Griffe parser warnings for mkdocs rendering |

Freshness checks are excluded because they require git context that is not available in single-file LSP mode.

!!! note
    Griffe checks require the `griffe` extra. Install with `pip install docvet[lsp,griffe]` to enable all three checks. Without it, griffe diagnostics are silently skipped.

### Severity Mapping

Diagnostics use two severity levels based on the rule category:

| Category | LSP Severity | Meaning |
|----------|-------------|---------|
| Required | Warning | Core quality issue — e.g., `missing-raises`, `missing-yields` |
| Recommended | Hint | Best practice suggestion — e.g., `missing-examples`, `missing-cross-references` |

See the [Rules reference](rules/missing-raises.md) for rule explanations and fix guidance.

### Configuration

The LSP server reads `[tool.docvet]` from `pyproject.toml` in your project root on startup. Enrichment rule toggles and project root settings apply to LSP diagnostics. File `exclude` patterns are not enforced — in LSP mode, the editor controls which files are checked. See the [Configuration reference](configuration.md) for details.

### Documentation Links

Each diagnostic includes a link to its rule page on the docs site. Click the link (or hover, depending on your editor) to see an explanation and fix guidance.

## Claude Code

docvet ships as a [Claude Code plugin](https://docs.anthropic.com/en/docs/claude-code/plugins) with minimal setup.

### Install

```bash
claude plugin install github:Alberto-Codes/docvet
```

**Prerequisites:** `pip install docvet[lsp]` (the plugin calls `docvet lsp` under the hood).

!!! note
    The `lsp` subcommand requires docvet 1.6.0 or later. If `docvet lsp` is not recognized, update with `pip install --upgrade docvet[lsp]`.

### What You Get

Open or save any `.py` file and diagnostics appear inline. The plugin uses the same LSP server described above — same checks, same severity mapping, same configuration.

### Verify

Create a Python file with a known issue:

```python
def greet(name):
    """Say hello."""
    if not name:
        raise ValueError("name must not be empty")
    return f"Hello, {name}"
```

A diagnostic should appear on the function — the docstring is missing a `Raises:` section for `ValueError`.

### Uninstall

```bash
claude plugin remove docvet-lsp
```

## Neovim

### nvim-lspconfig

Add to your Neovim configuration:

```lua
local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

if not configs.docvet then
  configs.docvet = {
    default_config = {
      cmd = { "docvet", "lsp" },
      filetypes = { "python" },
      root_dir = lspconfig.util.root_pattern("pyproject.toml", ".git"),
    },
  }
end

lspconfig.docvet.setup({})
```

### Manual (vim.lsp.start)

If you prefer not to use nvim-lspconfig:

```lua
vim.api.nvim_create_autocmd("FileType", {
  pattern = "python",
  callback = function()
    vim.lsp.start({
      name = "docvet",
      cmd = { "docvet", "lsp" },
      root_dir = vim.fs.root(0, { "pyproject.toml", ".git" }),
    })
  end,
})
```

## Other Editors

Any editor with LSP support can use docvet. The server communicates over stdio with these settings:

| Setting | Value |
|---------|-------|
| Command | `docvet lsp` |
| File types | Python (`.py`) |
| Root marker | `pyproject.toml` or `.git` |
| Transport | stdio |

Consult your editor's LSP documentation for how to register a custom language server.

## VS Code

A dedicated VS Code extension is planned (see [issue #160](https://github.com/Alberto-Codes/docvet/issues/160)). In the meantime, you can use a generic LSP client extension to connect to the `docvet lsp` server using the settings in the table above.
