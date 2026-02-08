from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from docvet.ast_utils import (
    get_body_range,
    get_docstring_range,
    get_documented_symbols,
    get_signature_range,
    map_lines_to_symbols,
)

pytestmark = pytest.mark.unit

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# TestGetDocumentedSymbols
# ---------------------------------------------------------------------------


class TestGetDocumentedSymbols:
    def test_simple_function_returns_function_symbol(self, parse_source):
        tree = parse_source(
            dedent("""\
            def greet(name):
                \"\"\"Say hello.\"\"\"
                return f"hi {name}"
        """)
        )
        symbols = get_documented_symbols(tree)
        funcs = [s for s in symbols if s.kind == "function"]
        assert len(funcs) == 1
        assert funcs[0].name == "greet"

    def test_function_no_docstring_has_none(self, parse_source):
        tree = parse_source(
            dedent("""\
            def noop():
                pass
        """)
        )
        symbols = get_documented_symbols(tree)
        funcs = [s for s in symbols if s.kind == "function"]
        assert funcs[0].docstring is None

    def test_class_with_methods_has_method_kind(self, parse_source):
        tree = parse_source(
            dedent("""\
            class Foo:
                \"\"\"A class.\"\"\"
                def bar(self):
                    \"\"\"A method.\"\"\"
                    pass
        """)
        )
        symbols = get_documented_symbols(tree)
        methods = [s for s in symbols if s.kind == "method"]
        assert len(methods) == 1
        assert methods[0].name == "bar"

    def test_method_parent_is_class_name(self, parse_source):
        tree = parse_source(
            dedent("""\
            class MyClass:
                def method(self):
                    pass
        """)
        )
        symbols = get_documented_symbols(tree)
        method = next(s for s in symbols if s.kind == "method")
        assert method.parent == "MyClass"

    def test_nested_function_parent_is_none(self, parse_source):
        tree = parse_source(
            dedent("""\
            def outer():
                def inner():
                    pass
        """)
        )
        symbols = get_documented_symbols(tree)
        inner = next(s for s in symbols if s.name == "inner")
        assert inner.parent is None

    def test_nested_class_method_parent_is_inner_class(self, parse_source):
        tree = parse_source(
            dedent("""\
            class Outer:
                class Inner:
                    def method(self):
                        pass
        """)
        )
        symbols = get_documented_symbols(tree)
        method = next(s for s in symbols if s.name == "method")
        assert method.parent == "Inner"

    def test_decorated_classmethod_is_method(self, parse_source):
        tree = parse_source(
            dedent("""\
            class Foo:
                @classmethod
                def create(cls):
                    pass
        """)
        )
        symbols = get_documented_symbols(tree)
        method = next(s for s in symbols if s.name == "create")
        assert method.kind == "method"

    def test_async_function_is_function(self, parse_source):
        tree = parse_source(
            dedent("""\
            async def fetch():
                \"\"\"Fetch data.\"\"\"
                pass
        """)
        )
        symbols = get_documented_symbols(tree)
        funcs = [s for s in symbols if s.kind == "function"]
        assert len(funcs) == 1
        assert funcs[0].name == "fetch"

    def test_module_docstring_extracted(self, parse_source):
        tree = parse_source(
            dedent("""\
            \"\"\"Module doc.\"\"\"
            def f():
                pass
        """)
        )
        symbols = get_documented_symbols(tree)
        module = next(s for s in symbols if s.kind == "module")
        assert module.docstring == "Module doc."

    def test_property_is_method(self, parse_source):
        tree = parse_source(
            dedent("""\
            class C:
                @property
                def value(self):
                    \"\"\"The value.\"\"\"
                    return 1
        """)
        )
        symbols = get_documented_symbols(tree)
        prop = next(s for s in symbols if s.name == "value")
        assert prop.kind == "method"

    def test_empty_module_returns_single_module_symbol(self, parse_source):
        tree = parse_source("")
        symbols = get_documented_symbols(tree)
        assert len(symbols) == 1
        mod = symbols[0]
        assert mod.name == "<module>"
        assert mod.kind == "module"
        assert mod.line == 1
        assert mod.definition_start == 1
        assert mod.end_line == 1
        assert mod.body_range == (1, 1)
        assert mod.signature_range is None
        assert mod.parent is None

    def test_fixture_file_comprehensive(self, parse_source):
        # NOTE: Line numbers and symbol count are coupled to the exact
        # formatting of tests/fixtures/nested_symbols.py. Update these
        # assertions if the fixture file changes.
        source = (FIXTURES_DIR / "nested_symbols.py").read_text()
        tree = parse_source(source)
        symbols = get_documented_symbols(tree)

        names = [(s.name, s.kind, s.parent) for s in symbols]

        # Module + top_level_function + OuterClass + __init__ +
        # regular_method + computed + static_helper + from_string +
        # InnerClass + inner_method + async_function +
        # decorated_multiline + no_docstring_function = 13
        assert len(symbols) == 13

        assert ("<module>", "module", None) in names
        assert ("top_level_function", "function", None) in names
        assert ("OuterClass", "class", None) in names
        assert ("__init__", "method", "OuterClass") in names
        assert ("regular_method", "method", "OuterClass") in names
        assert ("computed", "method", "OuterClass") in names
        assert ("static_helper", "method", "OuterClass") in names
        assert ("from_string", "method", "OuterClass") in names
        assert ("InnerClass", "class", "OuterClass") in names
        assert ("inner_method", "method", "InnerClass") in names
        assert ("async_function", "function", None) in names
        assert ("decorated_multiline", "function", None) in names
        assert ("no_docstring_function", "function", None) in names

        # Verify specific line numbers for key symbols.
        top_fn = next(s for s in symbols if s.name == "top_level_function")
        assert top_fn.line == 6

        outer = next(s for s in symbols if s.name == "OuterClass")
        assert outer.line == 18

        async_fn = next(s for s in symbols if s.name == "async_function")
        assert async_fn.line == 62

        no_doc = next(s for s in symbols if s.name == "no_docstring_function")
        assert no_doc.docstring is None


