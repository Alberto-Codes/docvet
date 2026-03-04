# Story 29.3: Documentation and Marketplace Publishing

Status: review
Branch: `feat/mcp-29-3-docs-and-marketplace`
GitHub Issue: https://github.com/Alberto-Codes/docvet/issues/268

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Claude user or AI tool developer**,
I want to find docvet's MCP server on the official MCP registry and in the docs,
so that I can discover and set up docvet integration with minimal friction.

## Acceptance Criteria

1. **Given** a user visits the docs site, **When** they navigate to Editor Integration, **Then** an "MCP Server" section documents: installation (`pip install docvet[mcp]`), starting the server (`docvet mcp`), available tools and their parameters, example response schema, and how MCP differs from the LSP server.

2. **Given** a user looks at the AI Agent Integration page, **When** they read the Claude Code section, **Then** it includes MCP server configuration for Claude Code's `~/.claude.json` `mcpServers` config, explaining how agents can invoke docvet checks programmatically instead of parsing CLI output.

3. **Given** the official MCP registry at `registry.modelcontextprotocol.io` exists, **When** the submission process is followed, **Then** docvet's MCP server is published with a `server.json` manifest and the PyPI README contains the `mcp-name:` marker required for registry validation.

4. **Given** the docs site builds with `mkdocs build --strict`, **When** all documentation changes are applied, **Then** the build succeeds with zero warnings.

## Tasks / Subtasks

- [x] Task 1: Add MCP Server section to `docs/site/editor-integration.md` (AC: 1)
  - [x] 1.1 Add "MCP Server" H2 section after the LSP Server section and before the Claude Code section
  - [x] 1.2 Document installation: `pip install docvet[mcp]`
  - [x] 1.3 Document starting the server: `docvet mcp` (stdio transport)
  - [x] 1.4 Document the two available tools: `docvet_check` (parameters: `path`, `checks`) and `docvet_rules` (no parameters)
  - [x] 1.5 Include example JSON response schema for `docvet_check` (findings, summary, presence_coverage)
  - [x] 1.6 Include example JSON response for `docvet_rules` (rules array)
  - [x] 1.7 Add a note explaining MCP vs LSP: MCP is for agentic/programmatic use (structured results), LSP is for real-time editor diagnostics (inline squiggles)
  - [x] 1.8 Document which checks run by default (all except freshness; griffe also excluded when not installed) and how to request specific checks
  - [x] 1.9 Verify all JSON examples in docs against `src/docvet/mcp.py` response construction at lines 570-588 — every field name and nesting level must match the implementation exactly
- [x] Task 2: Add MCP configuration to `docs/site/ai-integration.md` (AC: 2)
  - [x] 2.1 Add a new H2 section "MCP Server (Programmatic Access)" **before** the "Which File Should I Use?" / Snippets section — MCP is the richest integration, CLI snippets are the lightest; order from rich to light
  - [x] 2.2 Include Claude Code `~/.claude.json` mcpServers configuration example
  - [x] 2.3 Explain the benefit: structured JSON results vs CLI text parsing
  - [x] 2.4 Link back to Editor Integration MCP section for full tool reference
- [x] Task 3: Create `server.json` manifest for MCP Registry (AC: 3)
  - [x] 3.1 Create `server.json` at project root following the official schema (`https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json`)
  - [x] 3.2 Set name to `io.github.alberto-codes/docvet`
  - [x] 3.3 Set package registry to `pypi`, identifier to `docvet`, transport to `stdio`, runtime_hint to `uvx`
  - [x] 3.4 Set package_arguments to `[{"type": "positional", "value": "mcp"}]`
  - [x] 3.5 Include repository URL, website URL, and description
  - [x] 3.6 Validate `server.json` is well-formed JSON: `python -m json.tool server.json`
  - [x] 3.7 Add inline comment noting that `version` fields must be updated on each release (see Dev Notes on version staleness)
- [x] Task 4: Add `mcp-name:` marker to README (AC: 3)
  - [x] 4.1 Add `mcp-name: io.github.alberto-codes/docvet` line to README.md (PyPI validates this against server.json)
  - [x] 4.2 Place as visible plain text at the bottom of README.md — HTML comments are invisible to PyPI's API response and will fail registry validation. Use a minimal footer line or a small "Machine-readable metadata" section
