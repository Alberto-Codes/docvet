# Dependency Vulnerability Handling

When `uv audit` flags a vulnerability in CI or pre-commit, follow this process.

## Triage

1. **Check if a fix version exists** — look at the `Fixed in` line in the uv audit output
2. **Check if it's a direct or transitive dependency** — search `pyproject.toml` for the package name

## If a Fix Exists

Upgrade the dependency immediately:

```bash
# Direct dependency
uv add package-name --upgrade-package package-name

# Transitive dependency (not in pyproject.toml)
uv lock --upgrade-package package-name
```

No suppression needed — take the fix.

## If No Fix Exists

Use `--ignore-until-fixed` in the CI step (`.github/workflows/ci.yml`):

```yaml
- run: uv audit --ignore-until-fixed GHSA-xxxx-xxxx-xxxx
```

This auto-expires: once the maintainer ships a fix and the lockfile is updated, the ignore has no effect and can be cleaned up.

For vulnerabilities you want to permanently ignore (e.g., not applicable to your use case), use `--ignore` instead:

```yaml
- run: uv audit --ignore GHSA-xxxx-xxxx-xxxx
```

### Lifecycle

1. Vuln flagged with no fix -> add `--ignore-until-fixed GHSA-ID` to CI step
2. Maintainer ships a fix -> Dependabot opens a PR to bump the package
3. After merge, the ignore is inert -> remove it from CI step to keep config clean

## What NOT to Do

- **Don't skip `uv audit` entirely** — it's the only automated vuln check in the pipeline
- **Don't use `--ignore` for unfixed vulns** — use `--ignore-until-fixed` so it auto-expires
- **Don't suppress without a comment** — add a YAML comment explaining why
