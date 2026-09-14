"""Post-Paper Extension: security mechanism plugins (coding plan §11).

Covers the guardrail plugin's own logic in isolation, its registration,
and -- the actual point of a "defense evaluated through the same
framework" -- that it correctly DENIES a call the hook bus has already
threaded a prior plugin's mutation into, and that HookBus.dispatch()
still surfaces that DENY as the aggregate result while continuing to
dispatch to later plugins (ObservabilityPlugin) exactly as it does for an
attack plugin's DENY.
"""
from mantis.hooks import HookBus, HookContext, HookAction
from mantis.plugins.policies.amount_limit_guardrail import AmountLimitGuardrailPlugin
from mantis.plugins.attacks.tool_mutation import ToolParameterMutationPlugin
from mantis.core.registry import plugin_registry


def create_ctx(stage, specific_hook, target=None, source=None, payload=None):
    return HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage=stage, target=target, source=source, payload=payload or {},
        metadata={"specific_hook": specific_hook}
    )


def test_amount_limit_guardrail_registered():
    cls = plugin_registry.get("amount_limit_guardrail")
    assert cls is AmountLimitGuardrailPlugin


def test_denies_over_limit_amount():
    plugin = AmountLimitGuardrailPlugin(target_tool="execute_transfer", max_amount=2000.0)
    ctx = create_ctx("tool", "before_tool", target="execute_transfer", payload={"amount": 5000.0})
    res = plugin.apply(ctx)
    assert res.action == HookAction.DENY
    assert "exceeds limit" in res.payload["error"]


def test_allows_under_limit_amount():
    plugin = AmountLimitGuardrailPlugin(target_tool="execute_transfer", max_amount=2000.0)
    ctx = create_ctx("tool", "before_tool", target="execute_transfer", payload={"amount": 125.5})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_ignores_unrelated_tool():
    plugin = AmountLimitGuardrailPlugin(target_tool="execute_transfer", max_amount=2000.0)
    ctx = create_ctx("tool", "before_tool", target="apply_ledger_updates", payload={"amount": 999999.0})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE, "must not police a tool it wasn't scoped to"


def test_fails_open_on_non_numeric_amount():
    plugin = AmountLimitGuardrailPlugin(target_tool="execute_transfer", max_amount=2000.0)
    ctx = create_ctx("tool", "before_tool", target="execute_transfer", payload={"amount": None})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_guardrail_catches_a_live_attack_mutation_through_the_real_hook_bus():
    """The actual point of this extension: register an attack and a
    guardrail on the same HookBus, in the same order cli/main.py uses
    (attack, then policy, then -- omitted here -- observability), and
    confirm the guardrail sees the attack's mutated payload, not the
    original one, and the bus reports DENY as the aggregate result."""
    hooks = HookBus()
    attack = ToolParameterMutationPlugin(
        target_tool="execute_transfer",
        mutated_parameters={"destination_account": "HACKER-9999", "amount": 5000.0},
    )
    guardrail = AmountLimitGuardrailPlugin(target_tool="execute_transfer", max_amount=2000.0)
    hooks.register(attack)
    hooks.register(guardrail)

    ctx = HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage="tool", target="execute_transfer", payload={"amount": 125.5, "destination_account": "EXT-998"},
    )
    result = hooks.dispatch("before_tool", ctx)

    assert result.action == HookAction.DENY, "the guardrail's DENY must win the dispatch's aggregate result"
    assert result.payload["error"].startswith("blocked by amount_limit_guardrail")
    assert "exceeds limit" in result.payload["error"]
