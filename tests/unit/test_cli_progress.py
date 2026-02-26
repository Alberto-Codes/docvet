"""Unit tests for CLI progress bar integration."""

from __future__ import annotations

import sys
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
def mock_progressbar(mocker):
    """Mock typer.progressbar as a context manager yielding the input iterable."""
    mock_pb = mocker.patch("docvet.cli.typer.progressbar")

    # Store original iterable so context manager yields the actual files
    def make_ctx(*args, **kwargs):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=args[0] if args else [])
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    mock_pb.side_effect = make_ctx
    return mock_pb


# ---------------------------------------------------------------------------
# Task 1 + Task 4.1/4.2: _run_enrichment progress bar
# ---------------------------------------------------------------------------


class TestRunEnrichmentProgressBar:
    def test_enrichment_progressbar_hidden_false_when_show_progress_true(
        self, mocker, mock_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config, show_progress=True)

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="enrichment",
            file=sys.stderr,
            hidden=False,
        )

    def test_enrichment_progressbar_hidden_true_when_show_progress_false(
        self, mocker, mock_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config, show_progress=False)

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="enrichment",
            file=sys.stderr,
            hidden=True,
        )

    def test_enrichment_progressbar_default_show_progress_is_false(
        self, mocker, mock_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config)

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="enrichment",
            file=sys.stderr,
            hidden=True,
        )

    def test_enrichment_progressbar_writes_to_stderr_not_stdout(
        self, mocker, mock_progressbar, simple_py_file, config
    ):
        mocker.patch("docvet.cli.check_enrichment", return_value=[])

        _run_enrichment([simple_py_file], config, show_progress=True)

        assert mock_progressbar.call_args.kwargs["file"] is sys.stderr

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

        findings_with = _run_enrichment([simple_py_file], config, show_progress=True)
        findings_without = _run_enrichment(
            [simple_py_file], config, show_progress=False
        )

        assert findings_with == findings_without
        assert len(findings_with) == 1

    def test_enrichment_empty_files_returns_empty_list(self, config):
        assert _run_enrichment([], config, show_progress=True) == []


# ---------------------------------------------------------------------------
# Task 2 + Task 4.3: _run_freshness progress bar
# ---------------------------------------------------------------------------


class TestRunFreshnessProgressBar:
    def test_freshness_diff_progressbar_hidden_false_when_show_progress_true(
        self, mocker, mock_progressbar, simple_py_file, config
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

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            file=sys.stderr,
            hidden=False,
        )

    def test_freshness_diff_progressbar_hidden_true_when_show_progress_false(
        self, mocker, mock_progressbar, simple_py_file, config
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

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            file=sys.stderr,
            hidden=True,
        )

    def test_freshness_drift_progressbar_hidden_false_when_show_progress_true(
        self, mocker, mock_progressbar, simple_py_file, config
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

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            file=sys.stderr,
            hidden=False,
        )

    def test_freshness_drift_progressbar_hidden_true_when_show_progress_false(
        self, mocker, mock_progressbar, simple_py_file, config
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

        mock_progressbar.assert_called_once_with(
            [simple_py_file],
            label="freshness",
            file=sys.stderr,
            hidden=True,
        )

    def test_freshness_progressbar_writes_to_stderr_not_stdout(
        self, mocker, mock_progressbar, simple_py_file, config
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

        assert mock_progressbar.call_args.kwargs["file"] is sys.stderr

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

        findings_with = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DIFF,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=True,
        )
        findings_without = _run_freshness(
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

        findings_with = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DRIFT,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=True,
        )
        findings_without = _run_freshness(
            [simple_py_file],
            config,
            freshness_mode=FreshnessMode.DRIFT,
            discovery_mode=DiscoveryMode.DIFF,
            show_progress=False,
        )

        assert findings_with == findings_without
        assert len(findings_with) == 1

    def test_freshness_empty_files_returns_empty_list(self, config):
        assert _run_freshness([], config, show_progress=True) == []
