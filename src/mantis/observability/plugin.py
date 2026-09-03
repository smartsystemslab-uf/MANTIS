import hashlib
import json

from mantis.hooks import HookContext, HookResult, HookAction
from mantis.observability.events import (
    EventType,
    WorkflowEvent,
    AgentEvent,
    ToolEvent,
    InteractionEvent,
)
from mantis.observability.artifacts import TraceArtifactWriter
from mantis.observability.otel import get_tracer
from mantis.banking.tool_semantics import get_tool_semantics
from typing import Optional, Any
import time

def _hash_payload(payload: Optional[dict]) -> Optional[str]:
    if not payload:
        return None
    try:
        canonical = json.dumps(payload, sort_keys=True, default=str)
    except Exception:
        canonical = str(payload)
    return hashlib.sha256(canonical.encode()).hexdigest()

class ObservabilityPlugin:
    name = "observability_plugin"
    supported_stages = {"input", "agent", "interaction", "tool", "output"}

    def __init__(self, trace_writer: TraceArtifactWriter):
        self.trace_writer = trace_writer
        self.tracer = get_tracer()
        # To calculate latency, we can keep track of start times
        self.start_times = {}

    def apply(self, ctx: HookContext) -> HookResult:
        stage = ctx.metadata.get("specific_hook")
        # We record everything asynchronously but HookBus dispatch is synchronous
        # Here we just parse ctx and write to trace_writer
        try:
            self._handle_event(stage, ctx)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Observability failed to log event: {e}")

        return HookResult(action=HookAction.CONTINUE)

    def _handle_event(self, stage: str, ctx: HookContext):
        event: Optional[Any] = None
        now_ms = time.time() * 1000
        domain = ctx.metadata.get("business_domain")
        workflow_type = ctx.metadata.get("scenario")
        is_error = bool(ctx.metadata.get("error"))

        if stage == "before_input":
            event = WorkflowEvent(
                event_type=EventType.WORKFLOW_START,
                run_id=ctx.run_id,
                workflow_id=ctx.workflow_id,
                business_domain=domain,
                workflow_type=workflow_type,
                source=ctx.source,
                target=ctx.target
            )
        elif stage in ("before_output", "after_output"):
            event = WorkflowEvent(
                event_type=EventType.WORKFLOW_END,
                run_id=ctx.run_id,
                workflow_id=ctx.workflow_id,
                business_domain=domain,
                workflow_type=workflow_type,
                outcome=ctx.payload.get("status") if ctx.payload else None
            )
            # Only the final after_output marks the workflow as actually
            # finished; before_output shares the same outcome preview so a
            # leakage/redaction plugin registered on "output" can see it.
            if stage == "before_output":
                self.trace_writer.write_event(event)
                event = None
        elif stage == "before_agent":
            self.start_times[f"agent_{ctx.target}"] = now_ms
            event = AgentEvent(
                event_type=EventType.AGENT_START,
                run_id=ctx.run_id,
                agent_id=ctx.target or "unknown"
            )
        elif stage == "after_agent":
            start = self.start_times.get(f"agent_{ctx.target or ctx.source}", now_ms)
            latency = now_ms - start
            event = AgentEvent(
                event_type=EventType.AGENT_ERROR if is_error else EventType.AGENT_END,
                run_id=ctx.run_id,
                agent_id=ctx.target or ctx.source or "unknown",
                latency_ms=latency,
            )
        elif stage == "before_message":
            event = InteractionEvent(
                event_type=EventType.MESSAGE_SEND,
                run_id=ctx.run_id,
                agent_id=ctx.source or "unknown",
                business_domain=domain,
                content_hash=_hash_payload(ctx.payload),
                content_length=len(str(ctx.payload)) if ctx.payload else 0,
            )
            self.start_times["interaction"] = now_ms
        elif stage == "after_message":
            start = self.start_times.get("interaction", now_ms)
            event = InteractionEvent(
                event_type=EventType.MESSAGE_RECEIVE,
                run_id=ctx.run_id,
                agent_id=ctx.target or "unknown",
                business_domain=domain,
                content_hash=_hash_payload(ctx.payload),
                content_length=len(str(ctx.payload)) if ctx.payload else 0,
                latency_ms=now_ms - start,
            )
        elif stage == "before_tool":
            self.start_times[f"tool_{ctx.target}"] = now_ms
            semantics = get_tool_semantics(ctx.target)
            event = ToolEvent(
                event_type=EventType.TOOL_CALL,
                run_id=ctx.run_id,
                tool_name=ctx.target or "unknown",
                arguments=ctx.payload,  # arguments_hash is auto-derived by ToolEvent
                business_domain=domain,
                **semantics,
            )
        elif stage == "after_tool":
            start = self.start_times.get(f"tool_{ctx.source}", now_ms)
            latency = now_ms - start
            semantics = get_tool_semantics(ctx.source)
            event = ToolEvent(
                event_type=EventType.TOOL_ERROR if is_error else EventType.TOOL_RESULT,
                run_id=ctx.run_id,
                tool_name=ctx.source or "unknown",
                business_domain=domain,
                latency_ms=latency,
                result=str(ctx.payload),
                **semantics,
            )

        if event:
            self.trace_writer.write_event(event)

            # Record OTel span for tools
            if isinstance(event, ToolEvent) and event.event_type == EventType.TOOL_CALL:
                with self.tracer.start_as_current_span(f"tool_call:{event.tool_name}") as span:
                    span.set_attribute("mantis.run_id", event.run_id)
                    span.set_attribute("mantis.tool_name", event.tool_name)
                    if event.arguments_hash:
                        span.set_attribute("mantis.arguments_hash", event.arguments_hash)
