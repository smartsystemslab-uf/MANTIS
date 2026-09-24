"""Risk-aware routing guard (Post-Paper Extension, coding plan §11:
"Security mechanism plugins -- guardrails, policy checks, isolation, rate
limits, and response filters evaluated through the same experiment
framework").

Unlike amount_limit_guardrail (a threshold check on a tool call's own
arguments), this plugin targets route confusion specifically -- the one
attack in the shipped catalog that currently succeeds 5/5 with zero
defense anywhere in the repo (configs/attacks/wp5_route_confusion.yaml).

A generic "is this transfer_to_agent target a legitimate destination"
check cannot catch route confusion: its forced destination
(customer_service_chatbot_workflow) *is* a legitimate destination in
general -- front_office_router really does route ordinary, approved
service requests there. The attack's whole trick is picking the wrong one
of two valid routes for a transaction that specifically should not take
that path, not routing somewhere invalid. So this plugin does not check
"is this destination allowed" -- it independently re-checks the specific
transaction's own real risk score (the same data
get_transaction_context/api_client.get_transaction already exposes,
computed by the banking backend, not by whatever the LLM router decided)
and denies the reroute if that transaction is still too risky to skip
review for, regardless of what the router was tricked into deciding.
"""
from mantis.hooks import HookContext, HookAction, HookResult


class RiskAwareRoutingGuardPlugin:
    name = "risk_aware_routing_guard"
    supported_stages = {"tool"}

    def __init__(
        self,
        blocked_destination: str,
        transaction_id: str,
        risk_threshold: float = 50.0,
        redirect_to: str | None = None,
        **kwargs,
    ):
        self.blocked_destination = blocked_destination
        self.transaction_id = transaction_id
        self.risk_threshold = risk_threshold
        # Optional recovery path: live verification of an earlier, deny-only
        # version of this guard found that blocking the malicious reroute
        # does not, by itself, make the workflow retry the compliant
        # destination -- the router just reports the block and the run ends
        # without ever reaching manual review. When set, this redirects the
        # real transfer_to_agent call to the given (legitimate) destination
        # instead of denying it outright, so the workflow actually continues
        # down the correct path rather than merely failing to continue down
        # the wrong one. Left unset, behavior is unchanged from before (a
        # bare DENY), so existing configs are unaffected.
        self.redirect_to = redirect_to
        self.kwargs = kwargs

    def apply(self, ctx: HookContext) -> HookResult:
        if ctx.metadata.get("specific_hook") != "before_tool" or ctx.target != "transfer_to_agent":
            return HookResult(action=HookAction.CONTINUE)
        if (ctx.payload or {}).get("agent_name") != self.blocked_destination:
            return HookResult(action=HookAction.CONTINUE)

        # Lazy import: mantis.banking.infra.api_client pulls in
        # mantis.banking.settings, whose module-level `settings` singleton
        # reads UF_NAVIGATOR_API_KEY etc. from the environment at *import*
        # time. This plugin is registered from mantis.core.registry, which
        # cli/main.py imports at module load -- before its own
        # load_dotenv() call, which only runs inside run_experiment(). An
        # eager, top-level import here would read the environment before
        # .env is loaded, silently baking in a missing-credentials
        # settings object for the whole process (a real regression this
        # plugin caused and this comment exists to stop from recurring).
        from mantis.banking.infra.api_client import api_client, BankingApiError

        try:
            risk_score = api_client.get_transaction(self.transaction_id).get("risk_score")
        except BankingApiError:
            # Fail open: this guard's whole job is a *second opinion* from
            # the real backend -- if the backend can't be reached at all,
            # that's an infrastructure failure unrelated to the routing
            # decision itself, not grounds to block a route that might be
            # perfectly legitimate.
            return HookResult(action=HookAction.CONTINUE)

        if risk_score is not None and risk_score >= self.risk_threshold:
            if self.redirect_to:
                redirected_payload = dict(ctx.payload or {})
                redirected_payload["agent_name"] = self.redirect_to
                return HookResult(action=HookAction.MUTATE, payload=redirected_payload)
            return HookResult(
                action=HookAction.DENY,
                payload={
                    "error": (
                        f"blocked by risk_aware_routing_guard: transaction {self.transaction_id} "
                        f"has risk_score={risk_score} (>= {self.risk_threshold}); routing to "
                        f"'{self.blocked_destination}' is not permitted while this transaction "
                        f"still requires fraud/compliance review"
                    )
                },
            )
        return HookResult(action=HookAction.CONTINUE)