- [x] Task 5: Verify docs build (AC: 4)
  - [x] 5.1 Run `mkdocs build --strict` and verify zero warnings
  - [x] 5.2 Verify all internal links resolve correctly
- [x] Task 6: Run quality gates (AC: all)
  - [x] 6.1 Run `uv run ruff check .` and `uv run ruff format --check .`
  - [x] 6.2 Run `uv run pytest` -- all tests pass, no regressions
  - [x] 6.3 Run `uv run docvet check --all` -- zero findings
  - [x] 6.4 Run `uv run interrogate -v src/` -- coverage >= 95%

## AC-to-Test Mapping

<!-- Dev agent MUST fill this table before marking story done. Every AC needs at least one test. -->

| AC | Test(s) | Status |
|----|---------|--------|
| 1 | Manual: mkdocs build --strict + visual review of MCP section | PASS |
| 2 | Manual: mkdocs build --strict + visual review of AI integration MCP config | PASS |
| 3 | Manual: `python -m json.tool server.json` exits 0 + `mcp-name:` line visible in README.md | PASS |
| 4 | mkdocs build --strict exits 0 | PASS |

## Dev Notes

### This Is a Docs + Registry Story (No Code Changes)

This story modifies only documentation files and adds a registry manifest. No Python source code changes. No new tests required beyond the `mkdocs build --strict` verification.

### File Changes Summary

| File | Change Type | What |
|------|------------|------|
| `docs/site/editor-integration.md` | MODIFY | Add MCP Server section (tools, parameters, response schema) |
| `docs/site/ai-integration.md` | MODIFY | Add MCP server config for Claude Code |
| `server.json` | NEW | MCP Registry manifest at project root |
| `README.md` | MODIFY | Add `mcp-name:` marker for registry validation |

### Editor Integration Page Structure

The current page structure is: Quick Start -> LSP Server -> Claude Code -> Neovim -> Other Editors -> VS Code.

Insert the MCP Server section **after LSP Server and before Claude Code**, since MCP and LSP are the two server protocols, and Claude Code/Neovim/etc. are client configurations. The new structure:

```
Quick Start -> LSP Server -> MCP Server -> Claude Code -> Neovim -> Other Editors -> VS Code
```

### MCP Server Documentation Content

The `docvet_check` tool accepts:
- `path` (str, required): Path to a Python file or directory
- `checks` (list[str] | None, optional): Check names to run. Valid: `presence`, `enrichment`, `freshness`, `coverage`, `griffe`. Defaults to all except freshness.

Response schema (from `src/docvet/mcp.py:570-588`):
```json
{
  "findings": [
    {"file": "...", "line": 42, "symbol": "foo", "rule": "missing-raises", "message": "...", "category": "required"}
  ],
  "summary": {
    "total": 5,
    "by_category": {"required": 3, "recommended": 2},
    "files_checked": 10,
    "by_check": {"enrichment": 3, "presence": 2}
  },
  "presence_coverage": {
    "documented": 8, "total": 10, "percentage": 80.0,
    "threshold": 95.0, "passed": false
  }
}
```

The `docvet_rules` tool accepts no parameters and returns:
```json
{
  "rules": [
    {"name": "missing-raises", "check": "enrichment", "description": "...", "category": "required"},
    ...
  ]
}
```

### Claude Code MCP Configuration

Claude Code's `~/.claude.json` uses `mcpServers` to configure MCP servers. The config for docvet:

```json
{
  "mcpServers": {
    "docvet": {
      "command": "docvet",
      "args": ["mcp"]
    }
  }
}
```

Alternative with uvx (no pre-install needed):
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

### MCP Registry Submission

The official MCP Registry exists at `registry.modelcontextprotocol.io`. Key facts:
- Governed by the Agentic AI Foundation (Linux Foundation), not Anthropic directly
- Uses `mcp-publisher` CLI tool for submissions
- Requires a `server.json` manifest at project root
- PyPI packages must include `mcp-name: <registry-name>` in README for ownership validation
- Name format: `io.github.alberto-codes/docvet` (reverse-DNS with namespace)
- The registry is a metaregistry -- it points to PyPI, not hosting artifacts

