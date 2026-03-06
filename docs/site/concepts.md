---
title: Concepts
---

# Concepts

## The Problem

A developer renames a parameter, adds a new exception path, removes a return value. The code is correct — but the docstring still describes the old behavior. Now every human reading that docstring is misled, and every AI agent using it as context generates worse code.

This isn't a hypothetical. Research shows that incorrect documentation degrades LLM task success by 22.6 percentage points — while missing documentation has no statistically significant effect ([Macke & Doyle, NAACL 2024](https://arxiv.org/abs/2404.03114)). Wrong is worse than absent.

Most Python projects already lint docstring **style** with ruff's D rules. Some check **presence** — whether docstrings exist at all. But nobody checks whether docstrings are **true**. That's the gap docvet fills.

As the [2025 DORA report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report) puts it: "AI doesn't fix a team; it amplifies what's already there." Stale docstrings don't just confuse humans — they actively degrade the AI tools your team relies on.

## See It in Action

Here's a function with real docstring gaps — the kind that pass ruff and exist (so interrogate is happy) but actively mislead:

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

This docstring exists and is Google-style formatted. ruff sees no issues. But it's missing documentation for the `include_deleted` parameter, and it raises two exceptions (`ValueError`, `LookupError`) without a `Raises` section. Run docvet:

```text
src/myapp/users.py:4: missing-raises     Function 'fetch_user' raises ValueError, LookupError but Raises section is missing [required]
src/myapp/users.py:4: missing-examples   Function 'fetch_user' is a public function with parameters but has no Examples section [recommended]
Vetted 1 file [enrichment] — 2 findings (1 required, 1 recommended). (0.1s)
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

That's the difference between a docstring that exists and one that's complete. The first passes style checks. The second passes quality checks — and gives AI agents the context they need to use the function correctly.

## The Six-Layer Quality Model

Docstring quality isn't binary. It's a stack of six layers, each catching a different class of problem:

**Layer 1 — Presence.**
Does every public symbol have a docstring? A function without a docstring is invisible to documentation generators and opaque to AI agents. docvet's [`presence`](checks/presence.md) check catches missing docstrings and reports coverage metrics.

**Layer 2 — Style.**
Is the docstring formatted consistently? Google-style, NumPy-style, or Sphinx-style — pick one and enforce it. This is ruff's domain (D rules). docvet doesn't duplicate it.

**Layer 3 — Completeness.**
Does the docstring cover what the code actually does? A function that raises exceptions needs a `Raises` section. A class with attributes needs an `Attributes` section. A generator needs `Yields`. docvet's [`enrichment`](checks/enrichment.md) check uses AST analysis to detect these gaps — [10 rules](checks/enrichment.md) covering Raises, Yields, Receives, Warns, Attributes, Examples, and more.

**Layer 4 — Accuracy.**
Does the docstring still match the code? This is the most dangerous layer when it fails — research shows misleading documentation reduces LLM fault localization accuracy to 24.55% across 750,000 tasks ([Haroon et al., 2025](https://arxiv.org/abs/2504.04372)). docvet's [`freshness`](checks/freshness.md) check uses git diff and git blame to flag code that changed without a corresponding docstring update.

**Layer 5 — Rendering.**
Will the docstring render correctly in mkdocs? Griffe parser warnings indicate structural problems that produce broken or missing documentation on your site. docvet's [`griffe`](checks/griffe.md) check captures these warnings before they reach production.

**Layer 6 — Visibility.**
Will documentation generators even find the file? A Python package missing `__init__.py` in a parent directory is invisible to mkdocstrings. docvet's [`coverage`](checks/coverage.md) check finds these gaps.

Layer 1 was historically handled by tools like interrogate. docvet's `presence` check now covers this natively, so a single `docvet check` run covers layers 1 and 3–6. Combined with ruff for layer 2, two tools give you the complete stack.

## When to Use Each Check

| Check | Use when... | Learn more |
|-------|-------------|------------|
| [`presence`](checks/presence.md) | You want every public symbol to have a docstring, with coverage metrics | [Presence check](checks/presence.md) |
| [`enrichment`](checks/enrichment.md) | You want complete docstrings — Raises, Attributes, Examples, and more | [Enrichment check](checks/enrichment.md) |
| [`freshness`](checks/freshness.md) | Code changed but docstrings didn't get updated | [Freshness check](checks/freshness.md) |
| [`coverage`](checks/coverage.md) | Your mkdocs site is missing modules because of absent `__init__.py` files | [Coverage check](checks/coverage.md) |
| [`griffe`](checks/griffe.md) | mkdocstrings can't parse your docstrings correctly | [Griffe check](checks/griffe.md) |

Running `docvet check` executes all enabled checks in a single pass. You can also run individual checks when you need focused feedback — for example, `docvet freshness` during development to catch stale docstrings before they reach CI.

## Where docvet Fits

docvet is designed to complement ruff, not replace it:

- **ruff** enforces docstring **style** — formatting, conventions, section ordering (D rules).
- **docvet** enforces docstring **quality** — presence, completeness, accuracy, rendering, and visibility.

Together, they cover the full quality stack. ruff makes sure your docstrings look right. docvet makes sure they're right.

```text
ruff check .          # Style (layer 2)
docvet check --all    # Everything else (layers 1, 3–6)
```

!!! info "Further Reading"

    Research on how documentation quality affects AI coding tools:

    - **[Testing the Effect of Code Documentation on LLM Code Understanding](https://arxiv.org/abs/2404.03114)** (NAACL 2024) — Incorrect docs degrade LLM test generation success by 22.6pp; missing docs have no significant effect. Wrong is worse than absent.
    - **[Code Needs Comments: Enhancing Code LLMs with Comment Augmentation](https://arxiv.org/abs/2402.13013)** — Comment density improves code generation by 40–54%. Existing open-source corpora average only 16.7% comment density.
    - **[Impact of Code Changes on Fault Localizability of LLMs](https://arxiv.org/abs/2504.04372)** — Misleading comments drop LLM fault localization accuracy to 25.63% across 750K tasks and 10 frontier models.
    - **[Your Coding Intent is Secretly in the Context](https://arxiv.org/abs/2508.09537)** — Docstrings unlock 44–84% relative performance gains in code generation benchmarks.
    - **[2025 DORA Report](https://cloud.google.com/resources/content/2025-dora-ai-assisted-software-development-report)** — AI amplifies existing quality: 98% more PRs merged, but 9% more bugs without quality foundations.
    - **[Code Smells for AI Agents](https://stackoverflow.blog/2026/02/04/code-smells-for-ai-agents-q-and-a-with-eno-reyes-of-factory)** (Stack Overflow) — "The only signal was code quality. The higher-quality the codebase, the more AI accelerated the organization."
