from mantis.hooks import HookContext
from mantis.observability.plugin import ObservabilityPlugin
from mantis.observability.events import EventType, WorkflowEvent, AgentEvent, ToolEvent, InteractionEvent, SecurityEvent


class FakeTraceWriter:
    def __init__(self):
        self.events = []

    def write_event(self, event):
        self.events.append(event)


def _ctx(stage, specific_hook, target=None, source=None, payload=None, extra_metadata=None):
    metadata = {"specific_hook": specific_hook, "business_domain": "front_office", "scenario": "front_office_monitoring"}
    if extra_metadata:
        metadata.update(extra_metadata)
    return HookContext(
        run_id="run-1", trace_id="run-1", workflow_id="front_office_monitoring",
        stage=stage, target=target, source=source, payload=payload or {}, metadata=metadata,
    )


def test_full_mode_emits_agent_and_tool_events():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="full")

    plugin.apply(_ctx("agent", "before_agent", target="fraud_detection_agent"))
    plugin.apply(_ctx("tool", "before_tool", target="get_customer_context", payload={"customer_id": "CUST-001"}))

    types_seen = [e.event_type for e in writer.events]
    assert EventType.AGENT_START in types_seen
    assert EventType.TOOL_CALL in types_seen


def test_selective_mode_suppresses_agent_and_message_events_but_keeps_tool_and_security():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="selective")

    plugin.apply(_ctx("agent", "before_agent", target="fraud_detection_agent"))
    plugin.apply(_ctx("interaction", "before_message", source="fraud_detection_agent"))
    plugin.apply(_ctx("tool", "before_tool", target="get_customer_context", payload={"customer_id": "CUST-001"}))
    plugin.apply(_ctx(
        "tool", "before_tool", target="execute_transfer", payload={"amount": 1},
        extra_metadata={"security_actions": [{"plugin": "tool_mutation", "action": "mutate"}]},
    ))

    types_seen = [e.event_type for e in writer.events]
    assert EventType.AGENT_START not in types_seen
    assert EventType.MESSAGE_SEND not in types_seen
    assert EventType.TOOL_CALL in types_seen
    assert EventType.ATTACK_INJECTED in types_seen


def test_transfer_to_agent_emits_route_decision():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="full")

    plugin.apply(_ctx(
        "tool", "before_tool", source="teller_agent", target="transfer_to_agent",
        payload={"agent_name": "compliance_agent"},
    ))

    route_events = [e for e in writer.events if isinstance(e, WorkflowEvent) and e.event_type == EventType.ROUTE_DECISION]
    assert len(route_events) == 1
    assert route_events[0].source == "teller_agent"
    assert route_events[0].target == "compliance_agent"


def test_tool_call_id_propagates_to_tool_call_and_result_events():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="full")

    plugin.apply(_ctx(
        "tool", "before_tool", source="teller_agent", target="get_customer_context",
        payload={"customer_id": "CUST-001"}, extra_metadata={"tool_call_id": "fc-123"},
    ))
    plugin.apply(_ctx(
        "tool", "after_tool", source="get_customer_context", target="teller_agent",
        payload={"result": "ok"}, extra_metadata={"tool_call_id": "fc-123"},
    ))

    tool_events = [e for e in writer.events if isinstance(e, ToolEvent)]
    assert len(tool_events) == 2
    assert all(e.tool_call_id == "fc-123" for e in tool_events)


def test_invocation_id_propagates_to_interaction_events():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="full")

    plugin.apply(_ctx(
        "interaction", "before_message", source="teller_agent", target="model",
        payload={"messages": []}, extra_metadata={"invocation_id": "inv-1"},
    ))

    interaction_events = [e for e in writer.events if isinstance(e, InteractionEvent)]
    assert len(interaction_events) == 1
    assert interaction_events[0].invocation_id == "inv-1"


def test_route_decision_survives_selective_mode():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="selective")

    plugin.apply(_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "decision_making_agent"}))

    route_events = [e for e in writer.events if isinstance(e, WorkflowEvent) and e.event_type == EventType.ROUTE_DECISION]
    assert len(route_events) == 1
