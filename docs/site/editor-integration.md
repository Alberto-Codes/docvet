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

## MCP Server

The `docvet mcp` subcommand starts a [Model Context Protocol](https://modelcontextprotocol.io/) server on stdio. AI agents and tools that support MCP (Claude Code, Cursor, etc.) can invoke docvet checks programmatically and receive structured JSON results.

### Install

```bash
pip install docvet[mcp]
```

This installs `docvet` and the [`mcp`](https://pypi.org/project/mcp/) protocol library.

### Client Configuration

Your MCP client starts the server automatically. Configure it for your tool:

=== "Claude Code (CLI)"

    The fastest way — no JSON editing needed:

    ```bash
    claude mcp add --transport stdio --scope project docvet -- uvx "docvet[mcp]" mcp
    ```

    Use `--scope user` instead to make it available across all projects.

=== "Claude Code (JSON)"

    Add to `.mcp.json` in your project root:

    ```json
    {
      "mcpServers": {
        "docvet": {
          "command": "uvx",
          "args": ["docvet[mcp]", "mcp"]
        }
      }
    }
    ```

=== "VS Code"

    Add to `.vscode/mcp.json`:

    ```json
    {
      "servers": {
        "docvet": {
          "type": "stdio",
          "command": "uvx",
          "args": ["docvet[mcp]", "mcp"]
        }
      }
    }
    ```

    !!! warning
        VS Code uses `"servers"` as the top-level key, not `"mcpServers"`.

=== "Cursor"

    Add to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global):

    ```json
    {
      "mcpServers": {
        "docvet": {
          "command": "uvx",
          "args": ["docvet[mcp]", "mcp"]
        }
      }
    }
    ```

=== "Windsurf"

    Add to `~/.codeium/windsurf/mcp_config.json`:

    ```json
    {
      "mcpServers": {
        "docvet": {
          "command": "uvx",
          "args": ["docvet[mcp]", "mcp"]
        }
      }
    }
    ```

=== "Claude Desktop"

    Add to `claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/`, Windows: `%APPDATA%\Claude\`):

    ```json
    {
      "mcpServers": {
        "docvet": {
          "command": "uvx",
          "args": ["docvet[mcp]", "mcp"]
        }
      }
    }
    ```

    Restart Claude Desktop after editing.

docvet is also listed on the [MCP Registry](https://registry.modelcontextprotocol.io) — search for `docvet` to find it.

### Available Tools

The MCP server exposes two tools:

#### `docvet_check`

Run docvet checks on Python files.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | `str` | Yes | Path to a Python file or directory |
| `checks` | `list[str]` | No | Check names to run. Valid: `presence`, `enrichment`, `freshness`, `coverage`, `griffe`. Defaults to all except freshness. |

By default, freshness is excluded because it requires git context, and griffe is excluded when not installed.

**Response schema:**

```json
{
  "findings": [
    {
      "file": "src/mypackage/utils.py",
      "line": 42,
      "symbol": "parse_config",
      "rule": "missing-raises",
      "message": "Function 'parse_config' raises ValueError but has no Raises section",
      "category": "required"
    }
  ],
  "summary": {
    "total": 5,
    "by_category": {"required": 3, "recommended": 2},
    "files_checked": 10,
    "by_check": {"enrichment": 3, "presence": 2}
  },
  "presence_coverage": {
    "documented": 8,
    "total": 10,
    "percentage": 80.0,
    "threshold": 95.0,
    "passed": false
  }
}
```

The `presence_coverage` key only appears when the presence check runs. An `errors` key appears if any check encounters an internal error (e.g., griffe not installed, git unavailable). If the request itself is invalid (nonexistent path, unknown check name, or malformed configuration), the response contains only an `error` string instead of findings.

#### `docvet_rules`

List all available docvet rules. Takes no parameters.

**Response schema:**

```json
{
  "rules": [
    {
      "name": "missing-raises",
      "check": "enrichment",
      "description": "Function raises an exception not documented in Raises section.",
      "category": "required"
    }
  ]
}
```

### MCP vs LSP

Both servers run on stdio, but they serve different use cases:

| Feature | LSP Server | MCP Server |
|---------|-----------|------------|
| Protocol | Language Server Protocol | Model Context Protocol |
| Use case | Real-time editor diagnostics (inline squiggles) | Programmatic agent access (structured JSON) |
| Checks | 3 (Enrichment, Coverage, Griffe) | 4 by default (Presence, Enrichment, Coverage, Griffe); freshness on request |
| Output | Inline diagnostics | Structured JSON response |
| Install | `pip install docvet[lsp]` | `pip install docvet[mcp]` |
| Command | `docvet lsp` | `docvet mcp` |

**Choose LSP** when you want diagnostics in your editor as you type. **Choose MCP** when an AI agent needs to invoke checks and process results programmatically.

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
