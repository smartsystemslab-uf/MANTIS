"""Action isolation (Post-Paper Extension, coding plan §11: "Security
mechanism plugins -- guardrails, policy checks, isolation, rate limits, and
response filters evaluated through the same experiment framework").

Contains a run's blast radius: while active, tools with a chosen kind of
side effect cannot execute, whatever any agent -- or any attack that
rewrote its arguments -- asks for. This is the "shadow mode" / dry-run
posture a bank would use to let agents *propose* actions that a human or a
separate system then performs: reads and reasoning proceed normally, state
changes are refused.

It is deliberately not a per-domain allow-list of who may call what (that is
a different mechanism); it isolates by *effect*, using the same banking tool
metadata (`operation_type`, `financial_side_effect`) the observability layer
already records for every tool call.

  blocked_effects: which effects are contained. "financial_side_effect"
      (default) blocks tools that move money or post to the ledger;
      "write" blocks every state-changing tool.
  allow_tools: tools exempted from isolation.

Because it cannot tell a legitimate call from an attacked one, isolating an
effect also stops the legitimate use of it -- that is the point of the mode,
and a workflow that depends on the blocked step downstream will see the
denial as a failed step.
"""
from mantis.banking.tool_semantics import get_tool_semantics
from mantis.hooks import HookContext, HookAction, HookResult

_KNOWN_EFFECTS = {"financial_side_effect", "write"}


class ActionIsolationPlugin:
    name = "action_isolation"
    supported_stages = {"tool"}

    def __init__(self, blocked_effects: list[str] | None = None, allow_tools: list[str] | None = None, **kwargs):
        self.blocked_effects = list(blocked_effects) if blocked_effects else ["financial_side_effect"]
        unknown = set(self.blocked_effects) - _KNOWN_EFFECTS
        if unknown:
            raise ValueError(f"unknown blocked_effects {sorted(unknown)}; expected a subset of {sorted(_KNOWN_EFFECTS)}")
        self.allow_tools = set(allow_tools or [])
        self.kwargs = kwargs

    def _blocked_because(self, tool_name: str) -> str | None:
        sem = get_tool_semantics(tool_name)
        if "financial_side_effect" in self.blocked_effects and sem.get("financial_side_effect"):
            return "moves money or posts to the ledger"
        if "write" in self.blocked_effects and sem.get("operation_type") == "write":
            return "changes persisted state"
        return None

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") != "before_tool" or not ctx.target:
            return HookResult(action=HookAction.CONTINUE)
        if ctx.target in self.allow_tools:
            return HookResult(action=HookAction.CONTINUE)
        reason = self._blocked_because(ctx.target)
        if reason is None:
            return HookResult(action=HookAction.CONTINUE)
        return HookResult(
            action=HookAction.DENY,
            payload={
                "error": (
                    f"blocked by action_isolation: {ctx.target} {reason}, and this run is isolated "
                    f"(blocked effects: {', '.join(self.blocked_effects)})"
                )
            },
        )
