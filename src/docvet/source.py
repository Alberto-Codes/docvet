"""Shared, encoding-aware Python source loading without diagnostic side effects.

One cache belongs to one invocation. Consumers share both successful documents
and failed attempts, reading and parsing once unless refreshed after a fix. Documents
retain the original bytes and line endings for encoding-preserving fixes.
[`decode_source`][docvet.source.decode_source] exposes the same encoding
detection for consumers that need decoded text without parsing.

Examples:
    Load a document and inspect structured failures:

    ```python
    cache = SourceCache()
    document = cache.get(Path("module.py"))
    errors = cache.errors
    ```

See Also:
    [`docvet.discovery`][]: Input file selection.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


def decode_source(raw: bytes) -> tuple[str, str]:
    """Decode Python source bytes using their declared encoding.

    Follows the same detection as the interpreter: a UTF-8 BOM or a PEP 263
    declaration selects the codec, and ordinary UTF-8 is the default. No
    parsing happens, so comments in a file with syntax errors remain readable.

    Args:
        raw: Source bytes as read from disk.

    Returns:
        Tuple of the decoded text with original line endings and the encoding
        name detected by ``tokenize``.

    Raises:
        SyntaxError: The encoding declaration is invalid or conflicts with a BOM.
        UnicodeError: The bytes are not valid in the detected encoding.
        LookupError: The declared codec is unavailable.

    Examples:
        ```python
        text, encoding = decode_source(Path("module.py").read_bytes())
        assert text.encode(encoding) == Path("module.py").read_bytes()
        ```
    """
    encoding = _detect_encoding(raw)
    return raw.decode(encoding), encoding


def _detect_encoding(raw: bytes) -> str:
    """Detect the declared source encoding across every Python line terminator.

    ``tokenize.detect_encoding`` splits lines only at line feeds, so a coding
    cookie in a file using CR or CRLF terminators would be missed although the
    interpreter accepts it. Detection runs on a line-normalized copy; the
    original bytes are never altered.

    Args:
        raw: Source bytes as read from disk.

    Returns:
        Encoding name detected by ``tokenize``.

    Raises:
        SyntaxError: The encoding declaration is invalid or conflicts with a BOM.
    """
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    encoding, _ = tokenize.detect_encoding(io.BytesIO(normalized).readline)
    return encoding


@dataclass(frozen=True)
class InputError:
    """Structured failure encountered while selecting or processing an input.

    Attributes:
        file (str): Input path for the diagnostic.
        kind (str): Stage at which processing failed.
        message (str): Human-readable explanation of the failure.

    Examples:
        ```python
        error = InputError("missing.py", "input", "Target does not exist")
        ```
    """

    file: str
    kind: Literal["input", "read", "decode", "parse", "write"]
    message: str


@dataclass(frozen=True)
class SourceDocument:
    """Parsed Python source with its original encoding and byte representation.

    Attributes:
        path (Path): Resolved source path.
        text (str): Decoded source with exact original line endings.
        encoding (str): Python source encoding detected by ``tokenize``.
        original_bytes (bytes): Source bytes before decoding.
        tree (ast.Module): Parsed module tree shared by analysis consumers.

    Examples:
        ```python
        document = SourceCache().get(Path("module.py"))
        if document is not None:
            unchanged = document.encode(document.text)
        ```
    """

    path: Path
    text: str
    encoding: str
    original_bytes: bytes
    tree: ast.Module

    def encode(self, text: str) -> bytes:
        """Encode replacement source without changing its encoding or BOM.

        Reject sources whose codec cannot reproduce the original bytes and
        replacements whose encoding declaration no longer matches their bytes.
        This method performs no filesystem writes.

        Args:
            text: Replacement source preserving any unaffected line endings.

        Returns:
            Encoded replacement bytes ready for a caller-controlled write.

        Raises:
            UnicodeError: The source cannot safely round-trip or the replacement
                cannot be represented by its source encoding.
            LookupError: The source codec is unavailable.
        """
        if self.text.encode(self.encoding) != self.original_bytes:
            raise UnicodeError("Source encoding cannot reproduce the original bytes")
        encoded = text.encode(self.encoding)
        try:
            detected = _detect_encoding(encoded)
            decoded = encoded.decode(detected)
        except (SyntaxError, LookupError) as exc:
            raise UnicodeError(str(exc)) from exc
        if detected != self.encoding or decoded != text:
            raise UnicodeError("Replacement changes the source encoding declaration")
        return encoded


class SourceCache:
    """Invocation-scoped cache of source documents and structured failures.

    Attributes:
        errors (tuple[InputError, ...]): Deduplicated failures in encounter order.
        attempted_paths (frozenset[Path]): Paths whose loading was attempted.
        successful_paths (frozenset[Path]): Paths successfully decoded and parsed.

    Examples:
        ```python
        cache = SourceCache()
        document = cache.get(Path("module.py"))
        assert len(cache.attempted_paths) == 1
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty cache with no attempted inputs."""
        self._documents: dict[Path, SourceDocument | None] = {}
        self._errors: dict[tuple[Path, str, str], InputError] = {}

    @property
    def errors(self) -> tuple[InputError, ...]:
        """Deduplicated failures in encounter order."""
        return tuple(self._errors.values())

    @property
    def attempted_paths(self) -> frozenset[Path]:
        """Resolved paths whose loading was attempted, including failures."""
        return frozenset(self._documents)

    @property
    def successful_paths(self) -> frozenset[Path]:
        """Resolved paths that were decoded and parsed successfully."""
        return frozenset(
            path for path, doc in self._documents.items() if doc is not None
        )

    def record_error(self, error: InputError) -> None:
        """Record an external discovery or write failure without logging.

        Repeated errors for aliases of the same path are stored once. Recording
        an error does not itself count as an attempted source load.

        Args:
            error: Structured failure from discovery, loading, or fixing.
        """
        try:
            resolved = Path(error.file).resolve()
        except (OSError, RuntimeError, ValueError):
            resolved = Path(error.file).absolute()
        key = (resolved, error.kind, error.message)
        self._errors.setdefault(key, error)

    def refresh(self, path: Path) -> SourceDocument | None:
        """Reload source after a fix, replacing stale text and AST positions.

        Historical errors remain recorded. Attempted paths remain deduplicated,
        and successful paths reflect the latest loading result.

        Args:
            path: Python source path to invalidate and reload.

        Returns:
            Updated document, or ``None`` when reloading fails.
        """
        try:
            resolved = path.resolve()
        except (OSError, RuntimeError, ValueError):
            resolved = path.absolute()
        self._documents.pop(resolved, None)
        return self.get(path)

    def get(self, path: Path) -> SourceDocument | None:
        """Read, decode, and parse a source once per resolved path.

        Decoding follows :func:`decode_source`. Failures are cached and exposed
        through ``errors``. No consumer needs to catch ordinary filesystem,
        encoding, or Python syntax failures.

        Args:
            path: Python source path to load.

        Returns:
            Parsed source document, or ``None`` for an unsuccessful attempt.
        """
        try:
            path = path.resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            path = path.absolute()
            self._documents[path] = None
            self.record_error(InputError(str(path), "read", str(exc)))
            return None
        if path in self._documents:
            return self._documents[path]
        self._documents[path] = None
        try:
            raw = path.read_bytes()
        except (OSError, UnicodeError, ValueError) as exc:
            self.record_error(InputError(str(path), "read", str(exc)))
            return None
        try:
            text, encoding = decode_source(raw)
        except (SyntaxError, UnicodeError, LookupError) as exc:
            self.record_error(InputError(str(path), "decode", str(exc)))
            return None
        try:
            tree = ast.parse(text, filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            self.record_error(InputError(str(path), "parse", str(exc)))
            return None
        document = SourceDocument(path, text, encoding, raw, tree)
        self._documents[path] = document
        return document
