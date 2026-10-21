[![CI](https://img.shields.io/github/actions/workflow/status/Alberto-Codes/docvet/ci.yml?branch=main)](https://github.com/Alberto-Codes/docvet/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/Alberto-Codes/docvet/graph/badge.svg)](https://codecov.io/gh/Alberto-Codes/docvet)
[![PyPI](https://img.shields.io/pypi/v/docvet)](https://pypi.org/project/docvet/)
[![Python](https://img.shields.io/pypi/pyversions/docvet)](https://pypi.org/project/docvet/)
[![License](https://img.shields.io/pypi/l/docvet)](https://github.com/Alberto-Codes/docvet/blob/main/LICENSE)
[![Renovate enabled](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![docs vetted](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)

# docvet

**Better docstrings, better AI.**

## Why docvet?

docvet combines docstring presence metrics, structural checks, history-based staleness signals, and renderer diagnostics in one CLI, with editor and agent interfaces. These checks help reviewers find documentation gaps; they do not prove that prose describes runtime behavior correctly.

| Layer | Check | ruff | interrogate | pydoclint | **docvet** |
|-------|-------|------|-------------|-----------|------------|
| 1. Presence | "Does a docstring exist?" | Yes (D rules, opt-in) | Yes, with coverage metrics | Skips absent docstrings | **Yes, with coverage metrics** |
| 2. Style | "Is it formatted consistently?" | Yes (D rules, opt-in) | -- | Some parsing/style checks | Limited format checks |
| 3. Completeness | "Do sections and code structure agree?" | Partial (D rules; DOC rules in preview) | -- | Arguments, returns, yields, raises, attributes, type hints | **AST-based section and agreement checks** |
| 4. Accuracy | "What needs review for staleness?" | Structural checks above | -- | Structural checks above | **Git diff/blame heuristics; no semantic proof** |
| 5. Rendering | "Are there parser warnings?" | -- | -- | -- | **Griffe diagnostics** |
| 6. Visibility | "Is package discovery incomplete?" | -- | -- | -- | **Missing `__init__.py` checks** |

Comparison reviewed **2026-10-21** against primary documentation: Ruff's [D103 presence rule](https://docs.astral.sh/ruff/rules/undocumented-public-function/) and [DOC501 exception completeness rule](https://docs.astral.sh/ruff/rules/docstring-missing-exception/) (requires `--preview` and rule selection), [pydoclint's supported checks and styles](https://jsh9.github.io/pydoclint/), and [interrogate's coverage documentation](https://interrogate.readthedocs.io/en/latest/). Capabilities depend on enabled rules and configuration; `--` means no corresponding check is described in these sources.

**pydoclint** checks arguments, returns, yields, raises, class attributes, and type hints across Google, NumPy, and Sphinx styles. docvet's enrichment alone has 21 rules, including Raises, Yields, Receives, Warns, Attributes, Examples, cross-references, parameter agreement, and more. Add presence (coverage metrics + threshold enforcement), freshness (git diff/blame staleness signals), griffe rendering compatibility, and mkdocs coverage: 32 rules across 5 checks. Rule totals measure catalog entries, not equivalent coverage between tools.

Structural agreement checks compare documented elements with code structure. Freshness uses change history to suggest review: code can change without invalidating prose, and simultaneous code/docstring edits can still leave incorrect prose. Neither establishes semantic correctness.

**[Quickstart](#quickstart)** | **[GitHub Action](#github-action)** | **[Pre-commit](#pre-commit)** | **[Configuration](#configuration)** | **[AI Agent Integration](#ai-agent-integration)** | **[Docs](https://alberto-codes.github.io/docvet/)**

## What It Checks

**Presence** (existence) -- 2 rules:
`missing-docstring` `overload-has-docstring`

**Enrichment** (completeness) -- 21 rules:
`missing-raises` `missing-returns` `missing-yields` `missing-receives` `missing-warns` `missing-deprecation` `missing-param-in-docstring` `extra-param-in-docstring` `missing-other-parameters` `missing-attributes` `undocumented-init-params` `missing-typed-attributes` `missing-examples` `missing-cross-references` `extra-raises-in-docstring` `extra-yields-in-docstring` `extra-returns-in-docstring` `missing-return-type` `trivial-docstring` `prefer-fenced-code-blocks` `scaffold-incomplete`

**Freshness** (staleness signals) -- 5 rules:
`stale-signature` `stale-body` `stale-import` `stale-drift` `stale-age`

**Griffe** (rendering) -- 3 rules:
`griffe-unknown-param` `griffe-missing-type` `griffe-format-warning`

**Coverage** (visibility) -- 1 rule:
`missing-init`

## Quickstart

```bash
pip install docvet && docvet check --all
```

For optional griffe rendering checks:

```bash
pip install docvet[griffe]
```

Example output:

```
src/mypackage/helpers.py:1: missing-docstring Module has no docstring [required]
src/mypackage/utils.py:42: missing-raises Function 'parse_config' raises ValueError but has no Raises section [required]
src/mypackage/models.py:15: stale-signature Function 'process' signature changed but docstring not updated [required]
src/mypackage/api.py:1: missing-init Package directory missing __init__.py (invisible to mkdocs) [required]
```

## Configuration

Configure via `[tool.docvet]` in your `pyproject.toml`. All checks run and print findings. Checks listed in `fail-on` cause a non-zero exit code; unlisted checks are treated as warnings.

A check in `fail-on` that cannot run — most often `griffe` without the `docvet[griffe]` extra — never certified the gate you configured, so docvet reports it on stderr and exits 1. With `--format json` the `run` object reports `status: "unavailable"` and an `unavailable_checks` array, which is what distinguishes it from a gate that found problems. Set `fail-on-unavailable = false` (or pass `--no-fail-on-unavailable`) to warn and exit 0 instead. Unavailable checks that nothing gates on stay a quiet skip — though `fail-on` membership is not the only thing that gates: a `min-coverage` floor gates `presence` without naming it there.

```toml
[tool.docvet]
exclude = ["tests", "scripts"]
fail-on = ["griffe", "coverage"]

[tool.docvet.freshness]
drift-threshold = 30
age-threshold = 90
```

## Pre-commit

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v3.0.0
    hooks:
      - id: docvet
```

For griffe rendering checks, add the optional dependency:

```yaml
repos:
  - repo: https://github.com/Alberto-Codes/docvet
    rev: v3.0.0
    hooks:
      - id: docvet
        additional_dependencies: [griffe]
```

## GitHub Action

Add docvet to your GitHub Actions workflow — findings appear as inline annotations on your PR:

```yaml
- uses: Alberto-Codes/docvet@v3.0.0
```

Select specific checks or pin a version:

```yaml
- uses: Alberto-Codes/docvet@v3.0.0
  with:
    checks: 'enrichment,freshness'
    docvet-version: '3.0.0'
    python-version: '3.13'
```

The griffe rendering check needs no setup: the action installs `docvet[griffe]`, pinned or not, so every check the `checks` input offers is available. Note that docvet releases before 1.7.0 declare that extra without an upper bound, so pinning one installs whatever griffe publishes at the time rather than a version docvet was released against.

> **Behavior change — this can turn a passing build red.**
>
> Earlier releases installed plain `docvet`, so the griffe check was skipped and contributed zero findings. It now runs. `determine_run_outcome` (`src/docvet/reporting.py`) returns exit code 1 as soon as any check listed in `fail-on` reports findings, so if your `pyproject.toml` has `griffe` in `[tool.docvet] fail-on`, your build goes from green to failing with no change on your side. This repository's own `ci.yml` docvet job is exactly such a consumer.
>
> These are not new problems — it is the check finally running on docstrings that were always broken. To get back to green, fix the griffe findings or remove `griffe` from `fail-on`.

## AI Agent Integration

For tool-specific integration snippets, see the [full AI Agent Integration guide](https://alberto-codes.github.io/docvet/ai-integration/).

Add docvet to your AI coding workflow. Drop this into your `CLAUDE.md`, `.cursorrules`, or agent configuration:

```markdown
## Docstring Quality

After modifying Python functions, classes, or modules, run `docvet check` and fix all findings before committing.
```

Recommended `pyproject.toml` configuration:

```toml
[tool.docvet]
fail-on = ["enrichment", "freshness", "coverage", "griffe"]
```

### Subcommand Quick Reference

| Command | Description |
|---------|-------------|
| `docvet check` | Run all enabled checks (default: git diff files) |
| `docvet check --all` | Run all checks on entire codebase |
| `docvet check --staged` | Run all checks on staged files only |
| `docvet presence` | Check for missing docstrings with coverage metrics |
| `docvet enrichment` | Check for missing docstring sections |
| `docvet freshness` | Flag potentially stale docstrings via git |
| `docvet freshness --mode drift` | Review potential staleness via git blame |
| `docvet coverage` | Find files invisible to mkdocs |
| `docvet griffe` | Check mkdocs rendering compatibility |
| `docvet fix` | Scaffold missing docstring sections |
| `docvet fix --dry-run` | Preview scaffolding changes without writing files |
| `docvet config` | Show effective configuration with source annotations |
| `docvet lsp` | Start LSP server for real-time editor diagnostics |
| `docvet mcp` | Start MCP server for AI agent integration |

## Better Docstrings, Better AI

AI coding agents rely on docstrings as context when generating and modifying code. Agents modify code but often leave docstrings stale, and research shows stale or incorrect documentation is actively harmful, worse than no docs at all:

- Incorrect docs [degrade LLM task success by 22.6 percentage points](https://arxiv.org/abs/2404.03114)
- Comment density [improves code generation by 40-54%](https://arxiv.org/abs/2402.13013)
- Misleading comments [reduce LLM fault localization accuracy to 24.55%](https://arxiv.org/abs/2504.04372)
- Performance [drops substantially without docstrings](https://arxiv.org/abs/2508.09537)

As the [2025 DORA report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report) puts it: "AI doesn't fix a team; it amplifies what's already there." The [only signal correlating with AI productivity is code quality](https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory).

docvet's freshness heuristics flag potential staleness for review, and its enrichment rules check supported docstring sections against code structure. Run `docvet check` in your CI, pre-commit hooks, or agent toolchain.

## Badge

Add a badge to your project to show your docs are vetted:

```markdown
[![docs vetted | docvet](https://img.shields.io/badge/docs%20vetted-docvet-purple)](https://github.com/Alberto-Codes/docvet)
```

## Used By

Are you using docvet? Open a pull request to add your project here.

## License

MIT -- see [LICENSE](https://github.com/Alberto-Codes/docvet/blob/main/LICENSE) for details.

mcp-name: io.github.Alberto-Codes/docvet
