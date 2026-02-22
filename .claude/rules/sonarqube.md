# SonarQube Integration

This project has a SonarQube Community Edition instance on the local LAN, connected via the official `mcp/sonarqube` MCP server (global config in `~/.claude.json`).

## Project Details

- **Project key**: `docvet`
- **Server**: SonarQube Community Edition at `http://192.168.87.58:9000` (LAN only)
- **MCP server**: Official SonarSource `mcp/sonarqube` image, configured globally in `~/.claude.json`

## Network & Environment

- The SonarQube server runs on a LAN machine — not always reachable (user works across multiple machines, sometimes off-LAN)
- If MCP tools return connection errors, the server is likely unreachable — don't retry, just note it and move on
- When running on the machine that hosts the SonarQube server itself, the URL may be `localhost:9000` instead of the LAN IP
- The MCP server token and URL are in `~/.claude.json` — check there for the current configuration

## Scanning (Manual)

Community Edition has no branch analysis and no automatic scan triggers. Scans must be run manually after merging to develop.

**Scan command** (run from project root on develop branch):

```bash
# Optional: generate coverage report first
uv run pytest --cov=docvet --cov-report=xml

# Run scanner
podman run --rm \
  -v /var/home/Alberto-Codes/Projects/docvet:/usr/src:z \
  --userns=keep-id \
  --network host \
  docker.io/sonarsource/sonar-scanner-cli:latest \
  -Dsonar.host.url=http://192.168.87.58:9000 \
  -Dsonar.token=<token from ~/.claude.json>
```

The scanner reads `sonar-project.properties` from the project root. **Do NOT add `sonar.branch.name`** to that file — Community Edition doesn't support it and the scan will fail.

## When to Use

- After completing code changes, use `analyze_code_snippet` to check modified files for issues
- Use `search_sonar_issues_in_projects` with `projects: ["docvet"]` to review open issues
- Use `get_project_quality_gate_status` with `projectKey: "docvet"` to check gate status
- After a PR merges to develop, offer to run a scan if the user is on-LAN

## Known Issue Patterns

- The dominant finding is **cognitive complexity** (`python:S3776`, threshold 15). When refactoring functions, aim to stay under 15.
- Enrichment `_check_*` functions take a `node_index` parameter for interface consistency even when unused — these `S1172` findings are by design.
- `analyze_code_snippet` (MCP tool) and the full scanner may calculate CC slightly differently — always trust the full scanner results on the dashboard as the source of truth.

## Important Notes

- SonarQube dashboard results lag behind local changes — don't verify fixes via the dashboard API immediately after editing; use `analyze_code_snippet` for fast feedback during development
- The server may not be reachable in every session (off-LAN, server down)
- `sonar-project.properties` is committed to the repo — keep it minimal (no `sonar.branch.name`, no tokens)
