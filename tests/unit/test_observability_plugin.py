from mantis.hooks import HookContext
from mantis.observability.plugin import ObservabilityPlugin
from mantis.observability.events import EventType, WorkflowEvent, AgentEvent, ToolEvent, SecurityEvent


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

    plugin.apply(_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "compliance_agent"}))

    route_events = [e for e in writer.events if isinstance(e, WorkflowEvent) and e.event_type == EventType.ROUTE_DECISION]
    assert len(route_events) == 1
    assert route_events[0].target == "compliance_agent"


def test_route_decision_survives_selective_mode():
    writer = FakeTraceWriter()
    plugin = ObservabilityPlugin(writer, mode="selective")

    plugin.apply(_ctx("tool", "before_tool", target="transfer_to_agent", payload={"agent_name": "decision_making_agent"}))

    route_events = [e for e in writer.events if isinstance(e, WorkflowEvent) and e.event_type == EventType.ROUTE_DECISION]
    assert len(route_events) == 1
