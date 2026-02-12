"""Unit tests for griffe compatibility check module."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

from docvet.checks.griffe_compat import (
    _build_finding_from_record,
    _classify_warning,
    _resolve_file_set,
    _walk_objects,
    _WarningCollector,
    check_griffe_compat,
)


class TestWarningCollector:
    """Tests for _WarningCollector logging handler."""

    def test_collects_warning_records(self) -> None:
        """_WarningCollector collects WARNING-level records."""
        logger = logging.getLogger("griffe.test.collector")
        handler = _WarningCollector()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.warning("test warning message")
            assert len(handler.records) == 1
            assert handler.records[0].getMessage() == "test warning message"
        finally:
            logger.removeHandler(handler)

    def test_ignores_debug_records(self) -> None:
        """_WarningCollector ignores DEBUG-level records."""
        logger = logging.getLogger("griffe.test.collector.debug")
        handler = _WarningCollector()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.debug("debug message")
            assert len(handler.records) == 0
        finally:
            logger.removeHandler(handler)

    def test_ignores_info_records(self) -> None:
        """_WarningCollector ignores INFO-level records."""
        logger = logging.getLogger("griffe.test.collector.info")
        handler = _WarningCollector()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.info("info message")
            assert len(handler.records) == 0
        finally:
            logger.removeHandler(handler)

    def test_collects_multiple_warnings(self) -> None:
        """_WarningCollector accumulates multiple WARNING records."""
        logger = logging.getLogger("griffe.test.collector.multi")
        handler = _WarningCollector()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            logger.warning("warning 1")
            logger.warning("warning 2")
            logger.warning("warning 3")
            assert len(handler.records) == 3
        finally:
            logger.removeHandler(handler)

    def test_records_list_starts_empty(self) -> None:
        """_WarningCollector starts with an empty records list."""
        handler = _WarningCollector()
        assert handler.records == []

    def test_handler_level_is_warning(self) -> None:
        """_WarningCollector level is set to WARNING."""
        handler = _WarningCollector()
        assert handler.level == logging.WARNING


class TestClassifyWarning:
    """Tests for _classify_warning function."""

    def test_unknown_param_returns_required(self) -> None:
        """Unknown param pattern returns griffe-unknown-param, required."""
        rule, category = _classify_warning(
            "Parameter 'foo' does not appear in the function signature"
        )
        assert rule == "griffe-unknown-param"
        assert category == "required"

    def test_missing_type_returns_recommended(self) -> None:
        """Message with 'No type or annotation for' → griffe-missing-type, recommended."""
        rule, category = _classify_warning("No type or annotation for parameter 'bar'")
        assert rule == "griffe-missing-type"
        assert category == "recommended"

    def test_catchall_returns_format_warning(self) -> None:
        """Unrecognized message → griffe-format-warning, recommended."""
        rule, category = _classify_warning("Some future griffe warning format")
        assert rule == "griffe-format-warning"
        assert category == "recommended"

    def test_unknown_param_checked_before_missing_type(self) -> None:
        """Priority: unknown-param checked before missing-type (AC #11)."""
        # Message containing both patterns — unknown-param should win
        rule, category = _classify_warning(
            "No type or annotation for param that does not appear in the function signature"
        )
        assert rule == "griffe-unknown-param"
        assert category == "required"

    def test_empty_message_returns_catchall(self) -> None:
        """Empty message falls through to catch-all."""
        rule, category = _classify_warning("")
        assert rule == "griffe-format-warning"
        assert category == "recommended"

    def test_confusing_indentation_message(self) -> None:
        """Confusing indentation message → griffe-format-warning."""
        rule, category = _classify_warning(
            "Possible confusing indentation in docstring"
        )
        assert rule == "griffe-format-warning"
        assert category == "recommended"


def _make_griffe_obj(
    *,
    name: str = "my_func",
    kind_value: str = "function",
    filepath: Path = Path("/src/pkg/mod.py"),
    is_alias: bool = False,
    has_docstring: bool = True,
    members: dict | None = None,
) -> MagicMock:
    """Create a mock griffe object for testing."""
    obj = MagicMock()
    obj.name = name
    obj.kind.value = kind_value
    obj.filepath = filepath
    obj.is_alias = is_alias
    obj.docstring = MagicMock() if has_docstring else None
    obj.members = members if members is not None else {}
    return obj


def _make_log_record(message: str) -> MagicMock:
    """Create a mock log record with getMessage() returning the given message."""
    record = MagicMock(spec=logging.LogRecord)
    record.getMessage.return_value = message
    return record


class TestResolveFileSet:
    """Tests for _resolve_file_set function."""

    def test_resolves_paths_to_absolute(self, tmp_path: Path) -> None:
        """_resolve_file_set resolves relative paths to absolute."""
        f = tmp_path / "mod.py"
        f.touch()
        result = _resolve_file_set([f])
        assert len(result) == 1
        resolved = next(iter(result))
        assert resolved.is_absolute()

    def test_empty_input_returns_empty_set(self) -> None:
        """_resolve_file_set with empty input returns empty set."""
        result = _resolve_file_set([])
        assert result == set()

    def test_multiple_files(self, tmp_path: Path) -> None:
        """_resolve_file_set handles multiple files."""
        f1 = tmp_path / "a.py"
        f2 = tmp_path / "b.py"
        f1.touch()
        f2.touch()
        result = _resolve_file_set([f1, f2])
        assert len(result) == 2


class TestWalkObjects:
    """Tests for _walk_objects generator."""

    def test_yields_object_with_matching_file(self) -> None:
        """_walk_objects yields objects whose filepath is in file_set."""
        fp = Path("/src/pkg/mod.py")
        obj = _make_griffe_obj(filepath=fp)
        result = list(_walk_objects(obj, {fp}))
        assert len(result) == 1
        assert result[0] is obj

    def test_skips_alias_objects(self) -> None:
        """_walk_objects skips alias objects without accessing attributes."""
        fp = Path("/src/pkg/mod.py")
        obj = _make_griffe_obj(filepath=fp, is_alias=True)
        result = list(_walk_objects(obj, {fp}))
        assert len(result) == 0

    def test_skips_objects_without_docstring(self) -> None:
        """_walk_objects skips objects with no docstring."""
        fp = Path("/src/pkg/mod.py")
        obj = _make_griffe_obj(filepath=fp, has_docstring=False)
        result = list(_walk_objects(obj, {fp}))
        assert len(result) == 0

    def test_skips_objects_outside_file_set(self) -> None:
        """_walk_objects skips objects whose filepath is not in file_set."""
        obj = _make_griffe_obj(filepath=Path("/src/pkg/other.py"))
        result = list(_walk_objects(obj, {Path("/src/pkg/mod.py")}))
        assert len(result) == 0

    def test_walks_nested_members(self) -> None:
        """_walk_objects recursively walks nested members."""
        fp = Path("/src/pkg/mod.py")
        child = _make_griffe_obj(name="child_func", filepath=fp)
        parent = _make_griffe_obj(
            name="MyClass",
            kind_value="class",
            filepath=fp,
            members={"child_func": child},
        )
        result = list(_walk_objects(parent, {fp}))
        assert len(result) == 2
        names = [r.name for r in result]
        assert "MyClass" in names
        assert "child_func" in names

    def test_skips_alias_child_but_continues_siblings(self) -> None:
        """_walk_objects skips alias child but processes siblings."""
        fp = Path("/src/pkg/mod.py")
        alias_child = _make_griffe_obj(name="alias_func", filepath=fp, is_alias=True)
        good_child = _make_griffe_obj(name="good_func", filepath=fp)
        parent = _make_griffe_obj(
            name="pkg",
            kind_value="module",
            filepath=fp,
            members={"alias_func": alias_child, "good_func": good_child},
        )
        result = list(_walk_objects(parent, {fp}))
        names = [r.name for r in result]
        assert "alias_func" not in names
        assert "good_func" in names
        assert "pkg" in names


class TestBuildFindingFromRecord:
    """Tests for _build_finding_from_record function."""

    def test_matching_format_returns_finding(self) -> None:
        """_build_finding_from_record parses standard griffe warning format."""
        record = _make_log_record("mod.py:10: No type or annotation for parameter 'x'")
        obj = _make_griffe_obj(
            name="my_func",
            kind_value="function",
            filepath=Path("/src/pkg/mod.py"),
        )
        finding = _build_finding_from_record(record, obj)
        assert finding is not None
        assert finding.file == "/src/pkg/mod.py"
        assert finding.line == 10
        assert finding.symbol == "my_func"
        assert finding.rule == "griffe-missing-type"
        assert finding.category == "recommended"
        assert "Function" in finding.message
        assert "'my_func'" in finding.message
        assert "No type or annotation for parameter 'x'" in finding.message

    def test_non_matching_format_returns_none(self) -> None:
        """_build_finding_from_record returns None for unrecognized format."""
        record = _make_log_record("some unstructured warning")
        obj = _make_griffe_obj()
        finding = _build_finding_from_record(record, obj)
        assert finding is None

    def test_unknown_param_finding_fields(self) -> None:
        """_build_finding_from_record: unknown-param produces correct Finding fields."""
        record = _make_log_record(
            "mod.py:5: Parameter 'ghost' does not appear in the function signature"
        )
        obj = _make_griffe_obj(
            name="process",
            kind_value="function",
            filepath=Path("/src/pkg/mod.py"),
        )
        finding = _build_finding_from_record(record, obj)
        assert finding is not None
        assert finding.file == "/src/pkg/mod.py"
        assert finding.line == 5
        assert finding.symbol == "process"
        assert finding.rule == "griffe-unknown-param"
        assert finding.category == "required"
        assert "Function" in finding.message
        assert "'process'" in finding.message

    def test_format_warning_finding_fields(self) -> None:
        """_build_finding_from_record: format-warning produces correct Finding fields."""
        record = _make_log_record("mod.py:20: Possible confusing indentation")
        obj = _make_griffe_obj(
            name="MyClass",
            kind_value="class",
            filepath=Path("/src/pkg/mod.py"),
        )
        finding = _build_finding_from_record(record, obj)
        assert finding is not None
        assert finding.file == "/src/pkg/mod.py"
        assert finding.line == 20
        assert finding.symbol == "MyClass"
        assert finding.rule == "griffe-format-warning"
        assert finding.category == "recommended"
        assert "Class" in finding.message
        assert "'MyClass'" in finding.message

    def test_message_format_matches_convention(self) -> None:
        """Finding message follows format: "{Kind} '{name}' {message_text}" (AC #22)."""
        record = _make_log_record("mod.py:1: No type or annotation for param 'x'")
        obj = _make_griffe_obj(name="do_thing", kind_value="function")
        finding = _build_finding_from_record(record, obj)
        assert finding is not None
        assert (
            finding.message == "Function 'do_thing' No type or annotation for param 'x'"
        )


def _setup_package_dir(tmp_path: Path, *pkg_names: str) -> Path:
    """Create src_root with package directories containing __init__.py."""
    src_root = tmp_path / "src"
    src_root.mkdir()
    for name in pkg_names:
        pkg_dir = src_root / name
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").touch()
        (pkg_dir / "mod.py").write_text("# module")
    return src_root


class TestCheckGriffeCompat:
    """Tests for check_griffe_compat orchestrator."""

    def test_griffe_not_installed_returns_empty(self, tmp_path: Path, mocker) -> None:
        """check_griffe_compat returns [] when griffe is not installed (AC #6)."""
        mocker.patch("docvet.checks.griffe_compat.griffe", None)
        result = check_griffe_compat(tmp_path, [tmp_path / "mod.py"])
        assert result == []

    def test_empty_files_returns_empty(self, tmp_path: Path) -> None:
        """check_griffe_compat returns [] with empty files list (AC #7)."""
        result = check_griffe_compat(tmp_path, [])
        assert result == []

    def test_happy_path_missing_type(self, tmp_path: Path, mocker) -> None:
        """check_griffe_compat produces griffe-missing-type finding (AC #1)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        mod_path = src_root / "mypkg" / "mod.py"

        mock_obj = _make_griffe_obj(
            name="bad_func",
            kind_value="function",
            filepath=mod_path.resolve(),
        )
        mock_obj.members = {}

        mock_package = _make_griffe_obj(
            name="mypkg",
            kind_value="module",
            filepath=mod_path.resolve(),
            members={"bad_func": mock_obj},
        )
        # Package itself has no docstring to check
        mock_package.docstring = None

        # Mock griffe.load to return our mock package
        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.load.return_value = mock_package
        mock_griffe.LoadingError = Exception

        # Simulate griffe emitting a warning when docstring.parsed is accessed
        def emit_warning():
            logger = logging.getLogger("griffe")
            logger.warning("mod.py:10: No type or annotation for parameter 'x'")
            return []

        mock_obj.docstring.parsed = property(lambda self: emit_warning())
        # Since property on mock doesn't work the same, use side_effect approach
        type(mock_obj.docstring).parsed = PropertyMock(side_effect=emit_warning)

        result = check_griffe_compat(src_root, [mod_path])
        assert len(result) == 1
        assert result[0].rule == "griffe-missing-type"
        assert result[0].symbol == "bad_func"
        assert result[0].line == 10
        assert result[0].category == "recommended"
        assert result[0].file == str(mod_path.resolve())
        assert "Function" in result[0].message

    def test_happy_path_unknown_param(self, tmp_path: Path, mocker) -> None:
        """check_griffe_compat produces griffe-unknown-param finding (AC #2)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        mod_path = src_root / "mypkg" / "mod.py"

        mock_obj = _make_griffe_obj(
            name="phantom_func",
            kind_value="function",
            filepath=mod_path.resolve(),
        )
        mock_obj.members = {}

        mock_package = _make_griffe_obj(
            name="mypkg",
            kind_value="module",
            filepath=mod_path.resolve(),
            members={"phantom_func": mock_obj},
        )
        mock_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.load.return_value = mock_package
        mock_griffe.LoadingError = Exception

        def emit_warning():
            logger = logging.getLogger("griffe")
            logger.warning(
                "mod.py:5: Parameter 'ghost' does not appear in the function signature"
            )
            return []

        type(mock_obj.docstring).parsed = PropertyMock(side_effect=emit_warning)

        result = check_griffe_compat(src_root, [mod_path])
        assert len(result) == 1
        assert result[0].rule == "griffe-unknown-param"
        assert result[0].category == "required"
        assert result[0].symbol == "phantom_func"
        assert result[0].file == str(mod_path.resolve())
        assert result[0].line == 5
        assert "Function" in result[0].message
        assert "'phantom_func'" in result[0].message

    def test_happy_path_format_warning(self, tmp_path: Path, mocker) -> None:
        """check_griffe_compat produces griffe-format-warning finding (AC #3)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        mod_path = src_root / "mypkg" / "mod.py"

        mock_obj = _make_griffe_obj(
            name="messy_func",
            kind_value="function",
            filepath=mod_path.resolve(),
        )
        mock_obj.members = {}

        mock_package = _make_griffe_obj(
            name="mypkg",
            kind_value="module",
            filepath=mod_path.resolve(),
            members={"messy_func": mock_obj},
        )
        mock_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.load.return_value = mock_package
        mock_griffe.LoadingError = Exception

        def emit_warning():
            logger = logging.getLogger("griffe")
            logger.warning("mod.py:15: Possible confusing indentation")
            return []

        type(mock_obj.docstring).parsed = PropertyMock(side_effect=emit_warning)

        result = check_griffe_compat(src_root, [mod_path])
        assert len(result) == 1
        assert result[0].rule == "griffe-format-warning"
        assert result[0].category == "recommended"
        assert result[0].symbol == "messy_func"
        assert result[0].file == str(mod_path.resolve())
        assert result[0].line == 15
        assert "Function" in result[0].message
        assert "'messy_func'" in result[0].message

    def test_multiple_findings_per_symbol_not_deduplicated(
        self, tmp_path: Path, mocker
    ) -> None:
        """3 untyped params → 3 separate findings, not deduplicated (AC #4)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        mod_path = src_root / "mypkg" / "mod.py"

        mock_obj = _make_griffe_obj(
            name="multi_param",
            kind_value="function",
            filepath=mod_path.resolve(),
        )
        mock_obj.members = {}

        mock_package = _make_griffe_obj(
            name="mypkg",
            kind_value="module",
            filepath=mod_path.resolve(),
            members={"multi_param": mock_obj},
        )
        mock_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.load.return_value = mock_package
        mock_griffe.LoadingError = Exception

        def emit_warnings():
            logger = logging.getLogger("griffe")
            logger.warning("mod.py:10: No type or annotation for parameter 'a'")
            logger.warning("mod.py:11: No type or annotation for parameter 'b'")
            logger.warning("mod.py:12: No type or annotation for parameter 'c'")
            return []

        type(mock_obj.docstring).parsed = PropertyMock(side_effect=emit_warnings)

        result = check_griffe_compat(src_root, [mod_path])
        assert len(result) == 3
        assert all(f.rule == "griffe-missing-type" for f in result)
        assert all(f.symbol == "multi_param" for f in result)

    def test_well_documented_code_returns_empty(self, tmp_path: Path, mocker) -> None:
        """Well-documented code produces zero findings (AC #5)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        mod_path = src_root / "mypkg" / "mod.py"

        mock_obj = _make_griffe_obj(
            name="good_func",
            kind_value="function",
            filepath=mod_path.resolve(),
        )
        mock_obj.members = {}

        mock_package = _make_griffe_obj(
            name="mypkg",
            kind_value="module",
            filepath=mod_path.resolve(),
            members={"good_func": mock_obj},
        )
        mock_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.load.return_value = mock_package
        mock_griffe.LoadingError = Exception

        # No warnings emitted for well-documented code
        type(mock_obj.docstring).parsed = PropertyMock(return_value=[])

        result = check_griffe_compat(src_root, [mod_path])
        assert result == []

    def test_load_failure_skips_package_and_continues(
        self, tmp_path: Path, mocker
    ) -> None:
        """Load failure skips package, continues to next (AC #8)."""
        src_root = _setup_package_dir(tmp_path, "bad_pkg", "good_pkg")
        good_mod = src_root / "good_pkg" / "mod.py"

        mock_good_obj = _make_griffe_obj(
            name="good_func",
            kind_value="function",
            filepath=good_mod.resolve(),
        )
        mock_good_obj.members = {}

        mock_good_package = _make_griffe_obj(
            name="good_pkg",
            kind_value="module",
            filepath=good_mod.resolve(),
            members={"good_func": mock_good_obj},
        )
        mock_good_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.LoadingError = type("LoadingError", (Exception,), {})

        def load_side_effect(name, **kwargs):
            if name == "bad_pkg":
                raise mock_griffe.LoadingError("failed")
            return mock_good_package

        mock_griffe.load.side_effect = load_side_effect

        def emit_warning():
            logger = logging.getLogger("griffe")
            logger.warning("mod.py:1: No type or annotation for parameter 'x'")
            return []

        type(mock_good_obj.docstring).parsed = PropertyMock(side_effect=emit_warning)

        result = check_griffe_compat(src_root, [good_mod])
        assert len(result) == 1
        assert result[0].symbol == "good_func"

    def test_multiple_packages_sorted_order(self, tmp_path: Path, mocker) -> None:
        """Multiple packages loaded in sorted order (AC #9)."""
        src_root = _setup_package_dir(tmp_path, "z_pkg", "a_pkg")
        z_mod = src_root / "z_pkg" / "mod.py"
        a_mod = src_root / "a_pkg" / "mod.py"

        # Track load order
        load_order: list[str] = []

        mock_z_obj = _make_griffe_obj(
            name="z_func", kind_value="function", filepath=z_mod.resolve()
        )
        mock_z_obj.members = {}
        mock_z_package = _make_griffe_obj(
            name="z_pkg",
            kind_value="module",
            filepath=z_mod.resolve(),
            members={"z_func": mock_z_obj},
        )
        mock_z_package.docstring = None

        mock_a_obj = _make_griffe_obj(
            name="a_func", kind_value="function", filepath=a_mod.resolve()
        )
        mock_a_obj.members = {}
        mock_a_package = _make_griffe_obj(
            name="a_pkg",
            kind_value="module",
            filepath=a_mod.resolve(),
            members={"a_func": mock_a_obj},
        )
        mock_a_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.LoadingError = Exception

        def load_side_effect(name, **kwargs):
            load_order.append(name)
            if name == "a_pkg":
                return mock_a_package
            return mock_z_package

        mock_griffe.load.side_effect = load_side_effect

        # No warnings for either
        type(mock_z_obj.docstring).parsed = PropertyMock(return_value=[])
        type(mock_a_obj.docstring).parsed = PropertyMock(return_value=[])

        check_griffe_compat(src_root, [a_mod, z_mod])
        assert load_order == ["a_pkg", "z_pkg"]

    def test_handler_removed_in_finally(self, tmp_path: Path, mocker) -> None:
        """Handler removed from griffe logger even on exception (AC #15)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        mod_path = src_root / "mypkg" / "mod.py"

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        # Use a narrow exception so RuntimeError is NOT caught
        mock_griffe.LoadingError = type("LoadingError", (Exception,), {})
        mock_griffe.load.side_effect = RuntimeError("unexpected")

        griffe_logger = logging.getLogger("griffe")
        handlers_before = len(griffe_logger.handlers)

        # RuntimeError is not in the caught exception list, so it propagates
        with pytest.raises(RuntimeError, match="unexpected"):
            check_griffe_compat(src_root, [mod_path])

        # Handler should have been removed by try/finally cleanup
        handlers_after = len(griffe_logger.handlers)
        assert handlers_after == handlers_before

    def test_files_outside_package_produce_zero_findings(
        self, tmp_path: Path, mocker
    ) -> None:
        """Files outside loaded package produce zero findings (AC #16)."""
        src_root = _setup_package_dir(tmp_path, "mypkg")
        outside_file = tmp_path / "outside.py"
        outside_file.touch()

        mock_obj = _make_griffe_obj(
            name="func",
            kind_value="function",
            filepath=(src_root / "mypkg" / "mod.py").resolve(),
        )
        mock_obj.members = {}
        mock_package = _make_griffe_obj(
            name="mypkg",
            kind_value="module",
            filepath=(src_root / "mypkg" / "mod.py").resolve(),
            members={"func": mock_obj},
        )
        mock_package.docstring = None

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.load.return_value = mock_package
        mock_griffe.LoadingError = Exception

        # Warning would fire if the object were walked, but file is outside
        def emit_warning():
            logger = logging.getLogger("griffe")
            logger.warning("mod.py:1: No type or annotation for parameter 'x'")
            return []

        type(mock_obj.docstring).parsed = PropertyMock(side_effect=emit_warning)

        # Only pass the outside file — no files match the package objects
        result = check_griffe_compat(src_root, [outside_file])
        assert result == []

    def test_load_failure_module_not_found(self, tmp_path: Path, mocker) -> None:
        """ModuleNotFoundError during load skips package (AC #8)."""
        src_root = _setup_package_dir(tmp_path, "broken_pkg")
        mod_path = src_root / "broken_pkg" / "mod.py"

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.LoadingError = Exception
        mock_griffe.load.side_effect = ModuleNotFoundError("no module")

        result = check_griffe_compat(src_root, [mod_path])
        assert result == []

    def test_load_failure_syntax_error(self, tmp_path: Path, mocker) -> None:
        """SyntaxError during load skips package (AC #8)."""
        src_root = _setup_package_dir(tmp_path, "syntax_pkg")
        mod_path = src_root / "syntax_pkg" / "mod.py"

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.LoadingError = Exception
        mock_griffe.load.side_effect = SyntaxError("bad syntax")

        result = check_griffe_compat(src_root, [mod_path])
        assert result == []

    def test_load_failure_os_error(self, tmp_path: Path, mocker) -> None:
        """OSError during load skips package (AC #8)."""
        src_root = _setup_package_dir(tmp_path, "os_pkg")
        mod_path = src_root / "os_pkg" / "mod.py"

        mock_griffe = mocker.patch("docvet.checks.griffe_compat.griffe")
        mock_griffe.LoadingError = Exception
        mock_griffe.load.side_effect = OSError("disk error")

        result = check_griffe_compat(src_root, [mod_path])
        assert result == []
