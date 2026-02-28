---
applyTo: "**/*test*.py,**/test_*.py,**/tests/**/*.py,**/conftest.py"
description: "Pytest best practices for docvet test code"
---

# Pytest Best Practices

## Test File and Function Naming

### File Naming
- **MUST** use `test_*.py` or `*_test.py` pattern
- Place test files in `tests/` directory at project root
- Mirror application structure: `src/docvet/checks/enrichment.py` -> `tests/unit/checks/test_enrichment.py`

### Test Function Naming
- **MUST** prefix test functions with `test_`
- Use descriptive names: `test_<what>_<condition>_<expected_result>`
- Examples:
  - `test_enrichment_detects_missing_raises_section()`
  - `test_freshness_flags_signature_change_as_high()`
  - `test_coverage_finds_missing_init_py()`

### Test Class Naming
- **MUST** prefix test classes with `Test`
- No `__init__` method in test classes

```python
class TestEnrichmentCheck:
    def test_detects_missing_raises(self):
        pass

    def test_ignores_private_functions(self):
        pass
```

## Test Organization

### Directory Structure
```
tests/
    conftest.py              # Shared fixtures
    unit/
        checks/
            test_enrichment.py
            test_freshness.py
            test_coverage.py
            test_griffe_compat.py
        test_ast_utils.py
        test_config.py
        test_discovery.py
    integration/
        conftest.py          # Git repo fixtures
        test_freshness_diff.py
        test_freshness_drift.py
    fixtures/
        missing_raises.py    # Known docstring issues
        stale_signature.py
        complete_module.py
```

### Testing Pyramid
- **MOST tests**: Unit tests (feed Python source strings into AST analyzers, no git, no filesystem)
- **FEWER tests**: Integration tests (temp git repos, real git operations)
- **Fixture files**: `.py` files with known docstring issues for assertion

### Organization Principles
- Each test verifies ONE specific aspect
- Tests are independent - no execution order dependencies
- Tests are fast, deterministic, and readable

## Fixtures

### Basic Fixtures
```python
@pytest.fixture
def sample_source():
    return '''
def process(items: list[str]) -> int:
    """Process items."""
    if not items:
        raise ValueError("Empty list")
    return len(items)
'''

@pytest.fixture
def make_source():
    """Factory for creating Python source with specific patterns."""
    def _make(*, has_raise=False, has_yield=False, has_docstring=True):
        ...
    return _make
```

### conftest.py Usage
- Root `tests/conftest.py` for global fixtures (source factories, AST helpers)
- `tests/integration/conftest.py` for git repo fixtures (tmp_path-based temp repos)

### Fixture Anti-Patterns to Avoid
- Overloaded fixtures with too many responsibilities
- Hardcoded values (use factory pattern instead)
- Deep fixture dependency chains
- Duplicating fixtures across test files (use conftest.py)

## Parametrization

```python
@pytest.mark.parametrize("source, expected_sections", [
    (SOURCE_WITH_RAISE, ["Raises"]),
    (SOURCE_WITH_YIELD, ["Yields"]),
    (SOURCE_WITH_KWARGS, ["Other Parameters"]),
], ids=["raises", "yields", "kwargs"])
def test_enrichment_detects_missing_sections(source, expected_sections):
    findings = run_enrichment(source)
    assert [f.section for f in findings] == expected_sections
```

## Assertions

- **One assert per test** (recommended)
- Use plain `assert` statements
- Test public interfaces, not private methods

```python
def test_enrichment_finding_has_correct_severity():
    findings = run_enrichment(SOURCE_WITH_RAISE)
    assert findings[0].severity == "HIGH"

def test_invalid_config_raises_error():
    with pytest.raises(ConfigurationError) as excinfo:
        load_config({"src-root": ""})
    assert "src-root" in str(excinfo.value)
```

## Test Markers

### Module-Level Markers (Convention)

Every test file **MUST** have a module-level `pytestmark` assignment after imports (excluding `conftest.py` files, which contain fixtures, not tests):

- Unit test files (`tests/unit/`): `pytestmark = pytest.mark.unit`
- Integration test files (`tests/integration/`): `pytestmark = pytest.mark.integration`

Place the assignment after all imports, before any test code:

```python
from __future__ import annotations

import ast

import pytest

from docvet.checks import Finding

pytestmark = pytest.mark.unit


class TestSomething:
    ...
```

**Rationale:** Module-level `pytestmark` applies the marker to all tests in the file, enabling `pytest -m unit` for fast local feedback and `pytest -m integration` for targeted integration testing. All markers are registered in `pyproject.toml` with `--strict-markers` enforced.

Do **not** use class-level or function-level `@pytest.mark.unit`/`@pytest.mark.integration` decorators — the module-level convention makes them redundant.

### Additional Markers

Use function-level decorators for cross-cutting markers like `slow`:

```python
@pytest.mark.slow
def test_freshness_diff_with_real_git(tmp_path):
    ...
```

### Running Tests
```bash
uv run pytest                     # All tests
uv run pytest tests/unit          # Unit tests only (by directory)
uv run pytest -m unit             # Unit tests only (by marker)
uv run pytest -m integration      # Integration tests only (by marker)
uv run pytest -k "enrichment"    # Tests matching keyword
uv run pytest -m "not slow"      # Exclude slow tests
uv run pytest --cov=docvet --cov-report=term-missing  # With coverage
```

## Mocking

### When to Mock
- Git subprocess calls (for unit tests)
- File system operations (for unit tests)
- External tools (griffe parser in isolation)

### Patching Strategy
Patch where the object is USED, not where it's DEFINED:
```python
mocker.patch("docvet.checks.freshness.subprocess.run")  # Correct
mocker.patch("subprocess.run")  # Wrong - too broad
```

### Prefer Source Strings Over Mocks
For AST-based checks, prefer feeding Python source strings directly:
```python
def test_detects_missing_yields():
    source = '''
def gen():
    """A generator."""
    yield 42
'''
    tree = ast.parse(source)
    findings = check_enrichment(tree)
    assert any(f.section == "Yields" for f in findings)
```

## Testing Checklist

### Before Writing Tests
- [ ] Test files follow `test_*.py` naming
- [ ] Custom markers registered in pyproject.toml
- [ ] Fixtures in appropriate conftest.py

### While Writing Tests
- [ ] Descriptive test names (`test_<what>_<condition>_<expected>`)
- [ ] One assertion per test
- [ ] Tests are independent and order-free
- [ ] External deps mocked in unit tests
- [ ] Exception messages validated, not just types
