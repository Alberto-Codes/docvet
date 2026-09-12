"""Integration tests for the unavailable-check policy (issue #442).

A check listed in ``fail-on`` that cannot execute never certified the
gate it was asked to certify, so by default that fails the run. A
project that opts out with ``fail-on-unavailable = false`` still exits
0 but warns loudly. A check that is unavailable and that nothing gates
on stays a quiet skip either way -- and a ``min-coverage`` floor gates
``presence`` without ``fail-on`` ever naming it.

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
    min_coverage: float | None = None,
) -> None:
    """Write a ``[tool.docvet]`` section with the given policy.

    Args:
        repo: Repository root to write ``pyproject.toml`` into.
        fail_on: Check names to list in ``fail-on``.
        docstring_style: Value for ``docstring-style``.
        fail_on_unavailable: Value for ``fail-on-unavailable``, or
            *None* to omit the key and exercise the default, which is
            on.
        presence_enabled: Value for ``[tool.docvet.presence] enabled``,
            or *None* to omit the key.
        min_coverage: Value for ``[tool.docvet.presence] min-coverage``,
            or *None* to omit the key. The presence section is written
            when either presence key is given.
    """
    checks = ", ".join(f'"{c}"' for c in fail_on)
    opt_in = (
        ""
        if fail_on_unavailable is None
        else f"fail-on-unavailable = {str(fail_on_unavailable).lower()}\n"
    )
    presence = ""
    if presence_enabled is not None or min_coverage is not None:
        presence = "\n[tool.docvet.presence]\n"
        if presence_enabled is not None:
            presence += f"enabled = {str(presence_enabled).lower()}\n"
        if min_coverage is not None:
            presence += f"min-coverage = {min_coverage}\n"
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


class TestDefaultBlocksUnavailableCheck:
    """By default an unrunnable gate listed in ``fail-on`` fails."""

    def test_exits_non_zero_when_griffe_is_unavailable(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 1
        assert (
            "error: griffe check was configured to gate the run but could not run"
            in result.stderr
        )

    def test_stderr_names_the_remedy(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert "pip install 'docvet[griffe]'" in result.stderr

    def test_cli_flag_turns_the_behaviour_on_over_an_opt_out_config(
        self, repo, tmp_path
    ):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(
            repo, "--fail-on-unavailable", "check", "--all", env=_hide_griffe(tmp_path)
        )
        assert result.returncode == 1
        assert (
            "error: griffe check was configured to gate the run but could not run"
            in result.stderr
        )

    def test_cli_flag_turns_the_behaviour_off_without_config(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(
            repo,
            "--no-fail-on-unavailable",
            "check",
            "--all",
            env=_hide_griffe(tmp_path),
        )
        assert result.returncode == 0
        assert "error:" not in result.stderr
        assert (
            "warning: griffe check was configured to gate the run but could not run"
            in result.stderr
        )

    def test_flag_opt_out_does_not_blame_a_config_key_that_is_absent(
        self, repo, tmp_path
    ):
        _write_config(repo, fail_on=["griffe"])
        result = _run(
            repo,
            "--format",
            "json",
            "--no-fail-on-unavailable",
            "check",
            "--all",
            env=_hide_griffe(tmp_path),
        )
        assert result.returncode == 0
        assert (
            "fail-on-unavailable = false" not in (repo / "pyproject.toml").read_text()
        )
        assert (
            "this did not fail the run because fail-on-unavailable is disabled"
            " for this run" in result.stderr
        )
        assert "this project" not in result.stderr
        assert "this project" not in _run_block(result)["exit_reason"]

    def test_blocking_error_survives_quiet(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "--quiet", "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 1
        assert (
            "error: griffe check was configured to gate the run but could not run"
            " (griffe not installed)" in result.stderr
        )
        assert "pip install 'docvet[griffe]'" in result.stderr

    def test_json_distinguishes_unavailable_from_findings(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
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
                "configured_gate": True,
            }
        ]
        assert json.loads(result.stdout)["findings"] == []

    def test_sphinx_style_also_blocks_a_configured_griffe_gate(self, repo):
        _write_config(repo, fail_on=["griffe"], docstring_style="sphinx")
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert run["unavailable_checks"][0]["reason"] == (
            "incompatible with sphinx docstring style"
        )

    def test_griffe_subcommand_exits_non_zero(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"])
        result = _run(repo, "griffe", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 1


class TestOptOutWarnsButDoesNotBlock:
    """With ``fail-on-unavailable = false``, the gate only warns."""

    def test_exits_zero_when_opted_out(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert "error:" not in result.stderr

    def test_warning_names_the_check_and_the_reason(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert (
            "warning: griffe check was configured to gate the run but could not run"
            " (griffe not installed), so that gate never executed" in result.stderr
        )

    def test_warning_explains_the_opt_out_and_how_to_undo_it(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert (
            "this did not fail the run because fail-on-unavailable is disabled"
            " for this run" in result.stderr
        )
        assert "--fail-on-unavailable" in result.stderr
        assert "pip install 'docvet[griffe]'" in result.stderr

    def test_warning_survives_quiet(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(repo, "--quiet", "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert (
            "warning: griffe check was configured to gate the run but could not run"
            in result.stderr
        )

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
        assert "fail-on-unavailable disabled" in run["exit_reason"]
        assert run["unavailable_checks"] == [
            {
                "check": "griffe",
                "reason": "griffe not installed",
                "remedy": "pip install 'docvet[griffe]', or drop griffe from fail-on",
                "blocking": False,
                "configured_gate": True,
            }
        ]

    def test_griffe_subcommand_exits_zero(self, repo, tmp_path):
        _write_config(repo, fail_on=["griffe"], fail_on_unavailable=False)
        result = _run(repo, "griffe", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert (
            "warning: griffe check was configured to gate the run but could not run"
            in result.stderr
        )


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
                "configured_gate": False,
            }
        ]

    def test_stderr_reports_no_error_and_no_warning(self, repo, tmp_path):
        _write_config(repo, fail_on=["enrichment"])
        result = _run(repo, "check", "--all", env=_hide_griffe(tmp_path))
        assert result.returncode == 0
        assert "error:" not in result.stderr
        assert "warning: griffe" not in result.stderr

    def test_default_does_not_block_a_check_outside_fail_on(self, repo, tmp_path):
        _write_config(repo, fail_on=["enrichment"])
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
        _write_config(repo, fail_on=["griffe"])
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
        _write_config(
            repo,
            fail_on=["presence"],
            presence_enabled=False,
            fail_on_unavailable=False,
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == [
            {
                "check": "presence",
                "reason": "disabled by configuration, so its fail-on gate never ran",
                "remedy": (
                    "set enabled = true under [tool.docvet.presence], or drop"
                    " presence from fail-on"
                ),
                "blocking": False,
                "configured_gate": True,
            }
        ]
        assert (
            "presence (disabled by configuration, so its fail-on gate never ran)"
            in run["exit_reason"]
        )
        assert "no check in fail-on was unavailable" not in run["exit_reason"]

    def test_default_fails_the_run(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(repo, fail_on=["presence"], presence_enabled=False)
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert (
            "presence (disabled by configuration, so its fail-on gate never ran)"
            in run["exit_reason"]
        )
        assert run["unavailable_checks"][0]["blocking"] is True

    def test_warning_survives_quiet_on_the_opt_out_path(self, repo):
        _write_config(
            repo,
            fail_on=["presence"],
            presence_enabled=False,
            fail_on_unavailable=False,
        )
        result = _run(repo, "--quiet", "check", "--all")
        assert result.returncode == 0
        assert (
            "warning: presence check was configured to gate the run but could not run"
            " (disabled by configuration, so its fail-on gate never ran),"
            " so that gate never executed" in result.stderr
        )
        assert "set enabled = true under [tool.docvet.presence]" in result.stderr

    def test_disabled_presence_outside_fail_on_is_an_ordinary_opt_out(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(repo, fail_on=["enrichment"], presence_enabled=False)
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == []

    def test_enabled_presence_gate_is_never_reported_unavailable(self, repo):
        _write_config(repo, fail_on=["presence"], presence_enabled=True)
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        assert _run_block(result)["unavailable_checks"] == []


class TestDisabledPresenceWithCoverageFloor:
    """A ``min-coverage`` floor gates the run without using ``fail-on``."""

    @staticmethod
    def _add_undocumented_symbol(repo) -> None:
        """Give the presence check something it would have flagged."""
        (repo / "src" / "bare.py").write_text("def helper(x):\n    return x\n")

    def test_unmeasured_floor_is_reported_instead_of_a_clean_pass(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo,
            fail_on=["enrichment"],
            presence_enabled=False,
            min_coverage=95.0,
            fail_on_unavailable=False,
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        run = _run_block(result)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == [
            {
                "check": "presence",
                "reason": (
                    "disabled by configuration, so the 95.0% min-coverage"
                    " floor was never measured"
                ),
                "remedy": (
                    "set enabled = true under [tool.docvet.presence], or drop"
                    " min-coverage"
                ),
                "blocking": False,
                "configured_gate": True,
            }
        ]
        assert "95.0% min-coverage floor was never measured" in run["exit_reason"]

    def test_default_fails_the_run_without_presence_in_fail_on(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo, fail_on=["enrichment"], presence_enabled=False, min_coverage=95.0
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert "95.0% min-coverage floor was never measured" in run["exit_reason"]
        assert run["exit_reason"].startswith(
            "checks configured to gate the run could not run:"
        )
        assert "fail-on" not in run["exit_reason"]

    def test_no_floor_and_no_fail_on_entry_stays_an_ordinary_opt_out(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo, fail_on=["enrichment"], presence_enabled=False, min_coverage=0.0
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 0
        assert _run_block(result)["unavailable_checks"] == []

    def test_enabled_presence_measures_the_floor_and_fails_below_it(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo, fail_on=["enrichment"], presence_enabled=True, min_coverage=95.0
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "findings"
        assert "below the 95.0% threshold" in run["exit_reason"]
        assert run["unavailable_checks"] == []


class TestBlockedRunWithFindings:
    """A blocked run names the findings it also has."""

    def test_exit_reason_names_the_gate_and_the_findings(self, repo):
        _write_config(repo, fail_on=["griffe", "enrichment"], docstring_style="sphinx")
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
        payload = json.loads(result.stdout)
        run = payload["run"]
        assert run["status"] == "unavailable"
        assert "griffe (incompatible with sphinx docstring style)" in run["exit_reason"]
        assert (
            "checks configured in fail-on also have findings: enrichment"
            in run["exit_reason"]
        )
        assert payload["summary"]["total"] > 0

    def test_blocked_run_names_only_the_gate_when_no_fail_on_check_has_findings(
        self, repo
    ):
        _write_config(repo, fail_on=["griffe"], docstring_style="sphinx")
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert "griffe (incompatible with sphinx docstring style)" in run["exit_reason"]
        assert "also have findings" not in run["exit_reason"]


class TestPresenceGatedTwice:
    """Both presence gates configured must yield one complete remedy."""

    @staticmethod
    def _add_undocumented_symbol(repo) -> None:
        """Give the presence check something it would have flagged."""
        (repo / "src" / "bare.py").write_text("def helper(x):\n    return x\n")

    _BOTH_GATES_REMEDY = (
        "set enabled = true under [tool.docvet.presence], or drop both"
        " min-coverage and presence from fail-on"
    )

    def test_record_names_both_gates_and_both_actions(self, repo):
        self._add_undocumented_symbol(repo)
        _write_config(
            repo, fail_on=["presence"], presence_enabled=False, min_coverage=100.0
        )
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        run = _run_block(result)
        assert run["status"] == "unavailable"
        assert run["unavailable_checks"] == [
            {
                "check": "presence",
                "reason": (
                    "disabled by configuration, so the 100.0% min-coverage floor"
                    " was never measured and its fail-on gate never ran"
                ),
                "remedy": self._BOTH_GATES_REMEDY,
                "blocking": True,
                "configured_gate": True,
            }
        ]

    def test_remedy_is_printed_on_the_blocking_error(self, repo):
        _write_config(
            repo, fail_on=["presence"], presence_enabled=False, min_coverage=100.0
        )
        result = _run(repo, "check", "--all")
        assert result.returncode == 1
        assert f"  remedy: {self._BOTH_GATES_REMEDY}\n" in result.stderr

    def test_remedy_is_printed_on_the_opt_out_path_warning(self, repo):
        _write_config(
            repo,
            fail_on=["presence"],
            presence_enabled=False,
            min_coverage=100.0,
            fail_on_unavailable=False,
        )
        result = _run(repo, "check", "--all")
        assert result.returncode == 0
        assert f"  remedy: {self._BOTH_GATES_REMEDY}\n" in result.stderr

    def test_following_the_remedy_unblocks_the_run(self, repo):
        """Dropping both named settings must pass, not fail differently."""
        self._add_undocumented_symbol(repo)
        _write_config(
            repo, fail_on=["presence"], presence_enabled=False, min_coverage=100.0
        )
        blocked = _run(repo, "--format", "json", "check", "--all")
        assert blocked.returncode == 1
        assert _run_block(blocked)["unavailable_checks"][0]["remedy"] == (
            self._BOTH_GATES_REMEDY
        )

        _write_config(repo, fail_on=[], presence_enabled=False)
        after = _run(repo, "--format", "json", "check", "--all")
        assert after.returncode == 0
        run = _run_block(after)
        assert run["status"] == "passed"
        assert run["unavailable_checks"] == []

    def test_dropping_only_min_coverage_still_reports_the_fail_on_gate(self, repo):
        """The remedy never offers an action that leaves a gate in place."""
        self._add_undocumented_symbol(repo)
        _write_config(repo, fail_on=["presence"], presence_enabled=False)
        result = _run(repo, "--format", "json", "check", "--all")
        assert result.returncode == 1
        remedy = _run_block(result)["unavailable_checks"][0]["remedy"]
        assert remedy.endswith("or drop presence from fail-on")
        assert "min-coverage" not in remedy
