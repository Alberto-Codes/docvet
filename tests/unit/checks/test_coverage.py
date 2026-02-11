"""Tests for the coverage check module.

Tests check_coverage detection of missing __init__.py files in parent
directories of Python files, ensuring mkdocstrings discoverability.
"""

from __future__ import annotations

from pathlib import Path

from docvet.checks import Finding
from docvet.checks.coverage import check_coverage


class TestCheckCoverageBasicDetection:
    """Tests for basic missing __init__.py detection (AC #1)."""

    def test_missing_init_when_subdir_lacks_init_returns_finding(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg" / "sub"
        pkg.mkdir(parents=True)
        (src / "pkg" / "__init__.py").touch()
        # Intentionally omit pkg/sub/__init__.py
        module = pkg / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert len(findings) == 1
        assert findings[0].file == str(module)
        assert findings[0].line == 1
        assert findings[0].symbol == "<module>"
        assert findings[0].rule == "missing-init"
        assert findings[0].category == "required"
        assert "pkg/sub" in findings[0].message
        assert "1 file affected" in findings[0].message

    def test_missing_init_when_message_uses_relative_path_from_src_root(
        self, tmp_path: Path
    ) -> None:
        """AC #10: message uses dir path relative to src_root, not just leaf."""
        src = tmp_path / "src"
        deep = src / "pkg" / "sub" / "deep"
        deep.mkdir(parents=True)
        (src / "pkg" / "__init__.py").touch()
        (src / "pkg" / "sub" / "__init__.py").touch()
        # Missing: pkg/sub/deep/__init__.py
        module = deep / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert len(findings) == 1
        assert "pkg/sub/deep" in findings[0].message


class TestCheckCoverageZeroFindings:
    """Tests for zero findings when all __init__.py present (AC #2)."""

    def test_missing_init_when_all_inits_present_returns_empty(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg" / "sub"
        pkg.mkdir(parents=True)
        (src / "pkg" / "__init__.py").touch()
        (src / "pkg" / "sub" / "__init__.py").touch()
        module = pkg / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert findings == []


class TestCheckCoverageTopLevelModuleSkip:
    """Tests for top-level module skip (AC #3)."""

    def test_missing_init_when_file_directly_under_src_root_returns_empty(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        src.mkdir()
        module = src / "utils.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert findings == []


class TestCheckCoverageDeduplication:
    """Tests for deduplication: one finding per directory (AC #4)."""

    def test_missing_init_when_multiple_files_same_dir_returns_one_finding(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        # Missing: pkg/__init__.py
        a = pkg / "a.py"
        b = pkg / "b.py"
        c = pkg / "c.py"
        a.touch()
        b.touch()
        c.touch()

        findings = check_coverage(src, [c, a, b])

        assert len(findings) == 1
        assert findings[0].file == str(a)  # lexicographically first
        assert "3 files affected" in findings[0].message

    def test_missing_init_when_two_files_same_dir_uses_plural(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        a = pkg / "a.py"
        b = pkg / "b.py"
        a.touch()
        b.touch()

        findings = check_coverage(src, [b, a])

        assert len(findings) == 1
        assert "2 files affected" in findings[0].message

    def test_missing_init_when_one_file_uses_singular(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        module = pkg / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert len(findings) == 1
        assert "1 file affected" in findings[0].message


class TestCheckCoverageIntermediateGap:
    """Tests for intermediate directory gap detection (AC #5)."""

    def test_missing_init_when_intermediate_dir_lacks_init_returns_finding(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        deep = src / "pkg" / "sub" / "deep"
        deep.mkdir(parents=True)
        (src / "pkg" / "__init__.py").touch()
        # Missing: pkg/sub/__init__.py
        (src / "pkg" / "sub" / "deep" / "__init__.py").touch()
        module = deep / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert len(findings) == 1
        assert "pkg/sub" in findings[0].message

    def test_missing_init_when_deeply_nested_multiple_gaps_returns_all(
        self, tmp_path: Path
    ) -> None:
        """Deeply nested hierarchy with 3+ levels and multiple gaps."""
        src = tmp_path / "src"
        deep = src / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (src / "a" / "__init__.py").touch()
        # Missing: a/b/__init__.py
        (src / "a" / "b" / "c" / "__init__.py").touch()
        # Missing: a/b/c/d/__init__.py
        module = deep / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert len(findings) == 2
        dirs = [f.message for f in findings]
        assert any("a/b" in m and "a/b/c" not in m for m in dirs)
        assert any("a/b/c/d" in m for m in dirs)


class TestCheckCoverageEmptyInit:
    """Tests for empty __init__.py acceptance (AC #6)."""

    def test_missing_init_when_empty_init_exists_returns_empty(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        init = pkg / "__init__.py"
        init.touch()  # zero bytes
        assert init.stat().st_size == 0
        module = pkg / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert findings == []


class TestCheckCoverageOutsideSrcRoot:
    """Tests for files outside src_root skip (AC #7)."""

    def test_missing_init_when_file_outside_src_root_returns_empty(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        src.mkdir()
        tests = tmp_path / "tests"
        tests.mkdir()
        test_file = tests / "test_foo.py"
        test_file.touch()

        findings = check_coverage(src, [test_file])

        assert findings == []

    def test_missing_init_when_mixed_inside_outside_only_checks_inside(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        # Missing: pkg/__init__.py
        inside = pkg / "module.py"
        inside.touch()
        tests = tmp_path / "tests"
        tests.mkdir()
        outside = tests / "test_foo.py"
        outside.touch()

        findings = check_coverage(src, [inside, outside])

        assert len(findings) == 1
        assert findings[0].file == str(inside)


class TestCheckCoverageEmptyInput:
    """Tests for empty files list (AC #8)."""

    def test_missing_init_when_empty_files_list_returns_empty(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        src.mkdir()

        findings = check_coverage(src, [])

        assert findings == []


class TestCheckCoverageDeterministicSorting:
    """Tests for deterministic sorting by directory path (AC #9)."""

    def test_missing_init_when_multiple_dirs_returns_sorted_by_dir_path(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        # Create three missing directories in non-sorted order
        for name in ["zebra", "alpha", "middle"]:
            d = src / name
            d.mkdir(parents=True)
            (d / "module.py").touch()

        files = [
            src / "zebra" / "module.py",
            src / "alpha" / "module.py",
            src / "middle" / "module.py",
        ]

        findings = check_coverage(src, files)

        assert len(findings) == 3
        assert "alpha" in findings[0].message
        assert "middle" in findings[1].message
        assert "zebra" in findings[2].message

    def test_missing_init_when_nested_dirs_sorted_by_full_relative_path(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        # a/z and a/b — both missing
        for sub in ["z", "b"]:
            d = src / "a" / sub
            d.mkdir(parents=True)
            (d / "module.py").touch()
        (src / "a" / "__init__.py").touch()

        files = [
            src / "a" / "z" / "module.py",
            src / "a" / "b" / "module.py",
        ]

        findings = check_coverage(src, files)

        assert len(findings) == 2
        assert "a/b" in findings[0].message
        assert "a/z" in findings[1].message


class TestCheckCoverageFindingFields:
    """Tests for finding field values (AC #1, #10)."""

    def test_missing_init_finding_has_all_correct_fields(self, tmp_path: Path) -> None:
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        module = pkg / "module.py"
        module.touch()

        findings = check_coverage(src, [module])

        assert len(findings) == 1
        f = findings[0]
        assert isinstance(f, Finding)
        assert f.file == str(module)
        assert f.line == 1
        assert f.symbol == "<module>"
        assert f.rule == "missing-init"
        assert f.category == "required"
        assert f.message == "Directory 'pkg' lacks __init__.py (1 file affected)"

    def test_missing_init_finding_message_format_with_count(
        self, tmp_path: Path
    ) -> None:
        """Verify exact message format matches spec."""
        src = tmp_path / "src"
        pkg = src / "pkg" / "sub"
        pkg.mkdir(parents=True)
        (src / "pkg" / "__init__.py").touch()
        a = pkg / "a.py"
        b = pkg / "b.py"
        a.touch()
        b.touch()

        findings = check_coverage(src, [a, b])

        assert (
            findings[0].message
            == "Directory 'pkg/sub' lacks __init__.py (2 files affected)"
        )


class TestCheckCoverageEdgeCases:
    """Edge case tests (Epic 4+ retro learning)."""

    def test_missing_init_when_mix_of_passing_and_failing_dirs(
        self, tmp_path: Path
    ) -> None:
        src = tmp_path / "src"
        # good_pkg has __init__.py
        good = src / "good_pkg"
        good.mkdir(parents=True)
        (good / "__init__.py").touch()
        (good / "module.py").touch()
        # bad_pkg lacks __init__.py
        bad = src / "bad_pkg"
        bad.mkdir(parents=True)
        (bad / "module.py").touch()

        files = [good / "module.py", bad / "module.py"]
        findings = check_coverage(src, files)

        assert len(findings) == 1
        assert "bad_pkg" in findings[0].message

    def test_missing_init_when_src_root_itself_no_init_check(
        self, tmp_path: Path
    ) -> None:
        """src_root itself should never be checked for __init__.py."""
        src = tmp_path / "src"
        src.mkdir()
        module = src / "utils.py"
        module.touch()
        # src_root has no __init__.py — but that's fine, top-level modules

        findings = check_coverage(src, [module])

        assert findings == []

    def test_missing_init_when_file_is_init_py_itself(self, tmp_path: Path) -> None:
        """__init__.py files passed as input should not cause false positives."""
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        init = pkg / "__init__.py"
        init.touch()

        findings = check_coverage(src, [init])

        assert findings == []

    def test_missing_init_when_sibling_dirs_one_missing(self, tmp_path: Path) -> None:
        """Sibling directories where only one is missing __init__.py."""
        src = tmp_path / "src"
        pkg = src / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").touch()
        good = pkg / "good"
        good.mkdir()
        (good / "__init__.py").touch()
        (good / "module.py").touch()
        bad = pkg / "bad"
        bad.mkdir()
        (bad / "module.py").touch()

        files = [good / "module.py", bad / "module.py"]
        findings = check_coverage(src, files)

        assert len(findings) == 1
        assert "pkg/bad" in findings[0].message
