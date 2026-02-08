---
paths:
  - "**/*test*.py"
  - "**/test_*.py"
  - "**/tests/**/*.py"
  - "**/conftest.py"
---

# Pytest Best Practices

## Test File and Function Naming

### File Naming Conventions
- **MUST** use `test_*.py` or `*_test.py` pattern for pytest to discover tests
- Place test files in dedicated `tests/` directory at project root
- Mirror application structure in test directory
- Example: Testing `src/docvet/checks/enrichment.py` -> `tests/unit/checks/test_enrichment.py`

### Test Function Naming
- **MUST** prefix test functions with `test_`
- Use descriptive names following pattern: `test_<what>_<condition>_<expected_result>`
- Examples:
  - `test_enrichment_detects_missing_raises_section()`
  - `test_freshness_flags_signature_change_as_high()`
  - `test_coverage_finds_missing_init_py()`
- Avoid generic names like `test1()` or `test_function()`

### Test Class Naming
- **MUST** prefix test classes with `Test` (capital T)
- Class methods **MUST** start with `test_`
- No `__init__` method in test classes
- Use classes to group related tests for a specific feature or module

```python
class TestEnrichmentCheck:
    def test_detects_missing_raises(self):
        pass

    def test_ignores_private_functions(self):
        pass
```

## Test Organization and Structure

### Testing Pyramid
- **MOST tests**: Unit tests (fast, isolated — feed Python source strings into AST analyzers)
- **FEWER tests**: Integration tests (temp git repos with known commit histories)
- **Fixture files**: `.py` files in `tests/fixtures/` with known docstring issues

### Organization Principles
- Mirror application code structure in test directories
- Separate tests by type (unit/integration) using subdirectories
- Each test should verify ONE specific aspect of code
- Keep tests independent - no execution order dependencies
- Tests should be fast, deterministic, and readable

## Fixtures Best Practices

### Fixture Definition
```python
@pytest.fixture
def parse_source():
    def _parse(source: str) -> ast.Module:
        return ast.parse(source)
    return _parse

@pytest.fixture
def git_repo(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    yield tmp_path
```

### Fixture Scopes
- **function** (default): Created/destroyed for each test - maximum isolation
- **class**: Shared across all methods in a test class
- **module**: Shared across all tests in a module - for expensive setup
- **session**: Shared across entire test session - for very expensive operations

### conftest.py Usage
- Place shared fixtures in `conftest.py` for automatic discovery (no imports needed)
- Root-level `tests/conftest.py` for global fixtures (source factories, AST helpers)
- `tests/integration/conftest.py` for git repo fixtures

### Fixture Patterns

**Factory Fixtures (for flexibility):**
```python
@pytest.fixture
def make_source():
    def _make(*, has_raise=False, has_yield=False, has_docstring=True):
        ...
    return _make
```

### Fixture Anti-Patterns to Avoid
- Overloaded fixtures with too many responsibilities
- Hardcoded values (use factory pattern instead)
- Global state leakage without proper cleanup
- Deep fixture dependency chains
- Duplicating fixtures across test files (use conftest.py)

## Parametrization

### Parametrizing with IDs
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

## Assertions and Testing Patterns

### Assertion Principles
- **One assert per test** (recommended) - makes failures easier to diagnose
- Use plain `assert` statements - pytest provides detailed introspection
- Test public interfaces, not private methods or implementation details

### Exception Testing
```python
def test_invalid_config_raises_error():
    with pytest.raises(ConfigurationError) as excinfo:
        load_config({"src-root": ""})
    assert "src-root" in str(excinfo.value)
```

### Assertion Anti-Patterns
- Testing private methods (test public interface instead)
- Testing implementation details
- Non-deterministic assertions
- Multiple unrelated assertions in single test
- Not validating exception messages

## Test Markers

### Custom Markers
```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (temp git repos, slower)",
    "slow: Slow-running tests",
]
```

### Module-level Markers
```python
pytestmark = [pytest.mark.unit]
```

## Mocking and Patching

### When to Mock
- Git subprocess calls (for unit tests)
- File system operations (for unit tests)
- External tools (griffe parser in isolation)

### Patching Strategies
**Key Rule**: Patch where the object is USED, not where it's DEFINED

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

### Mocking Best Practices
- Use `autospec=True` to respect method signatures
- Prefer source strings and real AST parsing over mocks when possible
- Mock external dependencies, not internal logic

## Quick Reference

### Run Tests
```bash
uv run pytest                     # All tests
uv run pytest tests/unit          # Unit tests only
uv run pytest -k "enrichment"    # Tests matching keyword
uv run pytest -m "not slow"      # Exclude slow tests
uv run pytest --lf                # Run last failed tests
uv run pytest -x                  # Stop on first failure
```
