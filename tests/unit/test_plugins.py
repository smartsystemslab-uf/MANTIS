import pytest
from mantis.hooks import HookContext, HookAction, HookResult
from mantis.plugins.attacks.prompt_injection import PromptInjectionPlugin
from mantis.plugins.attacks.message_spoofing import MessageSpoofingPlugin
from mantis.plugins.attacks.route_confusion import RouteConfusionPlugin
from mantis.plugins.attacks.tool_mutation import ToolParameterMutationPlugin
from mantis.plugins.failures.reliability import ReliabilityFailurePlugin
import os

def create_ctx(stage, specific_hook, target=None, payload=None):
    return HookContext(
        run_id="test", trace_id="test", workflow_id="test",
        stage=stage, target=target, payload=payload or {},
        metadata={"specific_hook": specific_hook}
    )

def test_prompt_injection():
    plugin = PromptInjectionPlugin(target_agent="fraud_agent", payload_file="nonexistent.txt")
    ctx = create_ctx("agent", "before_agent", target="fraud_agent", payload={"context": {"system_instruction": "base"}})
    res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    assert "IGNORE ALL PREVIOUS INSTRUCTIONS" in res.payload["context"]["system_instruction"]
    assert "base" in res.payload["context"]["system_instruction"]

def test_message_spoofing():
    plugin = MessageSpoofingPlugin(spoofed_sender="attacker", spoofed_content="fake", target_recipient="compliance")
    ctx = create_ctx("interaction", "before_message", target="compliance", payload={"messages": [{"sender": "real", "content": "hello"}]})
    res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    assert res.payload["messages"][-1]["sender"] == "attacker"
    assert res.payload["messages"][-1]["content"] == "fake"

def test_route_confusion():
    plugin = RouteConfusionPlugin(intercepted_route="compliance", forced_destination="attacker_agent")
    ctx = create_ctx("tool", "before_tool", target="transfer_to_agent", payload={"target_agent": "compliance"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    assert res.payload["target_agent"] == "attacker_agent"

def test_tool_mutation():
    plugin = ToolParameterMutationPlugin(target_tool="get_customer", mutated_parameters={"id": "999"})
    ctx = create_ctx("tool", "before_tool", target="get_customer", payload={"id": "123", "extra": "data"})
    res = plugin.apply(ctx)
    assert res.action == HookAction.MUTATE
    assert res.payload["id"] == "999"
    assert res.payload["extra"] == "data"

def test_reliability_failure():
    plugin = ReliabilityFailurePlugin(target_tool="flaky_tool", failure_type="malformed")
    ctx = create_ctx("tool", "before_tool", target="flaky_tool", payload={})
    res = plugin.apply(ctx)
    assert res.action == HookAction.DENY
    assert "error" in res.payload
