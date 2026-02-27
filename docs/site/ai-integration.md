---
title: AI Agent Integration
---

# AI Agent Integration

Add docvet to your AI coding workflow. Drop a snippet into your agent's instruction file so it runs `docvet check` after modifying Python code.

## Which File Should I Use?

| Your AI Tool | Add This File |
|--------------|---------------|
| OpenAI Codex | `AGENTS.md` |
| Cursor | `.cursorrules` (also reads `AGENTS.md`) |
| GitHub Copilot | `.github/copilot-instructions.md` (also reads `AGENTS.md`) |
| Claude Code | `CLAUDE.md` |
| Windsurf | `.windsurfrules` |
| Kilo Code | `AGENTS.md` |

Place the file at your project root. Each snippet below contains the same core content adapted to the tool's conventions. Copy the one that matches your tool and paste it into the file.

## Snippets

### AGENTS.md

Used by OpenAI Codex, Cursor, GitHub Copilot, Windsurf, and Kilo Code. Standard markdown format.

````markdown
## Docstring Quality

This project uses [docvet](https://pypi.org/project/docvet/) for docstring quality checking.

After modifying Python functions, classes, or modules, run `docvet check --all` and fix all findings before committing.

Key commands:
- `docvet check --all` — run all checks on entire codebase
- `docvet check` — run all checks on files changed since last commit
- `docvet check --staged` — run checks on staged files only

Fix guidance: https://alberto-codes.github.io/docvet/rules/<rule-id>/
````

### CLAUDE.md

Used by Claude Code. Standard markdown format.

````markdown
## Docstring Quality

This project uses [docvet](https://pypi.org/project/docvet/) for docstring quality checking.

After modifying Python functions, classes, or modules, run `docvet check --all` and fix all findings before committing.

Key commands:
- `docvet check --all` — run all checks on entire codebase
- `docvet check` — run all checks on files changed since last commit
- `docvet check --staged` — run checks on staged files only

Fix guidance: https://alberto-codes.github.io/docvet/rules/<rule-id>/
````

### .cursorrules

Used by Cursor. Plain text format (no markdown rendering).

````text
Docstring Quality

This project uses docvet (https://pypi.org/project/docvet/) for docstring quality checking.

After modifying Python functions, classes, or modules, run `docvet check --all` and fix all findings before committing.

Key commands:
- docvet check --all -- run all checks on entire codebase
- docvet check -- run all checks on files changed since last commit
- docvet check --staged -- run checks on staged files only

Fix guidance: https://alberto-codes.github.io/docvet/rules/<rule-id>/
````

### .github/copilot-instructions.md

Used by GitHub Copilot. Standard markdown format.

````markdown
## Docstring Quality

This project uses [docvet](https://pypi.org/project/docvet/) for docstring quality checking.

After modifying Python functions, classes, or modules, run `docvet check --all` and fix all findings before committing.

Key commands:
- `docvet check --all` — run all checks on entire codebase
- `docvet check` — run all checks on files changed since last commit
- `docvet check --staged` — run checks on staged files only

Fix guidance: https://alberto-codes.github.io/docvet/rules/<rule-id>/
````

### .windsurfrules

Used by Windsurf. Plain text format (no markdown rendering).

````text
Docstring Quality

This project uses docvet (https://pypi.org/project/docvet/) for docstring quality checking.

After modifying Python functions, classes, or modules, run `docvet check --all` and fix all findings before committing.

Key commands:
- docvet check --all -- run all checks on entire codebase
- docvet check -- run all checks on files changed since last commit
- docvet check --staged -- run checks on staged files only

Fix guidance: https://alberto-codes.github.io/docvet/rules/<rule-id>/
````

## Configuration

See the [Configuration reference](configuration.md) for all available options including `fail-on`, `exclude`, freshness thresholds, and enrichment toggles.

## Rule Reference

Each finding includes a rule ID. Look up any rule for explanation and fix guidance in the [Rules reference](rules/missing-raises.md).
