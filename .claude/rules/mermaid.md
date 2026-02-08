---
paths:
  - "**/*architecture*.md"
---

# Mermaid Diagram Guidelines

Use Mermaid diagrams to make documentation clearer and easier to understand.

## Core Principle: Visualize for Clarity

**Use Mermaid diagrams when:**
- Visual representation makes concepts clearer than prose alone
- Showing relationships, flows, or structures
- Documenting processes, architectures, or interactions

**Avoid diagrams when:**
- Simple text or a list is equally clear
- The diagram would be overly complex (>20 nodes)

## Diagram Types

| Need to Show... | Use This Diagram Type |
|----------------|----------------------|
| Step-by-step process | Flowchart |
| System interactions over time | Sequence Diagram |
| Object structure and relationships | Class Diagram |
| State transitions | State Diagram |
| Project timeline | Gantt Chart |

## Best Practices

- Use `TD` (top-down) or `LR` (left-right) based on content flow
- Keep nodes descriptive but concise
- Use shapes meaningfully: rectangles for steps, diamonds for decisions
- Add labels to edges for clarity

## C4 Architecture Diagrams

**Do NOT use Mermaid's native C4 syntax** (`C4Context`, `C4Container`). These have hardcoded CSS colors that don't respond to themes.

Instead, express C4 concepts using **standard flowchart syntax with subgraphs**.

## Line Breaks in Node Labels

Use `<br>` for line breaks inside double-quoted node labels. **Never use `\n`**.

## General Standards

1. **Clarity over completeness**: Show what matters, hide details
2. **Consistent naming**: Use project terminology
3. **Keep it simple**: If >20 nodes, consider breaking it up
4. **Update diagrams when code changes**
