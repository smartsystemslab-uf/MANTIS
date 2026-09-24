"""Post-Paper Extension: security mechanism plugins (coding plan §11) --
the rate-limit category. Logic in isolation, registration, window expiry with
a controlled clock, per-argument grouping, and the real HookBus with a live
attack plugin registered ahead of it."""
import pytest

from mantis.core.registry import plugin_registry
from mantis.hooks import HookAction, HookBus, HookContext
from mantis.plugins.attacks.route_confusion import RouteConfusionPlugin
from mantis.plugins.policies import rate_limit_guardrail as rl
from mantis.plugins.policies.rate_limit_guardrail import RateLimitGuardrailPlugin


def ctx(target, payload=None, hook="before_tool"):
    return HookContext(run_id="t", trace_id="t", workflow_id="t", stage="tool", target=target,
                       payload=payload or {}, metadata={"specific_hook": hook})


def test_registered():
    assert plugin_registry.get("rate_limit_guardrail") is RateLimitGuardrailPlugin


def test_rejects_a_non_positive_limit():
    with pytest.raises(ValueError):
        RateLimitGuardrailPlugin(max_calls=0)


def test_allows_up_to_the_limit_then_denies():
    p = RateLimitGuardrailPlugin(target_tool="execute_transfer", max_calls=2)
    assert p.apply(ctx("execute_transfer")).action == HookAction.CONTINUE
    assert p.apply(ctx("execute_transfer")).action == HookAction.CONTINUE
    res = p.apply(ctx("execute_transfer"))
    assert res.action == HookAction.DENY
    assert "blocked by rate_limit_guardrail" in res.payload["error"] and "limit 2" in res.payload["error"]


def test_ignores_other_tools_and_non_before_tool_hooks():
    p = RateLimitGuardrailPlugin(target_tool="execute_transfer", max_calls=1)
    for _ in range(5):
        assert p.apply(ctx("search_policies")).action == HookAction.CONTINUE
        assert p.apply(ctx("execute_transfer", hook="after_tool")).action == HookAction.CONTINUE
    assert p.apply(ctx("execute_transfer")).action == HookAction.CONTINUE


def test_without_a_target_tool_every_tool_is_counted_separately():
    p = RateLimitGuardrailPlugin(max_calls=1)
    assert p.apply(ctx("get_customer_context")).action == HookAction.CONTINUE
    assert p.apply(ctx("search_policies")).action == HookAction.CONTINUE
    assert p.apply(ctx("get_customer_context")).action == HookAction.DENY


def test_window_expiry_frees_the_budget(monkeypatch):
    clock = {"t": 100.0}
    monkeypatch.setattr(rl, "_now", lambda: clock["t"])
    p = RateLimitGuardrailPlugin(target_tool="execute_transfer", max_calls=1, window_seconds=10)
    assert p.apply(ctx("execute_transfer")).action == HookAction.CONTINUE
    clock["t"] = 105.0
    assert p.apply(ctx("execute_transfer")).action == HookAction.DENY
    clock["t"] = 111.0  # first call is now older than the window
    assert p.apply(ctx("execute_transfer")).action == HookAction.CONTINUE


def test_group_by_counts_each_argument_value_separately():
    p = RateLimitGuardrailPlugin(target_tool="transfer_to_agent", group_by="agent_name", max_calls=1)
    assert p.apply(ctx("transfer_to_agent", {"agent_name": "front_office_router"})).action == HookAction.CONTINUE
    assert p.apply(ctx("transfer_to_agent", {"agent_name": "front_office_transaction_workflow"})).action == HookAction.CONTINUE
    res = p.apply(ctx("transfer_to_agent", {"agent_name": "front_office_router"}))
    assert res.action == HookAction.DENY and "front_office_router" in res.payload["error"]


def test_a_normal_hand_off_chain_never_trips_a_per_destination_limit():
    """No false positive on ordinary traffic: each destination is visited once."""
    p = RateLimitGuardrailPlugin(target_tool="transfer_to_agent", group_by="agent_name", max_calls=1)
    for dest in ["front_office_router", "mid_office_router", "loan_preapproval_agent"]:
        assert p.apply(ctx("transfer_to_agent", {"agent_name": dest})).action == HookAction.CONTINUE


def test_stops_a_route_hijack_loop_through_the_real_hook_bus():
    """The motivating case: the hijack rewrites every hand-off to
    front_office_router, including the downstream router's corrective
    hand-back, producing a self-transfer the framework rejects. The limiter
    sees the *rewritten* destination (it is registered after the attack) and
    denies the second attempt."""
    bus = HookBus()
    bus.register(RouteConfusionPlugin(intercepted_route="front_office_router", forced_destination="back_office_router"))
    bus.register(RateLimitGuardrailPlugin(target_tool="transfer_to_agent", group_by="agent_name", max_calls=1))
    first = bus.dispatch("before_tool", ctx("transfer_to_agent", {"agent_name": "front_office_router"}))
    assert first.action == HookAction.MUTATE and first.payload["agent_name"] == "back_office_router"
    second = bus.dispatch("before_tool", ctx("transfer_to_agent", {"agent_name": "front_office_router"}))
    assert second.action == HookAction.DENY
    assert "blocked by rate_limit_guardrail" in second.payload["error"]
