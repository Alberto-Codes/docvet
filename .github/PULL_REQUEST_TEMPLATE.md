<!--
AI: Remove all HTML comments when filling this template. Keep only visible content.

PR Title -> squash commit subject (50 chars, imperative)
Format: type(scope): description
Types: feat | fix | docs | refactor | test | chore | perf

Scope: A noun describing a section of the codebase (per conventionalcommits.org).
  feat(enrichment): add Raises section detection
  fix(freshness): correct hunk-to-symbol mapping
  NOT spec/issue numbers as scope

Breaking: add ! after scope -> feat(cli)!: remove deprecated flag
-->
<!--
Why this change? Problem solved? Contrast with previous behavior.
-->

<!--
What changed? 2-4 bullets, imperative mood.
e.g., - Add enrichment check for missing Raises sections
      - Map git diff hunks to AST symbols for freshness detection
-->
-

<!-- How to verify: command, manual steps, or "CI only" -->
Test: `uv run pytest -v`

<!--
Git trailers (one per line):
  Closes #123
  BREAKING CHANGE: remove deprecated foo() method
  Co-authored-by: Name <email>
-->
Closes #

<!--
Multi-commit PRs: Add additional conventional commit blocks as footers
at the bottom of the body (above the checklist). Release-please parses
these for changelog generation.

Example:
  feat(coverage): add __init__.py detection
  docs(reference): add enrichment rules table
-->

---

## PR Review

### Checklist
- [ ] Self-reviewed my code
- [ ] Tests pass (`uv run pytest`)
- [ ] Lint passes (`uv run ruff check .`)
- [ ] Types pass (`uv run ty check`)
- [ ] Breaking changes use `!` in title and `BREAKING CHANGE:` in body

### Review Focus
<!-- Where should reviewers concentrate? Known limitations? -->

### Related
<!-- Other PRs, issues, ADRs for context -->
