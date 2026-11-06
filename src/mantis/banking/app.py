import asyncio
import os
import sys
from pathlib import Path

from google.adk.apps import App

from .agents.root import build_root_agent
from .infra.bootstrap import bootstrap_runtime

bootstrap_runtime()


def create_app(mcp_session=None, mcp_tools=None, enable_aml: bool = False):
    """Build the native ADK App."""
    root_agent = build_root_agent(mcp_session=mcp_session, mcp_tools=mcp_tools, enable_aml=enable_aml)
    plugins = []

    # Current ADK exposes App.plugins. If an older compatible ADK release does
    # not, runner.py falls back to the legacy Runner(plugins=...) path.
    try:
        app = App(name="citi_banking_adk", root_agent=root_agent, plugins=plugins)
        object.__setattr__(app, "_mantis_configured_plugins", plugins)
        return app
    except Exception as exc:
        # Only use the compatibility path when plugin construction is unsupported
        # by the installed ADK App model. Preserve all other errors.
        text = str(exc).lower()
        if plugins and ("plugins" in text or "extra" in text or "unexpected" in text):
            app = App(name="citi_banking_adk", root_agent=root_agent)
            object.__setattr__(app, "_mantis_configured_plugins", plugins)
            return app
        raise


async def _create_app_with_mcp_async(enable_aml: bool) -> App:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_path = Path.cwd() / "citi_banking_mcp_server" / "mcp_server.py"
    if not server_path.exists():
        server_path = Path.cwd().parent / "citi_banking_mcp_server" / "mcp_server.py"
    if not server_path.exists():
        # zt-adk build runs with CWD=extensions/zero_trust/, not the repo
        # root the CLI assumes -- fall back to a path relative to this
        # file, which is always src/mantis/banking/app.py in the repo.
        server_path = Path(__file__).resolve().parents[3] / "citi_banking_mcp_server" / "mcp_server.py"
    server_params = StdioServerParameters(
        command=sys.executable, args=[str(server_path)], env=os.environ.copy()
    )
    # errlog=sys.__stderr__ (the real OS stderr Python saves at startup),
    # not stdio_client's own default of sys.stderr: under pytest's output
    # capture (the whole suite, not a single file run standalone), the
    # *current* sys.stderr is a capture object with no real file
    # descriptor, and the subprocess spawn's errwrite = stderr.fileno()
    # raises io.UnsupportedOperation -- sys.__stderr__ always has one.
    async with stdio_client(server_params, errlog=sys.__stderr__) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            return create_app(mcp_session=session, mcp_tools=tools_response.tools, enable_aml=enable_aml)


def create_app_for_scan():
    """Zero-arg entry point for extensions/zero_trust/zt_adk.yaml: builds
    the app the same way a live `mantis --run` does (cli/main.py's
    run_experiment), with a real MCP session/tools -- not the bare
    create_app() every other caller here uses. Needed because
    build_root_agent attaches one extra passthrough tool per MCP tool
    directly onto user_proxy_agent only when a real session is given (see
    its own mcp_session branch); scanning with mcp_session=None produces a
    structurally different graph (a different fingerprint) than any real
    run ever has, so a bundle built that way is StaleBundleError'd by
    every real run, not just a hypothetical drifted one. The MCP session
    closes when this returns -- fine for zt-adk's discovery, which only
    inspects each tool wrapper's __name__/__doc__, never calls one."""
    return asyncio.run(_create_app_with_mcp_async(enable_aml=False))


def create_app_with_aml_for_scan():
    """create_app_for_scan's counterpart for extensions/zero_trust/zt_adk_aml.yaml
    -- the AML-enabled bundle's zero-arg entry point (see create_app_for_scan's
    own docstring for why a real MCP session is needed at scan time)."""
    return asyncio.run(_create_app_with_mcp_async(enable_aml=True))
