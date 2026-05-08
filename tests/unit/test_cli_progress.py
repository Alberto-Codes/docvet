"""Unit tests for CLI progress bar integration."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from docvet.checks import Finding
from docvet.cli import FreshnessMode, _run_enrichment, _run_freshness
from docvet.config import DocvetConfig
from docvet.discovery import DiscoveryMode

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_py_file(tmp_path):
    p = tmp_path / "simple.py"
    p.write_text('"""Module doc."""\n\ndef foo():\n    """Foo doc."""\n    pass\n')
    return p


@pytest.fixture
def config(tmp_path):
    return DocvetConfig(project_root=tmp_path)


@pytest.fixture
def mock_maybe_progressbar(mocker):
    """Mock _maybe_progressbar as a context manager yielding the input iterable."""
    mock_pb = mocker.patch("docvet.cli._runners._maybe_progressbar")

    @contextmanager
    def make_ctx(items, *, label, show):
        yield iter(items)

    mock_pb.side_effect = make_ctx
    return mock_pb


# ---------------------------------------------------------------------------
# _run_enrichment progress bar
# ---------------------------------------------------------------------------


class TestRunEnrichmentProgressBar:
    def test_enrichment_progressbar_show_true(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config, show_progress=True)

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="enrichment",
            show=True,
        )

    def test_enrichment_progressbar_show_false(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config, show_progress=False)

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="enrichment",
            show=False,
        )

    def test_enrichment_progressbar_default_show_progress_is_false(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config)

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="enrichment",
            show=False,
        )

    def test_enrichment_findings_identical_with_and_without_progress(
        self, mocker, simple_py_file, config
    ):
        finding = Finding(
            file=str(simple_py_file),
            line=3,
            symbol="foo",
            rule="missing-raises",
            message="test finding",
            category="required",
        )
        mocker.patch("docvet.cli.check_enrichment", return_value=[finding])

        findings_with, _ = _run_enrichment([simple_py_file], config, show_progress=True)
        findings_without, _ = _run_enrichment(
            [simple_py_file], config, show_progress=False
        )

        assert findings_with == findings_without
        assert len(findings_with) == 1

    def test_enrichment_empty_files_returns_empty_list(self, config):
        findings, count = _run_enrichment([], config, show_progress=True)
        assert findings == []
        assert count == 0


# ---------------------------------------------------------------------------
# _run_freshness progress bar
# ---------------------------------------------------------------------------


class TestRunFreshnessProgressBar:
    def test_freshness_diff_progressbar_show_true(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
        mocker.patch("docvet.cli._get_git_diff", return_value="")

        _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DIFF,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=True,
        )

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            show=True,
        )

    def test_freshness_diff_progressbar_show_false(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_freshness_diff", return_value=[])
        mocker.patch("docvet.cli._get_git_diff", return_value="")

        _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DIFF,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=False,
        )

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            show=False,
        )

    def test_freshness_drift_progressbar_show_true(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
        mocker.patch("docvet.cli._get_git_blame", return_value="")

        _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DRIFT,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=True,
        )

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            show=True,
        )

    def test_freshness_drift_progressbar_show_false(
        self, mocker, mock_maybe_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_freshness_drift", return_value=[])
        mocker.patch("docvet.cli._get_git_blame", return_value="")

        _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DRIFT,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=False,
        )

        mock_maybe_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            show=False,
        )

    def test_freshness_findings_identical_with_and_without_progress(
        self, mocker, simple_py_file, config
    ):
        finding = Finding(
            file=str(simple_py_file),
            line=3,
            symbol="foo",
            rule="stale-signature",
            message="test finding",
            category="required",
        )
        mocker.patch("docvet.cli.check_freshness_diff", return_value=[finding])
        mocker.patch("docvet.cli._get_git_diff", return_value="fake diff")

        findings_with, _ = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DIFF,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=True,
        )
        findings_without, _ = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DIFF,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=False,
        )

        assert findings_with == findings_without
        assert len(findings_with) == 1

    def test_freshness_drift_findings_identical_with_and_without_progress(
        self, mocker, simple_py_file, config
    ):
        finding = Finding(
            file=str(simple_py_file),
            line=3,
            symbol="foo",
            rule="stale-drift",
            message="test drift finding",
            category="recommended",
        )
        mocker.patch("docvet.cli.check_freshness_drift", return_value=[finding])
        mocker.patch("docvet.cli._get_git_blame", return_value="fake blame")

        findings_with, _ = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DRIFT,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=True,
        )
        findings_without, _ = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DRIFT,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=False,
        )

        assert findings_with == findings_without
        assert len(findings_with) == 1

    def test_freshness_empty_files_returns_empty_list(self, config):
        findings, count = _run_freshness([], config, show_progress=True)
        assert findings == []
        assert count == 0


# ---------------------------------------------------------------------------
# _maybe_progressbar unit tests
# ---------------------------------------------------------------------------


class TestMaybeProgressbar:
    def test_show_false_yields_plain_iterator(self):
        from docvet.cli._runners import _maybe_progressbar

        items = [1, 2, 3]
        with _maybe_progressbar(items, label="test", show=False) as it:
            assert list(it) == [1, 2, 3]

    def test_show_true_calls_typer_progressbar(self, mocker):
        mock_pb = mocker.patch("docvet.cli._runners.typer.progressbar")
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=iter([1, 2, 3]))
        ctx.__exit__ = MagicMock(return_value=False)
        mock_pb.return_value = ctx

        from docvet.cli._runners import _maybe_progressbar

        with _maybe_progressbar([1, 2, 3], label="test", show=True) as it:
            result = list(it)

        assert result == [1, 2, 3]
        mock_pb.assert_called_once_with([1, 2, 3], label="test", file=sys.stderr)

    def test_show_false_does_not_call_typer_progressbar(self, mocker):
        mock_pb = mocker.patch("docvet.cli._runners.typer.progressbar")

        from docvet.cli._runners import _maybe_progressbar

        with _maybe_progressbar([1, 2], label="test", show=False) as it:
            list(it)

        mock_pb.assert_not_called()
