"""Rendering consumers share decoded sources with other checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from docvet.checks.griffe_compat import check_griffe_compat
from docvet.source import SourceCache

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "prefix,encoding", [("", "utf-8-sig"), ("# coding: latin-1\n", "latin-1")]
)
def test_griffe_checks_declared_encoding_with_shared_cache(
    tmp_path: Path, prefix, encoding
):
    pytest.importorskip("griffe")
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text('"""Package."""\n')
    module = package / "mod.py"
    source = (
        prefix + 'def f(x):\n    """Café.\n\n    Args:\n        x: Value.\n    """\n'
    )
    module.write_bytes(source.encode(encoding))
    cache = SourceCache()
    findings = check_griffe_compat(tmp_path, [module], source_cache=cache)
    assert [f.rule for f in findings] == ["griffe-missing-type"]
    assert findings[0].file == module.as_posix()
    assert not cache.errors


def test_failed_package_init_does_not_hide_valid_selected_module(tmp_path: Path):
    pytest.importorskip("griffe")
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text("def broken(:")
    module = package / "mod.py"
    module.write_text(
        'def f(x):\n    """Describe.\n\n    Args:\n        x: Value.\n    """\n'
    )
    cache = SourceCache()
    cache.get(package / "__init__.py")
    findings = check_griffe_compat(tmp_path, [module], source_cache=cache)
    assert [f.rule for f in findings] == ["griffe-missing-type"]
    assert len(cache.errors) == 1


def test_shared_source_loader_preserves_inherited_constructor(tmp_path: Path):
    pytest.importorskip("griffe")
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text('"""Package."""\n')
    (package / "base.py").write_text(
        "class Base:\n    def __init__(self, x: int): pass\n"
    )
    module = package / "mod.py"
    module.write_text(
        "from .base import Base\nclass Child(Base):\n"
        '    """Child.\n\n    Args:\n        x: Value.\n    """\n'
    )
    assert check_griffe_compat(tmp_path, [module], source_cache=SourceCache()) == []


def test_form_feed_line_does_not_shift_griffe_lines(tmp_path: Path):
    pytest.importorskip("griffe")
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text('"""Package."""\n')
    body = 'def f(x):\n    """Describe.\n\n    Args:\n        x: Value.\n    """\n'
    plain = package / "plain.py"
    plain.write_text('"""Mod."""\n' + body)
    paged = package / "paged.py"
    paged.write_text('"""Mod."""\n\x0c\n' + body)
    cache = SourceCache()
    findings = check_griffe_compat(tmp_path, [plain, paged], source_cache=cache)
    lines = {f.file: f.line for f in findings if f.rule == "griffe-missing-type"}
    assert lines[paged.as_posix()] == lines[plain.as_posix()] + 1
    assert not cache.errors
