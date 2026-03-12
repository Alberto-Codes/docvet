# GitHub Discussions API Reference

Working patterns for GitHub Discussions via `gh api graphql`. The REST API and `gh discussion` CLI command do NOT support discussions — GraphQL is the only path.

## Critical: Shell Escaping for Mutations

Mutations with `ID!` and `String!` in the query contain `!` and `$` characters that bash mangles even inside single quotes in some contexts. **Always use file-based query passing** for mutations:

1. Write the GraphQL query to a temp file
2. Use `-F query=@file` (not `-f query='...'`)
3. Use `-F body=@file` for markdown bodies (not `-f body="$VAR"`)

```bash
# Write query to temp file (do this once per session)
cat > /tmp/gh-create-discussion.graphql << 'EOF'
mutation($repoId: ID!, $catId: ID!, $title: String!, $body: String!) {
  createDiscussion(input: {repositoryId: $repoId, categoryId: $catId, title: $title, body: $body}) {
    discussion { number url }
  }
}
EOF

cat > /tmp/gh-update-discussion.graphql << 'EOF'
mutation($id: ID!, $body: String!) {
  updateDiscussion(input: {discussionId: $id, body: $body}) {
    discussion { number url }
  }
}
EOF
```

Read-only queries (no `!` types) work fine with inline `-f query='...'`.

## Key IDs

These are stable — no need to look them up each session:

- **Repository ID**: `R_kgDORLG_EQ`
- **Announcements category ID**: `DIC_kwDORLG_Ec4C3lBx`
- **General category ID**: `DIC_kwDORLG_Ec4C3lBy`
- **Ideas category ID**: `DIC_kwDORLG_Ec4C3lB0`
- **Polls category ID**: `DIC_kwDORLG_Ec4C3lB2`
- **Q&A category ID**: `DIC_kwDORLG_Ec4C3lBz`
- **Show and tell category ID**: `DIC_kwDORLG_Ec4C3lB1`

## Discussion Node IDs

Map of discussion numbers to GraphQL node IDs (needed for updates):

| # | Version | Node ID |
|---|---------|---------|
| 259 | v1.7 | `D_kwDORLG_Ec4Ake4B` |
| 274 | MCP Registry | `D_kwDORLG_Ec4AkgT_` |
| 298 | v1.9 | `D_kwDORLG_Ec4AkkHB` |
| 299 | v1.10 | `D_kwDORLG_Ec4AkkHE` |
| 304 | v1.11 | `D_kwDORLG_Ec4Akldu` |
| 335 | v1.0 | `D_kwDORLG_Ec4AknOy` |
| 336 | v1.1 | `D_kwDORLG_Ec4AknOz` |
| 337 | v1.2 | `D_kwDORLG_Ec4AknO1` |
| 338 | v1.3 | `D_kwDORLG_Ec4AknO2` |
| 339 | v1.4 | `D_kwDORLG_Ec4AknO4` |
| 340 | v1.5 | `D_kwDORLG_Ec4AknO6` |
| 341 | v1.6 | `D_kwDORLG_Ec4AknO7` |
| 342 | v1.8 | `D_kwDORLG_Ec4AknO9` |
| 343 | v1.12 | `D_kwDORLG_Ec4AknO-` |
| 348 | v1.13 | `D_kwDORLG_Ec4Akn7F` |

For new discussions, query the node ID after creation:

```bash
gh api graphql -f query='{ repository(owner:"Alberto-Codes", name:"docvet") { discussion(number: 348) { id } } }'
```

## Creating a Discussion

```bash
# Write body to temp file
cat > /tmp/disc-body.md << 'BODYEOF'
Your markdown body here.
BODYEOF

# Create using file-based query (see mutation files above)
gh api graphql \
  -F query=@/tmp/gh-create-discussion.graphql \
  -f repoId="R_kgDORLG_EQ" \
  -f catId="DIC_kwDORLG_Ec4C3lBx" \
  -f title="The title" \
  -F body=@/tmp/disc-body.md
```

