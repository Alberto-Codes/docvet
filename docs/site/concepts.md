---
title: Concepts
---

# Concepts

## The Problem

A developer renames a parameter, adds a new exception path, removes a return value. The code is correct — but the docstring still describes the old behavior. Now every human reading that docstring is misled, and every AI agent using it as context generates worse code.

This isn't a hypothetical. Research shows that incorrect documentation degrades LLM task success by 22.6 percentage points — while missing documentation has no statistically significant effect ([Macke & Doyle, NAACL 2024](https://arxiv.org/abs/2404.03114)). Wrong is worse than absent.

Ruff's opt-in D rules cover style and presence; its preview DOC rules add structural checks. pydoclint checks structural agreement across arguments, returns, yields, raises, attributes, and type hints. docvet combines structural checks with history-based staleness signals and renderer diagnostics. See the [dated, source-linked comparison](https://github.com/Alberto-Codes/docvet#why-docvet). None of these checks proves that prose is semantically true.

As the [2025 DORA report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report) puts it: "AI doesn't fix a team; it amplifies what's already there." Stale docstrings don't just confuse humans — they actively degrade the AI tools your team relies on.

## See It in Action

Here's a function whose docstring exists but omits parameters, returns, and raised exceptions:

```python
def fetch_user(user_id: int, *, include_deleted: bool = False) -> User:
    """Retrieve a user by ID.

    Args:
        user_id: The user's unique identifier.
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"Invalid user ID: {user_id}")

    query = select(User).where(User.id == user_id)
    if not include_deleted:
        query = query.where(User.is_active.is_(True))

    result = session.execute(query).scalar_one_or_none()
    if result is None:
        raise LookupError(f"User {user_id} not found")

    return result
```

Presence alone does not catch these omissions. Ruff and pydoclint can report structural gaps depending on selected rules and configuration. docvet's AST checks include parameter agreement and missing sections; this excerpt shows the missing `Raises` finding:

```text
src/myapp/users.py:4: missing-raises     Function 'fetch_user' raises LookupError, ValueError but has no Raises: section [required]
Vetted 1 files [enrichment] — 1 finding (1 required, 0 recommended). (0.1s)
```

Now fix the docstring:

```python
def fetch_user(user_id: int, *, include_deleted: bool = False) -> User:
    """Retrieve a user by ID.

    Args:
        user_id: The user's unique identifier.
        include_deleted: If True, include soft-deleted users in the
            lookup. Defaults to False.

    Returns:
        The matching user record.

    Raises:
        ValueError: If user_id is not a positive integer.
        LookupError: If no matching user is found.

    Examples:
        ```python
        user = fetch_user(42)
        admin = fetch_user(1, include_deleted=True)
        ```
    """
```

The expanded docstring documents the omitted structure and gives readers more context. A reviewer still needs to verify that the descriptions match the intended behavior.

## The Six-Layer Quality Model

Docstring quality isn't binary. It's a stack of six layers, each catching a different class of problem:

**Layer 1 — Presence.**
Does every public symbol have a docstring? A function without a docstring is invisible to documentation generators and opaque to AI agents. docvet's [`presence`](checks/presence.md) check catches missing docstrings and reports coverage metrics.

**Layer 2 — Style.**
Is the docstring formatted consistently? Google-style, NumPy-style, or Sphinx-style — pick one and enforce it. This is ruff's domain (D rules). docvet doesn't duplicate it.

**Layer 3 — Completeness.**
Does the docstring cover what the code actually does? A function that raises exceptions needs a `Raises` section. A class with attributes needs an `Attributes` section. A generator needs `Yields`. docvet's [`enrichment`](checks/enrichment.md) check uses AST analysis to detect these gaps — [{{ rule_count("enrichment") }} rules](checks/enrichment.md) covering Raises, Yields, Receives, Warns, Attributes, Examples, and more.

**Layer 4 — Accuracy.**
Does the docstring still match the code? This is the most dangerous layer when it fails — research shows misleading documentation reduces LLM fault localization accuracy to 25.63% across 750,000 tasks ([Haroon et al., 2025](https://arxiv.org/abs/2504.04372)). docvet's [`freshness`](checks/freshness.md) check uses git diff and git blame as staleness heuristics. Changes without docstring updates and old timestamps suggest review; they do not establish an error. Updating code and prose together does not establish correctness either.

**Layer 5 — Rendering.**
Will the docstring render correctly in mkdocs? Griffe parser warnings indicate structural problems that produce broken or missing documentation on your site. docvet's [`griffe`](checks/griffe.md) check captures these warnings before they reach production.

**Layer 6 — Visibility.**
Will documentation generators even find the file? A Python package missing `__init__.py` in a parent directory is invisible to mkdocstrings. docvet's [`coverage`](checks/coverage.md) check finds these gaps.

Layer 1 was historically handled by tools like interrogate. docvet's `presence` check now covers this natively, so a single `docvet check` run covers layers 1 and 3–6. Ruff can provide style checks alongside these signals; human review remains necessary for semantic accuracy.

## When to Use Each Check

| Check | Use when... | Learn more |
|-------|-------------|------------|
| `presence` | You want every public symbol to have a docstring, with coverage metrics | [Presence check](checks/presence.md) |
| `enrichment` | You want complete docstrings — Raises, Attributes, Examples, and more | [Enrichment check](checks/enrichment.md) |
| `freshness` | Code changed but docstrings didn't get updated | [Freshness check](checks/freshness.md) |
| `coverage` | Your mkdocs site is missing modules because of absent `__init__.py` files | [Coverage check](checks/coverage.md) |
| `griffe` | mkdocstrings can't parse your docstrings correctly | [Griffe check](checks/griffe.md) |

Running `docvet check` executes all enabled checks in a single pass. You can also run individual checks when you need focused feedback — for example, `docvet freshness` during development to catch stale docstrings before they reach CI.

## Where docvet Fits

docvet is designed to complement ruff, not replace it:

- **ruff** offers style and presence checks (D rules), plus partial structural completeness checks (preview DOC rules).
- **docvet** combines presence metrics, structural completeness, staleness heuristics, rendering diagnostics, and package visibility checks.

Enable the rules that fit your project. Passing checks does not certify semantic accuracy.

```text
ruff check .          # Configured Ruff rules
docvet check --all    # Structural checks and history/rendering signals
```

!!! info "Further Reading"

    Research on how documentation quality affects AI coding tools:

    - **[Testing the Effect of Code Documentation on LLM Code Understanding](https://arxiv.org/abs/2404.03114)** (NAACL 2024) — Incorrect docs degrade LLM test generation success by 22.6pp; missing docs have no significant effect. Wrong is worse than absent.
    - **[Code Needs Comments: Enhancing Code LLMs with Comment Augmentation](https://arxiv.org/abs/2402.13013)** — Comment density improves code generation by 40–54%. Existing open-source corpora average only 16.7% comment density.
    - **[Impact of Code Changes on Fault Localizability of LLMs](https://arxiv.org/abs/2504.04372)** — Misleading comments drop LLM fault localization accuracy to 25.63% across 750K tasks and 10 frontier models.
    - **[Your Coding Intent is Secretly in the Context](https://arxiv.org/abs/2508.09537)** — Docstrings unlock 44–84% relative performance gains in code generation benchmarks.
    - **[2025 DORA Report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report)** — AI amplifies existing quality: 98% more PRs merged, but 9% more bugs without quality foundations.
    - **[Code Smells for AI Agents](https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory)** (Stack Overflow) — "The only signal was code quality. The higher-quality the codebase, the more AI accelerated the organization."
