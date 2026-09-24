"""Post-Paper Extension: security mechanism plugins (coding plan §11).

Covers risk_aware_routing_guard's own logic in isolation, its
registration, and -- the actual point of a "defense evaluated through the
same framework" -- that it correctly DENIES route_confusion's live
reroute through the real HookBus, seeing the attack's already-mutated
agent_name, not the original one. Mirrors
test_amount_limit_guardrail.py's shape.
"""
from unittest.mock import patch

from mantis.hooks import HookBus, HookContext, HookAction
from mantis.plugins.policies.routing_guard import RiskAwareRoutingGuardPlugin
from mantis.plugins.attacks.route_confusion import RouteConfusionPlugin
from mantis.core.registry import plugin_registry


def create_ctx(stage, specific_hook, target=None, source=None, payload=None):
    return HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage=stage, target=target, source=source, payload=payload or {},
        metadata={"specific_hook": specific_hook}
    )


def test_risk_aware_routing_guard_registered():
    cls = plugin_registry.get("risk_aware_routing_guard")
    assert cls is RiskAwareRoutingGuardPlugin


def test_denies_reroute_when_transaction_risk_is_at_or_above_threshold():
    plugin = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow", transaction_id="TXN-1001", risk_threshold=50.0
    )
    ctx = create_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "customer_service_chatbot_workflow"})
    with patch("mantis.banking.infra.api_client.api_client.get_transaction", return_value={"risk_score": 65}):
        res = plugin.apply(ctx)
    assert res.action == HookAction.DENY
    assert "blocked by risk_aware_routing_guard" in res.payload["error"]


def test_allows_reroute_when_transaction_risk_is_below_threshold():
    plugin = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow", transaction_id="TXN-1002", risk_threshold=50.0
    )
    ctx = create_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "customer_service_chatbot_workflow"})
    with patch("mantis.banking.infra.api_client.api_client.get_transaction", return_value={"risk_score": 10}):
        res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_ignores_a_transfer_to_a_different_destination():
    plugin = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow", transaction_id="TXN-1001", risk_threshold=50.0
    )
    ctx = create_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "front_office_transaction_workflow"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE, "must not police a route it wasn't scoped to block"


def test_ignores_non_transfer_tool_calls():
    plugin = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow", transaction_id="TXN-1001", risk_threshold=50.0
    )
    ctx = create_ctx("tool", "before_tool", target="execute_transfer", payload={"agent_name": "customer_service_chatbot_workflow"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE


def test_fails_open_when_the_backend_is_unreachable():
    from mantis.banking.infra.api_client import BankingApiError
    plugin = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow", transaction_id="TXN-1001", risk_threshold=50.0
    )
    ctx = create_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "customer_service_chatbot_workflow"})
    with patch("mantis.banking.infra.api_client.api_client.get_transaction", side_effect=BankingApiError("backend down")):
        res = plugin.apply(ctx)
    assert res.action == HookAction.CONTINUE, "an unreachable backend is an infrastructure failure, not grounds to block a route"


def test_guard_blocks_a_live_route_confusion_mutation_through_the_real_hook_bus():
    """The actual point of this extension: register route_confusion and the
    guard on the same HookBus, in the same order cli/main.py uses (attack,
    then policy), and confirm the guard sees the attack's mutated
    agent_name -- not the router's original, legitimate destination -- and
    the bus reports DENY as the aggregate result."""
    hooks = HookBus()
    attack = RouteConfusionPlugin(
        intercepted_route="front_office_transaction_workflow",
        forced_destination="customer_service_chatbot_workflow",
    )
    guard = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow", transaction_id="TXN-1001", risk_threshold=50.0
    )
    hooks.register(attack)
    hooks.register(guard)

    ctx = HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage="tool", target="transfer_to_agent",
        payload={"agent_name": "front_office_transaction_workflow"},
        metadata={"specific_hook": "before_tool"},
    )
    with patch("mantis.banking.infra.api_client.api_client.get_transaction", return_value={"risk_score": 65}):
        result = hooks.dispatch("before_tool", ctx)

    assert result.action == HookAction.DENY, "the guard's DENY must win the dispatch's aggregate result"
    assert "blocked by risk_aware_routing_guard" in result.payload["error"]


def test_redirects_instead_of_denying_when_redirect_to_is_set():
    """Regression/feature test: an earlier deny-only version of this guard
    was live-verified to block the malicious reroute without making the
    workflow retry the compliant destination -- the router just reported
    the block and the run ended without reaching manual_review. redirect_to
    closes that gap by mutating the call to the legitimate destination
    instead of denying it outright."""
    plugin = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow",
        transaction_id="TXN-1001",
        risk_threshold=50.0,
        redirect_to="front_office_transaction_workflow",
    )
    ctx = create_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "customer_service_chatbot_workflow"})
    with patch("mantis.banking.infra.api_client.api_client.get_transaction", return_value={"risk_score": 65}):
        res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    assert res.payload["agent_name"] == "front_office_transaction_workflow"


def test_redirect_through_the_real_hook_bus_lets_the_call_actually_proceed_to_the_compliant_destination():
    """The real point of redirect_to: unlike a DENY (which stops the tool
    call from proceeding at all), a MUTATE lets the real transfer_to_agent
    call still go through -- to the corrected destination -- so the
    workflow can actually continue down the compliant path instead of
    simply failing to continue down the wrong one."""
    hooks = HookBus()
    attack = RouteConfusionPlugin(
        intercepted_route="front_office_transaction_workflow",
        forced_destination="customer_service_chatbot_workflow",
    )
    guard = RiskAwareRoutingGuardPlugin(
        blocked_destination="customer_service_chatbot_workflow",
        transaction_id="TXN-1001",
        risk_threshold=50.0,
        redirect_to="front_office_transaction_workflow",
    )
    hooks.register(attack)
    hooks.register(guard)

    ctx = HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage="tool", target="transfer_to_agent",
        payload={"agent_name": "front_office_transaction_workflow"},
        metadata={"specific_hook": "before_tool"},
    )
    with patch("mantis.banking.infra.api_client.api_client.get_transaction", return_value={"risk_score": 65}):
        result = hooks.dispatch("before_tool", ctx)

    assert result.action == HookAction.MUTATE, "a redirect must let the dispatch continue as a mutation, not a block"
    assert result.payload["agent_name"] == "front_office_transaction_workflow"
