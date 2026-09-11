"""Integration tests for the unavailable-check policy (issue #442).

A check listed in ``fail-on`` that cannot execute never certified the
gate it was asked to certify. With the opt-in ``fail-on-unavailable``
enabled that fails the run; with it off — the default — the run still
exits 0 but warns loudly. A check that is unavailable and not listed
in ``fail-on`` stays a quiet skip either way.

Each test drives the installed ``docvet`` console script in a temp git
repo and asserts on the process exit code and its JSON output.
"""

from __future__ import annotations

import json
import os
import subprocess
import textwrap

import pytest

pytestmark = pytest.mark.integration

CLEAN_MODULE = '''\
"""Provide a minimal module with no docstring findings.

Examples:
    Import the module to inspect the check result.

See Also:
    [`docvet`][]: Docstring quality checks.
"""
'''


@pytest.fixture
def repo(tmp_path):
    """Create a git repo holding one finding-free module."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text(textwrap.dedent(CLEAN_MODULE))
    return tmp_path


def _write_config(
    repo,
    *,
    fail_on: list[str],
    docstring_style: str = "google",
    fail_on_unavailable: bool | None = None,
    presence_enabled: bool | None = None,
) -> None:
    """Write a ``[tool.docvet]`` section with the given policy.

    Args:
        repo: Repository root to write ``pyproject.toml`` into.
        fail_on: Check names to list in ``fail-on``.
        docstring_style: Value for ``docstring-style``.
        fail_on_unavailable: Value for ``fail-on-unavailable``, or
            *None* to omit the key and exercise the default.
        presence_enabled: Value for ``[tool.docvet.presence] enabled``,
            or *None* to omit the section entirely.
    """
    checks = ", ".join(f'"{c}"' for c in fail_on)
    opt_in = (
        ""
        if fail_on_unavailable is None
        else f"fail-on-unavailable = {str(fail_on_unavailable).lower()}\n"
    )
    presence = (
        ""
        if presence_enabled is None
        else (f"\n[tool.docvet.presence]\nenabled = {str(presence_enabled).lower()}\n")
    )
    (repo / "pyproject.toml").write_text(
        "[tool.docvet]\n"
        'src-root = "src"\n'
        "exclude = []\n"
        f'docstring-style = "{docstring_style}"\n'
        f"fail-on = [{checks}]\n" + opt_in + presence
    )


def _hide_griffe(tmp_path) -> dict[str, str]:
    """Build an environment in which griffe is not importable.

    Binding ``sys.modules["griffe"]`` to *None* makes
    ``importlib.util.find_spec("griffe")`` return *None*, which is the
    same signal docvet gets from an environment that never installed
    the extra.

    Args:
        tmp_path: Directory to hold the generated ``sitecustomize``.

    Returns:
        An environment mapping to pass to :func:`subprocess.run`.
    """
    blocker = tmp_path / "griffe_blocker"
    blocker.mkdir()
    (blocker / "sitecustomize.py").write_text(
        'import sys\n\nsys.modules["griffe"] = None\n'
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(blocker)
    return env


def _run(repo, *args, env=None):
    """Run the docvet CLI in *repo* and return the completed process."""
    return subprocess.run(
        ["docvet", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _run_block(result):
    """Parse the ``run`` object out of a JSON CLI result."""
    return json.loads(result.stdout)["run"]


class TestOptInBlocksUnavailableCheck:
    """With ``fail-on-unavailable`` on, an unrunnable gate fails."""

    def test_exits_non_zero_when_griffe_is_unavailable(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=True)
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 1
        assert "error: griffe check is in fail-on but could not run" in result.stderr

    def test_stderr_names_the_remedy(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=True)
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert "pip install 'docvet[griffe]'" in result.stderr

    def test_cli_flag_turns_the_behaviour_on_without_config(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(
            repo, "--fail-on-unavailable", "check", "--all", env=_hide_griffe(tmp_path)
        )
        assert result.returncode == 1
        assert "error: griffe check is in fail-on but could not run" in result.stderr

    def test_json_distinguishes_unavailable_from_findings(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=True)
        result = _run(
            repo, "--format", "json", "check", "--all", env=_hide_griffe(tmp_path)
        )
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert run["exit_code"] == 1
        assert "griffe" in run["exit_reason"]
        assert run["unavailable_checks"] == [
            {
                "check": "griffe",
                "reason": "griffe not installed",
                "remedy": "pip install 'docvet[griffe]', or drop griffe from fail-on",
                "blocking": True,
                "in_fail_on": True,
            }
        ]
        assert json.loads(result.stdout)["findings"] == []

    def test_sphinx_style_also_blocks_a_configured_griffe_gate(self, repo):
        _write_config(
            repo,
            fail_on=["griffe"],
            docstring_style="sphinx",
            fail_on_unavailable=True,
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert run["unavailable_checks"][0]["reason"] == (
            "incompatible with sphinx docstring style"
        )

    def test_griffe_subcommand_exits_non_zero(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=True)
        result = _run(repo, "griffe", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 1


class TestDefaultWarnsButDoesNotBlock:
    """With the setting off, a configured gate that never ran warns."""

    def test_exits_zero_by_default(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert "error:" not in result.stderr

    def test_warning_names_the_check_and_the_reason(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert (
            "warning: griffe check is in fail-on but could not run"
            " (griffe not installed), so that gate never executed" in result.stderr
        )

    def test_warning_explains_the_gate_did_not_fail_and_the_opt_in(
        self, repo, tmp_path
    ):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert (
            "this did not fail the run because fail-on-unavailable is off"
            in result.stderr
        )
        assert "fail-on-unavailable = true" in result.stderr
        assert "--fail-on-unavailable" in result.stderr
        assert "a future major release will make this an error" in result.stderr
        assert "pip install 'docvet[griffe]'" in result.stderr

    def test_warning_survives_quiet(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "--quiet", "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert "warning: griffe check is in fail-on but could not run" in result.stderr

    def test_json_reports_unavailable_but_a_passing_run(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(
            repo, "--format", "json", "check", "--all", env=_hide_griffe(tmp_path)
        )
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["exit_code"] == 0
        assert "griffe (griffe not installed)" in run["exit_reason"]
        assert "fail-on-unavailable is off" in run["exit_reason"]
        assert run["unavailable_checks"] == [
            {
                "check": "griffe",
                "reason": "griffe not installed",
                "remedy": "pip install 'docvet[griffe]', or drop griffe from fail-on",
                "blocking": False,
                "in_fail_on": True,
            }
        ]

    def test_griffe_subcommand_exits_zero(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "griffe", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert "warning: griffe check is in fail-on but could not run" in result.stderr


class TestAdvisoryCheckUnavailable:
    """An unavailable check outside fail-on stays non-blocking."""

    def test_exits_zero_and_still_reports_the_skip(self, repo, tmp_path):
        _write_config(repo, fail_on=["enrichment"])
        result = _run(
            repo, "--format", "json", "check", "--all", env=_hide_griffe(tmp_path)
        )
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == [
            {
                "check": "griffe",
                "reason": "griffe not installed",
                "remedy": "pip install 'docvet[griffe]', or drop griffe from fail-on",
                "blocking": False,
                "in_fail_on": False,
            }
        ]

    def test_stderr_reports_no_error_and_no_warning(self, repo, tmp_path):
        _write_config(repo, fail_on=["enrichment"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert "error:" not in result.stderr
        assert "warning: griffe" not in result.stderr

    def test_opt_in_does_not_block_a_check_outside_fail_on(self, repo, tmp_path):
        _write_config(repo, fail_on=["enrichment"], fail_on_unavailable=True)
        result = _run(
            repo, "--format", "json", "check", "--all", env=_hide_griffe(tmp_path)
        )
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"][0]["blocking"] is False


class TestAllChecksAvailable:
    """A clean run reports no unavailable check."""

    def test_exits_zero_with_no_unavailable_status(self, repo):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=True)
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == []
        assert "griffe" in result.stderr

    def test_findings_status_is_distinct_from_unavailable(self, repo):
        _write_config(repo, fail_on=["enrichment"])
        (repo / "src" / "bad.py").write_text(
            textwrap.dedent(
                '''\
                """Provide a module whose function is missing a Raises section.

                Examples:
                    Call the function to see the failure.

                See Also:
                    [`docvet`][]: Docstring quality checks.
                """


                def validate(data):
                    """Validate input data.

                    Args:
                        data: Payload to validate.
                    """
                    if not data:
                        raise ValueError("empty")
                '''
            )
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "findings"
        assert run["unavailable_checks"] == []


class TestDisabledPresenceGate:
    """A presence gate switched off certified nothing."""

    @staticmethod
    def _add_undocumented_symbol(repo) -> None:
        """Give the presence check something it would have flagged."""
        (repo / "src" / "bare.py").write_text("def helper(x):\n    return x\n")

    def test_json_names_the_disabled_gate_instead_of_claiming_a_clean_pass(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(repo, fail_on=["presence"], presence_enabled=False)
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == [
            {
                "check": "presence",
                "reason": "disabled by configuration",
                "remedy": (
                    "set enabled = true under [tool.docvet.presence], or drop"
                    " presence from fail-on"
                ),
                "blocking": False,
                "in_fail_on": True,
            }
        ]
        assert "presence (disabled by configuration)" in run["exit_reason"]
        assert "no check in fail-on was unavailable" not in run["exit_reason"]

    def test_opt_in_fails_the_run(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo,
            fail_on=["presence"],
            presence_enabled=False,
            fail_on_unavailable=True,
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert "presence (disabled by configuration)" in run["exit_reason"]
        assert run["unavailable_checks"][0]["blocking"] is True

    def test_warning_survives_quiet_on_the_default_path(self, repo):
        _write_config(repo, fail_on=["presence"], presence_enabled=False)
        result = _run(repo, "--quiet", "check", "--all")
        assert result.returncode == 0
        assert (
            "warning: presence check is in fail-on but could not run"
            " (disabled by configuration), so that gate never executed" in result.stderr
        )
        assert "set enabled = true under [tool.docvet.presence]" in result.stderr

    def test_disabled_presence_outside_fail_on_is_an_ordinary_opt_out(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo,
            fail_on=["enrichment"],
            presence_enabled=False,
            fail_on_unavailable=True,
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == []

    def test_enabled_presence_gate_is_never_reported_unavailable(self, repo):
        _write_config(
            repo,
            fail_on=["presence"],
            presence_enabled=True,
            fail_on_unavailable=True,
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        assert _run_block(result)["unavailable_checks"] == []
