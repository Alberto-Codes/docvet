"""Macros hook for mkdocs-macros-plugin.

Loads rule metadata from docs/rules.yml and provides Jinja macros
for rendering consistent rule page headers and fix guidance sections.

Examples:
    Configure in ``mkdocs.yml``::

        plugins:
          - macros:
              module_name: docs/main

    Use in a rule page::

        {{rule_header()}}
        {{rule_fix()}}

See Also:
    :doc:`docs/rules.yml`: Rule metadata catalog consumed by this module.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def define_env(env):
    """Define macros and variables for mkdocs-macros-plugin.

    Registers the ``rule_header`` and ``rule_fix`` macros which render
    breadcrumb back-links, metadata tables, and "How to Fix" sections
    on rule reference pages.
    """
    rules_path = Path(env.project_dir) / "docs" / "rules.yml"
    rules_data = yaml.safe_load(rules_path.read_text())
    rules_by_id = {rule["id"]: rule for rule in rules_data}

    @env.macro
    def rule_header() -> str:
        """Render a back-link and metadata table for the current rule page.

        Looks up the rule by page filename in the ``rules_by_id`` dict and
        builds a markdown string with navigation and metadata.

        Returns:
            Markdown string with a breadcrumb back-link to the parent check
            page followed by a metadata table and summary blockquote.

        Raises:
            ValueError: If the page filename does not match any rule in rules.yml.
        """
        page_name = env.page.file.name  # e.g. "missing-raises.md"
        rule_id = page_name.removesuffix(".md")

        if rule_id not in rules_by_id:
            msg = (
                f"Rule '{rule_id}' not found in docs/rules.yml. "
                f"Available rules: {', '.join(sorted(rules_by_id))}"
            )
            raise ValueError(msg)

        rule = rules_by_id[rule_id]
        check = rule["check"]
        check_display = f"{check.capitalize()} Check"
        back_link = f"*Part of: [{check_display}](../checks/{check}.md)*\n\n"

        return (
            back_link + f"| | |\n"
            f"|---|---|\n"
            f"| **Check** | {check} |\n"
            f"| **Category** | {rule['category']} |\n"
            f"| **Applies to** | {rule['applies_to']} |\n"
            f"| **Since** | v{rule['since']} |\n"
            f"\n"
            f"> {rule['summary']}\n"
        )

    @env.macro
    def rule_fix() -> str:
        """Render a "How to Fix" section for the current rule page.

        Reads the ``fix`` field from rules.yml for the current page's rule
        and wraps it with a heading.

        Returns:
            Markdown string with a "How to Fix" heading and fix content,
            or empty string if no fix content exists.
        """
        rule_id = env.page.file.name.removesuffix(".md")
        rule = rules_by_id.get(rule_id)
        if not rule:
            return ""
        fix_content = rule.get("fix", "")
        if not fix_content:
            return ""
        return f"## How to Fix\n\n{fix_content}\n"
