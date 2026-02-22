"""Macros hook for mkdocs-macros-plugin.

Loads rule metadata from docs/rules.yml and provides Jinja macros
for rendering consistent rule page headers.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def define_env(env):
    """Define macros and variables for mkdocs-macros-plugin."""
    rules_path = Path(env.project_dir) / "docs" / "rules.yml"
    rules_data = yaml.safe_load(rules_path.read_text())
    rules_by_id = {rule["id"]: rule for rule in rules_data}

    @env.macro
    def rule_header() -> str:
        """Render a metadata table for the current rule page.

        Returns:
            Markdown string containing a metadata table and summary blockquote.

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

        return (
            f"| | |\n"
            f"|---|---|\n"
            f"| **Check** | {rule['check']} |\n"
            f"| **Category** | {rule['category']} |\n"
            f"| **Applies to** | {rule['applies_to']} |\n"
            f"| **Since** | v{rule['since']} |\n"
            f"\n"
            f"> {rule['summary']}\n"
        )
