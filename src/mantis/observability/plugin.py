from mantis.core.hooks import HookContext, HookResult, HookAction
from mantis.observability.events import (
    EventType,
    ExperimentEvent,
    WorkflowEvent,
    AgentEvent,
    ToolEvent,
    SecurityEvent
)
from mantis.observability.artifacts import TraceArtifactWriter
from mantis.observability.otel import get_tracer
from typing import Optional, Any
import time
from datetime import datetime

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
        
        if stage == "before_input":
            event = WorkflowEvent(
                event_type=EventType.WORKFLOW_START,
                run_id=ctx.run_id,
                workflow_id=ctx.workflow_id,
                source=ctx.source,
                target=ctx.target
            )
        elif stage == "after_output":
            event = WorkflowEvent(
                event_type=EventType.WORKFLOW_END,
                run_id=ctx.run_id,
                workflow_id=ctx.workflow_id,
                outcome=ctx.payload.get("status") if ctx.payload else None
            )
        elif stage == "before_agent":
            self.start_times[f"agent_{ctx.target}"] = now_ms
            event = AgentEvent(
                event_type=EventType.AGENT_START,
                run_id=ctx.run_id,
                agent_id=ctx.target or "unknown"
            )
        elif stage == "before_tool":
            self.start_times[f"tool_{ctx.target}"] = now_ms
            event = ToolEvent(
                event_type=EventType.TOOL_CALL,
                run_id=ctx.run_id,
                tool_name=ctx.target or "unknown",
                arguments=ctx.payload
            )
        elif stage == "after_tool":
            start = self.start_times.get(f"tool_{ctx.source}", now_ms)
            latency = now_ms - start
            event = ToolEvent(
                event_type=EventType.TOOL_RESULT,
                run_id=ctx.run_id,
                tool_name=ctx.source or "unknown",
                latency_ms=latency,
                result=str(ctx.payload)
            )

        if event:
            self.trace_writer.write_event(event)
            
            # Record OTel span for tools
            if isinstance(event, ToolEvent) and event.event_type == EventType.TOOL_CALL:
                with self.tracer.start_as_current_span(f"tool_call:{event.tool_name}") as span:
                    span.set_attribute("mantis.run_id", event.run_id)
                    span.set_attribute("mantis.tool_name", event.tool_name)
                    if event.arguments:
                        span.set_attribute("mantis.arguments", str(event.arguments))
