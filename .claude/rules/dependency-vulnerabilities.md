# Dependency Vulnerability Handling

When `uv-secure` flags a vulnerability in CI or pre-commit, follow this process.

## Triage

1. **Check if a fix version exists** — look at the `Fix Versions` column in the uv-secure output
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

Suppress the specific vulnerability ID in `pyproject.toml`:

```toml
[tool.uv-secure.vulnerability_criteria]
ignore_vulnerabilities = [
    "GHSA-xxxx-xxxx-xxxx",  # package-name X.Y.Z — brief description. No fix available.
]
allow_unused_ignores = false
```

### Required Comment Format

Every entry in `ignore_vulnerabilities` must have an inline TOML comment with:
- **Package name and version** affected
- **Brief description** of the vulnerability (e.g., "ReDoS in AdlLexer")
- **"No fix available"** to explain why it's suppressed

### The Safety Net: `allow_unused_ignores = false`

This setting is mandatory. It makes CI fail when a suppressed vulnerability no longer matches any finding — which happens when:
- Renovate bumps the package to a patched version
- The vulnerability is withdrawn or reclassified

This forces cleanup of stale entries automatically through CI failure.

### Lifecycle

1. Vuln flagged with no fix -> add GHSA ID + comment to `ignore_vulnerabilities`
2. Maintainer ships a fix -> Renovate opens a PR to bump the package
3. After merge, the ignore becomes unused -> CI fails on `allow_unused_ignores`
4. Remove the stale GHSA ID from `ignore_vulnerabilities` -> CI passes

## What NOT to Do

- **Don't use `ignore_unfixed = true`** — it's a blanket suppression that hides future unfixed vulns
- **Don't use `ignore_packages`** without version specifiers — suppresses all vulns for that package
- **Don't suppress without a comment** — undocumented entries rot silently
- **Don't leave `allow_unused_ignores` unset or true** — stale entries will accumulate
