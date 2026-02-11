# Dev Quality Checklist

Quality patterns learned across 6 epics. Apply these during development, not just review.

## AC-to-Test Traceability (Epic 6+)

Before marking a story done, fill the AC-to-Test Mapping table in the story file. Every acceptance criterion must have at least one test that directly verifies it. Tests should be written from the AC contract, not just from the implementation.

## Assertion Strength (Epic 5+)

- Verify ALL relevant fields, not just the primary one (e.g., all 6 Finding fields: `file`, `line`, `symbol`, `rule`, `message`, `category`)
- Use `assert_called_once_with(...)` not `assert_called_once()` — verify arguments, not just call count
- Add negative assertions where appropriate (e.g., a passing case produces zero findings)
- Include `assert len(results) == N` to catch deduplication breakage

## Edge Case Coverage (Epic 4+)

- Proactively add boundary tests: exact threshold values, empty inputs, deeply nested structures
- Test mix scenarios: some passing + some failing in same input
- Test skip conditions: inputs that should produce zero results

## Task Tracking Accuracy (Epic 6+)

- Before marking a subtask `[x]` done, verify the code change actually exists
- Run the relevant test to confirm the change is real
- Do not mark implementation tasks done based on intent — only on verified code
