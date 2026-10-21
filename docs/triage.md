# docvet — Triage Issues

Use this procedure to read a filed issue and give it a state, a priority, a
fit and a size. The labels drive every view. There are no sprints and no
boards. Ported from judgevet's maintainer triage page on 2026-10-21.

- Labels are metadata. A saved search slices them; nobody moves cards.
- A blocker that is an issue is a GitHub native `blocked by` relation. The
  `blocked` label covers blockers that are not issues.
- Work is release-driven. Work P1 and P2 until empty, release, re-read P3.
- BMAD labels (`story`, `epic-NN`, `retro-action`) are unchanged and sit
  beside this scheme.

## Labels

Descriptions are quoted as the labels carry them (`gh label list`).

### Priority

Priority measures impact, not urgency.

| Label | Meaning |
|---|---|
| `P1` | Wrong output, a leaked secret, or a claim the repo cannot support |
| `P2` | An output a session or Alberto reads and acts on is wrong |
| `P3` | The record, the process, a gate, or a capability |
| `P4` | Drift and nits |

An issue with no `P` label is ungroomed.

### Fit and size

Fit says who does the work. Size says whether a worker can take it whole.

| Label | Meaning |
|---|---|
| `pi-fit` | Mechanical and machine-checkable: delegate to any worker harness |
| `judgment` | Needs the orchestrating model: design, verdicts, done-ness |
| `size-S` | One file, one gate. A worker run under ~10 min |
| `size-M` | A few files behind one acceptance check. ~10-25 min |
| `size-L` | Too big to delegate whole. Split before assigning |

### State

| Label | Meaning |
|---|---|
| `needs-triage` | Filed, not yet read by Alberto |
| `question` | A decision or a missing fact must be settled before work can start |
| `ready` | Actionable now: an accepted definition of ready and done sits in an issue comment |
| `blocked` | Waits on a named commit, key, release or date; the body names it |

Every form under `.github/ISSUE_TEMPLATE/` applies `needs-triage`, so a new
issue lands in the ungroomed search.

### Kind

| Label | Meaning |
|---|---|
| `task` | Bounded change with a mechanical acceptance check |
| `epic` | Capability the repo needs; parent tracker |

Retired on 2026-10-21 and kept on closed issues for history: `priority:high`,
`priority:medium`, `backlog`. Do not apply them.

## Status is inferred

Status is never a label. Read it from the labels, the assignee and the
relations.

| Status | How it is determined |
|---|---|
| Ungroomed | `needs-triage`, or no `P` label |
| Triaged | Has `P`, fit and size labels, no contract comment yet |
| Ready | Has `ready`, no assignee, not blocked |
| In progress | Assigned, or a branch or draft PR names it |
| Blocked | Has `blocked`, or an open native `blocked by` relation |
| Done | Closed |

## Saved searches

`-l` cannot see native relations. Every actionable search goes through
`--search` with `-is:blocked`.

```bash
# ungroomed
gh issue list --search 'is:open label:needs-triage'
gh issue list --search 'is:open -label:P1 -label:P2 -label:P3 -label:P4'
# ready work by priority
gh issue list --search 'is:open label:ready label:P1 no:assignee -label:blocked -is:blocked'
gh issue list --search 'is:open label:ready label:P2 no:assignee -label:blocked -is:blocked'
# release cycle: P1 and P2 ready work
gh issue list --search 'is:open label:ready label:P1,P2 no:assignee -label:blocked -is:blocked'
# P1 and P2 not yet ready: specify next
gh issue list --search 'is:open label:P1,P2 -label:ready -label:blocked -is:blocked'
# pi-fit ready queue: a worker harness can take it whole
gh issue list --search 'is:open label:ready label:pi-fit no:assignee -label:size-L -label:blocked -is:blocked'
# judgment ready queue: the orchestrating model starts with a decision
gh issue list --search 'is:open label:ready label:judgment no:assignee -label:blocked -is:blocked'
# blocked (inventory, so no -is:blocked)
gh issue list --search 'is:open label:blocked'
gh issue list --search 'is:open is:blocked'
# questions to settle
gh issue list --search 'is:open label:question'
# split before assigning (inventory)
gh issue list --search 'is:open label:size-L'
```

Verified on 2026-10-21, in the order above: none; none; none; 486; 486; 472;
466, 486, 488, 491; none; 72, 435, 437, 438; 437, 438; 158, 160, 163, 256,
307, 436, 441, 451, 452, 472; 158, 160, 164, 310, 390, 433, 436, 437, 438,
439, 441, 472.

## Groom an issue

1. Read the issue. Treat its claims as a hypothesis until they reproduce on
   `main`; name the commit you checked.
