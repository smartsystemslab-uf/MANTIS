"""Zero Trust Backplane enforcement plugin (toggleable integration of the
real github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane project --
see src/mantis/plugins/policies/zero_trust_enforcement.py).

Entirely offline and genuinely real, not mocked: build_zero_trust_plugin()
loads the actual committed, signed bundle and the plugin's own decision
engine, so these tests exercise the real project's own authorization
decisions (not reimplemented or re-tested here) directly, with no live
model/backend and no network call -- `before_tool_callback` reads its
caller from a plain `tool_context.agent_name` attribute (see
`ZeroTrustPlugin._tool_owner`), so a MagicMock stands in for ADK's own
object without needing a full Runner/session. Skipped entirely if the
optional dependency isn't installed, same as the other optional-dependency
exporter tests in this suite.

Finding worth stating plainly: the new generic scanner's placements are
per-agent (which agent's own `tools=[]` list the tool is actually wired
into), not per-domain -- *stricter* than the old integration's "agent may
act on a tool in its own domain" claim, which was a domain-wide grant.
test_same_domain_sibling_agent_without_the_tool_is_still_denied below is
exactly that: same domain, different agent, no access. Cross-domain denial
(the old claim) still holds -- it's a strict consequence of per-agent
placement, just not the only boundary enforced now.
"""
import asyncio
from unittest.mock import MagicMock

import pytest

pytest.importorskip("zt_adk")

from mantis.banking.app import create_app_for_scan
from mantis.plugins.policies.zero_trust_enforcement import build_zero_trust_plugin


def _tool_ctx(agent_name, call_id="c1", inv="inv1"):
    tc = MagicMock()
    tc.agent_name = agent_name
    tc.invocation_id = inv
    tc.function_call_id = call_id
    tc.node_path = ""
    return tc


def _tool(name):
    t = MagicMock()
    t.name = name
    return t


@pytest.fixture(scope="module")
def plugin():
    # create_app_for_scan(), not create_app(): the committed bundle is
    # built against a real MCP session (build_root_agent attaches one
    # extra passthrough tool per MCP tool onto user_proxy_agent only then
    # -- see create_app_for_scan's docstring), so matching it here means
    # spawning the real MCP server subprocess, the same as a live run.
    app = create_app_for_scan()
    return build_zero_trust_plugin(app.root_agent)


def _call(plugin, agent_name, tool_name, tool_args=None, inv="inv"):
    return asyncio.run(plugin.before_tool_callback(
        tool=_tool(tool_name), tool_args=tool_args or {},
        tool_context=_tool_ctx(agent_name, inv=inv),
    ))


def test_an_agent_calling_its_own_real_tool_is_allowed(plugin):
    # compliance_agent/search_policies is a real placement (see
    # extensions/zero_trust/.zt/bundle/REPORT.md) -- None means ADK proceeds
    # to call the real tool.
    assert _call(plugin, "compliance_agent", "search_policies", inv="allow") is None


def test_cross_domain_call_is_denied(plugin):
    # transaction_monitoring_agent is front office; get_eod_batch belongs to
    # eod_processing_agent, back office.
    result = _call(plugin, "transaction_monitoring_agent", "get_eod_batch", inv="cross")
    assert result is not None
    assert result["status"] == "zero_trust_denied"
    assert result["decision"] == "DENY"


def test_same_domain_sibling_agent_without_the_tool_is_still_denied(plugin):
    # fraud_detection_agent is front office, same domain as compliance_agent
    # (search_policies' real owner) -- but never wired to call it. Per-agent
    # placement denies this even though a domain-wide grant would not.
    result = _call(plugin, "fraud_detection_agent", "search_policies", inv="sibling")
    assert result is not None
    assert result["status"] == "zero_trust_denied"
    assert result["decision"] == "DENY"


def test_unrecognized_agent_is_denied(plugin):
    result = _call(plugin, "not_a_real_mantis_agent", "get_eod_batch", inv="unknown")
    assert result is not None
    assert result["status"] == "zero_trust_denied"
    assert result["decision"] == "DENY"


def test_transfer_to_agent_routing_is_unconstrained_by_this_toggle(plugin):
    # transfer_to_agent is deliberately out of scope for this toggle's
    # profile (policies.deny_cross_domain_routes: false in zt_adk.yaml) --
    # MANTIS's own agent tree uses legitimate cross-domain routing (e.g.
    # back_office_router handing off to front_office_router) as normal
    # behavior, and risk_aware_routing_guard already covers routing
    # decisions. See zero_trust_enforcement.py's module docstring.
    result = _call(plugin, "front_office_router", "transfer_to_agent",
                    tool_args={"agent_name": "mid_office_router"}, inv="transfer")
    assert result is None


def test_the_dedicated_toggle_validates(tmp_path, monkeypatch):
    from pathlib import Path

    from mantis.cli.main import validate_config

    cfg = tmp_path / "zt_toggle.yaml"
    cfg.write_text(
        "experiment:\n  name: zt_toggle_test\n  domain: front_office\n"
        "  workflow: front_office_monitoring\n  scenario: front_office_monitoring\n"
        "zero_trust:\n  enabled: true\n"
    )
    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    assert validate_config(str(cfg)) is True


def test_toggle_disabled_does_not_require_the_dependency_at_all(tmp_path, monkeypatch):
    """enabled: false must validate even if the dependency were somehow
    unavailable -- the whole point of a toggle is that off means off."""
    import mantis.core.registry as registry
    from mantis.cli.main import validate_config
    from pathlib import Path

    cfg = tmp_path / "zt_toggle_off.yaml"
    cfg.write_text(
        "experiment:\n  name: zt_toggle_off_test\n  domain: front_office\n"
        "  workflow: front_office_monitoring\n  scenario: front_office_monitoring\n"
        "zero_trust:\n  enabled: false\n"
    )
    monkeypatch.chdir(Path(__file__).resolve().parents[2])
    original = registry.ZERO_TRUST_AVAILABLE
    try:
        registry.ZERO_TRUST_AVAILABLE = False
        import mantis.cli.main as cli_main
        monkeypatch.setattr(cli_main, "ZERO_TRUST_AVAILABLE", False)
        assert validate_config(str(cfg)) is True
    finally:
        registry.ZERO_TRUST_AVAILABLE = original
