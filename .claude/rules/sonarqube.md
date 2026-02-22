# SonarQube Integration

This project has a SonarQube instance connected via the official `mcp/sonarqube` MCP server (global config).

## Project Details

- **Project key**: `docvet`
- **MCP server**: Official SonarSource `mcp/sonarqube` image, configured globally in `~/.claude.json`

## When to Use

- After completing code changes, use `analyze_code_snippet` to check modified files for issues
- Use `search_sonar_issues_in_projects` with `projects: ["docvet"]` to review open issues
- Use `get_project_quality_gate_status` with `projectKey: "docvet"` to check gate status

## Known Issue Patterns

- The dominant finding is **cognitive complexity** (`python:S3776`, threshold 15). When refactoring functions, aim to stay under 15.
- Enrichment `_check_*` functions take a `node_index` parameter for interface consistency even when unused — these `S1172` findings are by design.

## Important Notes

- SonarQube results lag behind local changes — don't verify fixes via the API immediately after editing
- The server may not be running in every session
- SonarLint config (`.sonarlint/`) and `sonar-project.properties` are local-only, not committed to `develop` unless intentional
