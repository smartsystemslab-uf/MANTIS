"""Amount-limit guardrail (Post-Paper Extension, coding plan §11:
"Security mechanism plugins -- guardrails, policy checks, isolation, rate
limits, and response filters evaluated through the same experiment
framework").

The first concrete PolicyPlugin (see plugins/policies/__init__.py, which
was interface-only for Paper 1). Registers into the same HookBus, at the
same "tool" control point, through the identical apply(ctx) -> HookResult
contract every attack plugin already uses -- a defense evaluated through
the same framework as the attacks, not a bolted-on special case.

Denies a tool call whose declared amount field exceeds a configured limit,
before the call reaches the real banking backend. Registering it alongside
an attack plugin (e.g. tool_mutation raising a transfer's amount) and
seeing it DENY the mutated call is the point: see
configs/extensions/guardrail_blocks_tool_mutation.yaml.
"""
from mantis.hooks import HookContext, HookAction, HookResult


class AmountLimitGuardrailPlugin:
    name = "amount_limit_guardrail"
    supported_stages = {"tool"}

    def __init__(self, target_tool: str, max_amount: float, amount_field: str = "amount", **kwargs):
        self.target_tool = target_tool
        self.max_amount = max_amount
        self.amount_field = amount_field
        self.kwargs = kwargs

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") != "before_tool" or ctx.target != self.target_tool:
            return HookResult(action=HookAction.CONTINUE)

        raw_amount = (ctx.payload or {}).get(self.amount_field)
        try:
            amount = float(raw_amount)
        except (TypeError, ValueError):
            # Nothing to police if the tool call doesn't carry a numeric
            # amount at all -- fail open rather than block an unrelated or
            # malformed call this guardrail was never scoped to evaluate.
            return HookResult(action=HookAction.CONTINUE)

        if amount > self.max_amount:
            return HookResult(
                action=HookAction.DENY,
                payload={
                    "error": (
                        f"blocked by amount_limit_guardrail: {self.target_tool}."
                        f"{self.amount_field}={amount} exceeds limit {self.max_amount}"
                    )
                },
            )

        return HookResult(action=HookAction.CONTINUE)
