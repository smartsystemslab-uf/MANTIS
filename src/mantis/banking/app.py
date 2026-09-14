from google.adk.apps import App

from .agents.root import build_root_agent
from .infra.bootstrap import bootstrap_runtime

bootstrap_runtime()


def create_app(mcp_session=None, mcp_tools=None):
    """Build the native ADK App."""
    root_agent = build_root_agent(mcp_session=mcp_session, mcp_tools=mcp_tools)
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