**server.json** must follow schema at `https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json`:

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json",
  "name": "io.github.alberto-codes/docvet",
  "description": "Docstring quality vetting -- enrichment, freshness, coverage, presence, and griffe checks for Python projects",
  "version": "1.8.0",
  "status": "active",
  "repository": {
    "url": "https://github.com/Alberto-Codes/docvet",
    "source": "github"
  },
  "website_url": "https://alberto-codes.github.io/docvet/",
  "packages": [
    {
      "registry_type": "pypi",
      "identifier": "docvet",
      "version": "1.8.0",
      "transport": {
        "type": "stdio"
      },
      "runtime_hint": "uvx",
      "package_arguments": [
        {
          "type": "positional",
          "value": "mcp"
        }
      ]
    }
  ]
}
```

**Publishing steps** (for the user to run after story is merged):
1. Install `mcp-publisher` (brew or binary)
2. Run `mcp-publisher login github` (OAuth flow)
3. Run `mcp-publisher publish` from project root
4. Verify at `https://registry.modelcontextprotocol.io/v0/servers?search=io.github.alberto-codes/docvet`

The story creates the `server.json` and adds the README marker. The actual `mcp-publisher publish` command is run by the maintainer after merging (requires GitHub OAuth).

### server.json Version Staleness

The `version` fields in `server.json` (both top-level and inside `packages[0]`) must match the current PyPI release. The MCP registry schema requires a specific version — no ranges, no "latest". This means:

