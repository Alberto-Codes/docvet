<!-- Docstring Concepts -->
*[docstring]: A string literal at the beginning of a module, class, method, or function that documents it. Python stores these as the object's __doc__ attribute.
*[Docstring]: A string literal at the beginning of a module, class, method, or function that documents it. Python stores these as the object's __doc__ attribute.
*[docstrings]: String literals at the beginning of modules, classes, methods, or functions that document them. Python stores these as the object's __doc__ attribute.
*[Docstrings]: String literals at the beginning of modules, classes, methods, or functions that document them. Python stores these as the object's __doc__ attribute.
*[Google-style docstring]: A docstring formatted using Google's conventions with named sections like Args, Returns, Raises, and Examples — the format docvet expects.
*[Google-style docstrings]: Docstrings formatted using Google's conventions with named sections like Args, Returns, Raises, and Examples — the format docvet expects.
*[symbol]: Any named Python construct — function, class, method, or module — that can have a docstring attached to it.
*[Symbol]: Any named Python construct — function, class, method, or module — that can have a docstring attached to it.
*[symbols]: Named Python constructs — functions, classes, methods, or modules — that can have docstrings attached to them.
*[Symbols]: Named Python constructs — functions, classes, methods, or modules — that can have docstrings attached to them.
*[required]: A docvet severity level indicating a docstring section that must be present when the corresponding code pattern exists.
*[Required]: A docvet severity level indicating a docstring section that must be present when the corresponding code pattern exists.
*[recommended]: A docvet severity level indicating a docstring section that should be present but is not strictly required.
*[Recommended]: A docvet severity level indicating a docstring section that should be present but is not strictly required.

*[public symbol]: A symbol without a leading underscore, expected to have a docstring.
*[Public symbol]: A symbol without a leading underscore, expected to have a docstring.
*[public symbols]: Symbols without leading underscores, expected to have docstrings.
*[Public symbols]: Symbols without leading underscores, expected to have docstrings.
*[magic method]: A method with double underscores (e.g., __init__, __str__), also called a dunder method.
*[Magic method]: A method with double underscores (e.g., __init__, __str__), also called a dunder method.
*[magic methods]: Methods with double underscores (e.g., __init__, __str__), also called dunder methods.
*[Magic methods]: Methods with double underscores (e.g., __init__, __str__), also called dunder methods.
*[dunder]: A method with double underscores (e.g., __init__, __str__), also called a magic method.

<!-- Check Types -->
*[presence check]: Docvet's layer 1 check for missing docstrings on public symbols, with coverage metrics.
*[Presence check]: Docvet's layer 1 check for missing docstrings on public symbols, with coverage metrics.
*[enrichment check]: Docvet's layer 3 check that uses AST analysis to detect missing docstring sections such as Raises, Yields, Attributes, and Examples.
*[Enrichment check]: Docvet's layer 3 check that uses AST analysis to detect missing docstring sections such as Raises, Yields, Attributes, and Examples.
*[freshness check]: Docvet's layer 4 check that detects stale docstrings — code that has changed without a corresponding docstring update.
*[Freshness check]: Docvet's layer 4 check that detects stale docstrings — code that has changed without a corresponding docstring update.
*[coverage check]: Docvet's layer 6 check that detects missing __init__.py files that prevent mkdocstrings from discovering Python packages.
*[Coverage check]: Docvet's layer 6 check that detects missing __init__.py files that prevent mkdocstrings from discovering Python packages.
*[griffe compatibility check]: Docvet's layer 5 check that captures griffe parser warnings to ensure docstrings render correctly with mkdocstrings.
*[Griffe compatibility check]: Docvet's layer 5 check that captures griffe parser warnings to ensure docstrings render correctly with mkdocstrings.
*[diff mode]: A freshness check strategy that maps git diff hunks to AST symbols, flagging code changes that lack corresponding docstring updates.
*[Diff mode]: A freshness check strategy that maps git diff hunks to AST symbols, flagging code changes that lack corresponding docstring updates.
*[drift mode]: A freshness check strategy using git blame timestamps to detect docstrings not updated after code changed. Controlled by drift-threshold and age-threshold.
*[Drift mode]: A freshness check strategy using git blame timestamps to detect docstrings not updated after code changed. Controlled by drift-threshold and age-threshold.
*[sweep]: Freshness drift mode's full-codebase scan via git blame to detect docstrings drifted out of sync.
*[Sweep]: Freshness drift mode's full-codebase scan via git blame to detect docstrings drifted out of sync.

