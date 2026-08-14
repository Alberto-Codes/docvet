---
name: Chore
about: Maintenance work — dependencies, toolchain, CI, packaging
title: 'Chore: '
labels: 'chore'
assignees: ''
---

## What Needs Maintaining
<!-- Which dependency, tool, workflow, or config? Include current and target versions. -->
- **Target:**
- **Current version:**
- **Target version:**

## Why Now
<!-- Security advisory? Deprecation? Blocking another change? Accumulated drift? -->


## Expected Fallout
<!-- What breaks when this lands? New lint errors, reformatted files, API changes, test failures.
     Quantify where possible — reviewers use this to judge whether to split the work. -->


## Verification
<!-- Which gates must pass? Note any that need a manual run. -->
- [ ] `uv run pytest`
- [ ] `uv run ruff check .` / `uv run ruff format --check .`
- [ ] `uv run ty check`
- [ ] `uv audit`
- [ ] `uv run docvet check --all`

---

### BMAD Workflow
Maintenance work usually skips the story pipeline:
- `/bmad-bmm-quick-spec` -> `/bmad-bmm-quick-dev` for anything non-trivial
- Straight to a PR for routine bumps
