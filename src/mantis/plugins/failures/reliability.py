from mantis.hooks import HookContext, HookAction, HookResult
import time

class ReliabilityFailurePlugin:
    name = "reliability_failure"
    supported_stages = {"tool"}

    def __init__(self, target_tool: str, failure_type: str = "timeout", delay_ms: int = 5000, **kwargs):
        self.target_tool = target_tool
        self.failure_type = failure_type
        self.delay_ms = delay_ms
        self.kwargs = kwargs

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") == "before_tool" and ctx.target == self.target_tool:
            if self.failure_type == "delay":
                # A slow dependency, not a broken one: the call still
                # succeeds, just after the bus (not this plugin -- see
                # HookAction.DELAY in hooks/__init__.py) waits delay_ms.
                # Distinct from "timeout" below, which fails outright.
                return HookResult(action=HookAction.DELAY, delay_ms=self.delay_ms)

            if self.failure_type == "timeout":
                # Simulate a timeout
                time.sleep(self.delay_ms / 1000.0)
                return HookResult(action=HookAction.ERROR, error_message=f"Timeout of {self.delay_ms}ms exceeded for tool {self.target_tool}")

            elif self.failure_type == "malformed":
                # Return malformed JSON directly, simulating an API breakage
                return HookResult(action=HookAction.DENY, payload={"error": "Malformed JSON from upstream server: {invalid_syntax"})

        return HookResult(action=HookAction.CONTINUE)