## Updating a Discussion

```bash
# Write body to temp file
cat > /tmp/disc-body.md << 'BODYEOF'
Updated markdown body.
BODYEOF

# Update using file-based query and node ID from table above
gh api graphql \
  -F query=@/tmp/gh-update-discussion.graphql \
  -f id="D_kwDORLG_Ec4AknOy" \
  -F body=@/tmp/disc-body.md
```

Can also update `title` and `categoryId` by adding them to the mutation and passing as `-f` args.

## Listing Discussions

```bash
# All discussions with category
gh api graphql -f query='{
  repository(owner:"Alberto-Codes", name:"docvet") {
    discussions(first:20, orderBy:{field:CREATED_AT, direction:DESC}) {
      nodes { number title category { name } body }
    }
  }
}'

# Filter by category
gh api graphql -f query='{
  repository(owner:"Alberto-Codes", name:"docvet") {
    discussions(first:20, categoryId:"DIC_kwDORLG_Ec4C3lBx") {
      nodes { number title body }
    }
  }
}'

# All node IDs (for building the ID table)
gh api graphql -f query='{
  repository(owner:"Alberto-Codes", name:"docvet") {
    discussions(first:20, categoryId:"DIC_kwDORLG_Ec4C3lBx", orderBy:{field:CREATED_AT, direction:ASC}) {
      nodes { id number title }
    }
  }
}' --jq '.data.repository.discussions.nodes[] | "\(.number)\t\(.id)\t\(.title)"'
```

## Reading a Single Discussion

```bash
gh api graphql -f query='{
  repository(owner:"Alberto-Codes", name:"docvet") {
    discussion(number: 348) { id title body category { name } createdAt }
  }
}'
```

## Pinned Discussions

### Reading pins

```bash
gh api graphql -f query='{
  repository(owner:"Alberto-Codes", name:"docvet") {
    pinnedDiscussions(first:10) {
      nodes {
        id pattern preconfiguredGradient
        discussion { number title category { name } }
      }
    }
  }
}'
```

### Pinning and unpinning — UI ONLY

The GraphQL API has **no `pinDiscussion` or `unpinDiscussion` mutation**. Pin management must be done through the GitHub web UI. Maximum 4 pinned discussions per repository.

When pin changes are needed, tell the user to visit the Discussions page and do it manually.

## Schema Gotchas

- **`-f query='...'` breaks on mutations** — `ID!` contains `!` which bash history expansion can mangle. Always use `-F query=@file` for mutations.
- **`-f body="$VAR"` breaks on complex markdown** — use `-F body=@file` instead.
- `-F` (capital F) reads from file; `-f` (lowercase) passes raw string value.
- `Discussion` has no `isPinned` field — check `repository.pinnedDiscussions` instead.
- `PinnedDiscussion` has `gradientStopColors` (not `gradientBackgroundColor`).
- No `gh discussion` CLI subcommand exists — always use `gh api graphql`.
- The REST endpoint `repos/{owner}/{repo}/discussions` works for reading (GET) but use GraphQL for mutations.
- Announcement category discussions can only be created by maintainers.

## Pinning Strategy

Maintain 4 pinned discussions serving these roles:

| Role | Purpose |
|------|---------|
| **Latest release** | Most recent version announcement — rotate on each release |
| **Origin story** | "What is docvet?" entry point for newcomers (currently #335, v1.0) |
| **AI integration** | MCP / agent integration story (currently #274) |
| **Power features** | Biggest feature milestone (currently #341, v1.6) |

## Announcement Template

Lead with the problem solved, not the feature shipped:

```
## Opening (1-2 sentences)
What couldn't you do before? What can you do now?

## Headline feature (2-3 paragraphs)
Show, don't list. Include code examples or output.

## Also in this release (bullets)
Secondary features, brief.

## Try it
One install command. One run command.

[Full changelog](link) · [Docs](link)
```

No boilerplate closers. No links footers with 5+ links. One clear CTA.