- **On each release**, the maintainer must update `server.json` and re-run `mcp-publisher publish`
- **Follow-up opportunity**: Automate this via release-please (add `server.json` to its `extra-files` config). Out of scope for this story.
- The dev agent should set the version to the current release (`1.8.0`) and add a JSON comment (not valid JSON — use a note in the story's completion notes instead) reminding about the update obligation

Since JSON doesn't support comments, add a note to the repo's `CLAUDE.md` or release checklist instead.

### README mcp-name Marker

The `mcp-name:` marker must appear in the README as **visible plain text** so that PyPI includes it in its API response (`https://pypi.org/pypi/docvet/json` `description` field). The MCP registry validates package ownership by checking this field.

**HTML comments will NOT work** — PyPI's API returns rendered content where comments are stripped. The marker must be visible text.

Place it at the very bottom of README.md as a standalone line:

```markdown
mcp-name: io.github.alberto-codes/docvet
```

This is a standard convention for MCP-registered PyPI packages. It's technically visible but nobody reads the bottom of a README.

### MCP vs LSP Comparison Note

Include a brief note in the editor-integration MCP section:

| Feature | LSP Server | MCP Server |
|---------|-----------|------------|
| Protocol | Language Server Protocol | Model Context Protocol |
| Transport | stdio | stdio |
| Use case | Real-time editor diagnostics (inline) | Programmatic agent access (structured) |
| Checks | 3 (Enrichment, Coverage, Griffe) | 4 by default (Presence, Enrichment, Coverage, Griffe); freshness on request |
| Output | Inline diagnostics (squiggles) | Structured JSON response |
| Install | `pip install docvet[lsp]` | `pip install docvet[mcp]` |
| Command | `docvet lsp` | `docvet mcp` |

### Previous Story Intelligence (29.2)

From story 29.2:
- `docvet mcp` subcommand is already wired at `cli.py:1268-1287`
- `docs/site/cli-reference.md` already has `docvet mcp` entry (added in 29.2)
- Integration tests confirm MCP server works end-to-end with `mcp` client SDK
- `start_server as mcp_start_server` alias used to avoid name shadowing

### Post-Merge Verification (Maintainer)

After merge, the maintainer should verify:
1. `uvx docvet[mcp] mcp` starts the server correctly (uvx may handle extras differently than pip)
2. `mcp-publisher publish` succeeds against the registry
3. The `mcp-name:` marker appears in `https://pypi.org/pypi/docvet/json` `description` field after the next PyPI release

These are NOT dev agent tasks — they require the next PyPI release to be live.

### mkdocs Build Verification

The docs site uses mkdocs-material with `--strict` mode. Key checks:
- All internal `[link](target.md)` references must resolve
- Cross-references to rule pages use existing patterns from `docs/rules.yml`
- Admonitions use `!!! note` / `!!! tip` syntax
- Code blocks use triple-backtick fencing with language tags

Run: `uv run mkdocs build --strict` (or `mkdocs build --strict` if mkdocs is installed globally)

### Project Structure Notes

- No new directories needed
- `server.json` at project root (standard location for MCP registry)
- No Python source changes -- docs-only story
- No new dependencies

### References

- [Source: src/docvet/mcp.py] -- MCP server implementation (tool parameters, response schema)
- [Source: docs/site/editor-integration.md] -- Current editor integration page (LSP + Claude Code)
- [Source: docs/site/ai-integration.md] -- Current AI agent integration page (CLI snippets)
- [Source: docs/site/cli-reference.md] -- CLI reference (already has `docvet mcp` entry from 29.2)
- [Source: mkdocs.yml] -- Docs site nav structure
- [Source: _bmad-output/implementation-artifacts/29-2-cli-wiring-and-tests.md] -- Previous story
- [Source: _bmad-output/implementation-artifacts/29-1-core-mcp-server-implementation.md] -- MCP core story
- [Source: _bmad-output/planning-artifacts/epics-presence-mcp.md#Story 29.3] -- Epic AC definition
- [MCP Registry: https://registry.modelcontextprotocol.io/] -- Official MCP server registry
- [MCP Registry schema: https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json] -- server.json schema

### Documentation Impact

<!-- REQUIRED: Every story must identify affected docs pages or explicitly acknowledge "None". Do NOT leave blank or use vague language like "update docs if needed". -->

- Pages: docs/site/editor-integration.md, docs/site/ai-integration.md, README.md
- Nature of update: Add MCP Server section to editor-integration (tool docs, response schema, LSP comparison). Add Claude Code MCP config to ai-integration. Add mcp-name marker to README for registry validation.

## Quality Gates

<!-- Dev agent MUST run all gates before marking story done. All gates are mandatory — no exceptions. -->

- [x] `uv run ruff check .` -- zero lint violations
- [x] `uv run ruff format --check .` -- zero format issues
- [x] `uv run ty check` -- zero type errors
- [x] `uv run pytest` -- all tests pass, no regressions (1170 passed)
- [x] `uv run docvet check --all` -- zero docvet findings, 100% coverage
- [x] `uv run interrogate -v` -- docstring coverage 100%

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None — docs-only story, no debugging needed.

### Completion Notes List

- Added MCP Server H2 section to editor-integration.md with install, start, tools (docvet_check + docvet_rules), response schemas, and MCP vs LSP comparison table. Placed after LSP Server, before Claude Code.
- Added MCP Server (Programmatic Access) H2 section to ai-integration.md with Claude Code `~/.claude.json` config (direct + uvx), benefit explanation, and link back to editor-integration MCP section. Placed before "Which File Should I Use?" section.
- Created `server.json` at project root following official MCP registry schema. Version set to 1.7.0 (current release). Note: story spec said 1.8.0 but that doesn't exist yet — used actual current version from `.release-please-manifest.json`.
- Added `mcp-name: io.github.alberto-codes/docvet` as visible plain text at bottom of README.md for PyPI registry validation.
- JSON examples verified against `src/docvet/mcp.py:570-588` — field names and nesting match exactly.
- Version staleness note: `server.json` version fields (top-level and `packages[0].version`) must be updated on each release and re-published with `mcp-publisher publish`. Follow-up: consider adding `server.json` to release-please `extra-files` config.
- Task 3.7 (inline comment): JSON doesn't support comments, so the version update obligation is documented in this completion note and in the story Dev Notes.

### Change Log

- 2026-03-03: Story 29.3 implemented — MCP documentation, server.json manifest, README mcp-name marker

### File List

- `docs/site/editor-integration.md` — MODIFIED: added MCP Server section (install, start, tools, response schemas, MCP vs LSP table)
- `docs/site/ai-integration.md` — MODIFIED: added MCP Server (Programmatic Access) section with Claude Code config
- `server.json` — NEW: MCP Registry manifest at project root
- `README.md` — MODIFIED: added `mcp-name:` marker at bottom
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — MODIFIED: story status updated
- `_bmad-output/implementation-artifacts/29-3-documentation-and-marketplace-publishing.md` — MODIFIED: story file updated

## Code Review

<!-- MANDATORY: This section must be filled before marking the story done. Code review is required on every story — no exceptions (Epic 8 retro). -->

### Reviewer

### Outcome

### Findings Summary

| ID | Severity | Description | Resolution |
|----|----------|-------------|------------|

### Verification

- [ ] All acceptance criteria verified
- [ ] All quality gates pass
- [ ] Story file complete (AC-to-Test Mapping, Dev Notes, Change Log, File List all filled)