# ---------------------------------------------------------------------------
# TestGetDocstringRange
# ---------------------------------------------------------------------------


class TestGetDocstringRange:
    def test_non_scope_node_returns_none(self, parse_source):
        tree = parse_source("x = 1\n")
        node = tree.body[0]  # ast.Assign — not a scope node
        assert get_docstring_range(node) is None

    def test_module_with_docstring(self, parse_source):
        tree = parse_source(
            dedent("""\
            \"\"\"Module doc.\"\"\"
            x = 1
        """)
        )
        assert get_docstring_range(tree) == (1, 1)

    def test_single_line_docstring_range(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                \"\"\"One liner.\"\"\"
                pass
        """)
        )
        node = tree.body[0]
        result = get_docstring_range(node)
        assert result == (2, 2)

    def test_multi_line_docstring_range(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                \"\"\"First line.

                More detail.
                \"\"\"
                pass
        """)
        )
        node = tree.body[0]
        result = get_docstring_range(node)
        assert result == (2, 5)

    def test_no_docstring_returns_none(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                pass
        """)
        )
        node = tree.body[0]
        assert get_docstring_range(node) is None


# ---------------------------------------------------------------------------
# TestGetBodyRange
# ---------------------------------------------------------------------------


class TestGetBodyRange:
    def test_non_scope_node_returns_degenerate(self, parse_source):
        tree = parse_source("x = 1\n")
        node = tree.body[0]  # ast.Assign — not a scope node
        result = get_body_range(node)
        assert result[0] == result[1]

    def test_module_body_excludes_docstring(self, parse_source):
        tree = parse_source(
            dedent("""\
            \"\"\"Module doc.\"\"\"
            x = 1
        """)
        )
        result = get_body_range(tree)
        assert result == (2, 2)

    def test_body_excludes_docstring(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                \"\"\"Doc.\"\"\"
                return 1
        """)
        )
        node = tree.body[0]
        result = get_body_range(node)
        assert result == (3, 3)

    def test_body_without_docstring_starts_at_first_stmt(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                return 1
        """)
        )
        node = tree.body[0]
        result = get_body_range(node)
        assert result == (2, 2)

    def test_single_line_function_body(self, parse_source):
        tree = parse_source("def f(): pass\n")
        node = tree.body[0]
        result = get_body_range(node)
        assert result == (1, 1)

    def test_docstring_only_body_clamped(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                \"\"\"Only a docstring.\"\"\"
        """)
        )
        node = tree.body[0]
        result = get_body_range(node)
        assert result == (2, 2)


# ---------------------------------------------------------------------------
# TestGetSignatureRange
# ---------------------------------------------------------------------------


class TestGetSignatureRange:
    def test_single_line_signature(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f(x):
                pass
        """)
        )
        node = tree.body[0]
        result = get_signature_range(node)
        assert result == (1, 1)

    def test_multi_line_signature(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f(
                a,
                b,
            ):
                pass
        """)
        )
        node = tree.body[0]
        result = get_signature_range(node)
        assert result == (1, 4)

    def test_excludes_decorators(self, parse_source):
        tree = parse_source(
            dedent("""\
            @decorator
            def f():
                pass
        """)
        )
        node = tree.body[0]
        result = get_signature_range(node)
        assert result == (2, 2)

    def test_inline_pass_single_line(self, parse_source):
        tree = parse_source("def f(): pass\n")
        node = tree.body[0]
        result = get_signature_range(node)
        assert result == (1, 1)


# ---------------------------------------------------------------------------
# TestMapLinesToSymbols
# ---------------------------------------------------------------------------


class TestMapLinesToSymbols:
    def test_top_level_function_line(self, parse_source):
        tree = parse_source(
            dedent("""\
            def f():
                pass
        """)
        )
        line_map = map_lines_to_symbols(tree)
        assert line_map[1].name == "f"

    def test_method_line_returns_method_not_class(self, parse_source):
        tree = parse_source(
            dedent("""\
            class C:
                def m(self):
                    pass
        """)
        )
        line_map = map_lines_to_symbols(tree)
        assert line_map[2].name == "m"
        assert line_map[2].kind == "method"

    def test_nested_function_returns_inner(self, parse_source):
        tree = parse_source(
            dedent("""\
            def outer():
                def inner():
                    pass
        """)
        )
        line_map = map_lines_to_symbols(tree)
        assert line_map[2].name == "inner"

    def test_decorator_line_maps_to_function(self, parse_source):
        tree = parse_source(
            dedent("""\
            @decorator
            def f():
                pass
        """)
        )
        line_map = map_lines_to_symbols(tree)
        assert line_map[1].name == "f"

    def test_module_level_line_returns_module(self, parse_source):
        tree = parse_source(
            dedent("""\
            import os

            x = 1
        """)
        )
        line_map = map_lines_to_symbols(tree)
        assert line_map[1].kind == "module"
        assert line_map[3].kind == "module"
