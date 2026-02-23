# Project Conventions

Foundational principles for the docvet codebase. These guide design decisions and resolve ambiguity.

## Every Symbol Deserves Its Natural Language Representation

Docstrings are the human-readable and AI-readable translation of what code does. Every public symbol — function, class, method, module — should have a docstring that explains its purpose, parameters, return values, exceptions, and behavior in plain language.

This principle emerged from Epic 9 dogfooding: when docvet ran on its own codebase, it surfaced real gaps — missing Raises sections, undocumented attributes, absent examples. The fix was to write genuine docstrings, not suppress the rules.

### Practical Implications

- No config suppression to silence own rules on own codebase — fix the docstring, don't override the check
- Genuine docstrings over `[tool.docvet.enrichment]` overrides — if a symbol needs a section, write it
- Full-strength dogfooding: `docvet check --all` runs on itself with zero config exemptions
- Examples, Attributes, Raises, Yields — all sections serve as the natural language bridge between code and understanding
