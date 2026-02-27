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

- PRs target `main` unless explicitly told otherwise
- Always run `git diff main..HEAD` and `git log --oneline main..HEAD` to understand the full scope before writing the PR body

## Diff Before PR

Before creating a PR, always:

1. `git diff --stat main..HEAD` — understand file scope
2. `git log --oneline main..HEAD` — understand commit history
3. Read ALL commits (not just the latest) to write an accurate description

## No Co-Authored-By

Never add `Co-Authored-By` trailers (or any variation) to commit messages or PR descriptions. Commits and PRs should not attribute authorship to Claude.

## Hash References Are GitHub-Only

The `#N` syntax (e.g., `#180`, `Closes #42`) is **reserved for GitHub issues and PRs**. GitHub auto-links any `#N` to the corresponding item, so using it for non-GitHub references creates incorrect links.

- **Correct**: `Closes #180` (real GitHub issue), `feat(ci): add hook definition` (no story ref needed)
- **Wrong**: `feat(ci): add hook definition (#23.4)` — GitHub links `#23` to issue/PR 23
- BMAD story IDs (e.g., 23.4) must NOT appear with `#` prefix in commit messages, PR titles, or PR bodies
- The branch name already carries the story ID (e.g., `feat/ci-23-4-pre-commit-hook-definition`) — no need to repeat it in the commit subject
- If a story reference is needed in the PR body, use plain text: `Story 23.4` (no `#`)

## Push Before PR

Ensure the branch is pushed to remote with `-u` before creating the PR:

```bash
git push -u origin <branch-name>
```

## Squash and Merge

When squash-merging a PR via `gh pr merge --squash`:

- Always use `--subject` and `--body` to control the commit message
- `--subject`: The PR title (conventional commit format)
- `--body`: Only the content above the `---` separator (why paragraph + what-changed bullets)
- Never include the PR Review section (checklist, review focus, related) in the commit message
- Always use `--delete-branch` to clean up the feature branch

```bash
gh pr merge <NUMBER> --squash --delete-branch \
  --subject "<PR title>" \
  --body "<description + bullets only>"
```