<!-- Quality Model -->
*[six-layer model]: Docvet's framework for docstring quality: presence, style, completeness, accuracy, rendering, and visibility. Docvet implements layers 1 and 3–6; layer 2 is handled by ruff.
*[Six-layer model]: Docvet's framework for docstring quality: presence, style, completeness, accuracy, rendering, and visibility. Docvet implements layers 1 and 3–6; layer 2 is handled by ruff.
*[finding]: A single issue detected by a docvet check, containing file path, line number, symbol name, rule ID, message, and category.
*[Finding]: A single issue detected by a docvet check, containing file path, line number, symbol name, rule ID, message, and category.
*[findings]: Issues detected by docvet checks, each containing file path, line number, symbol name, rule ID, message, and category.
*[Findings]: Issues detected by docvet checks, each containing file path, line number, symbol name, rule ID, message, and category.
*[rule]: A specific check condition docvet evaluates, identified by a slug like missing-raises or stale-signature.
*[Rule]: A specific check condition docvet evaluates, identified by a slug like missing-raises or stale-signature.
*[freshness drift]: The time gap between the last code change to a symbol and the last docstring update, measured via git blame timestamps.
*[Freshness drift]: The time gap between the last code change to a symbol and the last docstring update, measured via git blame timestamps.
*[cognitive complexity]: A measure of how difficult code is to understand, calculated by counting control flow nesting and breaks in linear flow.
*[Cognitive complexity]: A measure of how difficult code is to understand, calculated by counting control flow nesting and breaks in linear flow.
*[docstring coverage]: The percentage of public symbols that have docstrings, measured by the presence check.
*[Docstring coverage]: The percentage of public symbols that have docstrings, measured by the presence check.
*[stale docstring]: A docstring that has not been updated to reflect recent code changes, detected by the freshness check.
*[Stale docstring]: A docstring that has not been updated to reflect recent code changes, detected by the freshness check.

<!-- Infrastructure & Tooling -->
*[AST]: Abstract Syntax Tree — Python's parsed representation of source code, used by docvet to analyze code structure.
*[griffe]: A Python documentation framework that extracts information from source code. Used by docvet for rendering checks and by mkdocstrings for API docs.
*[Griffe]: A Python documentation framework that extracts information from source code. Used by docvet for rendering checks and by mkdocstrings for API docs.
*[mkdocstrings]: An MkDocs plugin that auto-generates API documentation from Python source code using griffe.
*[dogfooding]: The practice of using your own product — docvet runs its own checks on its own codebase.
*[Dogfooding]: The practice of using your own product — docvet runs its own checks on its own codebase.
*[hunk]: A contiguous block of changed lines in a git diff, mapped to symbols by comparing line numbers against AST line ranges.
*[Hunk]: A contiguous block of changed lines in a git diff, mapped to symbols by comparing line numbers against AST line ranges.
*[LSP]: Language Server Protocol — a standard for editor integration providing real-time diagnostics.
*[Interrogate]: A third-party Python tool for docstring presence checking, superseded by docvet's presence check.
*[interrogate]: A third-party Python tool for docstring presence checking, superseded by docvet's presence check.

<!-- CLI & Configuration -->
*[fail-on]: A CLI flag controlling which severity levels cause a non-zero exit code.
*[Fail-on]: A CLI flag controlling which severity levels cause a non-zero exit code.
*[threshold]: A configurable numeric limit used by checks (e.g., drift-threshold, age-threshold, min-coverage).
*[Threshold]: A configurable numeric limit used by checks (e.g., drift-threshold, age-threshold, min-coverage).
*[staged]: The git staging area; the --staged flag restricts checks to staged files.
*[Staged]: The git staging area; the --staged flag restricts checks to staged files.
