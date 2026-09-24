"""Rate-limit guardrail (Post-Paper Extension, coding plan §11: "Security
mechanism plugins -- guardrails, policy checks, isolation, rate limits, and
response filters evaluated through the same experiment framework").

Caps how many times a tool may be called -- overall, per time window, or
per distinct value of one argument -- and DENYs the call that would exceed
the cap. Registered after any attack plugin (like every policy plugin), so
`group_by` sees the argument value the attack actually produced, not the
agent's original one.

The motivating case is a runaway or adversarially induced loop, not an
ordinary over-quota caller: live testing of the extended attack library
found that hijacking the root agent's hand-off makes the downstream router
try to send the request back, the hijack rewrites that hand-back too, and
the framework crashes on the resulting self-transfer. Capping hand-offs per
destination (`target_tool: transfer_to_agent`, `group_by: agent_name`,
`max_calls: 1`) stops the loop at the second attempt and lets the run end
with a recorded result instead of an unhandled exception.
"""
import time
from collections import defaultdict, deque

from mantis.hooks import HookContext, HookAction, HookResult


def _now() -> float:
    return time.monotonic()


class RateLimitGuardrailPlugin:
    name = "rate_limit_guardrail"
    supported_stages = {"tool"}

    def __init__(
        self,
        max_calls: int,
        target_tool: str | None = None,
        window_seconds: float | None = None,
        group_by: str | None = None,
        **kwargs,
    ):
        if max_calls < 1:
            raise ValueError("max_calls must be at least 1")
        self.max_calls = max_calls
        self.target_tool = target_tool  # None = every tool
        self.window_seconds = window_seconds  # None = the whole run
        self.group_by = group_by
        self.kwargs = kwargs
        # One call-timestamp history per (tool, group value).
        self._calls: dict[tuple, deque] = defaultdict(deque)

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") != "before_tool":
            return HookResult(action=HookAction.CONTINUE)
        if self.target_tool is not None and ctx.target != self.target_tool:
            return HookResult(action=HookAction.CONTINUE)

        group_value = (ctx.payload or {}).get(self.group_by) if self.group_by else None
        key = (ctx.target, group_value)
        history = self._calls[key]
        now = _now()
        if self.window_seconds is not None:
            while history and now - history[0] > self.window_seconds:
                history.popleft()

        if len(history) >= self.max_calls:
            scope = f" for {self.group_by}={group_value!r}" if self.group_by else ""
            span = f" within {self.window_seconds}s" if self.window_seconds is not None else " in this run"
            return HookResult(
                action=HookAction.DENY,
                payload={
                    "error": (
                        f"blocked by rate_limit_guardrail: {ctx.target} already called "
                        f"{len(history)} time(s){scope}{span} (limit {self.max_calls})"
                    )
                },
            )
        history.append(now)
        return HookResult(action=HookAction.CONTINUE)
