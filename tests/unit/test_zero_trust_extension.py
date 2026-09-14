"""Post-Paper Extension: Zero Trust Backplane (coding plan §11).

Covers extensions/zero_trust/ -- a package MANTIS's own code never
imports (see that directory's README for why). These tests import it
directly, the same way extensions/zero_trust/run_with_zero_trust.py does,
and verify both the policy generated from a real live inventory and the
enforcement plugin's actual DENY/CONTINUE behavior -- not just that
importing it doesn't raise.
"""
from mantis.hooks import HookContext, HookAction
from mantis.runtime.adapter import NativeBankingAdapter
from extensions.zero_trust.policy_generator import (
    generate_default_deny_policy,
    to_zt_manifest_subjects,
)
from extensions.zero_trust.enforcement_plugin import ZeroTrustEnforcementPlugin
from mantis.core.registry import plugin_registry


def create_ctx(target=None, source=None, payload=None):
    return HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage="tool", target=target, source=source, payload=payload or {},
        metadata={"specific_hook": "before_tool"},
    )


def test_self_registers_into_the_shared_plugin_registry():
    # Importing enforcement_plugin (done at module load, above) must have
    # already registered it -- this is the entire integration surface
    # run_with_zero_trust.py relies on.
    assert plugin_registry.get("zero_trust_enforcement") is ZeroTrustEnforcementPlugin


def test_policy_generated_from_real_live_inventory_covers_all_three_domains():
    policy = generate_default_deny_policy()
    assert set(policy["domains"].keys()) == {"front_office", "mid_office", "back_office"}
    for domain, data in policy["domains"].items():
        assert data["agents"], f"{domain} must have real agents from inventory()"
        assert data["allowed_tools"], f"{domain} must have real tools from inventory()"


def test_to_zt_manifest_subjects_uses_the_real_backplane_canonical_id_convention():
    subjects = to_zt_manifest_subjects()
    assert subjects, "must produce at least one subject from the live inventory"
    by_id = {s["id"]: s for s in subjects}
    inv = NativeBankingAdapter().inventory()
    front_office_agents = inv.domains["front_office"]["agents"]
    example_agent = front_office_agents[0]
    canonical_id = f"agent.front_office.{example_agent}"
    assert canonical_id in by_id
    assert by_id[canonical_id]["bindings"]["mantis"]["runtime_id"] == example_agent


def test_enforcement_plugin_allows_an_agents_own_domain_tool():
    plugin = ZeroTrustEnforcementPlugin()
    domain, data = next(iter(plugin.policy["domains"].items()))
    agent = data["agents"][0]
    tool = data["allowed_tools"][0]
    ctx = create_ctx(target=tool, source=agent)
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_enforcement_plugin_denies_cross_domain_tool_access():
    """The actual security property this slice demonstrates: an agent from
    one domain must not be able to call a tool exclusive to a different
    domain -- lateral movement across banking domains."""
    plugin = ZeroTrustEnforcementPlugin()
    mid_office_agent = plugin.policy["domains"]["mid_office"]["agents"][0]
    back_office_only_tools = (
        set(plugin.policy["domains"]["back_office"]["allowed_tools"])
        - set(plugin.policy["domains"]["mid_office"]["allowed_tools"])
        - set(plugin.policy["domains"]["front_office"]["allowed_tools"])
    )
    assert back_office_only_tools, "test needs at least one tool exclusive to back_office"
    target_tool = next(iter(back_office_only_tools))

    ctx = create_ctx(target=target_tool, source=mid_office_agent)
    res = plugin.apply(ctx)
    assert res.action == HookAction.DENY
    assert "not permitted to call" in res.payload["error"]


def test_enforcement_plugin_always_allows_routing():
    plugin = ZeroTrustEnforcementPlugin()
    ctx = create_ctx(target="transfer_to_agent", source="user_proxy_agent")
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_enforcement_plugin_denies_unrecognized_agent():
    plugin = ZeroTrustEnforcementPlugin()
    ctx = create_ctx(target="execute_transfer", source="some_agent_not_in_any_domain")
    res = plugin.apply(ctx)
    assert res.action == HookAction.DENY
    assert "not recognized" in res.payload["error"]
