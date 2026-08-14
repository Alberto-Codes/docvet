---
name: Refactor
about: Restructure internals without changing behavior
title: 'Refactor: '
labels: 'refactor'
assignees: ''
---

## Current Structure
<!-- What exists today and where? Include line counts if the 500-line module gate applies. -->
- **File(s):**
- **Module/Package:**

## Why Restructure
<!-- Module size gate? Import coupling? Duplication? Blocking a dependency upgrade?
     Be concrete about the cost of leaving it alone. -->


## Proposed Structure
<!-- Target layout. Name the modules and what moves into each. -->


## Behavior Contract
<!-- Refactors must not change observable behavior. Note anything that legitimately shifts
     (import side effects, startup time, error message wording) so reviewers can check it. -->
- [ ] No public API change
- [ ] No CLI output change
- [ ] Existing tests pass unmodified

## Verification
<!-- How do we prove behavior held? Existing suite, import-linter contracts, manual CLI diff. -->
- [ ] `uv run pytest` passes with no test changes
- [ ] `uv run lint-imports` contracts still kept

---

### BMAD Workflow
- `/bmad-bmm-quick-spec` -> `/bmad-bmm-quick-dev` for contained restructuring
- Larger splits may warrant a story via `/bmad-bmm-create-story`