2. Ask judgevet-gemma before labelling: the readiness Choice (`ask_choice`
   over `ready` / `question` / `blocked`) and the size and priority Scores
   (`ask_score` over `size-S`..`size-L` and `P4`..`P1`). Copy the label
   definitions above into `criteria`; thin labels lower agreement. Use
   `ask_noul` for one proposition and `evaluate_policy` for several under one
   rule. Send no secret.
3. Add one `P` label by impact, one fit label and one size label; add `task`
   or `epic` when the issue is a bounded change or a parent tracker. The
   form's own label (`bug`, `feature`, `chore`, ...) stays. Remove
   `needs-triage`.
4. Post a triage comment with your decision and the model's answers beside
   it. The answers are advisory; confidence is not accuracy.

   ```text
   Triage 2026-10-21: **P2 · pi-fit · size-M · ready**. Still present on main
   e12870c. judgevet-gemma (gemma-4-31b-kv9-text, advisory): P2 (1.00),
   pi-fit (0.97), size-M (1.00), ready (1.00).
   ```

5. If it waits, add `blocked` and name the blocker in the body, or add a
   native relation (below).
6. Split a `size-L` issue into `task` children before anyone takes it.
7. To make it `ready`, post the contract comment, then add `ready`. A `P`
   label alone does not make an issue ready.

## Contract comment

The contract is the definition of ready and done. Keep it under 150 words.
Revise it by posting revision N+1, never by editing in place.

```text
**Accepted specification — #N, <title>, revision 1**
Baseline: main <sha>. <what is true on main today, with file and line>.
Classification: pi-fit, size-M, P2.
Decision: <the one behaviour to build>.
Allowed edits: <paths>.
Preserve: <behaviour that must not change>.
Done when:
1. <failing test that goes green>.
2. `uv run pytest`, ruff, ty and `docvet check --all` pass.
```

A `judgment` issue may carry a **Proposed specification** first; it becomes
accepted when Alberto or the orchestrating session accepts it. #429 and #470
carry real examples.

## Work and receipt

- Branch from `main`: `fix/<scope>-<name>`, `feat/<scope>-<name>`,
  `docs/<name>`, `refactor/<name>`, `chore/<name>`.
- Write the failing test first and keep its red output for the receipt.
- Gates before push: `uv run pytest`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run ty check`,
  `uv run docvet check --all`, `uv run lint-imports`, and
  `uv run mkdocs build --strict` when docs change. The pre-push hook runs
  `uv audit`.
- Open a draft PR, squash-merge to `main` with `Closes #N`.
- A code slice gets an acceptance review from a fresh agent when the
  contract requires one. A finding outside the allowed edits becomes a new
  `needs-triage` issue, linked from the receipt.

Post the run receipt on the issue:

```text
**Run receipt — #N, <date>**
- Commit: <sha> on <branch>, squash-merged to main as <sha> via PR #M.
- Gates: <each gate and its result, local and CI>.
- Red phase: <the failing assertion before the fix>.
- Acceptance review: <verdict; findings taken; follow-ups filed as #K>.
- judgevet-gemma (advisory): acceptance → accept (1.00); commit type → fix
  (1.00). My verdict: accept, fix.
- Not anticipated by the contract: <numbered list, or "nothing">.
```

## Release cycle

1. Work until the release-cycle search (P1 and P2 ready) and the
   "specify next" search are empty, epics excepted.
2. Release: merge the release-please PR on `main`. Publishing and the `v1`
   floating tag follow from the release (see `CLAUDE.md`).
3. Re-read every open P3. Promote one whose impact grew to `P2`; demote one
   that turned into drift to `P4`.
4. Run both ungroomed searches for anything missed.

## Blocked-by relations

GitHub supports native issue dependencies
([documentation](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/adding-dependencies-to-issues)).

```bash
R=repos/Alberto-Codes/docvet
# read the blockers of issue N
gh api $R/issues/N/dependencies/blocked_by --jq '.[].number'
# the numeric id of the blocking issue B, which the add call needs
gh api $R/issues/B --jq .id
# add one
gh api -X POST $R/issues/N/dependencies/blocked_by -F issue_id=<id of B>
```

Verified on 2026-10-21 against this repository: #437 and #438 are blocked by
#436, and #435 is blocked by #428; the listing call on #435 returned `428`.
The listing includes closed blockers (#428 is closed), so it says what an
issue waited on, not whether it still waits; only `is:blocked` says that.

GitHub refuses a cycle and a duplicate, so read before you add. The relation
moves no label. `is:blocked` drops an issue once its blocker closes, but the
`blocked` label stays; when a blocker lands, check each dependant, remove
`blocked`, and add `ready` only when every prerequisite holds.

## Maintenance

| Task | When |
|---|---|
| Groom `needs-triage` issues | At the start of a session |
| Review blocked issues and stale `blocked` labels | Weekly |
| Re-prioritize P3 | After each release |
