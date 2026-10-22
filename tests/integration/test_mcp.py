"""Integration tests for the docvet MCP server.

End-to-end tests that spawn the MCP server via the ``mcp`` client SDK,
call tools, and verify responses match expectations. Each test uses its
own ``tmp_path`` with an isolated ``pyproject.toml`` to prevent config
walkup from finding the project root's config.

Examples:
    Run integration tests only:

    ```bash
    uv run pytest tests/integration/test_mcp.py -v
    ```
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

mcp_pkg = pytest.importorskip("mcp")

from mcp import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.skipif(
        sys.platform == "win32",
        reason="MCP stdio_client subprocess cleanup unreliable on Windows",
    ),
]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SERVER_TIMEOUT = 30.0


@pytest.fixture()
def isolated_project(tmp_path: Path) -> Path:
    """Create a tmp directory with a pyproject.toml for config isolation."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\nname = 'test-mcp'\n\n[tool.docvet]\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def undocumented_file(isolated_project: Path) -> Path:
    """Create a Python file with docstring issues for multi-check coverage."""
    p = isolated_project / "bad.py"
    p.write_text(
        textwrap.dedent('''\
        def foo():
            pass


        def bar():
            """Do something."""
            raise ValueError("bad")
        '''),
        encoding="utf-8",
    )
    return p


