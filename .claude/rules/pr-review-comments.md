# PR Review Comment Handling Rules

When asked to review, address, or respond to PR review comments, follow this workflow exactly.

## Step 1: Read the PR Description and Comments

Always start by reading the PR description and all review comments together. This provides the full context for evaluating feedback.

```bash
# Get PR description (what we're trying to do)
gh pr view <PR_NUMBER>

# Get ALL review comments (inline code comments from reviewers)
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments --jq '.[] | {id, path, line, body, user: .user.login, in_reply_to_id, created_at}'

# Get review summaries (top-level review verdicts)
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/reviews --jq '.[] | {id, state, body, user: .user.login}'
```

Use the actual owner/repo from `gh repo view --json owner,name` if needed.

## Step 2: Evaluate Each Comment

For each review comment, categorize it:

- **Actionable**: Real issues — bugs, missing edge cases, architecture violations, security concerns, test gaps. Implement these.
- **Style/ticky-tacky**: Cosmetic preferences that conflict with project conventions in `.claude/rules/` or add no value. Push back politely with rationale.
- **Questions**: Clarification requests. Answer with context from the code.
- **Suggestions**: Optional improvements. Present to the user for decision.

Always evaluate against:
1. The PR description (what problem are we solving?)
2. Project rules in `.claude/rules/` and `CLAUDE.md`
3. Whether the suggestion is in scope for this PR

## Step 3: Present Findings to User

Before making changes, present a summary:

```
## PR #X Review Comments

### Will implement:
- [comment by @reviewer] "feedback text" -> what we'll change

### Pushing back on:
- [comment by @reviewer] "feedback text" -> why (cite project convention)

### Need your input:
- [comment by @reviewer] "feedback text" -> options A vs B
```

Wait for user confirmation before proceeding.

## Step 4: Make Changes

After user approval, implement the agreed changes. The user will commit and push.

## Step 5: Reply to Comments

After changes are pushed, reply to each review comment thread.

### Replying to a review comment thread

A review comment has an `id`. To reply **in the same thread**, use the reply endpoint:

```bash
gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments/<COMMENT_ID>/replies \
  -f body="<your reply>"
```

**IMPORTANT:** `<COMMENT_ID>` is the `id` of the **top-level** comment in the thread (the original reviewer comment), NOT `in_reply_to_id`. If a comment has `in_reply_to_id: null`, it IS the top-level comment — use its `id`. If it has `in_reply_to_id: 12345`, reply to `12345` instead.

### Common mistakes to avoid

- **WRONG**: `gh pr comment <PR_NUMBER> -b "..."` — this creates an issue-level comment, NOT a thread reply
- **WRONG**: `gh api repos/{owner}/{repo}/issues/<PR_NUMBER>/comments` — this is issue comments, NOT review thread comments
- **RIGHT**: `gh api repos/{owner}/{repo}/pulls/<PR_NUMBER>/comments/<ROOT_COMMENT_ID>/replies -f body="..."`

### Reply content guidelines

- Keep replies concise (1-3 sentences)
- If implemented: "Addressed in latest push — [brief description of what changed]."
- If pushing back: "Keeping as-is — [rationale citing project convention]."
- If clarifying: Answer the question directly, reference code if helpful.
