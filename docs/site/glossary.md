# Glossary

Domain-specific terms used throughout the docvet documentation. Hover over
highlighted terms on any page to see their tooltip definitions.

## Docstring Concepts

**Docstring**
:   A string literal placed at the beginning of a module, class, method, or
    function that documents it. Python stores these as the object's `__doc__`
    attribute.

**Google-style docstring**
:   A docstring formatted using Google's conventions with named sections like
    Args, Returns, Raises, and Examples. This is the format docvet expects and
    validates.

**Symbol**
:   Any named Python construct — function, class, method, or module — that can
    have a docstring attached to it.

**Public symbol**
:   A symbol without a leading underscore, expected to have a docstring.
    Docvet's presence check counts public symbols to calculate docstring
    coverage. By default, `__init__`, magic methods, and private symbols are
    excluded — configure via `ignore-init`, `ignore-magic`, and
    `ignore-private`.

**Magic method**
:   A method with double underscores (e.g., `__init__`, `__str__`), also called
    a dunder method. The presence check can be configured to require or skip
    docstrings on magic methods.

**Required**
:   A docvet severity level indicating a docstring section that must be present
    when the corresponding code pattern exists. Missing required sections
    produce errors.

**Recommended**
:   A docvet severity level indicating a docstring section that should be
    present but is not strictly required. Missing recommended sections produce
    warnings.

## Check Types

**Presence check**
:   Docvet's layer 1 check for missing docstrings on public symbols. Reports
    per-file and overall coverage percentages and enforces a configurable
    minimum coverage threshold.

**Enrichment check**
:   Docvet's layer 3 check that uses AST analysis to detect missing docstring
    sections such as Raises, Yields, Attributes, and Examples.

**Freshness check**
:   Docvet's layer 4 check that detects stale docstrings — code that has
    changed without a corresponding docstring update.

**Coverage check**
:   Docvet's layer 6 check that detects missing `__init__.py` files in Python
    packages, which prevents mkdocstrings from discovering and documenting
    those packages.

**Griffe compatibility check**
:   Docvet's layer 5 check that captures griffe parser warnings to ensure
    docstrings render correctly in mkdocstrings-based documentation sites.

**Mode**
:   A check variant that selects a specific strategy. For example, the
    freshness check has diff mode (git diff) and drift mode (git blame).

**Diff mode**
:   A freshness check strategy that maps git diff hunks to AST symbols,
    flagging code changes in the current diff that lack corresponding docstring
    updates.

**Drift mode**
:   A freshness check strategy that uses git blame timestamps to detect
    docstrings that haven't been updated for a configurable period after their
    associated code changed. Controlled by `drift-threshold` (days since code
    changed) and `age-threshold` (days since docstring last touched).

**Sweep**
:   Freshness drift mode's full-codebase scan. Runs `git blame` on every file
    to detect docstrings that have drifted out of sync with their code over
    time.

## Quality Model

**Six-layer model**
:   Docvet's conceptual framework for docstring quality, progressing from
    presence (layer 1) through style (layer 2), completeness (layer 3),
    accuracy (layer 4), rendering (layer 5), and visibility (layer 6). Docvet
    implements layers 1 and 3–6. Layer 1 can alternatively be handled by
    interrogate; layer 2 by ruff.

**Finding**
:   A single issue detected by a docvet check, containing the file path, line
    number, symbol name, rule identifier, message, and category.

**Rule**
:   A specific check condition that docvet evaluates, identified by a slug like
    `missing-raises` or `stale-signature`. Each rule maps to one finding type.

**Freshness drift**
:   The time gap between the last code change to a symbol and the last
    docstring update for that symbol, measured via git blame timestamps.

**Cognitive complexity**
:   A measure of how difficult code is to understand, calculated by counting
    control flow nesting and breaks in linear flow. SonarQube uses a threshold
    of 15.

**Docstring coverage**
:   The percentage of public symbols that have docstrings, measured by the
    presence check. Enforced via a configurable `min-coverage` threshold.

**Stale docstring**
:   A docstring that has not been updated to reflect recent code changes.
    Detected by the freshness check in both diff mode and drift mode.

## Infrastructure & Tooling

**AST**
:   Abstract Syntax Tree — Python's parsed representation of source code, used
    by docvet to analyze code structure and detect patterns like raise
    statements or yield expressions.

**Griffe**
:   A Python documentation framework that extracts information from source
    code. Docvet uses griffe to detect docstring rendering issues, and
    mkdocstrings uses griffe to generate API documentation.

**mkdocstrings**
:   An MkDocs plugin that auto-generates API documentation from Python source
    code using griffe. Docvet's griffe compatibility check ensures docstrings
    render correctly with this tool.

**Dogfooding**
:   The practice of using your own product. Docvet runs its own checks on its
    own codebase to ensure its docstrings meet the same quality standards it
    enforces for others.

**Hunk**
:   A contiguous block of changed lines in a git diff output. The freshness
    diff mode maps hunks to specific symbols by comparing changed line numbers
    against each symbol's AST line range to identify which docstrings need
    updating.

**LSP**
:   Language Server Protocol — a standard for editor integration. Docvet's LSP
    server provides real-time diagnostics (enrichment, coverage, griffe) as you
    type.

**Interrogate**
:   A third-party Python tool for docstring presence checking. Docvet's
    presence check supersedes it by adding coverage metrics and fail-on
    integration.

## CLI & Configuration

**Fail-on**
:   A CLI flag that controls which severity levels cause a non-zero exit code.
    For example, `--fail-on required` fails only on required findings.

**Threshold**
:   A configurable numeric limit used by checks. Examples include
    `drift-threshold` (days), `age-threshold` (days), and `min-coverage`
    (percentage).

**Staged**
:   The git staging area. The `--staged` flag restricts checks to files in the
    staging area, useful as a pre-commit hook.

**Pyproject.toml**
:   The Python project configuration file. Docvet reads its settings from the
    `[tool.docvet]` section.

**Src-root**
:   The source root directory (e.g., `src/`) used for package discovery. Docvet
    auto-detects it or accepts an explicit `src-root` configuration.

**Exclude/extend-exclude**
:   Configuration options for file exclusion patterns. `exclude` replaces the
    defaults; `extend-exclude` adds to them without removing the built-in
    exclusions.

**Markdown/JSON output**
:   CLI output format options. `--format json` produces machine-readable JSON
    for CI and editor integration; the default is human-readable terminal
    output.

**Suppress/Ignore**
:   Excluding specific rules or files from checks via configuration. Use
    `exclude` and `extend-exclude` in `[tool.docvet]` to skip files, or
    per-check settings to disable individual rules.
