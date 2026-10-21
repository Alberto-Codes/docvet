"""Regression coverage for shared Python source loading and safe encoding."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from docvet.source import InputError, SourceCache

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "raw,encoding",
    [
        (b'"""Module."""\nx = 1\n', "utf-8"),
        (b'\xef\xbb\xbf"""Module."""\nx = 1\n', "utf-8-sig"),
        (b'# coding: latin-1\n"""Caf\xe9."""\nx = 1\n', "iso-8859-1"),
        (b'"""Module."""\r\nx = 1\r\n', "utf-8"),
        (b'"""Module."""\r\nx = 1\ny = 2\r', "utf-8"),
    ],
)
def test_valid_source_preserves_bytes_and_newlines(tmp_path, raw, encoding):
    path = tmp_path / "module.py"
    path.write_bytes(raw)
    cache = SourceCache()
    document = cache.get(path)
    assert document is not None
    assert document.path == path.resolve()
    assert document.encoding == encoding
    assert document.original_bytes == raw
    assert isinstance(document.tree, ast.Module)
    assert document.text == raw.decode(encoding)
    assert document.encode(document.text) == raw
    assert document.encode(document.text.replace("x = 1", "x = 3")) == raw.replace(
        b"x = 1", b"x = 3"
    )
    assert cache.errors == ()
    assert cache.attempted_paths == cache.successful_paths == {path.resolve()}


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize(
    "prefix,codec,encoding",
    [
        (b"# coding: latin-1\n", "latin-1", "iso-8859-1"),
        (b"\n# coding: latin-1\n", "latin-1", "iso-8859-1"),
        (
            b"#!/usr/bin/env python\n# -*- coding: latin-1 -*-\n",
            "latin-1",
            "iso-8859-1",
        ),
        (b"\xef\xbb\xbf", "utf-8", "utf-8-sig"),
        (b"\xef\xbb\xbf# coding: utf-8\n", "utf-8", "utf-8-sig"),
    ],
    ids=["cookie-first", "cookie-second", "cookie-after-shebang", "bom", "bom-cookie"],
)
def test_declared_encoding_is_detected_for_every_line_terminator(
    tmp_path, newline, prefix, codec, encoding
):
    """A coding cookie counts on any interpreter-accepted line terminator."""
    body = '"""Caf\u00e9."""\nx = 1\n'.encode(codec)
    raw = (prefix + body).replace(b"\n", newline)
    compile(raw, "<module>", "exec")
    path = tmp_path / "module.py"
    path.write_bytes(raw)
    cache = SourceCache()
    document = cache.get(path)
    assert document is not None, cache.errors
    assert document.encoding == encoding
    assert document.original_bytes == raw
    assert document.text == raw.decode(encoding)
    assert document.tree.body[-1].lineno == raw.count(newline)
    assert document.encode(document.text) == raw
    assert document.encode(document.text.replace("x = 1", "x = 3")) == raw.replace(
        b"x = 1", b"x = 3"
    )
    assert cache.errors == ()
    assert cache.attempted_paths == cache.successful_paths == {path.resolve()}


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize(
    "raw",
    [
        b"\xef\xbb\xbf# coding: latin-1\nx = 1\n",
        b"\n# coding: unknown-encoding\nx = 1\n",
        b'x = 1\ny = 2\n# coding: latin-1\n"""Caf\xe9."""\n',
    ],
    ids=["bom-conflict", "unknown-codec", "cookie-too-late"],
)
def test_invalid_declared_encoding_fails_for_every_line_terminator(
    tmp_path, newline, raw
):
    """Malformed or conflicting declarations fail in a controlled way."""
    raw = raw.replace(b"\n", newline)
    with pytest.raises(SyntaxError):
        compile(raw, "<module>", "exec")
    path = tmp_path / "invalid.py"
    path.write_bytes(raw)
    cache = SourceCache()
    assert cache.get(path) is None
    assert len(cache.errors) == 1
    assert cache.errors[0].kind == "decode"
    assert cache.errors[0].message
    assert cache.successful_paths == set()


@pytest.mark.parametrize(
    "raw,kind",
    [
        (b"# coding: unknown-encoding\nx = 1\n", "decode"),
        (b"\xef\xbb\xbf# coding: latin-1\nx = 1\n", "decode"),
        (b'"""\xff"""\n', "decode"),
        (b"if True:\n", "parse"),
        (b'x = "\x00"\n', "parse"),
    ],
)
def test_invalid_source_records_failure_once(tmp_path, raw, kind):
    path = tmp_path / "invalid.py"
    path.write_bytes(raw)
    cache = SourceCache()
    assert cache.get(path) is None
    assert cache.get(path.parent / "." / path.name) is None
    assert len(cache.errors) == 1
    assert cache.errors[0].file == str(path.resolve())
    assert cache.errors[0].kind == kind
    assert cache.errors[0].message
    assert cache.attempted_paths == {path.resolve()}
    assert cache.successful_paths == set()


@pytest.mark.parametrize("directory", [False, True])
def test_read_errors_are_controlled(tmp_path, directory):
    path = tmp_path / "unreadable.py"
    if directory:
        path.mkdir()
    cache = SourceCache()
    assert cache.get(path) is None
    assert cache.errors[0].kind == "read"


def test_cache_reads_success_and_failure_only_once(tmp_path, monkeypatch):
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text('"""Good."""\n')
    bad.write_text("def broken(\n")
    cache = SourceCache()
    document = cache.get(good)
    assert cache.get(bad) is None

    def unexpected_read(path):
        pytest.fail("cached sources must not be read again")

    monkeypatch.setattr(Path, "read_bytes", unexpected_read)
    assert cache.get(good) is document
    assert cache.get(bad) is None


def test_record_error_deduplicates_resolved_aliases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache = SourceCache()
    cache.record_error(InputError("missing.py", "input", "Missing target"))
    cache.record_error(
        InputError(str(tmp_path / "missing.py"), "input", "Missing target")
    )
    assert len(cache.errors) == 1
    assert cache.attempted_paths == set()
    with pytest.raises(FrozenInstanceError):
        setattr(cache.errors[0], "message", "changed")  # noqa: B010


def test_encoding_rejects_unrepresentable_changes_without_writing(tmp_path):
    path = tmp_path / "latin.py"
    raw = b'# coding: latin-1\n"""Caf\xe9."""\n'
    path.write_bytes(raw)
    document = SourceCache().get(path)
    assert document is not None
    with pytest.raises(UnicodeError):
        document.encode(document.text + "# \u2603\n")
    assert path.read_bytes() == raw


def test_encoding_rejects_cookie_changes(tmp_path):
    path = tmp_path / "latin.py"
    path.write_bytes(b'# coding: latin-1\n"""Caf\xe9."""\n')
    document = SourceCache().get(path)
    assert document is not None
    with pytest.raises(UnicodeError):
        document.encode(document.text.replace("latin-1", "utf-8"))


def test_noncanonical_encoding_is_readable_but_cannot_be_rewritten(tmp_path):
    path = tmp_path / "utf7.py"
    raw = b'# coding: utf-7\n"""+AEE-."""\n'
    path.write_bytes(raw)
    document = SourceCache().get(path)
    assert document is not None
    assert '"""A."""' in document.text
    with pytest.raises(UnicodeError, match="original bytes"):
        document.encode(document.text)
    assert path.read_bytes() == raw


def test_permission_error_is_controlled(tmp_path, monkeypatch):
    def deny_read(path):
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "read_bytes", deny_read)
    cache = SourceCache()
    assert cache.get(tmp_path / "restricted.py") is None
    assert cache.errors[0].kind == "read"
    assert "permission denied" in cache.errors[0].message


def test_unresolvable_symlink_is_controlled(tmp_path):
    path = tmp_path / "loop.py"
    path.symlink_to(path)
    cache = SourceCache()
    assert cache.get(path) is None
    assert cache.get(path) is None
    assert len(cache.errors) == 1
    assert cache.errors[0].kind == "read"
    assert cache.attempted_paths == {path}


def test_refresh_updates_source_and_ast_line_positions(tmp_path):
    path = tmp_path / "fixed.py"
    path.write_bytes(b'"""Module."""\r\nx = 1\r\n')
    cache = SourceCache()
    before = cache.get(path)
    path.write_bytes(b'"""Module.\r\n\r\nDetails.\r\n"""\r\nx = 1\r\n')
    after = cache.refresh(path.parent / "." / path.name)
    assert before is not None and after is not None
    assert before.tree.body[1].lineno == 2
    assert after.tree.body[1].lineno == 5
    assert after.original_bytes == path.read_bytes()
    assert cache.get(path) is after
    assert cache.attempted_paths == cache.successful_paths == {path.resolve()}
    assert cache.errors == ()


def test_refresh_retries_failed_input_preserving_errors(tmp_path):
    path = tmp_path / "fixed.py"
    cache = SourceCache()
    assert cache.get(path) is None
    errors = cache.errors
    path.write_text('"""Fixed."""\n')
    assert cache.refresh(path) is not None
    assert cache.errors == errors
    assert cache.attempted_paths == cache.successful_paths == {path.resolve()}


def test_refresh_failure_removes_stale_success(tmp_path):
    path = tmp_path / "fixed.py"
    path.write_text('"""Module."""\n')
    cache = SourceCache()
    assert cache.get(path) is not None
    path.unlink()
    assert cache.refresh(path) is None
    assert cache.get(path) is None
    assert cache.attempted_paths == {path.resolve()}
    assert cache.successful_paths == set()
    assert len(cache.errors) == 1
    assert cache.errors[0].kind == "read"


def test_refresh_unresolvable_path_records_error(tmp_path):
    path = tmp_path / "loop.py"
    path.symlink_to(path)
    cache = SourceCache()
    assert cache.refresh(path) is None
    assert len(cache.errors) == 1
    assert cache.errors[0].kind == "read"


def test_null_byte_path_is_structured_failure():
    cache = SourceCache()
    assert cache.get(Path("bad\x00.py")) is None
    assert cache.errors[0].kind == "read"
    assert len(cache.errors) == 1
