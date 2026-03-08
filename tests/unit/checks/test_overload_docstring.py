"""Tests for the overload-has-docstring presence rule.

Verifies that ``@overload``-decorated functions with docstrings are
flagged, while overloads without docstrings and implementation functions
with docstrings are not.
"""

from __future__ import annotations

import textwrap

import pytest

from docvet.checks._finding import Finding
from docvet.checks.presence import check_presence
from docvet.config import PresenceConfig

pytestmark = pytest.mark.unit


def _run(source: str, **config_kwargs: object) -> list[Finding]:
    """Run presence check and return only overload-has-docstring findings."""
    config = PresenceConfig(**config_kwargs)  # type: ignore[arg-type]
    findings, _ = check_presence(textwrap.dedent(source), "test.py", config)
    return [f for f in findings if f.rule == "overload-has-docstring"]


class TestOverloadBareNameWithDocstring:
    """AC 1: bare @overload with docstring produces a finding."""

    def test_bare_overload_with_docstring(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None:
            """Connect with string address."""
            ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        assert findings[0].symbol == "connect"


class TestOverloadAttributeFormWithDocstring:
    """AC 2: @typing.overload and @typing_extensions.overload with docstring."""

    def test_typing_dot_overload_with_docstring(self) -> None:
        source = '''\
        import typing

        @typing.overload
        def process(data: str) -> str:
            """Process string data."""
            ...

        def process(data):
            """Process data."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        assert findings[0].symbol == "process"

    def test_typing_extensions_dot_overload_with_docstring(self) -> None:
        source = '''\
        import typing_extensions

        @typing_extensions.overload
        def parse(value: int) -> int:
            """Parse integer."""
            ...

        def parse(value):
            """Parse value."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        assert findings[0].symbol == "parse"


class TestOverloadWithoutDocstring:
    """AC 3: @overload without docstring produces no finding."""

    def test_bare_overload_no_docstring(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None: ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 0


class TestImplementationWithDocstring:
    """AC 4: implementation function (no @overload) with docstring is fine."""

    def test_implementation_not_flagged(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None: ...

        @overload
        def connect(address: tuple) -> None: ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 0


class TestOverloadStubsExcludedFromMissingDocstring:
    """Overload stubs must not emit missing-docstring or count in stats."""

    def test_no_missing_docstring_for_overload_stubs(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None: ...

        @overload
        def connect(address: tuple) -> None: ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        config = PresenceConfig()
        all_findings, stats = check_presence(textwrap.dedent(source), "test.py", config)
        # No missing-docstring for overload stubs, no overload-has-docstring either
        missing = [
            f
            for f in all_findings
            if f.symbol == "connect" and f.rule == "missing-docstring"
        ]
        assert len(missing) == 0
        # Overload stubs excluded from coverage stats (only module + implementation)
        assert stats.total == 2
        assert stats.documented == 1  # implementation has docstring, module doesn't

    def test_overload_stubs_excluded_even_when_rule_disabled(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None: ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        config = PresenceConfig(check_overload_docstrings=False)
        all_findings, stats = check_presence(textwrap.dedent(source), "test.py", config)
        missing = [
            f
            for f in all_findings
            if f.symbol == "connect" and f.rule == "missing-docstring"
        ]
        assert len(missing) == 0
        assert stats.total == 2


class TestConfigToggle:
    """AC 5: check_overload_docstrings=False skips the rule."""

    def test_disabled_produces_no_findings(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None:
            """Connect with string."""
            ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        findings = _run(source, check_overload_docstrings=False)
        assert len(findings) == 0


class TestFindingFields:
    """Verify all 6 Finding fields are correct."""

    def test_all_finding_fields(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def fetch(url: str) -> bytes:
            """Fetch from URL."""
            ...

        def fetch(url):
            """Fetch data."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        f = findings[0]
        assert f.file == "test.py"
        assert f.line == 4
        assert f.symbol == "fetch"
        assert f.rule == "overload-has-docstring"
        assert "fetch" in f.message
        assert "document the implementation" in f.message
        assert f.category == "required"


class TestMultipleOverloads:
    """Multiple overloads with docstrings produce multiple findings."""

    def test_multiple_findings(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None:
            """Connect with string."""
            ...

        @overload
        def connect(address: tuple) -> None:
            """Connect with tuple."""
            ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 2


class TestMixedOverloads:
    """Mix of overloads with and without docstrings."""

    def test_correct_count(self) -> None:
        source = '''\
        from typing import overload

        @overload
        def connect(address: str) -> None:
            """Has docstring — flagged."""
            ...

        @overload
        def connect(address: tuple) -> None: ...

        def connect(address):
            """Connect to server."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1


class TestOverloadOnClassMethod:
    """AC boundary: @overload on a method inside a class."""

    def test_method_overload_with_docstring(self) -> None:
        source = '''\
        from typing import overload

        class Client:
            """A client."""

            @overload
            def send(self, data: str) -> None:
                """Send string data."""
                ...

            @overload
            def send(self, data: bytes) -> None: ...

            def send(self, data):
                """Send data to server."""
                ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        assert findings[0].symbol == "send"


class TestOverloadOnAsyncFunction:
    """@overload on async function with docstring produces a finding."""

    def test_async_overload_with_docstring(self) -> None:
        source = '''\
        from typing import overload

        @overload
        async def fetch(url: str) -> bytes:
            """Fetch from URL."""
            ...

        async def fetch(url):
            """Fetch data."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        assert findings[0].symbol == "fetch"


class TestNonTypingOverloadDecorator:
    """Decorator named 'overload' from non-typing module is still detected."""

    def test_custom_overload_decorator(self) -> None:
        source = '''\
        from mylib import overload

        @overload
        def process(data: str) -> str:
            """Process string."""
            ...
        '''
        findings = _run(source)
        assert len(findings) == 1
        assert findings[0].symbol == "process"