@pytest.fixture()
def documented_file(isolated_project: Path) -> Path:
    """Create a well-documented Python file that produces zero findings."""
    p = isolated_project / "good.py"
    p.write_text(
        textwrap.dedent('''\
        """Module docstring.

        Examples:
            Usage:

            ```python
            import good
            ```

        See Also:
            [`builtins`][]: Python builtins.
        """

        from __future__ import annotations


        def greet(name: str) -> str:
            """Return a greeting.

            Args:
                name: The name to greet.

            Returns:
                A greeting string.

            Examples:
                Basic usage:

                ```python
                greet("world")
                ```

            See Also:
                [`builtins.print`][]: Print to stdout.
            """
            return f"Hello, {name}"
        '''),
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _docvet_executable() -> str:
    """Return the path to the docvet console script in the active venv."""
    return str(Path(sys.executable).parent / "docvet")


def _server_params() -> StdioServerParameters:
    """Build StdioServerParameters for the docvet MCP server."""
    return StdioServerParameters(command=_docvet_executable(), args=["mcp"])


async def _call_tool(
    session: ClientSession,
    name: str,
    arguments: dict | None = None,
) -> dict:
    """Call an MCP tool and parse the JSON response."""
    result = await asyncio.wait_for(
        session.call_tool(name, arguments=arguments or {}),
        timeout=_SERVER_TIMEOUT,
    )
    content_block = result.content[0]
    return json.loads(content_block.text)  # ty: ignore[unresolved-attribute]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("optout", [False, True])
@pytest.mark.parametrize("case", ["ownership", "nonrepository", "missing", "healthy"])
def test_freshness_prerequisite_cli_mcp_parity(isolated_project, case, optout):
    """Real processes report identical prerequisites without changing Git trust."""
    root = isolated_project
    target = root / "a.py"
    target.write_text('"""Module."""\n', encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[tool.docvet]\nfail-on=["freshness"]\n'
        f"fail-on-unavailable={str(not optout).lower()}\n",
        encoding="utf-8",
    )
    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR")
        if key in os.environ
    }
    env["GIT_CEILING_DIRECTORIES"] = str(root.parent)
    if case in {"ownership", "healthy"}:
        subprocess.run(["git", "init", "-q"], cwd=root, env=env, check=True)
        subprocess.run(["git", "add", "."], cwd=root, env=env, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-qm",
                "initial",
            ],
            cwd=root,
            env=env,
            check=True,
        )
    config_path = root / ".git" / "config"
    config_before = config_path.read_bytes() if config_path.exists() else None
    if case == "ownership":
        env.update(
            GIT_TEST_ASSUME_DIFFERENT_OWNER="1",
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="safe.directory",
            GIT_CONFIG_VALUE_0="",
            LC_ALL="C",
        )
        probe = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert probe.returncode != 0
        assert "dubious ownership" in probe.stderr
    elif case == "missing":
        env["PATH"] = str(root / "no-bin")

    cli_args = [
        _docvet_executable(),
        "--format",
        "json",
        "freshness",
        str(target),
    ]
    cli = subprocess.run(
        cli_args,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    cli_run = json.loads(cli.stdout)["run"]

    async def call():
        params = StdioServerParameters(
            command=_docvet_executable(), args=["mcp"], env=env, cwd=str(root)
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            return await _call_tool(
                session,
                "docvet_check",
                {"path": str(target), "checks": ["freshness"]},
            )

    response = asyncio.run(asyncio.wait_for(call(), timeout=_SERVER_TIMEOUT))
    assert response["run"] == cli_run
    assert cli.returncode == int(case != "healthy" and not optout)
    assert cli_run["status"] == (
        "unavailable" if case != "healthy" and not optout else "passed"
    )
    if case == "healthy":
        assert cli_run["unavailable_checks"] == []
        assert response["summary"]["files_analyzed"] == 1
    else:
        unavailable = cli_run["unavailable_checks"][0]
        expected = {
            "ownership": "dubious ownership",
            "nonrepository": "not a git repository",
            "missing": "not installed",
        }[case]
        assert expected in unavailable["reason"]
        assert response["errors"] == [unavailable["reason"]]
        assert unavailable["configured_gate"] is True
        assert unavailable["blocking"] is (not optout)
        # MCP preloads valid source before dispatch; unavailable is reported
        # by the run record, not inferred from the source-analysis count.
        assert response["summary"]["files_analyzed"] == 1
        terminal = subprocess.run(
            [_docvet_executable(), "freshness", str(target)],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert terminal.returncode == cli.returncode
        assert unavailable["reason"] in terminal.stderr
        assert unavailable["remedy"] in terminal.stderr
    assert (config_path.read_bytes() if config_path.exists() else None) == config_before


class TestDocvetCheck:
    """End-to-end tests for the docvet_check MCP tool."""

    def test_returns_findings_and_summary(self, undocumented_file: Path):
        """3.2: docvet_check returns findings and summary keys."""

        async def _run():
            async with (
                stdio_client(_server_params()) as (read, write),
                ClientSession(read, write) as session,
            ):
                await asyncio.wait_for(session.initialize(), timeout=_SERVER_TIMEOUT)
                return await _call_tool(
                    session,
                    "docvet_check",
                    {"path": str(undocumented_file.parent)},
                )

        content = asyncio.run(_run())
        assert "findings" in content
        assert "summary" in content
        assert content["summary"]["total"] > 0

    def test_well_documented_file_returns_zero_findings(self, documented_file: Path):
        """3.6: docvet_check on a well-documented file returns zero findings."""

        async def _run():
            async with (
                stdio_client(_server_params()) as (read, write),
                ClientSession(read, write) as session,
            ):
                await asyncio.wait_for(session.initialize(), timeout=_SERVER_TIMEOUT)
                return await _call_tool(
                    session,
                    "docvet_check",
                    {"path": str(documented_file.parent)},
                )

        content = asyncio.run(_run())
        assert content["summary"]["total"] == 0
        assert content["findings"] == []

    def test_explicit_checks_parameter(self, undocumented_file: Path):
        """3.7: docvet_check with explicit checks parameter filters results."""

        async def _run():
            async with (
                stdio_client(_server_params()) as (read, write),
                ClientSession(read, write) as session,
            ):
                await asyncio.wait_for(session.initialize(), timeout=_SERVER_TIMEOUT)
                return await _call_tool(
                    session,
                    "docvet_check",
                    {
                        "path": str(undocumented_file.parent),
                        "checks": ["presence"],
                    },
                )

        content = asyncio.run(_run())
        assert "findings" in content
        assert "presence_coverage" in content
        # All findings should be from the presence check
        for finding in content["findings"]:
            assert finding["rule"] == "missing-docstring"


class TestDocvetRules:
    """End-to-end tests for the docvet_rules MCP tool."""

    def test_returns_all_32_rules(self):
        """3.3: docvet_rules returns all 32 rules with required fields."""

        async def _run():
            async with (
                stdio_client(_server_params()) as (read, write),
                ClientSession(read, write) as session,
            ):
                await asyncio.wait_for(session.initialize(), timeout=_SERVER_TIMEOUT)
                return await _call_tool(session, "docvet_rules")

        content = asyncio.run(_run())
        assert "rules" in content
        rules = content["rules"]
        assert len(rules) == 32

        for rule in rules:
            assert "name" in rule
            assert "check" in rule
            assert "description" in rule
            assert "category" in rule


class TestResponseParity:
    """Verify MCP response matches CLI JSON output."""

    def test_findings_match_cli_json(self, undocumented_file: Path):
        """3.4: MCP findings match CLI --format json output."""
        project_dir = undocumented_file.parent

        # Run CLI JSON output (--format is a global option before subcommand)
        cli_result = subprocess.run(
            [
                _docvet_executable(),
                "--format",
                "json",
                "check",
                "--all",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(project_dir),
        )
        cli_data = json.loads(cli_result.stdout)

        # Run MCP check
        async def _run():
            async with (
                stdio_client(_server_params()) as (read, write),
                ClientSession(read, write) as session,
            ):
                await asyncio.wait_for(session.initialize(), timeout=_SERVER_TIMEOUT)
                return await _call_tool(
                    session,
                    "docvet_check",
                    {"path": str(project_dir)},
                )

        mcp_data = asyncio.run(_run())

        # Compare by (rule, symbol, message) tuples — ignore file (path
        # format differs: MCP absolute vs CLI relative)
        cli_tuples = {
            (f["rule"], f["symbol"], f["message"])
            for f in cli_data["findings"]
            # Exclude freshness findings from CLI (MCP excludes by default)
            if not f["rule"].startswith("stale-")
        }
        mcp_tuples = {
            (f["rule"], f["symbol"], f["message"]) for f in mcp_data["findings"]
        }
        assert mcp_tuples == cli_tuples

        # Compare summary totals (excluding freshness from CLI count)
        cli_non_freshness_total = sum(
            1 for f in cli_data["findings"] if not f["rule"].startswith("stale-")
        )
        assert mcp_data["summary"]["total"] == cli_non_freshness_total

        # Verify summary.by_check is present and internally consistent
        # (CLI JSON doesn't include by_check, so validate against findings)
        mcp_by_check = mcp_data["summary"]["by_check"]
        assert isinstance(mcp_by_check, dict)
        assert sum(mcp_by_check.values()) == mcp_data["summary"]["total"]


class TestCleanShutdown:
    """Verify server shuts down cleanly when client disconnects."""

    def test_server_terminates_on_client_disconnect(self):
        """3.5: Server shuts down cleanly when client disconnects."""

        async def _run():
            async with (
                stdio_client(_server_params()) as (read, write),
                ClientSession(read, write) as session,
            ):
                await asyncio.wait_for(session.initialize(), timeout=_SERVER_TIMEOUT)
                # Call a tool to confirm server is working
                await _call_tool(session, "docvet_rules")
                # Session and client exit cleanly via context managers
            # If we get here without error, the server shut down cleanly
            return True

        # Outer timeout covers context-manager exit (subprocess teardown),
        # which has no per-operation wait_for.  Use 2x to avoid false kills
        # when initialize() + call_tool() each consume part of _SERVER_TIMEOUT.
        assert (
            asyncio.run(asyncio.wait_for(_run(), timeout=2 * _SERVER_TIMEOUT)) is True
        )
