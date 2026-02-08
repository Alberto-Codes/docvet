# Pull Request Rules

When creating a pull request, you MUST follow these rules exactly.

## Always Draft

Always create PRs as **draft** using `--draft` flag. Ready PRs trigger automated code review from GitHub Copilot, so PRs must stay draft until the author explicitly marks them ready.

```bash
gh pr create --draft ...
```

## Always Use the PR Template

Read `.github/PULL_REQUEST_TEMPLATE.md` before composing the PR body. The body MUST follow the template structure exactly:

1. **Remove all HTML comments** from the template — keep only visible content
2. **PR title** follows conventional commits: `type(scope): description`
   - Types: `feat | fix | docs | refactor | test | chore | perf`
   - Scope: a noun describing a section of the codebase (NOT spec/issue numbers)
   - Breaking changes: add `!` after scope
3. **Body structure** (in order):
   - Why paragraph (problem solved, contrast with previous behavior)
   - What changed (2-4 bullets, imperative mood)
   - `Test:` line (command, manual steps, or "CI only")
   - `Closes #` trailer (if applicable)
   - Multi-commit footer blocks for release-please (if PR has multiple logical changes)
   - `---` separator
   - `## PR Review` section with Checklist, Review Focus, and Related subsections

## Base Branch

- PRs target `develop` unless explicitly told otherwise
- Always run `git diff develop..HEAD` and `git log --oneline develop..HEAD` to understand the full scope before writing the PR body

## Diff Before PR

Before creating a PR, always:

1. `git diff --stat develop..HEAD` — understand file scope
2. `git log --oneline develop..HEAD` — understand commit history
3. Read ALL commits (not just the latest) to write an accurate description

## No Co-Authored-By

Never add `Co-Authored-By` trailers (or any variation) to commit messages or PR descriptions. Commits and PRs should not attribute authorship to Claude.

## Push Before PR

Ensure the branch is pushed to remote with `-u` before creating the PR:

```bash
git push -u origin <branch-name>
```
