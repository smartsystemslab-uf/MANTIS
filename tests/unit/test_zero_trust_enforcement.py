"""Zero Trust Backplane enforcement plugin (toggleable integration of the
real github.com/smartsystemslab-uf/Citi_P3_Zero_Trust_Backplane project --
see src/mantis/plugins/policies/zero_trust_enforcement.py).

Entirely offline: the real PDP's HTTP calls (httpx.post) are mocked here,
so these tests need neither the zero_trust optional dependency's PDP
service running nor a live model/backend -- they check the plugin's own
dispatch logic (which stage/target it acts on, how it maps a decision to
HookResult, and that it fails closed), not the real project's own
authorization logic (which is its own code, exercised live and manually --
see extensions/zero_trust/README.md -- not reimplemented or re-tested
here). Skipped entirely if the optional dependency isn't installed, same
as the other optional-dependency exporter tests in this suite.
"""
import pytest

pytest.importorskip("zt_backplane")

from unittest.mock import patch, MagicMock

from mantis.core.registry import plugin_registry
from mantis.hooks import HookContext, HookAction
from mantis.plugins.policies.zero_trust_enforcement import ZeroTrustEnforcementPlugin


def _ctx(target="get_transaction_context", source="transaction_monitoring_agent", hook="before_tool"):
    return HookContext(
        run_id="r1", trace_id="t1", workflow_id="front_office_monitoring", stage="tool",
        source=source, target=target, payload={}, metadata={"specific_hook": hook},
    )


def test_registered_in_the_real_plugin_registry():
    assert "zero_trust_enforcement" in plugin_registry.all()
    assert plugin_registry.get("zero_trust_enforcement") is ZeroTrustEnforcementPlugin


def test_ignores_stages_other_than_before_tool():
    plugin = ZeroTrustEnforcementPlugin()
    with patch("httpx.post") as mock_post:
        result = plugin.apply(_ctx(hook="after_tool"))
    assert result.action == HookAction.CONTINUE
    mock_post.assert_not_called()


def test_out_of_scope_target_is_never_checked():
    """transfer_to_agent is the routing tool, not a domain-owned resource --
    see the module docstring for why risk_aware_routing_guard covers it
    instead. The PDP is never even called for it."""
    plugin = ZeroTrustEnforcementPlugin()
    with patch("httpx.post") as mock_post:
        result = plugin.apply(_ctx(target="transfer_to_agent"))
    assert result.action == HookAction.CONTINUE
    mock_post.assert_not_called()


def test_unknown_agent_denies_without_calling_the_pdp():
    plugin = ZeroTrustEnforcementPlugin()
    with patch("httpx.post") as mock_post:
        result = plugin.apply(_ctx(source="not_a_real_mantis_agent"))
    assert result.action == HookAction.DENY
    assert "not a known MANTIS agent" in result.payload["error"]
    mock_post.assert_not_called()


def test_allow_decision_continues():
    plugin = ZeroTrustEnforcementPlugin()
    challenge_resp = MagicMock(status_code=200)
    challenge_resp.json.return_value = {"nonce": "n1"}
    authorize_resp = MagicMock()
    authorize_resp.json.return_value = {"decision": "ALLOW", "reason": "matched_policy:x"}
    with patch("httpx.post", side_effect=[challenge_resp, authorize_resp]):
        result = ZeroTrustEnforcementPlugin().apply(_ctx())
    assert result.action == HookAction.CONTINUE


def test_allow_with_obligations_also_continues():
    plugin = ZeroTrustEnforcementPlugin()
    challenge_resp = MagicMock(status_code=200)
    challenge_resp.json.return_value = {"nonce": "n1"}
    authorize_resp = MagicMock()
    authorize_resp.json.return_value = {"decision": "ALLOW_WITH_OBLIGATIONS", "reason": "matched_policy:x"}
    with patch("httpx.post", side_effect=[challenge_resp, authorize_resp]):
        result = plugin.apply(_ctx())
    assert result.action == HookAction.CONTINUE


def test_deny_decision_denies():
    challenge_resp = MagicMock(status_code=200)
    challenge_resp.json.return_value = {"nonce": "n1"}
    authorize_resp = MagicMock()
    authorize_resp.json.return_value = {"decision": "DENY", "reason": "default_deny_no_matching_policy"}
    with patch("httpx.post", side_effect=[challenge_resp, authorize_resp]):
        result = ZeroTrustEnforcementPlugin().apply(_ctx())
    assert result.action == HookAction.DENY
    assert "default_deny_no_matching_policy" in result.payload["error"]


def test_unrecognized_subject_at_challenge_stage_denies():
    challenge_resp = MagicMock(status_code=404)
    with patch("httpx.post", return_value=challenge_resp):
        result = ZeroTrustEnforcementPlugin().apply(_ctx())
    assert result.action == HookAction.DENY


def test_pdp_unreachable_fails_closed():
    """A down security layer must deny, not silently allow."""
    import httpx
    with patch("httpx.post", side_effect=httpx.ConnectError("refused")):
        result = ZeroTrustEnforcementPlugin().apply(_ctx())
    assert result.action == HookAction.DENY
    assert "PDP unavailable" in result.payload["error"]
