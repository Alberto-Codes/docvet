---
title: Privacy Policy
---

# Privacy Policy

**Effective date:** March 4, 2026

## Overview

docvet is an open-source Python CLI tool for docstring quality analysis. It runs entirely on your local machine and does not collect, transmit, or store any user data.

## Data Collection

docvet collects **no data**. Specifically:

- No telemetry or usage analytics
- No crash reports or error tracking
- No personal information
- No source code leaves your machine

All analysis (AST parsing, git operations, griffe checks) is performed locally using your filesystem and local git repository.

## Network Access

docvet makes **no network requests**. It has no internet-facing dependencies at runtime. The only network activity occurs during installation (`pip install docvet`), which is handled by pip/uv and the PyPI registry.

## Third-Party Services

docvet does not integrate with any third-party analytics, advertising, or tracking services.

## Editor and Agent Integrations

The LSP server (`docvet lsp`) and MCP server (`docvet mcp`) communicate exclusively over stdio with the local editor or agent process. No data is sent to external servers.

## Changes

If this policy changes, updates will be posted to this page with a revised effective date.

## Contact

For questions about this policy, open an issue on [GitHub](https://github.com/Alberto-Codes/docvet/issues).
