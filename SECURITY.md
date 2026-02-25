# Security Policy

## Supported Versions

Only the latest release is supported with security fixes.

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
| < Latest | No       |

## Scope

docvet is a static analysis tool that reads Python source files and calls `git` via subprocess. By design it:

- Parses `.py` files using Python's `ast` module (no `eval`, no `exec`)
- Runs `git diff`, `git blame`, and `git log` via `subprocess.run` with explicit argument lists (no shell expansion)
- Does **not** make network requests, download packages, or execute analyzed code

Reports about these expected behaviors are not security vulnerabilities. If you believe docvet's approach in these areas can be hardened, please open a regular issue.

## Reporting a Vulnerability

Please report security vulnerabilities through GitHub's [private vulnerability reporting](https://github.com/Alberto-Codes/docvet/security/advisories/new).

Do **not** open a public issue for security vulnerabilities.

## Disclosure

Critical vulnerabilities will be disclosed via GitHub's [security advisory](https://github.com/Alberto-Codes/docvet/security) system.

## Security Scanning

This project runs [CodeQL](https://github.com/Alberto-Codes/docvet/actions/workflows/codeql.yml) on every pull request and weekly, scanning for command injection, XSS, and other OWASP vulnerability patterns.
