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

**Required**
:   A docvet severity level indicating a docstring section that must be present
    when the corresponding code pattern exists. Missing required sections
    produce errors.

**Recommended**
:   A docvet severity level indicating a docstring section that should be
    present but is not strictly required. Missing recommended sections produce
    warnings.

## Check Types

**Enrichment check**
:   Docvet's layer 3 check that uses AST analysis to detect missing docstring
    sections such as Raises, Yields, Attributes, and Examples.

**Freshness check**
:   Docvet's layer 4 check that detects stale docstrings — code that has
    changed without a corresponding docstring update.

**Coverage check**
:   Docvet's layer 6 check that detects missing `__init__.py` files in Python
    packages, which prevents mkdocs from discovering and documenting those
    packages.

**Griffe compatibility check**
:   Docvet's layer 5 check that captures griffe parser warnings to ensure
    docstrings render correctly in mkdocstrings-based documentation sites.

**Diff mode**
:   A freshness check strategy that maps git diff hunks to AST symbols,
    flagging code changes in the current diff that lack corresponding docstring
    updates.

**Drift mode**
:   A freshness check strategy that uses git blame timestamps to detect
    docstrings that haven't been updated for a configurable period after their
    associated code changed.

## Quality Model

**Six-layer model**
:   Docvet's conceptual framework for docstring quality, progressing from
    presence (layer 1) through style (layer 2), completeness (layer 3),
    accuracy (layer 4), rendering (layer 5), and visibility (layer 6). Docvet
    implements layers 3 through 6.

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
    diff mode maps hunks to AST symbols to identify which docstrings need
    updating.
